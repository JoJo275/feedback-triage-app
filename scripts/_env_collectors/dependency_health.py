"""Dependency health collector — outdated deps, vulnerabilities, licenses.

Discovers:
- Outdated packages via pip
- Known vulnerabilities (pip-audit if available)
- Dependency groups from pyproject.toml
"""

from __future__ import annotations

import json
import shutil
import subprocess  # nosec B404
from pathlib import Path
from typing import Any

from _env_collectors._base import BaseCollector

_tier = None


def _get_tier():  # type: ignore[no-untyped-def]
    global _tier
    if _tier is None:
        from _env_collectors import Tier

        _tier = Tier
    return _tier


def _get_outdated_packages() -> list[dict[str, str]]:
    """Get outdated packages using pip list --outdated."""
    pip_exe = shutil.which("pip")
    if not pip_exe:
        return []
    try:
        result = subprocess.run(  # nosec B603
            [pip_exe, "list", "--outdated", "--format=json"],
            capture_output=True,
            text=True,
            timeout=30.0,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass
    return []


def _run_pip_audit() -> dict[str, Any]:
    """Run pip-audit to check for known vulnerabilities."""
    audit_exe = shutil.which("pip-audit")
    if not audit_exe:
        return {"available": False, "vulnerabilities": []}
    try:
        result = subprocess.run(  # nosec B603
            [audit_exe, "--format=json", "--progress-spinner=off"],
            capture_output=True,
            text=True,
            timeout=60.0,
        )
        data = json.loads(result.stdout) if result.stdout.strip() else {}
        vulns = data.get("dependencies", [])
        vuln_list = [
            {
                "package": dep.get("name", ""),
                "version": dep.get("version", ""),
                "id": v.get("id", ""),
                "fix_versions": ", ".join(v.get("fix_versions", [])),
                "description": v.get("description", "")[:120],
            }
            for dep in vulns
            for v in dep.get("vulns", [])
        ]
        return {"available": True, "vulnerabilities": vuln_list}
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return {"available": True, "vulnerabilities": [], "error": "pip-audit failed"}


def _parse_dependency_groups(repo_root: Path) -> dict[str, list[str]]:
    """Parse dependency groups from pyproject.toml."""
    pyproject = repo_root / "pyproject.toml"
    if not pyproject.is_file():
        return {}
    try:
        import tomllib

        data = tomllib.loads(pyproject.read_bytes().decode("utf-8"))
        project = data.get("project", {})
        groups: dict[str, list[str]] = {}

        # Core dependencies
        core_deps = project.get("dependencies", [])
        if core_deps:
            groups["core"] = core_deps

        # Optional dependency groups
        groups |= project.get("optional-dependencies", {})

        return groups
    except (OSError, ImportError, ValueError):
        return {}


class DependencyHealthCollector(BaseCollector):
    """Collect dependency health information."""

    name = "dependency_health"
    timeout = 45.0

    @property
    def tier(self):  # type: ignore[override]
        return _get_tier().STANDARD

    def collect(self) -> dict[str, Any]:
        from _imports import find_repo_root

        repo_root = find_repo_root()

        outdated = _get_outdated_packages()
        audit = _run_pip_audit()
        dep_groups = _parse_dependency_groups(repo_root)

        # Classify outdated by severity
        security_pkgs = {"pip", "setuptools", "certifi", "urllib3", "cryptography"}
        critical = [p for p in outdated if p.get("name", "").lower() in security_pkgs]
        normal = [p for p in outdated if p.get("name", "").lower() not in security_pkgs]

        return {
            "outdated": outdated,
            "outdated_count": len(outdated),
            "critical_outdated": critical,
            "normal_outdated": normal,
            "audit": audit,
            "vulnerability_count": len(audit.get("vulnerabilities", [])),
            "pip_audit_available": audit.get("available", False),
            "dependency_groups": dep_groups,
            "total_groups": len(dep_groups),
        }
