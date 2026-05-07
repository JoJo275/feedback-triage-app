"""``/api/v1/feedback`` — workspace-scoped CRUD on the v2 schema (PR 2.2).

Replaces the v1 anonymous router under
``feedback_triage.routes.feedback``. Every route depends on
:class:`WorkspaceContextDep` (404 on cross-tenant per ADR 060) and
on :func:`current_user_required` transitively. Writes additionally
require :func:`require_writable` so demo users get ``403`` with the
documented ``code=demo_read_only`` envelope rather than silently
mutating the demo workspace.

The notes sub-resource (``/feedback/{id}/notes``) is mounted on the
same router so the workspace context resolves once per request and
the spec's grouping is preserved (api.md — Notes).
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import asc, desc, func
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import attributes
from sqlmodel import col, select

from feedback_triage.api.v1._feedback_schemas import (
    FeedbackCreateV2,
    FeedbackListEnvelopeV2,
    FeedbackResponseV2,
    FeedbackTagsReplaceRequest,
    FeedbackUpdateV2,
    NoteCreateRequest,
    NoteListEnvelope,
    NoteResponse,
    NoteUpdateRequest,
)
from feedback_triage.auth.deps import CurrentUserDep
from feedback_triage.config import Settings, get_settings
from feedback_triage.database import get_db
from feedback_triage.enums import (
    FeedbackType,
    Priority,
    Source,
    Status,
    UserRole,
    WorkspaceRole,
)
from feedback_triage.models import (
    FeedbackItem,
    FeedbackNote,
    FeedbackTag,
    Tag,
)
from feedback_triage.services.stale_detector import stale_clause
from feedback_triage.services.status_change_notifier import notify_status_change
from feedback_triage.tenancy import (
    WorkspaceContext,
    WorkspaceContextDep,
    require_writable,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])

DbDep = Annotated[DbSession, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]

# How long an author can edit a note after creation.
NOTE_EDIT_WINDOW = timedelta(minutes=15)

_FEEDBACK_NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Feedback item not found",
)
_NOTE_NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Note not found",
)
_NOTE_EDIT_WINDOW_CLOSED = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail={
        "code": "edit_window_closed",
        "message": "Notes can only be edited within 15 minutes of creation.",
    },
)

# Sort whitelist; ``-`` prefix = descending. Anything outside this set
# is rejected with 422 — keeps the API surface tight and the index
# coverage predictable.
_SORTABLE_FIELDS: frozenset[str] = frozenset(
    {
        "created_at",
        "-created_at",
        "updated_at",
        "-updated_at",
        "pain_level",
        "-pain_level",
        "status",
        "-status",
    }
)
_SORT_COLUMNS = {
    "created_at": col(FeedbackItem.created_at),
    "updated_at": col(FeedbackItem.updated_at),
    "pain_level": col(FeedbackItem.pain_level),
    "status": col(FeedbackItem.status),
}


def _scoped_get(
    db: DbSession,
    item_id: int,
    workspace_id: uuid.UUID,
) -> FeedbackItem:
    """Load a feedback item by id within the caller's workspace.

    Cross-tenant access is a tenant leak risk, so a row that exists
    in another workspace must look identical to a missing row — both
    raise the same 404.
    """
    item = db.get(FeedbackItem, item_id)
    if item is None or item.workspace_id != workspace_id:
        raise _FEEDBACK_NOT_FOUND
    return item


# ---------------------------------------------------------------------------
# Feedback CRUD
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=FeedbackResponseV2,
    status_code=status.HTTP_201_CREATED,
    summary="Create a feedback item (authenticated team submission)",
)
def create_feedback(
    payload: FeedbackCreateV2,
    response: Response,
    ctx: Annotated[WorkspaceContext, Depends(require_writable)],
    db: DbDep,
) -> FeedbackResponseV2:
    """Insert a new feedback item scoped to the caller's workspace."""
    item = FeedbackItem(
        **payload.model_dump(),
        workspace_id=ctx.id,
    )
    db.add(item)
    db.flush()
    db.refresh(item)
    response.headers["Location"] = f"/api/v1/feedback/{item.id}"
    return FeedbackResponseV2.model_validate(item)


