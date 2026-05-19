"""Page route for the workspace dashboard.

Phase 4 serves the React shell directly on ``/w/{slug}/dashboard``.
Legacy dashboard templates and the isolated pilot route are removed.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DbSession
from starlette.requests import Request
from starlette.responses import Response

from feedback_triage.database import get_db
from feedback_triage.models import Workspace
from feedback_triage.pages.react_shell import maybe_render_workspace_react_shell
from feedback_triage.tenancy import WorkspaceContextDep

router = APIRouter(include_in_schema=False)

DbDep = Annotated[DbSession, Depends(get_db)]


@router.get("/w/{slug}/dashboard", summary="Workspace dashboard")
def dashboard_page(
    request: Request,
    ctx: WorkspaceContextDep,
    db: DbDep,
) -> Response:
    """Render the dashboard for workspace ``slug``."""
    workspace = db.get(Workspace, ctx.id)
    assert workspace is not None

    return maybe_render_workspace_react_shell(
        request,
        workspace_slug=workspace.slug,
        workspace_name=workspace.name,
        active_section="dashboard",
        page_key="dashboard",
        page_title="Dashboard",
    )
