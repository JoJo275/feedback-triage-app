"""Shared environment data-collection module.

Plugin-based collector system used by both the CLI (``env_inspect.py``)
and the web dashboard (``tools/dev-tools/env-dashboard/``).

Entry point::

    from _env_collectors import gather_env_info, Tier, RedactLevel

    data = gather_env_info(tier=Tier.STANDARD, redact_level=RedactLevel.SECRETS)
"""

from __future__ import annotations

import concurrent.futures
import logging
import time
from enum import Enum
from typing import Any

from _env_collectors._base import BaseCollector
from _env_collectors._redact import RedactLevel, redact

SCHEMA_VERSION = "1.0"


class Tier(Enum):
    """Data collection tier — controls how much data is gathered."""

    MINIMAL = "minimal"
    STANDARD = "standard"
    FULL = "full"


# Tier ordering for comparison
_TIER_ORDER = {Tier.MINIMAL: 0, Tier.STANDARD: 1, Tier.FULL: 2}


def _discover_collectors() -> list[type[BaseCollector]]:
    """Import and return all collector classes."""
    # Import each collector module to trigger registration
    from _env_collectors.ci_cd_status import CiCdStatusCollector
    from _env_collectors.container import ContainerCollector
    from _env_collectors.dependency_health import DependencyHealthCollector
    from _env_collectors.disk_workspace import DiskWorkspaceSizeCollector
    from _env_collectors.docs_status import DocsStatusCollector
    from _env_collectors.filesystem import FilesystemCollector
    from _env_collectors.git_info import GitInfoCollector
    from _env_collectors.hardware import HardwareCollector
    from _env_collectors.insights import InsightsCollector
    from _env_collectors.network import NetworkCollector
    from _env_collectors.packages import PackagesCollector
    from _env_collectors.path_analysis import PathAnalysisCollector
    from _env_collectors.pip_environments import PipEnvironmentsCollector
    from _env_collectors.precommit_hooks import PrecommitHooksCollector
    from _env_collectors.project import ProjectCollector
    from _env_collectors.project_commands import ProjectCommandsCollector
    from _env_collectors.runtimes import RuntimesCollector
    from _env_collectors.security import SecurityCollector
    from _env_collectors.system import SystemCollector
    from _env_collectors.venv import VenvCollector

    return [
        SystemCollector,
        HardwareCollector,
        RuntimesCollector,
        PathAnalysisCollector,
        ProjectCollector,
        ProjectCommandsCollector,
        GitInfoCollector,
        VenvCollector,
        PipEnvironmentsCollector,
        PackagesCollector,
        NetworkCollector,
        FilesystemCollector,
        SecurityCollector,
        ContainerCollector,
        PrecommitHooksCollector,
        CiCdStatusCollector,
        DependencyHealthCollector,
        DiskWorkspaceSizeCollector,
        DocsStatusCollector,
        InsightsCollector,  # Must be LAST — depends on other sections' data
    ]


def gather_env_info(
    *,
    tier: Tier = Tier.STANDARD,
    redact_level: RedactLevel = RedactLevel.SECRETS,
) -> dict[str, Any]:
    """Gather environment info from all registered collectors.

    Args:
        tier: Maximum data tier to collect (MINIMAL, STANDARD, FULL).
        redact_level: Redaction level to apply to collected data.

    Returns:
        A dict matching the stable schema (see SCHEMA_VERSION).
    """
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    sections: dict[str, Any] = {}
    warnings: list[dict[str, str]] = []

    collector_classes = _discover_collectors()
    max_tier = _TIER_ORDER[tier]

    log = logging.getLogger(__name__)

    # Separate InsightsCollector (runs last) from parallel collectors
    insights_cls = None
    eligible: list[type[BaseCollector]] = []
    for cls in collector_classes:
        if cls.__name__ == "InsightsCollector":
            insights_cls = cls
            continue
        if _TIER_ORDER.get(cls.tier, 0) > max_tier:
            continue
        eligible.append(cls)

    # Run all collectors in parallel (I/O-bound: subprocess calls, fs scans)
    def _run(cls: type[BaseCollector]) -> tuple[str, dict[str, Any]]:
        collector = cls()
        return collector.name, collector.safe_collect()

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(_run, cls) for cls in eligible]
        for future in concurrent.futures.as_completed(futures):
            try:
                name, result = future.result()
                sections[name] = result
            except Exception:
                log.exception("Parallel collector failed")

    # Derive insights from collected sections
    if insights_cls is not None and _TIER_ORDER.get(insights_cls.tier, 0) <= max_tier:
        ins = insights_cls()
        ins._sections = sections  # pass collected data
        result = ins.safe_collect()
        sections[ins.name] = result
        warnings = result.get("warnings", [])

    # Build summary from key sections
    summary = _build_summary(sections, warnings)

    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "meta": {
            "timestamp": timestamp,
            "tier": tier.value,
            "redact_level": redact_level.value,
        },
        "summary": summary,
        "warnings": warnings,
        "sections": sections,
    }

    # Apply redaction
    if redact_level != RedactLevel.NONE:
        report = redact(report, redact_level)

    return report


def _build_summary(
    sections: dict[str, Any], warnings: list[dict[str, str]]
) -> dict[str, Any]:
    """Build the top summary bar data from collected sections."""
    system = sections.get("system", {})
    runtimes = sections.get("runtimes", {})
    git = sections.get("git", {})
    container = sections.get("container", {})

    python_info = runtimes.get("python", {})

    return {
        "os": system.get("os", "unknown"),
        "hostname": system.get("hostname", "unknown"),
        "username": system.get("username", "unknown"),
        "shell": system.get("shell", "unknown"),
        "python_version": python_info.get("version", "unknown"),
        "git_repo_detected": git.get("repo_detected", False),
        "container_detected": container.get("detected", False),
        "warnings_count": len(warnings),
    }


__all__ = [
    "SCHEMA_VERSION",
    "BaseCollector",
    "RedactLevel",
    "Tier",
    "gather_env_info",
    "redact",
]