@router.get(
    "",
    response_model=FeedbackListEnvelopeV2,
    summary="List feedback items in the workspace",
)
def list_feedback(
    ctx: WorkspaceContextDep,
    db: DbDep,
    settings: SettingsDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int | None, Query(ge=1, le=1000)] = None,
    status_filter: Annotated[Status | None, Query(alias="status")] = None,
    source: Annotated[Source | None, Query()] = None,
    type_filter: Annotated[FeedbackType | None, Query(alias="type")] = None,
    priority: Annotated[Priority | None, Query()] = None,
    tag: Annotated[uuid.UUID | None, Query()] = None,
    submitter_id: Annotated[uuid.UUID | None, Query()] = None,
    q: Annotated[str | None, Query(min_length=1, max_length=200)] = None,
    published_to_roadmap: Annotated[bool | None, Query()] = None,
    published_to_changelog: Annotated[bool | None, Query()] = None,
    created_after: Annotated[datetime | None, Query()] = None,
    created_before: Annotated[datetime | None, Query()] = None,
    stale: Annotated[bool | None, Query()] = None,
    sort_by: Annotated[str, Query()] = "-created_at",
) -> FeedbackListEnvelopeV2:
    """Return a paginated, filtered envelope of feedback in this workspace."""
    if sort_by not in _SORTABLE_FIELDS:
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "loc": ["query", "sort_by"],
                    "msg": f"sort_by must be one of {sorted(_SORTABLE_FIELDS)}",
                    "type": "value_error",
                }
            ],
        )
    descending = sort_by.startswith("-")
    column = _SORT_COLUMNS[sort_by[1:] if descending else sort_by]
    order = desc(column) if descending else asc(column)

    effective_limit = min(
        limit if limit is not None else settings.page_size_default,
        settings.page_size_max,
    )

    base = select(FeedbackItem).where(col(FeedbackItem.workspace_id) == ctx.id)
    count_q = (
        select(func.count())
        .select_from(FeedbackItem)
        .where(col(FeedbackItem.workspace_id) == ctx.id)
    )

    from sqlalchemy.sql import Select

    def _apply(query: Select) -> Select:  # type: ignore[type-arg]
        if status_filter is not None:
            query = query.where(col(FeedbackItem.status) == status_filter)
        if source is not None:
            query = query.where(col(FeedbackItem.source) == source)
        if type_filter is not None:
            query = query.where(col(FeedbackItem.type) == type_filter)
        if priority is not None:
            query = query.where(col(FeedbackItem.priority) == priority)
        if submitter_id is not None:
            query = query.where(col(FeedbackItem.submitter_id) == submitter_id)
        if published_to_roadmap is not None:
            query = query.where(
                col(FeedbackItem.published_to_roadmap) == published_to_roadmap,
            )
        if published_to_changelog is not None:
            query = query.where(
                col(FeedbackItem.published_to_changelog) == published_to_changelog,
            )
        if created_after is not None:
            query = query.where(col(FeedbackItem.created_at) >= created_after)
        if created_before is not None:
            query = query.where(col(FeedbackItem.created_at) <= created_before)
        if stale is True:
            query = query.where(stale_clause())
        elif stale is False:
            query = query.where(~stale_clause())
        if q is not None:
            pattern = f"%{q}%"
            query = query.where(
                col(FeedbackItem.title).ilike(pattern)
                | col(FeedbackItem.description).ilike(pattern),
            )
        if tag is not None:
            query = query.join(
                FeedbackTag,
                col(FeedbackTag.feedback_id) == col(FeedbackItem.id),
            ).where(col(FeedbackTag.tag_id) == tag)
        return query

    total = db.execute(_apply(count_q)).scalar_one()
    items = (
        db.execute(_apply(base).order_by(order).offset(skip).limit(effective_limit))
        .scalars()
        .all()
    )
    return FeedbackListEnvelopeV2(
        items=[FeedbackResponseV2.model_validate(i) for i in items],
        total=total,
        skip=skip,
        limit=effective_limit,
    )


@router.get(
    "/{item_id}",
    response_model=FeedbackResponseV2,
    summary="Get one feedback item",
)
def get_feedback(
    item_id: int,
    ctx: WorkspaceContextDep,
    db: DbDep,
) -> FeedbackResponseV2:
    """Return a single feedback item, scoped to the workspace."""
    item = _scoped_get(db, item_id, ctx.id)
    return FeedbackResponseV2.model_validate(item)


