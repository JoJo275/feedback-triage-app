"""Page route for the workspace inbox.

Renders the triage queue at ``/w/{slug}/inbox``.
Phase 4 serves the shared React shell directly for inbox and feedback
list routes.

The default filter is ``status IN ('new', 'needs_info', 'reviewing')``
per ``docs/project/spec/v2/information-architecture.md`` — Inbox.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session as DbSession
from starlette.requests import Request
from starlette.responses import Response

from feedback_triage.database import get_db
from feedback_triage.models import Workspace
from feedback_triage.pages.react_shell import maybe_render_workspace_react_shell
from feedback_triage.templating import templates
from feedback_triage.tenancy import WorkspaceContextDep

router = APIRouter(include_in_schema=False)

DbDep = Annotated[DbSession, Depends(get_db)]


@router.get("/w/{slug}/inbox", summary="Workspace inbox (triage queue)")
def inbox_page(
    request: Request,
    ctx: WorkspaceContextDep,
    db: DbDep,
) -> Response:
    """Render the inbox shell for workspace ``slug``."""
    workspace = db.get(Workspace, ctx.id)
    assert workspace is not None

    return maybe_render_workspace_react_shell(
        request,
        workspace_slug=workspace.slug,
        workspace_name=workspace.name,
        active_section="inbox",
        page_key="inbox",
        page_title="Inbox",
    )


@router.get("/w/{slug}/feedback", summary="Workspace feedback (full archive)")
def feedback_list_page(
    request: Request,
    ctx: WorkspaceContextDep,
    db: DbDep,
) -> Response:
    """Render the feedback list route (same React surface as inbox)."""
    workspace = db.get(Workspace, ctx.id)
    assert workspace is not None

    return maybe_render_workspace_react_shell(
        request,
        workspace_slug=workspace.slug,
        workspace_name=workspace.name,
        active_section="feedback",
        page_key="feedback",
        page_title="Feedback",
    )


@router.get("/w/{slug}/feedback/new", summary="Create-feedback page (workspace-scoped)")
def feedback_new_page(
    request: Request,
    ctx: WorkspaceContextDep,
    db: DbDep,
) -> HTMLResponse:
    """Render the workspace-scoped create-feedback form."""
    workspace = db.get(Workspace, ctx.id)
    assert workspace is not None
    return templates.TemplateResponse(
        request,
        "pages/feedback_new.html",
        {
            "workspace_slug": workspace.slug,
            "workspace_name": workspace.name,
            "active": "inbox",
        },
    )
