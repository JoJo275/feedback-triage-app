"""``/api/v1/submitters`` — workspace-scoped submitter endpoints (PR 2.2).

A ``submitter`` row collapses repeat senders into a single triage
identity per workspace. The v2.0 surface is read + edit-metadata; new
submitters are created automatically by the public-submission link
service in PR 2.4 (``services/submitter_link.py``), not by this
router.

See ``docs/project/spec/v2/api.md`` — Submitters.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session as DbSession
from sqlmodel import col, select

from feedback_triage.api.v1._feedback_schemas import (
    SubmitterListEnvelope,
    SubmitterResponse,
    SubmitterUpdateRequest,
)
from feedback_triage.config import Settings, get_settings
from feedback_triage.database import get_db
from feedback_triage.models import Submitter
from feedback_triage.tenancy import (
    WorkspaceContext,
    WorkspaceContextDep,
    require_writable,
)

router = APIRouter(prefix="/api/v1/submitters", tags=["submitters"])

DbDep = Annotated[DbSession, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]

_NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Submitter not found",
)


def _scoped_get(
    db: DbSession,
    submitter_id: uuid.UUID,
    workspace_id: uuid.UUID,
) -> Submitter:
    """Load a submitter, asserting it belongs to the caller's workspace."""
    submitter = db.get(Submitter, submitter_id)
    if submitter is None or submitter.workspace_id != workspace_id:
        raise _NOT_FOUND
    return submitter


@router.get("", response_model=SubmitterListEnvelope, summary="List submitters")
def list_submitters(
    ctx: WorkspaceContextDep,
    db: DbDep,
    settings: SettingsDep,
    q: Annotated[str | None, Query(min_length=1, max_length=200)] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int | None, Query(ge=1, le=1000)] = None,
) -> SubmitterListEnvelope:
    """Return submitters; ``q`` matches name and email (case-insensitive)."""
    effective_limit = min(
        limit if limit is not None else settings.page_size_default,
        settings.page_size_max,
    )
    base = select(Submitter).where(col(Submitter.workspace_id) == ctx.id)
    count_q = (
        select(func.count())
        .select_from(Submitter)
        .where(col(Submitter.workspace_id) == ctx.id)
    )
    if q is not None:
        pattern = f"%{q}%"
        # ``email`` is CITEXT so plain ``ilike`` matches case-
        # insensitively without forcing a function index.
        predicate = or_(
            col(Submitter.name).ilike(pattern),
            col(Submitter.email).ilike(pattern),
        )
        base = base.where(predicate)
        count_q = count_q.where(predicate)

    total = db.execute(count_q).scalar_one()
    rows = (
        db.execute(
            base.order_by(desc(col(Submitter.last_seen_at)))
            .offset(skip)
            .limit(effective_limit),
        )
        .scalars()
        .all()
    )
    return SubmitterListEnvelope(
        items=[SubmitterResponse.model_validate(s) for s in rows],
        total=total,
        skip=skip,
        limit=effective_limit,
    )


@router.get(
    "/{submitter_id}",
    response_model=SubmitterResponse,
    summary="Get one submitter",
)
def get_submitter(
    submitter_id: uuid.UUID,
    ctx: WorkspaceContextDep,
    db: DbDep,
) -> SubmitterResponse:
    """Return a single submitter scoped to the workspace."""
    submitter = _scoped_get(db, submitter_id, ctx.id)
    return SubmitterResponse.model_validate(submitter)


@router.patch(
    "/{submitter_id}",
    response_model=SubmitterResponse,
    summary="Edit submitter name / internal notes",
)
def patch_submitter(
    submitter_id: uuid.UUID,
    payload: SubmitterUpdateRequest,
    ctx: Annotated[WorkspaceContext, Depends(require_writable)],
    db: DbDep,
) -> SubmitterResponse:
    """Apply a partial update; only ``name`` and ``internal_notes`` are writable."""
    submitter = _scoped_get(db, submitter_id, ctx.id)
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(submitter, field, value)
    db.add(submitter)
    db.flush()
    db.refresh(submitter)
    return SubmitterResponse.model_validate(submitter)
