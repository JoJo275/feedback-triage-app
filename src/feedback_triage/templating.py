"""Render helpers for v2.0 Jinja templates.

Single source of truth for the ``Jinja2Templates`` instance and the
``static_url`` helper, which resolves logical filenames
(``"app.css"``) to their hashed, content-addressed counterparts
(``"app.<hash>.css"``) via the manifest written by
``scripts/build_css.py``.

If the manifest is missing (e.g. someone forgot ``task build:css``),
``static_url`` falls back to the bare filename rather than raising —
the page still renders and the missing-CSS condition is visible in
the browser instead of a 500 from Jinja. The "missing manifest"
warning is logged once per process; subsequent calls are silent so a
misconfigured deploy doesn't flood logs at request rate.

The parsed manifest is cached in-memory and only re-parsed when the
file's mtime changes, so each request is a single ``stat`` call.

See docs/project/spec/v2/css.md.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi.templating import Jinja2Templates

logger = logging.getLogger(__name__)

PACKAGE_DIR: Path = Path(__file__).resolve().parent
TEMPLATES_DIR: Path = PACKAGE_DIR / "templates"
STATIC_DIR: Path = PACKAGE_DIR / "static"
CSS_MANIFEST: Path = STATIC_DIR / "css" / "manifest.json"

# Cached parsed manifest plus the source mtime it was loaded from.
# ``None`` mtime means "not yet loaded"; ``-1.0`` means "missing /
# unreadable, do not warn again until the file appears".
_manifest_cache: dict[str, str] = {}
_manifest_mtime: float | None = None


def _load_manifest() -> dict[str, str]:
    """Return the parsed manifest, re-reading only when the file changes."""
    global _manifest_cache, _manifest_mtime

    try:
        mtime = CSS_MANIFEST.stat().st_mtime
    except FileNotFoundError:
        if _manifest_mtime != -1.0:
            logger.warning(
                "CSS manifest %s missing — run `task build:css`. "
                "Falling back to unhashed filenames.",
                CSS_MANIFEST,
            )
            _manifest_cache = {}
            _manifest_mtime = -1.0
        return _manifest_cache

    if mtime == _manifest_mtime:
        return _manifest_cache

    try:
        data = json.loads(CSS_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Could not parse CSS manifest %s: %s", CSS_MANIFEST, exc)
        _manifest_cache = {}
        _manifest_mtime = mtime
        return _manifest_cache

    _manifest_cache = (
        {str(k): str(v) for k, v in data.items()} if isinstance(data, dict) else {}
    )
    _manifest_mtime = mtime
    return _manifest_cache


def static_url(filename: str) -> str:
    """Return the public URL for a static asset, hashed when applicable."""
    resolved = _load_manifest().get(filename, filename)
    return (
        f"/static/css/{resolved}"
        if filename.endswith(".css")
        else f"/static/{resolved}"
    )


templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
templates.env.globals["static_url"] = static_url
