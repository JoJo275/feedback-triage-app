"""Pydantic v2 request/response schemas for the v2 feedback surface.

Covers the four resource families introduced in PR 2.2 — feedback,
tags, feedback notes, submitters — plus the shared list-envelope
shape every list endpoint emits. The v1 :mod:`feedback_triage.schemas`
module stays untouched for existing imports; v2 schemas live here so
the API boundary tracks ``docs/project/spec/v2/api.md`` and
``schema.md`` in one place.

Datetime serialisation follows the v1 convention (ISO 8601 with
microseconds + ``Z`` suffix) — see ``docs/project/spec/v2/api.md``
— Datetime serialization.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from feedback_triage.enums import (
    FeedbackType,
    Priority,
    Source,
    Status,
)

# Tag colour palette — keep in lock-step with the
# ``tags_color_palette`` CHECK constraint in Migration B2.
TagColor = Literal[
    "slate",
    "teal",
    "amber",
    "rose",
    "indigo",
    "sky",
    "green",
    "violet",
]


def _serialize_datetime(value: datetime) -> str:
    """Render a datetime as ISO 8601 UTC with microseconds + ``Z``."""
    value = value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
    return value.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------


class FeedbackCreateV2(BaseModel):
    """Payload for ``POST /api/v1/feedback`` (workspace-scoped)."""

    model_config = ConfigDict(extra="forbid")

    title: Annotated[str, Field(min_length=1, max_length=200)]
    description: Annotated[str | None, Field(default=None, max_length=5000)] = None
    source: Source
    source_other: Annotated[str | None, Field(default=None, max_length=60)] = None
    pain_level: Annotated[int, Field(ge=1, le=5)]
    status: Status = Status.NEW
    type: FeedbackType = FeedbackType.OTHER
    type_other: Annotated[str | None, Field(default=None, max_length=60)] = None
    priority: Priority | None = None

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title must not be blank")
        return value

    @field_validator("status")
    @classmethod
    def _no_rejected_writes(cls, value: Status) -> Status:
        # ``rejected`` is forbidden by the DB CHECK; reject early so
        # the caller gets a 422 rather than a 500.
        if value == Status.REJECTED:
            raise ValueError("status 'rejected' is not writable in v2 (ADR 063)")
        return value


class FeedbackUpdateV2(BaseModel):
    """Partial-update payload for ``PATCH /api/v1/feedback/{id}``."""

    model_config = ConfigDict(extra="forbid")

    title: Annotated[str | None, Field(default=None, min_length=1, max_length=200)] = (
        None
    )
    description: Annotated[str | None, Field(default=None, max_length=5000)] = None
    source: Source | None = None
    source_other: Annotated[str | None, Field(default=None, max_length=60)] = None
    pain_level: Annotated[int | None, Field(default=None, ge=1, le=5)] = None
    status: Status | None = None
    type: FeedbackType | None = None
    type_other: Annotated[str | None, Field(default=None, max_length=60)] = None
    priority: Priority | None = None
    published_to_roadmap: bool | None = None
    published_to_changelog: bool | None = None
    release_note: Annotated[str | None, Field(default=None, max_length=280)] = None

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("title must not be blank")
        return value

    @field_validator("status")
    @classmethod
    def _no_rejected_writes(cls, value: Status | None) -> Status | None:
        if value == Status.REJECTED:
            raise ValueError("status 'rejected' is not writable in v2 (ADR 063)")
        return value


class FeedbackResponseV2(BaseModel):
    """Outbound representation of a v2 feedback item."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    workspace_id: uuid.UUID
    submitter_id: uuid.UUID | None
    title: str
    description: str | None
    source: Source
    source_other: str | None
    type: FeedbackType
    type_other: str | None
    priority: Priority | None
    pain_level: int
    status: Status
    published_to_roadmap: bool
    published_to_changelog: bool
    release_note: str | None
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def _ser_dt(self, value: datetime) -> str:
        return _serialize_datetime(value)


class FeedbackListEnvelopeV2(BaseModel):
    """Paginated envelope for ``GET /api/v1/feedback``."""

    items: list[FeedbackResponseV2]
    total: int
    skip: int
    limit: int


