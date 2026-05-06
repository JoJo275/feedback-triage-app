"""Public submission page route.

The only page that does **not** require authentication or workspace
membership.

Mounted at ``/w/{slug}/submit``. Resolves the workspace by slug and
404s on miss with the same envelope-shaped response a private route
would return; we never confirm or deny workspace existence to
anonymous callers via a different status.

The actual write happens against
:func:`feedback_triage.api.v1.public_feedback.submit_public_feedback`.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session as DbSession
from sqlmodel import col, select
from starlette.requests import Request

from feedback_triage.database import get_db
from feedback_triage.models import Workspace
from feedback_triage.templating import templates

router = APIRouter(include_in_schema=False)

DbDep = Annotated[DbSession, Depends(get_db)]


@router.get("/w/{slug}/submit", summary="Public feedback submission form")
def public_submit_page(
    slug: str,
    request: Request,
    db: DbDep,
) -> HTMLResponse:
    """Render the public submission form for workspace ``slug``."""
    workspace = db.execute(
        select(Workspace).where(col(Workspace.slug) == slug),
    ).scalar_one_or_none()
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Workspace not found."},
        )
    # When the owner has flipped the kill switch we 404 with the same
    # envelope as an unknown slug. Returning a different status here
    # would let an anonymous probe distinguish "exists but closed"
    # from "doesn't exist", which the spec ``security.md`` Public
    # form section forbids.
    if not workspace.public_submit_enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Workspace not found."},
        )
    return templates.TemplateResponse(
        request,
        "pages/public_submit.html",
        {
            "workspace_slug": workspace.slug,
            "workspace_name": workspace.name,
        },
    )
