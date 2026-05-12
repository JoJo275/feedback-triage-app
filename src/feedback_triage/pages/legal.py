"""Static legal pages: ``/privacy`` and ``/terms`` (PR 3.4).

Plain Jinja-rendered HTML, served unauthenticated. Linked from the
landing footer; the same footer partial is included on these pages
so navigation between them works without bouncing through ``/``.

Per ``docs/project/spec/v2/information-architecture.md`` -- Landing footer.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from starlette.requests import Request

from feedback_triage.templating import templates

router = APIRouter(include_in_schema=False)

# Static-ish HTML; treat them like the landing page for caching
# (``performance-budgets.md`` -- Public-page caching).
_CACHE_CONTROL = "public, max-age=300, stale-while-revalidate=600"


@router.get("/privacy", summary="Privacy policy")
def privacy_page(request: Request) -> HTMLResponse:
    """Render the privacy policy."""
    response = templates.TemplateResponse(request, "pages/legal/privacy.html")
    response.headers["Cache-Control"] = _CACHE_CONTROL
    return response


@router.get("/terms", summary="Terms of service")
def terms_page(request: Request) -> HTMLResponse:
    """Render the terms of service."""
    response = templates.TemplateResponse(request, "pages/legal/terms.html")
    response.headers["Cache-Control"] = _CACHE_CONTROL
    return response
