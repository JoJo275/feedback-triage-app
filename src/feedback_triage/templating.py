"""Render helpers for v2.0 Jinja templates.

Single source of truth for the ``Jinja2Templates`` instance and the
``static_url`` helper, which resolves logical filenames
(``"app.css"``) to their hashed, content-addressed counterparts
(``"app.<hash>.css"``) via the manifest written by
``scripts/build_css.py``.

If the manifest is missing (e.g. someone forgot ``task build:css``),
``static_url`` falls back to the bare filename rather than raising —
the page still renders and the missing-CSS condition is visible in
the browser instead of a 500 from Jinja.

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


def _load_manifest() -> dict[str, str]:
    """Load the CSS manifest. Empty dict if missing or unreadable."""
    if not CSS_MANIFEST.is_file():
        logger.warning(
            "CSS manifest %s missing — run `task build:css`. "
            "Falling back to unhashed filenames.",
            CSS_MANIFEST,
        )
        return {}
    try:
        data = json.loads(CSS_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Could not parse CSS manifest %s: %s", CSS_MANIFEST, exc)
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k): str(v) for k, v in data.items()}


def static_url(filename: str) -> str:
    """Return the public URL for a static asset, hashed when applicable."""
    manifest = _load_manifest()
    resolved = manifest.get(filename, filename)
    return (
        f"/static/css/{resolved}"
        if filename.endswith(".css")
        else f"/static/{resolved}"
    )


templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
templates.env.globals["static_url"] = static_url
