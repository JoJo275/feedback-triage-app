"""``/api/v1/tags`` — workspace-scoped tag CRUD (PR 2.2).

Tags are per-workspace categorisation chips (see
``docs/project/spec/v2/schema.md`` — ``tags``). Read access is open
to any workspace member; create/update/delete are owner-only per
``docs/project/spec/v2/api.md`` — Tags. Demo workspaces are
read-only via :func:`require_writable`.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import asc, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession
from sqlmodel import col, select

from feedback_triage.api.v1._feedback_schemas import (
    TagCreateRequest,
    TagListEnvelope,
    TagResponse,
    TagUpdateRequest,
)
from feedback_triage.config import Settings, get_settings
from feedback_triage.database import get_db
from feedback_triage.enums import WorkspaceRole
from feedback_triage.models import Tag
from feedback_triage.tenancy import (
    WorkspaceContext,
    WorkspaceContextDep,
    require_workspace_role,
    require_writable,
)

router = APIRouter(prefix="/api/v1/tags", tags=["tags"])

DbDep = Annotated[DbSession, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]

_NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Tag not found",
)
_SLUG_CONFLICT = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail={
        "code": "tag_slug_taken",
        "message": "A tag with this slug already exists in the workspace.",
    },
)


def _scoped_get(db: DbSession, tag_id: uuid.UUID, workspace_id: uuid.UUID) -> Tag:
    """Load a tag by id within the caller's workspace."""
    tag = db.get(Tag, tag_id)
    if tag is None or tag.workspace_id != workspace_id:
        raise _NOT_FOUND
    return tag


@router.get("", response_model=TagListEnvelope, summary="List tags")
def list_tags(
    ctx: WorkspaceContextDep,
    db: DbDep,
    settings: SettingsDep,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int | None, Query(ge=1, le=1000)] = None,
) -> TagListEnvelope:
    """Return all tags in the workspace, ordered by name."""
    effective_limit = min(
        limit if limit is not None else settings.page_size_default,
        settings.page_size_max,
    )
    base = (
        select(Tag).where(col(Tag.workspace_id) == ctx.id).order_by(asc(col(Tag.name)))
    )
    count_q = (
        select(func.count()).select_from(Tag).where(col(Tag.workspace_id) == ctx.id)
    )
    total = db.execute(count_q).scalar_one()
    rows = db.execute(base.offset(skip).limit(effective_limit)).scalars().all()
    return TagListEnvelope(
        items=[TagResponse.model_validate(t) for t in rows],
        total=total,
        skip=skip,
        limit=effective_limit,
    )


@router.post(
    "",
    response_model=TagResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a tag (owner only)",
    dependencies=[Depends(require_workspace_role(WorkspaceRole.OWNER))],
)
def create_tag(
    payload: TagCreateRequest,
    ctx: Annotated[WorkspaceContext, Depends(require_writable)],
    db: DbDep,
) -> TagResponse:
    """Create a workspace-scoped tag.

    Returns ``409`` with ``code=tag_slug_taken`` on slug collisions
    rather than letting the unique-constraint IntegrityError bubble
    to the generic 500 handler.
    """
    tag = Tag(
        workspace_id=ctx.id,
        name=payload.name,
        slug=payload.slug,
        color=payload.color,
    )
    db.add(tag)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        if "tags_workspace_slug_uq" in str(exc.orig):
            raise _SLUG_CONFLICT from exc
        raise
    db.refresh(tag)
    return TagResponse.model_validate(tag)


@router.patch(
    "/{tag_id}",
    response_model=TagResponse,
    summary="Rename or recolour a tag (owner only)",
    dependencies=[Depends(require_workspace_role(WorkspaceRole.OWNER))],
)
def patch_tag(
    tag_id: uuid.UUID,
    payload: TagUpdateRequest,
    ctx: Annotated[WorkspaceContext, Depends(require_writable)],
    db: DbDep,
) -> TagResponse:
    """Apply a partial update to a tag."""
    tag = _scoped_get(db, tag_id, ctx.id)
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(tag, field, value)
    db.add(tag)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        if "tags_workspace_slug_uq" in str(exc.orig):
            raise _SLUG_CONFLICT from exc
        raise
    db.refresh(tag)
    return TagResponse.model_validate(tag)


@router.delete(
    "/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a tag (owner only); cascades to feedback_tags",
    dependencies=[Depends(require_workspace_role(WorkspaceRole.OWNER))],
)
def delete_tag(
    tag_id: uuid.UUID,
    ctx: Annotated[WorkspaceContext, Depends(require_writable)],
    db: DbDep,
) -> Response:
    """Delete a tag; the FK cascade removes its ``feedback_tags`` rows."""
    tag = _scoped_get(db, tag_id, ctx.id)
    db.delete(tag)
    db.flush()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
