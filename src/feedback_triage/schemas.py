"""Pydantic request and response schemas for the feedback API.

These are the API boundary, separate from the SQLModel ORM in
``models.py``. Datetimes always serialize as ISO 8601 in UTC with a
trailing ``Z`` and microsecond precision (see spec — Datetime
serialization). The list endpoint always returns the
``FeedbackListEnvelope`` shape, never a bare array.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from feedback_triage.enums import Source, Status


def _serialize_datetime(value: datetime) -> str:
    """Render a datetime as ISO 8601 with microseconds and a ``Z`` suffix."""
    value = value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
    return value.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


# Sortable fields for ``GET /feedback?sort_by=...``. ``-`` prefix means
# descending. Anything outside this allow-list is rejected with 422
# (see spec — Validation Rules).
SORTABLE_FIELDS: frozenset[str] = frozenset(
    {
        "created_at",
        "-created_at",
        "pain_level",
        "-pain_level",
        "status",
        "-status",
        "source",
        "-source",
    }
)


class FeedbackBase(BaseModel):
    """Shared validation rules for create/update payloads."""

    model_config = ConfigDict(str_strip_whitespace=False, extra="forbid")

    title: Annotated[str, Field(min_length=1, max_length=200)]
    description: Annotated[str | None, Field(default=None, max_length=5000)] = None
    source: Source
    pain_level: Annotated[int, Field(ge=1, le=5)]
    status: Status = Status.NEW

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title must not be blank")
        return value


class FeedbackCreate(FeedbackBase):
    """Payload for ``POST /feedback``."""


class FeedbackUpdate(BaseModel):
    """Partial-update payload for ``PATCH /feedback/{id}``.

    All fields are optional; only those present are applied. Field-level
    rules mirror :class:`FeedbackCreate` so a partial update cannot
    smuggle a value the create endpoint would reject.
    """

    model_config = ConfigDict(extra="forbid")

    title: Annotated[str | None, Field(default=None, min_length=1, max_length=200)] = (
        None
    )
    description: Annotated[str | None, Field(default=None, max_length=5000)] = None
    source: Source | None = None
    pain_level: Annotated[int | None, Field(default=None, ge=1, le=5)] = None
    status: Status | None = None

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("title must not be blank")
        return value


class FeedbackResponse(BaseModel):
    """Outbound representation of a feedback item."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    source: Source
    pain_level: int
    status: Status
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def _ser_dt(self, value: datetime) -> str:
        return _serialize_datetime(value)


class FeedbackListEnvelope(BaseModel):
    """Paginated list response. See spec — List."""

    items: list[FeedbackResponse]
    total: int
    skip: int
    limit: int
