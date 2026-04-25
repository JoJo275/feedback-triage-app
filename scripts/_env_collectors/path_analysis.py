"""PATH analysis collector — directories, duplicates, dead entries, ordering."""

from __future__ import annotations

import os
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


class PathAnalysisCollector(BaseCollector):
    """Analyse PATH directories for duplicates, dead entries, and exec counts."""

    name = "path"
    timeout = 10.0

    @property
    def tier(self):  # type: ignore[override]
        return _get_tier().MINIMAL

    def collect(self) -> dict[str, Any]:
        path_dirs = os.environ.get("PATH", "").split(os.pathsep)
        entries: list[dict[str, Any]] = []
        seen: set[str] = set()
        dead_count = 0
        dup_count = 0

        for dir_path in path_dirs:
            normalized = str(Path(dir_path).resolve()).casefold()
            is_duplicate = normalized in seen
            seen.add(normalized)
            if is_duplicate:
                dup_count += 1

            p = Path(dir_path)
            if not p.is_dir():
                dead_count += 1
                entries.append(
                    {
                        "path": dir_path,
                        "exists": False,
                        "executable_count": 0,
                        "duplicate": is_duplicate,
                    }
                )
                continue

            try:
                executables = sum(
                    1 for f in p.iterdir() if f.is_file() and os.access(f, os.X_OK)
                )
            except (PermissionError, OSError):
                executables = 0

            entries.append(
                {
                    "path": dir_path,
                    "exists": True,
                    "executable_count": executables,
                    "duplicate": is_duplicate,
                }
            )

        return {
            "entries": entries,
            "total": len(entries),
            "duplicates": dup_count,
            "dead_entries": dead_count,
        }