@router.patch(
    "/{item_id}",
    response_model=FeedbackResponseV2,
    summary="Partially update a feedback item",
)
def patch_feedback(
    item_id: int,
    payload: FeedbackUpdateV2,
    ctx: Annotated[WorkspaceContext, Depends(require_writable)],
    db: DbDep,
    settings: SettingsDep,
) -> FeedbackResponseV2:
    """Apply a partial update; missing fields are left untouched."""
    item = _scoped_get(db, item_id, ctx.id)
    old_status = item.status
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(item, field, value)
    if not changes:
        # Empty PATCH still triggers UPDATE so the BEFORE UPDATE
        # trigger fires and ``updated_at`` advances.
        attributes.flag_modified(item, "updated_at")
    db.add(item)
    db.flush()
    db.refresh(item)
    new_status = item.status
    response = FeedbackResponseV2.model_validate(item)
    # Status-change notifications (PR 3.1). The transaction boundary
    # lives in ``get_db`` (database.py) — handlers must not commit
    # themselves. ``EmailClient.send`` is fail-soft per ADR 061 and
    # uses a separate session for ``email_log`` writes, so a provider
    # outage cannot roll back this PATCH. Any *unexpected* exception
    # from the notifier (template render, attribute error, …) is
    # caught and logged here so it can't either.
    if old_status != new_status:
        try:
            notify_status_change(
                db=db,
                settings=settings,
                item=item,
                old_status=old_status,
                new_status=new_status,
            )
        except Exception:
            logger.exception(
                "feedback.patch: status-change notifier raised; "
                "PATCH will still commit (item_id=%s)",
                item_id,
            )
    return response


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a feedback item",
)
def delete_feedback(
    item_id: int,
    ctx: Annotated[WorkspaceContext, Depends(require_writable)],
    db: DbDep,
) -> Response:
    """Hard-delete a feedback item; cascades to tags + notes."""
    item = _scoped_get(db, item_id, ctx.id)
    db.delete(item)
    db.flush()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Tag replace
# ---------------------------------------------------------------------------


@router.post(
    "/{item_id}/tags",
    response_model=FeedbackResponseV2,
    summary="Replace the tag set on a feedback item",
)
def replace_feedback_tags(
    item_id: int,
    payload: FeedbackTagsReplaceRequest,
    ctx: Annotated[WorkspaceContext, Depends(require_writable)],
    db: DbDep,
) -> FeedbackResponseV2:
    """Replace ``feedback_tags`` rows for ``item_id``.

    Every requested tag must belong to the same workspace as the
    feedback item; cross-tenant tag ids 404 (not 400) so the response
    cannot be used to enumerate tag ids in another workspace.
    """
    item = _scoped_get(db, item_id, ctx.id)
    requested = list(dict.fromkeys(payload.tag_ids))  # preserve order, dedupe
    if requested:
        rows = (
            db.execute(
                select(Tag).where(
                    col(Tag.id).in_(requested),
                    col(Tag.workspace_id) == ctx.id,
                ),
            )
            .scalars()
            .all()
        )
        if len(rows) != len(requested):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more tags not found in this workspace.",
            )

    # Drop existing pairs, insert the new set. The composite PK plus
    # ``ON DELETE CASCADE`` keeps the join clean.
    db.execute(
        FeedbackTag.__table__.delete().where(  # type: ignore[attr-defined]
            col(FeedbackTag.feedback_id) == item.id,
        ),
    )
    for tag_id in requested:
        db.add(FeedbackTag(feedback_id=item.id, tag_id=tag_id))
    # Bump updated_at on the parent feedback row so the timeline
    # reflects the tag change.
    attributes.flag_modified(item, "updated_at")
    db.add(item)
    db.flush()
    db.refresh(item)
    return FeedbackResponseV2.model_validate(item)


# ---------------------------------------------------------------------------
# Notes sub-resource
# ---------------------------------------------------------------------------


