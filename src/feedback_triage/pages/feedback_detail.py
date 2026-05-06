"""Page route for the feedback detail "case file" view.

Renders ``/w/{slug}/feedback/{item_id}``. The page is a
server-rendered shell that boots the item id into the DOM; the
detail view, timeline, notes thread, tag editor, and publishing
toggles are wired client-side by ``static/js/feedback_detail.js``
against the v2 ``/api/v1/feedback/{id}`` and ``…/notes`` endpoints
shipped in PR 2.2.

A cross-tenant probe — `/w/{other-slug}/feedback/{my-item-id}` —
gets the canonical ``404`` because the workspace context resolves
``slug`` against the caller's memberships before the route body
runs (ADR 060). Item ids that exist but are owned by a different
workspace also 404 here, mirroring the JSON API.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session as DbSession
from starlette.requests import Request

from feedback_triage.database import get_db
from feedback_triage.models import FeedbackItem, Workspace
from feedback_triage.templating import templates
from feedback_triage.tenancy import WorkspaceContextDep

router = APIRouter(include_in_schema=False)

DbDep = Annotated[DbSession, Depends(get_db)]


@router.get(
    "/w/{slug}/feedback/{item_id}",
    summary="Feedback detail (case file)",
)
def feedback_detail_page(
    request: Request,
    item_id: int,
    ctx: WorkspaceContextDep,
    db: DbDep,
) -> HTMLResponse:
    """Render the case-file shell for feedback ``item_id``."""
    workspace = db.get(Workspace, ctx.id)
    assert workspace is not None
    item = db.get(FeedbackItem, item_id)
    if item is None or item.workspace_id != ctx.id:
        # Mirror the JSON API's cross-tenant 404 (ADR 060).
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Feedback item not found."},
        )
    return templates.TemplateResponse(
        request,
        "pages/feedback_detail.html",
        {
            "workspace_slug": workspace.slug,
            "workspace_name": workspace.name,
            "active": "feedback",
            "feedback_id": item.id,
            "feedback_title": item.title,
        },
    )
