"""Landing page route (PR 3.4).

Mounted at ``/`` and served unauthenticated. Hosts the FU1 mini
demo and the public marketing surface described in
``docs/project/spec/v2/information-architecture.md`` -- Landing.

Per ``docs/project/spec/v2/performance-budgets.md`` -- Public-page
caching: ``Cache-Control: public, max-age=300,
stale-while-revalidate=600``.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session as DbSession
from starlette.requests import Request

from feedback_triage.auth.deps import CurrentUserOptionalDep
from feedback_triage.auth.service import primary_workspace_slug
from feedback_triage.database import get_db
from feedback_triage.templating import templates

router = APIRouter(include_in_schema=False)

_CACHE_CONTROL = "public, max-age=300, stale-while-revalidate=600"

DbDep = Annotated[DbSession, Depends(get_db)]


@router.get("/", summary="Marketing landing page")
def landing_page(
    request: Request,
    user: CurrentUserOptionalDep,
    db: DbDep,
) -> Response:
    """Render the v2.0 SignalNest landing page.

    Per ``information-architecture.md``: signed-in users are redirected
    to their dashboard instead of seeing the public marketing surface.
    """
    dashboard_slug: str | None = None
    if user is not None:
        dashboard_slug = primary_workspace_slug(db, user_id=user.id)  # type: ignore[arg-type]

    if dashboard_slug is not None:
        redirect_response = RedirectResponse(
            url=f"/w/{dashboard_slug}/dashboard",
            status_code=status.HTTP_302_FOUND,
        )
        redirect_response.headers["Cache-Control"] = "private, no-store"
        return redirect_response

    template_response = templates.TemplateResponse(
        request,
        "pages/landing.html",
        {
            "current_user": user,
            "primary_workspace_slug": dashboard_slug,
        },
    )
    # Logged-in views must not be cached on shared proxies.
    if user is None:
        template_response.headers["Cache-Control"] = _CACHE_CONTROL
    else:
        template_response.headers["Cache-Control"] = "private, no-store"
    return template_response
