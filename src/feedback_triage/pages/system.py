"""System page routes for IA-defined error pages.

Renders explicit HTML surfaces for ``/404``, ``/403``, and ``/500``
as listed in ``docs/project/spec/v2/information-architecture.md``.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session as DbSession

from feedback_triage.auth.deps import CurrentUserOptionalDep
from feedback_triage.auth.service import primary_workspace_slug
from feedback_triage.database import get_db
from feedback_triage.templating import templates

router = APIRouter(include_in_schema=False)

DbDep = Annotated[DbSession, Depends(get_db)]


def _dashboard_or_home(user: CurrentUserOptionalDep, db: DbDep) -> tuple[str, str]:
    """Return CTA label + href for system pages."""
    if user is None:
        return ("Back to home", "/")

    slug = primary_workspace_slug(db, user_id=user.id)  # type: ignore[arg-type]
    if slug is None:
        return ("Back to home", "/")

    return ("Back to dashboard", f"/w/{slug}/dashboard")


@router.get("/404", summary="Not found page")
def not_found_page(
    request: Request,
    user: CurrentUserOptionalDep,
    db: DbDep,
) -> HTMLResponse:
    """Render the IA-defined not-found page."""
    cta_label, cta_href = _dashboard_or_home(user, db)
    return templates.TemplateResponse(
        request,
        "pages/system/error.html",
        {
            "page_title": "Not found · SignalNest",
            "heading": "Not found.",
            "message": "We couldn't find that page.",
            "cta_label": cta_label,
            "cta_href": cta_href,
            "request_id": "",
        },
        status_code=404,
    )


@router.get("/403", summary="Forbidden page")
def forbidden_page(
    request: Request,
    user: CurrentUserOptionalDep,
    db: DbDep,
) -> HTMLResponse:
    """Render the IA-defined forbidden page."""
    cta_label, cta_href = _dashboard_or_home(user, db)
    return templates.TemplateResponse(
        request,
        "pages/system/error.html",
        {
            "page_title": "Forbidden · SignalNest",
            "heading": "You don't have access to that.",
            "message": "You don't have access to that.",
            "cta_label": cta_label,
            "cta_href": cta_href,
            "request_id": "",
        },
        status_code=403,
    )


@router.get("/500", summary="Server error page")
def internal_error_page(
    request: Request,
    user: CurrentUserOptionalDep,
    db: DbDep,
) -> HTMLResponse:
    """Render the IA-defined server error page."""
    cta_label, cta_href = _dashboard_or_home(user, db)
    request_id = getattr(request.state, "request_id", "")
    return templates.TemplateResponse(
        request,
        "pages/system/error.html",
        {
            "page_title": "Server error · SignalNest",
            "heading": "Something went wrong.",
            "message": "Something went wrong. The team has been notified.",
            "cta_label": cta_label,
            "cta_href": cta_href,
            "request_id": request_id,
        },
        status_code=500,
    )
