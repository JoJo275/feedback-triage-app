"""Static HTML page routes.

These handlers serve the three vanilla HTML/JS pages that make up the
v1.0 frontend (see spec — Frontend Delivery Model). They sit on
unversioned paths because they're user-facing URLs, not part of the
JSON API contract under ``/api/v1/``.

The HTML files live in ``feedback_triage/static/`` and are also mounted
at ``/static`` for their CSS/JS asset siblings — see
:func:`feedback_triage.main.create_app`.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

STATIC_DIR: Path = Path(__file__).resolve().parent.parent / "static"

router = APIRouter(include_in_schema=False)


def _page(filename: str) -> FileResponse:
    return FileResponse(STATIC_DIR / filename, media_type="text/html")


@router.get("/", summary="Feedback list page")
def index_page() -> FileResponse:
    """Serve the feedback list / dashboard HTML."""
    return _page("index.html")


@router.get("/new", summary="Create-feedback page")
def new_page() -> FileResponse:
    """Serve the create-feedback form HTML."""
    return _page("new.html")


@router.get("/feedback/{item_id}", summary="Feedback detail page")
def detail_page(item_id: int) -> FileResponse:
    """Serve the feedback detail/edit HTML.

    The numeric ``item_id`` path parameter exists purely so the URL is
    routable; the page itself reads the ID client-side and fetches the
    item from the JSON API.
    """
    del item_id  # Page-level routing only; rendering happens client-side.
    return _page("detail.html")
