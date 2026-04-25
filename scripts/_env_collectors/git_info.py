"""Git info collector — version, branch, dirty state, remote URLs."""

from __future__ import annotations

import re
import shutil
import subprocess  # nosec B404
from typing import Any

from _imports import find_repo_root

from _env_collectors._base import BaseCollector

_tier = None


def _get_tier():  # type: ignore[no-untyped-def]
    global _tier
    if _tier is None:
        from _env_collectors import Tier

        _tier = Tier
    return _tier


class GitInfoCollector(BaseCollector):
    """Collect Git version, branch, dirty state, and remote URLs."""

    name = "git"
    timeout = 10.0

    @property
    def tier(self):  # type: ignore[override]
        return _get_tier().MINIMAL

    def collect(self) -> dict[str, Any]:
        git_cmd = shutil.which("git")
        if not git_cmd:
            return {"available": False, "repo_detected": False}

        root = find_repo_root()
        info: dict[str, Any] = {"available": True, "path": git_cmd}

        # Version
        info["version"] = self._run_git(git_cmd, ["--version"], root)

        # Repo detection
        rc = subprocess.run(  # nosec B603
            [git_cmd, "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=root,
        )
        info["repo_detected"] = rc.returncode == 0

        if not info["repo_detected"]:
            return info

        # Branch
        branch = self._run_git(git_cmd, ["rev-parse", "--abbrev-ref", "HEAD"], root)
        info["branch"] = branch.strip() if branch else "unknown"

        # Dirty state
        dirty_rc = subprocess.run(  # nosec B603
            [git_cmd, "diff", "--quiet", "HEAD"],
            capture_output=True,
            timeout=5,
            cwd=root,
        )
        info["dirty"] = dirty_rc.returncode != 0

        # Stash count
        stash_out = self._run_git(git_cmd, ["stash", "list"], root)
        info["stash_count"] = len(stash_out.strip().splitlines()) if stash_out else 0

        # Remote URLs
        remotes_out = self._run_git(git_cmd, ["remote", "-v"], root)
        remotes: list[dict[str, str]] = []
        if remotes_out:
            for line in remotes_out.strip().splitlines():
                parts = line.split()
                if len(parts) >= 2:
                    remotes.append({"name": parts[0], "url": parts[1]})
        info["remotes"] = remotes

        return info

    @staticmethod
    def _run_git(git_cmd: str, args: list[str], cwd: object) -> str:
        try:
            result = subprocess.run(  # nosec B603
                [git_cmd, *args],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(cwd),
            )
            if result.returncode == 0:
                out = result.stdout.strip()
                # Extract version number from "git version X.Y.Z"
                if args == ["--version"]:
                    m = re.search(r"(\d+\.\d+[\.\d]*)", out)
                    return m.group(1) if m else out
                return out
        except (subprocess.TimeoutExpired, OSError):
            pass
        return ""