def _scoped_note(
    db: DbSession,
    *,
    item_id: int,
    note_id: uuid.UUID,
    workspace_id: uuid.UUID,
) -> tuple[FeedbackItem, FeedbackNote]:
    """Load (item, note) pair, asserting both belong to this workspace."""
    item = _scoped_get(db, item_id, workspace_id)
    note = db.get(FeedbackNote, note_id)
    if note is None or note.feedback_id != item.id:
        raise _NOTE_NOT_FOUND
    return item, note


@router.get(
    "/{item_id}/notes",
    response_model=NoteListEnvelope,
    summary="List internal notes for a feedback item",
)
def list_notes(
    item_id: int,
    ctx: WorkspaceContextDep,
    db: DbDep,
    settings: SettingsDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int | None, Query(ge=1, le=1000)] = None,
) -> NoteListEnvelope:
    """Return notes ordered oldest-first (timeline order)."""
    item = _scoped_get(db, item_id, ctx.id)
    effective_limit = min(
        limit if limit is not None else settings.page_size_default,
        settings.page_size_max,
    )
    base = (
        select(FeedbackNote)
        .where(col(FeedbackNote.feedback_id) == item.id)
        .order_by(asc(col(FeedbackNote.created_at)))
    )
    count_q = (
        select(func.count())
        .select_from(FeedbackNote)
        .where(col(FeedbackNote.feedback_id) == item.id)
    )
    total = db.execute(count_q).scalar_one()
    rows = db.execute(base.offset(skip).limit(effective_limit)).scalars().all()
    return NoteListEnvelope(
        items=[NoteResponse.model_validate(n) for n in rows],
        total=total,
        skip=skip,
        limit=effective_limit,
    )


@router.post(
    "/{item_id}/notes",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an internal note to a feedback item",
)
def create_note(
    item_id: int,
    payload: NoteCreateRequest,
    ctx: Annotated[WorkspaceContext, Depends(require_writable)],
    user: CurrentUserDep,
    db: DbDep,
) -> NoteResponse:
    """Append an internal note authored by the current user."""
    item = _scoped_get(db, item_id, ctx.id)
    assert user.id is not None
    note = FeedbackNote(
        feedback_id=item.id,
        author_user_id=user.id,
        body=payload.body,
    )
    db.add(note)
    db.flush()
    db.refresh(note)
    return NoteResponse.model_validate(note)


@router.patch(
    "/{item_id}/notes/{note_id}",
    response_model=NoteResponse,
    summary="Edit an internal note (author + 15-minute window)",
)
def patch_note(
    item_id: int,
    note_id: uuid.UUID,
    payload: NoteUpdateRequest,
    ctx: Annotated[WorkspaceContext, Depends(require_writable)],
    user: CurrentUserDep,
    db: DbDep,
) -> NoteResponse:
    """Edit a note's body within 15 minutes of creation, by the author."""
    _, note = _scoped_note(db, item_id=item_id, note_id=note_id, workspace_id=ctx.id)
    if note.author_user_id != user.id:
        # Same shape as cross-tenant: do not reveal whether the note
        # belongs to a different author by returning 403; ``404``
        # keeps the surface uniform.
        raise _NOTE_NOT_FOUND
    age = datetime.now(tz=UTC) - note.created_at
    if age > NOTE_EDIT_WINDOW:
        raise _NOTE_EDIT_WINDOW_CLOSED
    note.body = payload.body
    db.add(note)
    db.flush()
    db.refresh(note)
    return NoteResponse.model_validate(note)


@router.delete(
    "/{item_id}/notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a note (author or workspace owner)",
)
def delete_note(
    item_id: int,
    note_id: uuid.UUID,
    ctx: Annotated[WorkspaceContext, Depends(require_writable)],
    user: CurrentUserDep,
    db: DbDep,
) -> Response:
    """Delete an internal note; allowed to its author or the workspace owner."""
    _, note = _scoped_note(db, item_id=item_id, note_id=note_id, workspace_id=ctx.id)
    is_author = note.author_user_id == user.id
    is_owner = ctx.role in (WorkspaceRole.OWNER, "admin") or (
        user.role == UserRole.ADMIN
    )
    if not (is_author or is_owner):
        raise _NOTE_NOT_FOUND
    db.delete(note)
    db.flush()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