class FeedbackTagsReplaceRequest(BaseModel):
    """Payload for ``POST /api/v1/feedback/{id}/tags``."""

    model_config = ConfigDict(extra="forbid")

    tag_ids: Annotated[list[uuid.UUID], Field(max_length=50)]


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------

_SLUG_PATTERN = r"^[a-z0-9](?:[a-z0-9-]{0,38}[a-z0-9])?$"


class TagCreateRequest(BaseModel):
    """Payload for ``POST /api/v1/tags``."""

    model_config = ConfigDict(extra="forbid")

    name: Annotated[str, Field(min_length=1, max_length=40)]
    slug: Annotated[str, Field(min_length=1, max_length=40, pattern=_SLUG_PATTERN)]
    color: TagColor = "slate"


class TagUpdateRequest(BaseModel):
    """Payload for ``PATCH /api/v1/tags/{id}``."""

    model_config = ConfigDict(extra="forbid")

    name: Annotated[str | None, Field(default=None, min_length=1, max_length=40)] = None
    slug: Annotated[
        str | None,
        Field(default=None, min_length=1, max_length=40, pattern=_SLUG_PATTERN),
    ] = None
    color: TagColor | None = None


class TagResponse(BaseModel):
    """Outbound representation of a tag."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    slug: str
    color: str
    created_at: datetime

    @field_serializer("created_at")
    def _ser_dt(self, value: datetime) -> str:
        return _serialize_datetime(value)


class TagListEnvelope(BaseModel):
    """Paginated envelope for ``GET /api/v1/tags``."""

    items: list[TagResponse]
    total: int
    skip: int
    limit: int


# ---------------------------------------------------------------------------
# Notes
# ---------------------------------------------------------------------------


class NoteCreateRequest(BaseModel):
    """Payload for ``POST /api/v1/feedback/{id}/notes``."""

    model_config = ConfigDict(extra="forbid")

    body: Annotated[str, Field(min_length=1, max_length=4000)]


class NoteUpdateRequest(BaseModel):
    """Payload for ``PATCH /api/v1/feedback/{id}/notes/{note_id}``."""

    model_config = ConfigDict(extra="forbid")

    body: Annotated[str, Field(min_length=1, max_length=4000)]


class NoteResponse(BaseModel):
    """Outbound representation of an internal feedback note."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    feedback_id: int
    author_user_id: uuid.UUID
    body: str
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def _ser_dt(self, value: datetime) -> str:
        return _serialize_datetime(value)


class NoteListEnvelope(BaseModel):
    """Paginated envelope for ``GET /api/v1/feedback/{id}/notes``."""

    items: list[NoteResponse]
    total: int
    skip: int
    limit: int


# ---------------------------------------------------------------------------
# Submitters
# ---------------------------------------------------------------------------


class SubmitterUpdateRequest(BaseModel):
    """Payload for ``PATCH /api/v1/submitters/{id}``."""

    model_config = ConfigDict(extra="forbid")

    name: Annotated[str | None, Field(default=None, max_length=120)] = None
    internal_notes: Annotated[str | None, Field(default=None, max_length=4000)] = None


class SubmitterResponse(BaseModel):
    """Outbound representation of a submitter."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    email: str | None
    name: str | None
    internal_notes: str | None
    submission_count: int
    first_seen_at: datetime
    last_seen_at: datetime
    created_at: datetime
    updated_at: datetime

    @field_serializer(
        "first_seen_at",
        "last_seen_at",
        "created_at",
        "updated_at",
    )
    def _ser_dt(self, value: datetime) -> str:
        return _serialize_datetime(value)


class SubmitterListEnvelope(BaseModel):
    """Paginated envelope for ``GET /api/v1/submitters``."""

    items: list[SubmitterResponse]
    total: int
    skip: int
    limit: int


__all__ = [
    "FeedbackCreateV2",
    "FeedbackListEnvelopeV2",
    "FeedbackResponseV2",
    "FeedbackTagsReplaceRequest",
    "FeedbackUpdateV2",
    "NoteCreateRequest",
    "NoteListEnvelope",
    "NoteResponse",
    "NoteUpdateRequest",
    "SubmitterListEnvelope",
    "SubmitterResponse",
    "SubmitterUpdateRequest",
    "TagColor",
    "TagCreateRequest",
    "TagListEnvelope",
    "TagResponse",
    "TagUpdateRequest",
]
