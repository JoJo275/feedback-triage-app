"""Manifest helpers for the Phase 0 React frontend bundle.

The React scaffold under ``web/`` is built by Vite into
``src/feedback_triage/static/app`` with a ``manifest.json`` file.
This module resolves logical entrypoints (for example, ``index.html``)
to their hashed script and CSS URLs and provides a startup validation
seam for fail-closed deployments.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from feedback_triage.templating import STATIC_DIR

logger = logging.getLogger(__name__)

REACT_MANIFEST: Path = STATIC_DIR / "app" / "manifest.json"

_manifest_cache: dict[str, dict[str, Any]] = {}
_manifest_mtime: float | None = None


@dataclass(frozen=True, slots=True)
class ReactEntryAssets:
    """Resolved static URLs for one React entrypoint."""

    script_url: str
    css_urls: tuple[str, ...]


def reset_manifest_cache() -> None:
    """Clear the manifest cache (test seam)."""
    global _manifest_cache, _manifest_mtime
    _manifest_cache = {}
    _manifest_mtime = None


def _load_manifest() -> dict[str, dict[str, Any]]:
    """Return the parsed Vite manifest, reloading on file changes."""
    global _manifest_cache, _manifest_mtime

    try:
        mtime = REACT_MANIFEST.stat().st_mtime
    except FileNotFoundError:
        _manifest_cache = {}
        _manifest_mtime = -1.0
        return _manifest_cache

    if mtime == _manifest_mtime:
        return _manifest_cache

    try:
        parsed = json.loads(REACT_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.error("Could not parse React manifest %s: %s", REACT_MANIFEST, exc)
        _manifest_cache = {}
        _manifest_mtime = mtime
        return _manifest_cache

    if not isinstance(parsed, dict):
        logger.error("React manifest %s is not a JSON object", REACT_MANIFEST)
        _manifest_cache = {}
        _manifest_mtime = mtime
        return _manifest_cache

    normalized: dict[str, dict[str, Any]] = {
        key: value
        for key, value in parsed.items()
        if isinstance(key, str) and isinstance(value, dict)
    }

    _manifest_cache = normalized
    _manifest_mtime = mtime
    return _manifest_cache


def resolve_react_entry(entrypoint: str) -> ReactEntryAssets | None:
    """Resolve one Vite manifest entry to script/CSS URLs.

    Args:
        entrypoint: Logical manifest key, for example ``index.html``.

    Returns:
        The resolved asset URLs, or ``None`` when the entry is missing
        or malformed.
    """
    entry = _load_manifest().get(entrypoint)
    if not isinstance(entry, dict):
        return None

    script_file = entry.get("file")
    if not isinstance(script_file, str) or not script_file:
        return None

    css_files = entry.get("css")
    css_urls: list[str] = []
    if isinstance(css_files, list):
        css_urls.extend(
            f"/static/app/{item}" for item in css_files if isinstance(item, str)
        )

    return ReactEntryAssets(
        script_url=f"/static/app/{script_file}",
        css_urls=tuple(css_urls),
    )


def validate_react_manifest(required_entries: tuple[str, ...]) -> tuple[str, ...]:
    """Return required entries missing from the manifest."""
    manifest = _load_manifest()
    missing: list[str] = []

    for entrypoint in required_entries:
        entry = manifest.get(entrypoint)
        if not isinstance(entry, dict):
            missing.append(entrypoint)
            continue

        script_file = entry.get("file")
        if not isinstance(script_file, str) or not script_file:
            missing.append(entrypoint)

    return tuple(missing)
