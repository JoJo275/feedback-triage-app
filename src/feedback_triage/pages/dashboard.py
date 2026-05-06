"""Page route for the workspace dashboard.

Renders the empty-state shell at ``/w/{slug}/dashboard``. Real
dashboard widgets land in PR 2.x — this PR ships only the empty
state so the post-signup redirect lands on a real page rather than
a 404.

The slug is resolved via ``WorkspaceContextDep`` so cross-tenant
probes 404 the same way the JSON API does (ADR 060).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session as DbSession
from starlette.requests import Request

from feedback_triage.database import get_db
from feedback_triage.models import Workspace
from feedback_triage.templating import templates
from feedback_triage.tenancy import WorkspaceContextDep

router = APIRouter(include_in_schema=False)

DbDep = Annotated[DbSession, Depends(get_db)]


@router.get("/w/{slug}/dashboard", summary="Workspace dashboard (empty state)")
def dashboard_page(
    request: Request,
    ctx: WorkspaceContextDep,
    db: DbDep,
) -> HTMLResponse:
    """Render the empty-state dashboard for workspace ``slug``."""
    workspace = db.get(Workspace, ctx.id)
    assert workspace is not None
    return templates.TemplateResponse(
        request,
        "pages/dashboard/empty.html",
        {
            "workspace_slug": workspace.slug,
            "workspace_name": workspace.name,
            "active": "dashboard",
        },
    )
