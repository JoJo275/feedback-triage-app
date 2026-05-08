"""Page route for the workspace inbox.

Renders the triage queue at ``/w/{slug}/inbox``. The page is a
server-rendered shell — the table body, summary cards, and filter
state are populated client-side by ``static/js/inbox.js`` against
the v2 ``GET /api/v1/feedback`` endpoint shipped in PR 2.2.

The default filter is ``status IN ('new', 'needs_info', 'reviewing')``
per ``docs/project/spec/v2/pages.md`` — Inbox.
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


@router.get("/w/{slug}/inbox", summary="Workspace inbox (triage queue)")
def inbox_page(
    request: Request,
    ctx: WorkspaceContextDep,
    db: DbDep,
) -> HTMLResponse:
    """Render the inbox shell for workspace ``slug``."""
    workspace = db.get(Workspace, ctx.id)
    assert workspace is not None
    return templates.TemplateResponse(
        request,
        "pages/inbox.html",
        {
            "workspace_slug": workspace.slug,
            "workspace_name": workspace.name,
            "active": "inbox",
            "page_mode": "inbox",
        },
    )


@router.get("/w/{slug}/feedback", summary="Workspace feedback (full archive)")
def feedback_list_page(
    request: Request,
    ctx: WorkspaceContextDep,
    db: DbDep,
) -> HTMLResponse:
    """Render the feedback list shell — same template as inbox, no default status filter."""
    workspace = db.get(Workspace, ctx.id)
    assert workspace is not None
    return templates.TemplateResponse(
        request,
        "pages/inbox.html",
        {
            "workspace_slug": workspace.slug,
            "workspace_name": workspace.name,
            "active": "feedback",
            "page_mode": "feedback",
        },
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
