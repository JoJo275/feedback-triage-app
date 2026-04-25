"""Pre-commit hooks collector — installed hooks, stages, and versions.

Discovers:
- Hooks defined in .pre-commit-config.yaml
- Hook stages (pre-commit, commit-msg, pre-push, manual)
- pre-commit tool version
- Installation status
"""

from __future__ import annotations

import re
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


def _get_precommit_version() -> str | None:
    """Get installed pre-commit version."""
    exe = shutil.which("pre-commit")
    if not exe:
        return None
    try:
        result = subprocess.run(  # nosec B603
            [exe, "--version"],
            capture_output=True,
            text=True,
            timeout=10.0,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def _check_hooks_installed(repo_root: Path) -> dict[str, bool]:
    """Check which hook types are installed in .git/hooks/."""
    hooks_dir = repo_root / ".git" / "hooks"
    installed: dict[str, bool] = {}
    for stage in ("pre-commit", "commit-msg", "pre-push"):
        hook_file = hooks_dir / stage
        if hook_file.is_file():
            try:
                content = hook_file.read_text(encoding="utf-8", errors="replace")
                installed[stage] = "pre-commit" in content
            except OSError:
                installed[stage] = False
        else:
            installed[stage] = False
    return installed


def _parse_precommit_config(repo_root: Path) -> dict[str, Any]:
    """Parse .pre-commit-config.yaml to extract hooks and stages."""
    config_file = repo_root / ".pre-commit-config.yaml"
    if not config_file.is_file():
        return {"found": False, "repos": [], "hooks": [], "by_stage": {}}

    hooks: list[dict[str, Any]] = []
    try:
        content = config_file.read_text(encoding="utf-8")

        # Simple YAML parsing without PyYAML dependency
        current_repo = ""
        current_rev = ""
        in_hooks = False

        for line in content.splitlines():
            stripped = line.strip()

            # Track repo URL
            repo_match = re.match(r"-?\s*repo:\s*(.+)", stripped)
            if repo_match:
                current_repo = repo_match.group(1).strip()
                current_rev = ""
                in_hooks = False
                continue

            rev_match = re.match(r"rev:\s*(.+)", stripped)
            if rev_match:
                current_rev = rev_match.group(1).strip()
                continue

            if stripped == "hooks:":
                in_hooks = True
                continue

            if in_hooks:
                id_match = re.match(r"-?\s*id:\s*(.+)", stripped)
                if id_match:
                    hook_id = id_match.group(1).strip()
                    hooks.append(
                        {
                            "id": hook_id,
                            "repo": current_repo,
                            "rev": current_rev,
                            "stages": [],
                            "language": "",
                        }
                    )
                    continue

                stages_match = re.match(r"stages:\s*\[(.+)\]", stripped)
                if stages_match and hooks:
                    stages = [
                        s.strip().strip("'\"") for s in stages_match.group(1).split(",")
                    ]
                    hooks[-1]["stages"] = stages
                    continue

                lang_match = re.match(r"language:\s*(.+)", stripped)
                if lang_match and hooks:
                    hooks[-1]["language"] = lang_match.group(1).strip()
                    continue

        # Group by stage — store full hook dicts for template access
        by_stage: dict[str, list[dict[str, Any]]] = {
            "pre-commit": [],
            "commit-msg": [],
            "pre-push": [],
            "manual": [],
        }
        for hook in hooks:
            stages = hook.get("stages", [])
            if not stages:
                stages = ["pre-commit"]  # default stage
            for stage in stages:
                by_stage.setdefault(stage, []).append(hook)

        return {
            "found": True,
            "hooks": hooks,
            "total_hooks": len(hooks),
            "by_stage": {k: v for k, v in by_stage.items() if v},
        }
    except OSError:
        return {"found": False, "repos": [], "hooks": [], "by_stage": {}}


class PrecommitHooksCollector(BaseCollector):
    """Collect pre-commit hook configuration and installation status."""

    name = "precommit_hooks"
    timeout = 15.0

    @property
    def tier(self):  # type: ignore[override]
        return _get_tier().STANDARD

    def collect(self) -> dict[str, Any]:
        from _imports import find_repo_root

        repo_root = find_repo_root()

        version = _get_precommit_version()
        installed = _check_hooks_installed(repo_root)
        config = _parse_precommit_config(repo_root)

        return {
            "precommit_version": version,
            "precommit_available": version is not None,
            "hooks_installed": installed,
            "all_stages_installed": all(installed.values()) if installed else False,
            "config_found": config.get("found", False),
            "config": config,
            "total_hooks": config.get("total_hooks", 0),
            "by_stage": config.get("by_stage", {}),
            "hooks": config.get("hooks", []),
        }
