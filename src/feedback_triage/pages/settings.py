"""Page route for the workspace settings page (PR 2.5).

Renders ``/w/{slug}/settings`` through the shared React shell.
Authorization and tenancy are still enforced server-side through
``WorkspaceContextDep`` and API-level role checks.
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


@router.get("/w/{slug}/settings", summary="Workspace settings")
def settings_page(
    request: Request,
    ctx: WorkspaceContextDep,
    db: DbDep,
) -> Response:
    """Render the settings page for workspace ``slug``."""
    workspace = db.get(Workspace, ctx.id)
    assert workspace is not None

    return maybe_render_workspace_react_shell(
        request,
        workspace_slug=workspace.slug,
        workspace_name=workspace.name,
        active_section="settings",
        page_key="settings",
        page_title="Settings",
    )
