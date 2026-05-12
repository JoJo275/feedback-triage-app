"""Public changelog page route (PR 3.2).

Mounted at ``/w/{slug}/changelog/public``. Unauthenticated, read-only.

Reverse-chronological list of feedback items where ``status =
'shipped'`` *and* ``published_to_changelog = true``. Per
``docs/project/spec/v2/information-architecture.md`` -- Public changelog.

The shipped date is sourced from ``updated_at`` -- v2.0 does not
maintain a separate ``shipped_at`` timestamp (the trigger keeps
``updated_at`` fresh on every row mutation, so the most recent
status flip lands there).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session as DbSession
from sqlmodel import col, select
from starlette.requests import Request

from feedback_triage.database import get_db
from feedback_triage.enums import Status
from feedback_triage.models import FeedbackItem, Workspace
from feedback_triage.templating import templates

router = APIRouter(include_in_schema=False)

DbDep = Annotated[DbSession, Depends(get_db)]

# Per ``docs/project/spec/v2/performance-budgets.md`` -- Public-page
# caching. 5 min fresh, 10 min stale-while-revalidate.
_CACHE_CONTROL = "public, max-age=300, stale-while-revalidate=600"


@router.get(
    "/w/{slug}/changelog/public",
    summary="Public changelog (read-only, unauthenticated)",
)
def public_changelog_page(
    slug: str,
    request: Request,
    db: DbDep,
) -> HTMLResponse:
    """Render the public changelog for workspace ``slug``."""
    workspace = db.execute(
        select(Workspace).where(col(Workspace.slug) == slug),
    ).scalar_one_or_none()
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Workspace not found."},
        )

    items = list(
        db.execute(
            select(FeedbackItem)
            .where(col(FeedbackItem.workspace_id) == workspace.id)
            .where(col(FeedbackItem.status) == Status.SHIPPED)
            .where(col(FeedbackItem.published_to_changelog).is_(True))
            .order_by(col(FeedbackItem.updated_at).desc()),
        ).scalars(),
    )

    entries = [
        {
            "id": item.id,
            "title": item.title,
            "release_note": item.release_note,
            "shipped_at": item.updated_at,
            "shipped_at_iso": item.updated_at.isoformat(),
            "shipped_at_label": item.updated_at.strftime("%Y-%m-%d"),
        }
        for item in items
    ]

    response = templates.TemplateResponse(
        request,
        "pages/public/changelog.html",
        {
            "workspace_slug": workspace.slug,
            "workspace_name": workspace.name,
            "entries": entries,
        },
    )
    response.headers["Cache-Control"] = _CACHE_CONTROL
    return response
