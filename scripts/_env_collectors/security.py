"""Security collector — secret scan, permissions, insecure PATH entries."""

from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Any

from _env_collectors._base import BaseCollector
from _env_collectors._redact import _SECRET_NAME_PATTERNS

_tier = None


def _get_tier():  # type: ignore[no-untyped-def]
    global _tier
    if _tier is None:
        from _env_collectors import Tier

        _tier = Tier
    return _tier


class SecurityCollector(BaseCollector):
    """Scan for secret exposure, insecure PATH entries, and permission issues."""

    name = "security"
    timeout = 10.0

    @property
    def tier(self):  # type: ignore[override]
        return _get_tier().STANDARD

    def collect(self) -> dict[str, Any]:
        return {
            "secret_env_vars": self._scan_secret_env_vars(),
            "insecure_path_entries": self._check_insecure_path(),
            "ssh_keys_exposed": self._check_ssh_keys(),
        }

    @staticmethod
    def _scan_secret_env_vars() -> list[dict[str, str]]:
        """Find env vars whose names match secret patterns."""
        secrets: list[dict[str, str]] = []
        for name in sorted(os.environ):
            for pattern in _SECRET_NAME_PATTERNS:
                if pattern.search(name):
                    secrets.append({"name": name, "pattern": pattern.pattern})
                    break
        return secrets

    @staticmethod
    def _check_insecure_path() -> list[dict[str, str]]:
        """Check for world-writable or suspicious PATH directories."""
        issues: list[dict[str, str]] = []
        path_dirs = os.environ.get("PATH", "").split(os.pathsep)

        for dir_path in path_dirs:
            p = Path(dir_path)
            if not p.is_dir():
                continue

            # Check for current directory in PATH (security risk)
            if dir_path in (".", ""):
                issues.append(
                    {
                        "path": dir_path or ".",
                        "issue": "Current directory in PATH — allows binary hijacking",
                    }
                )
                continue

            # On Unix, check for world-writable directories
            if os.name != "nt":
                try:
                    mode = p.stat().st_mode
                    if mode & stat.S_IWOTH:
                        issues.append(
                            {
                                "path": dir_path,
                                "issue": "World-writable directory in PATH",
                            }
                        )
                except OSError:
                    pass

        return issues

    @staticmethod
    def _check_ssh_keys() -> list[dict[str, str]]:
        """Check if SSH-related secrets are exposed in environment."""
        exposed: list[dict[str, str]] = []
        for name, value in os.environ.items():
            name_upper = name.upper()
            if ("SSH" in name_upper or "PRIVATE" in name_upper) and (
                "KEY" in name_upper or "-----BEGIN" in value[:20]
            ):
                exposed.append({"name": name, "type": "SSH/private key content"})
        return exposed
