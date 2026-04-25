"""Disk and workspace size collector — cache sizes, workspace footprint.

Discovers:
- Total workspace size and breakdown by directory
- Cache directory sizes (__pycache__, .mypy_cache, .ruff_cache, .git)
- Build artifact sizes (dist/, *.egg-info)
"""

from __future__ import annotations

import contextlib
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


def _format_size(size_bytes: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if abs(size_bytes) < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024  # type: ignore[assignment]
    return f"{size_bytes:.1f} TB"


def _dir_size(path: Path) -> int:
    """Calculate total size of a directory (non-recursive into symlinks)."""
    total = 0
    try:
        for f in path.rglob("*"):
            if f.is_file() and not f.is_symlink():
                try:
                    total += f.stat().st_size
                except OSError:
                    continue
    except OSError:
        pass
    return total


def _count_files(path: Path, pattern: str = "*") -> int:
    """Count files matching a pattern."""
    try:
        return sum(1 for f in path.rglob(pattern) if f.is_file())
    except OSError:
        return 0


class DiskWorkspaceSizeCollector(BaseCollector):
    """Collect workspace size and cache information."""

    name = "disk_workspace"
    timeout = 30.0

    @property
    def tier(self):  # type: ignore[override]
        return _get_tier().STANDARD

    def collect(self) -> dict[str, Any]:
        from _imports import find_repo_root

        repo_root = find_repo_root()

        # Cache directories to measure
        cache_dirs: dict[str, list[Path]] = {
            "__pycache__": [],
            ".mypy_cache": [repo_root / ".mypy_cache"],
            ".ruff_cache": [repo_root / ".ruff_cache"],
            ".pytest_cache": [repo_root / ".pytest_cache"],
            ".git": [repo_root / ".git"],
            "dist": [repo_root / "dist"],
            "*.egg-info": [],
            "node_modules": [repo_root / "node_modules"],
            "site": [repo_root / "site"],
        }

        # Discover all venvs (directories with pyvenv.cfg) at repo root
        with contextlib.suppress(OSError):
            for child in repo_root.iterdir():
                if child.is_dir() and (child / "pyvenv.cfg").is_file():
                    cache_dirs[child.name] = [child]

        # Find all __pycache__ directories
        with contextlib.suppress(OSError):
            cache_dirs["__pycache__"] = list(repo_root.rglob("__pycache__"))

        # Find all *.egg-info directories
        with contextlib.suppress(OSError):
            cache_dirs["*.egg-info"] = [
                d for d in repo_root.rglob("*.egg-info") if d.is_dir()
            ]

        # Measure each cache type
        caches: list[dict[str, Any]] = []
        total_cache_size = 0
        for name, paths in cache_dirs.items():
            existing = [p for p in paths if p.exists()]
            if not existing:
                continue
            size = sum(_dir_size(p) for p in existing)
            total_cache_size += size
            caches.append(
                {
                    "path": name,
                    "file_count": len(existing),
                    "size_bytes": size,
                    "size_display": _format_size(size),
                }
            )

        # Sort by size descending
        caches.sort(key=lambda c: c["size_bytes"], reverse=True)

        # Top-level directory sizes
        top_dirs: list[dict[str, Any]] = []
        for d in sorted(repo_root.iterdir()):
            if d.is_dir() and not d.name.startswith("."):
                size = _dir_size(d)
                if size > 0:
                    top_dirs.append(
                        {
                            "path": d.name + "/",
                            "size_bytes": size,
                            "size_display": _format_size(size),
                            "file_count": _count_files(d),
                        }
                    )
        top_dirs.sort(key=lambda d: d["size_bytes"], reverse=True)

        # Total workspace (approximate — skip very large dirs for speed)
        total_files = _count_files(repo_root)

        return {
            "caches": caches,
            "total_cache_size": total_cache_size,
            "total_cache_size_display": _format_size(total_cache_size),
            "top_directories": top_dirs[:15],
            "total_files": total_files,
            "repo_root": str(repo_root),
        }
