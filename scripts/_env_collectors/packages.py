"""Packages collector — installed packages, outdated, duplicates, entry points."""

from __future__ import annotations

import importlib.metadata
import re
import sys
from typing import Any

from _env_collectors._base import BaseCollector

_tier = None


def _get_tier():  # type: ignore[no-untyped-def]
    global _tier
    if _tier is None:
        from _env_collectors import Tier

        _tier = Tier
    return _tier


class PackagesCollector(BaseCollector):
    """Collect installed packages, outdated status, duplicates, and entry points."""

    name = "packages"
    timeout = 60.0

    @property
    def tier(self):  # type: ignore[override]
        return _get_tier().FULL

    def collect(self) -> dict[str, Any]:
        all_packages = self._all_installed()
        unique = self._deduplicate(all_packages)
        grouped = self._group_by_location(all_packages)
        duplicates = self._find_duplicates(all_packages)
        entry_points = self._collect_entry_points()

        return {
            "packages": unique,
            "packages_by_location": grouped,
            "duplicate_packages": duplicates,
            "entry_points": entry_points,
            "total": len(unique),
        }

    @staticmethod
    def _all_installed() -> list[dict[str, str]]:
        packages = []
        for dist in importlib.metadata.distributions():
            name = dist.metadata["Name"]
            version = dist.metadata["Version"]
            summary = dist.metadata.get("Summary", "")
            location = str(dist._path.parent) if hasattr(dist, "_path") else ""
            packages.append(
                {
                    "name": name,
                    "version": version,
                    "summary": summary or "",
                    "location": location,
                }
            )
        return sorted(packages, key=lambda p: (p["name"] or "").lower())

    @staticmethod
    def _deduplicate(packages: list[dict[str, str]]) -> list[dict[str, str]]:
        seen: set[str] = set()
        unique: list[dict[str, str]] = []
        for pkg in packages:
            key = (pkg["name"] or "").lower()
            if key not in seen:
                seen.add(key)
                unique.append(pkg)
        return unique

    @staticmethod
    def _group_by_location(
        packages: list[dict[str, str]],
    ) -> dict[str, list[dict[str, str]]]:
        groups: dict[str, list[dict[str, str]]] = {}
        for pkg in packages:
            category = _categorize_location(pkg.get("location", ""))
            groups.setdefault(category, []).append(pkg)
        return groups

    @staticmethod
    def _find_duplicates(
        packages: list[dict[str, str]],
    ) -> dict[str, list[dict[str, str]]]:
        by_name: dict[str, list[dict[str, str]]] = {}
        for pkg in packages:
            key = (pkg.get("name") or "").lower()
            if key:
                by_name.setdefault(key, []).append(pkg)
        return {
            name: entries
            for name, entries in by_name.items()
            if len({e.get("location", "") for e in entries}) > 1
        }

    @staticmethod
    def _collect_entry_points() -> list[dict[str, str]]:
        entries = [
            {"name": ep.name, "value": ep.value, "group": "console_scripts"}
            for ep in importlib.metadata.entry_points(group="console_scripts")
        ]
        entries.extend(
            {"name": ep.name, "value": ep.value, "group": "gui_scripts"}
            for ep in importlib.metadata.entry_points(group="gui_scripts")
        )
        return sorted(entries, key=lambda e: e["name"])


def _categorize_location(location: str) -> str:
    """Classify a package install path into a human-readable category."""
    if not location:
        return "Unknown"

    loc_lower = location.lower().replace("\\", "/")

    if "/.local/share/hatch/" in loc_lower or "/hatch/env/" in loc_lower:
        m = re.search(r"hatch/env[s]?/([^/]+)", loc_lower)
        if m:
            return f"Hatch ({m.group(1)})"
        return "Hatch Environment"

    if "appdata" in loc_lower and "hatch" in loc_lower:
        m = re.search(r"hatch/env[s]?/([^/]+)", loc_lower)
        if m:
            return f"Hatch ({m.group(1)})"
        return "Hatch Environment"

    if "/.tox/" in loc_lower or "\\.tox\\" in location.lower():
        return "Tox Environment"

    if "/.nox/" in loc_lower or "\\.nox\\" in location.lower():
        return "Nox Environment"

    if "/pypoetry/" in loc_lower:
        return "Poetry Environment"

    if "/conda/" in loc_lower or "/envs/" in loc_lower:
        m = re.search(r"envs/([^/\\]+)", loc_lower)
        if m:
            return f"Conda ({m.group(1)})"
        return "Conda Environment"

    if any(kw in loc_lower for kw in ("/.venv/", "/venv/")):
        return "Virtual Environment (.venv)"
    if any(kw in location.lower() for kw in ("\\.venv\\", "\\venv\\")):
        return "Virtual Environment (.venv)"

    if "/pipx/" in loc_lower:
        return "pipx"

    if "/site-packages" in loc_lower and (
        "/.local/" in loc_lower or "/appdata/" in loc_lower
    ):
        if sys.prefix != sys.base_prefix:
            return "Virtual Environment"
        return "User (--user)"

    if sys.prefix != sys.base_prefix:
        prefix_norm = sys.prefix.lower().replace("\\", "/")
        if loc_lower.startswith(prefix_norm):
            return "Virtual Environment (active)"

    return "Global (system)"
