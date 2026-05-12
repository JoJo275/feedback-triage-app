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

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session as DbSession
from starlette.requests import Request

from feedback_triage.auth.deps import CurrentUserOptionalDep
from feedback_triage.auth.service import list_memberships
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
) -> HTMLResponse:
    """Render the v2.0 SignalNest landing page.

    When the caller is signed in we surface their first workspace as a
    "Go to dashboard" button at the top of the page so they don't have
    to type the route into the URL bar.
    """
    primary_workspace_slug: str | None = None
    if user is not None:
        rows = list_memberships(db, user_id=user.id)  # type: ignore[arg-type]
        if rows:
            # Pick a deterministic "primary" workspace: prefer one the
            # user owns, otherwise the first by slug.
            owned = [w for m, w in rows if m.role == "owner"]
            chosen = owned[0] if owned else rows[0][1]
            primary_workspace_slug = chosen.slug
    response = templates.TemplateResponse(
        request,
        "pages/landing.html",
        {
            "current_user": user,
            "primary_workspace_slug": primary_workspace_slug,
        },
    )
    # Logged-in views must not be cached on shared proxies.
    if user is None:
        response.headers["Cache-Control"] = _CACHE_CONTROL
    else:
        response.headers["Cache-Control"] = "private, no-store"
    return response
