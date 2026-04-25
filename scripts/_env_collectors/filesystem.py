"""Filesystem collector — writable dirs, disk space, mounts."""

from __future__ import annotations

import os
import shutil
import tempfile
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


class FilesystemCollector(BaseCollector):
    """Collect filesystem info — writable dirs, disk space."""

    name = "filesystem"
    timeout = 5.0

    @property
    def tier(self):  # type: ignore[override]
        return _get_tier().STANDARD

    def collect(self) -> dict[str, Any]:
        # Disk usage for current working directory
        cwd = str(Path.cwd())
        try:
            usage = shutil.disk_usage(cwd)
            disk = {
                "path": cwd,
                "total_gb": round(usage.total / (1024**3), 1),
                "used_gb": round(usage.used / (1024**3), 1),
                "free_gb": round(usage.free / (1024**3), 1),
                "percent_used": round(usage.used / usage.total * 100, 1)
                if usage.total
                else 0,
            }
        except OSError:
            disk = {"path": cwd, "error": "Could not read disk usage"}

        # Check writable directories
        tmp_dir = tempfile.gettempdir()
        writable_checks = {
            "temp_dir": {"path": tmp_dir, "writable": os.access(tmp_dir, os.W_OK)},
            "cwd": {"path": cwd, "writable": os.access(cwd, os.W_OK)},
        }

        home = Path.home()
        writable_checks["home"] = {
            "path": str(home),
            "writable": os.access(str(home), os.W_OK),
        }

        return {
            "disk": disk,
            "writable": writable_checks,
            "temp_dir": tmp_dir,
        }
