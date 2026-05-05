"""Static HTML page routes.

These handlers serve the three vanilla HTML/JS pages that make up the
v1.0 frontend (see spec — Frontend Delivery Model). They sit on
unversioned paths because they're user-facing URLs, not part of the
JSON API contract under ``/api/v1/``.

The HTML files live in ``feedback_triage/static/`` and are also mounted
at ``/static`` for their CSS/JS asset siblings — see
:func:`feedback_triage.main.create_app`.

The v2.0 ``/styleguide`` route is the first Jinja-rendered page in the
project ([ADR 056](../../../docs/adr/056-style-guide-page.md)). It
links to the hashed Tailwind bundle produced by ``task build:css``.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse

from feedback_triage.templating import templates

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


@router.get("/styleguide", summary="Design-system style guide")
def styleguide_page(request: Request) -> HTMLResponse:
    """Serve the v2.0 styleguide stub.

    Empty shell at this point — components arrive in later PRs.
    Confirms the Tailwind pipeline (input.css → app.<hash>.css)
    and the Jinja base template are wired end-to-end.
    """
    return templates.TemplateResponse(request, "styleguide.html")
