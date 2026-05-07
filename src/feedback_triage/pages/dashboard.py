"""Page route for the workspace dashboard.

PR 1.8 shipped an empty-state shell at ``/w/{slug}/dashboard``;
PR 3.4 fills it in. The route resolves the slug through
:class:`WorkspaceContextDep` (cross-tenant probes 404 per ADR 060)
and asks
:func:`feedback_triage.services.dashboard_aggregator.get_summary`
for the five summary counts, the 30-day intake sparkline, the top
five tags, and the ten most recent activity entries.

When the workspace has no feedback yet we keep the original
empty-state template -- it's a richer surface than five zero-cards.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session as DbSession
from starlette.requests import Request

from feedback_triage.database import get_db
from feedback_triage.models import Workspace
from feedback_triage.services import dashboard_aggregator
from feedback_triage.templating import templates
from feedback_triage.tenancy import WorkspaceContextDep

router = APIRouter(include_in_schema=False)

DbDep = Annotated[DbSession, Depends(get_db)]


@router.get("/w/{slug}/dashboard", summary="Workspace dashboard")
def dashboard_page(
    request: Request,
    ctx: WorkspaceContextDep,
    db: DbDep,
) -> HTMLResponse:
    """Render the dashboard for workspace ``slug``."""
    workspace = db.get(Workspace, ctx.id)
    assert workspace is not None

    summary = dashboard_aggregator.get_summary(
        db,
        workspace_id=ctx.id,
        role=ctx.role,
    )

    if summary.total_items == 0:
        return templates.TemplateResponse(
            request,
            "pages/dashboard/empty.html",
            {
                "workspace_slug": workspace.slug,
                "workspace_name": workspace.name,
                "active": "dashboard",
            },
        )

    return templates.TemplateResponse(
        request,
        "pages/dashboard/index.html",
        {
            "workspace_slug": workspace.slug,
            "workspace_name": workspace.name,
            "active": "dashboard",
            "summary": summary,
        },
    )
