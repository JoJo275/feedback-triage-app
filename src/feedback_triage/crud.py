"""Database-layer functions for the ``feedback_item`` resource.

These are pure DB helpers: they take a session and primitive arguments,
return ORM rows or counts, and raise nothing HTTP-shaped. Route handlers
in ``routes/feedback.py`` translate to/from API schemas and HTTP status
codes. Keeping the split clean means the CRUD layer is reusable from
scripts (``scripts/seed.py``) without importing FastAPI.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session
from sqlmodel import col

from feedback_triage.enums import Source, Status
from feedback_triage.models import FeedbackItem
from feedback_triage.schemas import FeedbackCreate, FeedbackUpdate

_SORT_COLUMNS = {
    "created_at": col(FeedbackItem.created_at),
    "pain_level": col(FeedbackItem.pain_level),
    "status": col(FeedbackItem.status),
    "source": col(FeedbackItem.source),
}


def create_item(session: Session, payload: FeedbackCreate) -> FeedbackItem:
    """Insert a new feedback item and return the persisted row."""
    item = FeedbackItem(**payload.model_dump())
    session.add(item)
    # Flush so server defaults (id, created_at, updated_at) are populated
    # before the response is built — see spec — Transaction boundaries.
    session.flush()
    session.refresh(item)
    return item


def get_item(session: Session, item_id: int) -> FeedbackItem | None:
    """Return a single feedback item by id, or ``None`` if missing."""
    return session.get(FeedbackItem, item_id)


def list_items(
    session: Session,
    *,
    skip: int,
    limit: int,
    status: Status | None,
    source: Source | None,
    sort_by: str,
) -> tuple[Sequence[FeedbackItem], int]:
    """Return ``(items, total)`` for the filtered/sorted/paginated query."""
    descending = sort_by.startswith("-")
    column_key = sort_by[1:] if descending else sort_by
    column = _SORT_COLUMNS[column_key]
    order = desc(column) if descending else asc(column)

    base = select(FeedbackItem)
    count_q = select(func.count()).select_from(FeedbackItem)
    if status is not None:
        base = base.where(col(FeedbackItem.status) == status)
        count_q = count_q.where(col(FeedbackItem.status) == status)
    if source is not None:
        base = base.where(col(FeedbackItem.source) == source)
        count_q = count_q.where(col(FeedbackItem.source) == source)

    total = session.execute(count_q).scalar_one()
    items = session.execute(base.order_by(order).offset(skip).limit(limit)).scalars()
    return items.all(), total


def update_item(
    session: Session, item: FeedbackItem, payload: FeedbackUpdate
) -> FeedbackItem:
    """Apply a partial update to an existing feedback item.

    Empty payloads are allowed: the row is still flushed so the
    ``BEFORE UPDATE`` trigger fires and ``updated_at`` advances.
    """
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(item, field, value)
    # Force an UPDATE even when no fields changed so the trigger fires
    # (see spec — API Tests, "patch with empty body").
    if not changes:
        from sqlalchemy.orm import attributes

        attributes.flag_modified(item, "updated_at")
    session.add(item)
    session.flush()
    session.refresh(item)
    return item


def delete_item(session: Session, item: FeedbackItem) -> None:
    """Delete a feedback item."""
    session.delete(item)
    session.flush()
