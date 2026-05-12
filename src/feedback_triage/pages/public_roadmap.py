"""Public roadmap page route (PR 3.2).

Mounted at ``/w/{slug}/roadmap/public``. Unauthenticated, read-only.

Renders three columns -- *Planned*, *In progress*, *Recently shipped
(last 30 days)* -- of feedback items where ``published_to_roadmap``
is ``true``. Per ``docs/project/spec/v2/information-architecture.md`` -- Public roadmap.

Cards show title, type, and tags only -- never submitter info. The
spec security model treats the roadmap as a fully public surface, so
we 404 with the standard envelope when the workspace slug is unknown
(matches the public submit form's behaviour).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session as DbSession
from sqlmodel import col, select
from starlette.requests import Request

from feedback_triage.database import get_db
from feedback_triage.enums import Status
from feedback_triage.models import FeedbackItem, FeedbackTag, Tag, Workspace
from feedback_triage.templating import templates

router = APIRouter(include_in_schema=False)

DbDep = Annotated[DbSession, Depends(get_db)]

# Per ``docs/project/spec/v2/performance-budgets.md`` -- Public-page
# caching. 5 min fresh, 10 min stale-while-revalidate.
_CACHE_CONTROL = "public, max-age=300, stale-while-revalidate=600"

# "Recently shipped" window per ``information-architecture.md`` -- Public roadmap.
_RECENT_SHIPPED_WINDOW = timedelta(days=30)


def _serialise_item(
    item: FeedbackItem,
    tags_by_feedback: dict[int, list[Tag]],
) -> dict[str, object]:
    """Project a feedback row to the dict shape the template consumes."""
    assert item.id is not None  # NOT NULL post-insert; satisfies mypy.
    return {
        "id": item.id,
        "title": item.title,
        "type": item.type.value,
        "type_other": item.type_other,
        "tags": [
            {"name": t.name, "slug": t.slug, "color": t.color}
            for t in tags_by_feedback.get(item.id, [])
        ],
    }


@router.get(
    "/w/{slug}/roadmap/public",
    summary="Public roadmap (read-only, unauthenticated)",
)
def public_roadmap_page(
    slug: str,
    request: Request,
    db: DbDep,
) -> HTMLResponse:
    """Render the public roadmap shell for workspace ``slug``."""
    workspace = db.execute(
        select(Workspace).where(col(Workspace.slug) == slug),
    ).scalar_one_or_none()
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Workspace not found."},
        )

    cutoff = datetime.now(UTC) - _RECENT_SHIPPED_WINDOW

    # Push the 30-day "recently shipped" cutoff into SQL so Postgres
    # filters before we materialise rows. Planned / in-progress rows
    # are unbounded; only the SHIPPED column is windowed.
    items = list(
        db.execute(
            select(FeedbackItem)
            .where(col(FeedbackItem.workspace_id) == workspace.id)
            .where(col(FeedbackItem.published_to_roadmap).is_(True))
            .where(
                col(FeedbackItem.status).in_(
                    [Status.PLANNED, Status.IN_PROGRESS, Status.SHIPPED],
                ),
            )
            .where(
                or_(
                    col(FeedbackItem.status) != Status.SHIPPED,
                    col(FeedbackItem.updated_at) >= cutoff,
                ),
            )
            .order_by(col(FeedbackItem.updated_at).desc()),
        ).scalars(),
    )

    tags_by_feedback = _load_tags_for(db, [i.id for i in items if i.id is not None])

    columns = {
        "planned": [
            _serialise_item(i, tags_by_feedback)
            for i in items
            if i.status is Status.PLANNED
        ],
        "in_progress": [
            _serialise_item(i, tags_by_feedback)
            for i in items
            if i.status is Status.IN_PROGRESS
        ],
        "shipped": [
            _serialise_item(i, tags_by_feedback)
            for i in items
            if i.status is Status.SHIPPED
        ],
    }

    response = templates.TemplateResponse(
        request,
        "pages/public/roadmap.html",
        {
            "workspace_slug": workspace.slug,
            "workspace_name": workspace.name,
            "columns": columns,
            "is_empty": not any(columns.values()),
        },
    )
    response.headers["Cache-Control"] = _CACHE_CONTROL
    return response


def _load_tags_for(
    db: DbSession,
    feedback_ids: list[int],
) -> dict[int, list[Tag]]:
    """Fetch tags grouped by feedback id with a single round trip."""
    if not feedback_ids:
        return {}
    rows = db.execute(
        select(FeedbackTag.feedback_id, Tag)
        .join(Tag, col(Tag.id) == col(FeedbackTag.tag_id))
        .where(col(FeedbackTag.feedback_id).in_(feedback_ids))
        .order_by(col(Tag.name)),
    ).all()
    grouped: dict[int, list[Tag]] = {}
    for feedback_id, tag in rows:
        grouped.setdefault(feedback_id, []).append(tag)
    return grouped
