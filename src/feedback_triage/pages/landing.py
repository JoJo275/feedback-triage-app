"""Landing page route (PR 3.4).

Mounted at ``/`` and served unauthenticated. Hosts the FU1 mini
demo and the public marketing surface described in
``docs/project/spec/v2/pages.md`` -- Landing.

Per ``docs/project/spec/v2/performance-budgets.md`` -- Public-page
caching: ``Cache-Control: public, max-age=300,
stale-while-revalidate=600``.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from starlette.requests import Request

from feedback_triage.templating import templates

router = APIRouter(include_in_schema=False)

_CACHE_CONTROL = "public, max-age=300, stale-while-revalidate=600"


@router.get("/", summary="Marketing landing page")
def landing_page(request: Request) -> HTMLResponse:
    """Render the v2.0 SignalNest landing page."""
    response = templates.TemplateResponse(request, "pages/landing.html")
    response.headers["Cache-Control"] = _CACHE_CONTROL
    return response
