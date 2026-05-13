"""SQLModel ORM model for the ``feedback_item`` table.

The model defines the shape; the canonical schema is owned by Alembic
(see ``alembic/versions/0001_create_feedback_item.py``). Both must agree
with the Postgres specification in ``docs/project/spec/spec-v1.md``.

Key choices (see spec — PostgreSQL Specification):

- ``text`` columns; length is enforced by ``CHECK`` constraints in the
  migration, not ``VARCHAR(n)``.
- Native Postgres enums (``source_enum``, ``status_enum``) created and
  owned by the migration; ``create_type=False`` keeps SQLAlchemy's
  ``metadata.create_all()`` from trying to manage the type.
- ``server_default=func.now()`` on both timestamps; ``updated_at`` is
  bumped by a ``BEFORE UPDATE`` trigger, not ORM ``onupdate``.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, SmallInteger, func, text
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlmodel import Column, Field, SQLModel

from feedback_triage.enums import (
    PRIORITY_ENUM,
    TYPE_ENUM,
    FeedbackType,
    Priority,
    Source,
    Status,
)

# Native Postgres enum types. ``create_type=False`` because the migration
# owns the CREATE TYPE / DROP TYPE lifecycle — see spec — SQLModel /
# SQLAlchemy mapping.
SOURCE_ENUM = PgEnum(
    Source,
    name="source_enum",
    values_callable=lambda enum_cls: [m.value for m in enum_cls],
    create_type=False,
)

STATUS_ENUM = PgEnum(
    Status,
    name="status_enum",
    values_callable=lambda enum_cls: [m.value for m in enum_cls],
    create_type=False,
)


class FeedbackItem(SQLModel, table=True):
    """A single piece of customer feedback awaiting triage."""

    __tablename__ = "feedback_item"
    __table_args__ = (
        CheckConstraint(
            "pain_level BETWEEN 1 AND 5",
            name="feedback_item_pain_level_range",
        ),
        CheckConstraint(
            "length(btrim(title)) > 0",
            name="feedback_item_title_not_blank",
        ),
        CheckConstraint(
            "length(title) <= 200",
            name="feedback_item_title_max_len",
        ),
        CheckConstraint(
            "description IS NULL OR length(description) <= 5000",
            name="feedback_item_description_max_len",
        ),
        # Migration B (PR 2.1) — workflow columns. ``rejected`` is no
        # longer a writeable status (ADR 063); the application is
        # forbidden from producing it via this CHECK and the
        # backfill rewrites every legacy row to ``closed``.
        CheckConstraint(
            "status <> 'rejected'",
            name="feedback_item_status_not_rejected",
        ),
        CheckConstraint(
            "source_other IS NULL OR length(source_other) <= 60",
            name="feedback_item_source_other_max_len",
        ),
        CheckConstraint(
            "type_other IS NULL OR length(type_other) <= 60",
            name="feedback_item_type_other_max_len",
        ),
        # One-way invariant: a free-text fallback is only valid when
        # its enum is ``other``. See the migration for the rationale
        # for not using the spec's biconditional form.
        CheckConstraint(
            "source_other IS NULL OR source = 'other'",
            name="feedback_item_source_other_chk",
        ),
        CheckConstraint(
            "type_other IS NULL OR type = 'other'",
            name="feedback_item_type_other_chk",
        ),
        CheckConstraint(
            "release_note IS NULL OR length(release_note) <= 280",
            name="feedback_item_release_note_max_len",
        ),
    )

    id: int | None = Field(
        default=None,
        sa_column=Column(
            BigInteger,
            primary_key=True,
            autoincrement=True,
        ),
    )
    title: str = Field(sa_column=Column("title", nullable=False))
    description: str | None = Field(
        default=None,
        sa_column=Column("description", nullable=True),
    )
    source: Source = Field(sa_column=Column(SOURCE_ENUM, nullable=False))
    pain_level: int = Field(sa_column=Column(SmallInteger, nullable=False))
    status: Status = Field(
        default=Status.NEW,
        sa_column=Column(
            STATUS_ENUM,
            nullable=False,
            server_default=text("'new'::status_enum"),
        ),
    )
    created_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=func.now(),
        ),
    )
    updated_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=func.now(),
        ),
    )
    # ------------------------------------------------------------------
    # v2 columns (Migration A added ``workspace_id`` nullable; PR 2.1's
    # Migration B flips it to NOT NULL and adds the rest below).
    # ------------------------------------------------------------------
    workspace_id: uuid.UUID = Field(
        sa_column=Column(
            PgUUID(as_uuid=True),
            ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    submitter_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            PgUUID(as_uuid=True),
            ForeignKey("submitters.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    assignee_user_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            PgUUID(as_uuid=True),
            ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    type: FeedbackType = Field(
        default=FeedbackType.OTHER,
        sa_column=Column(
            TYPE_ENUM,
            nullable=False,
            server_default=text("'other'::type_enum"),
        ),
    )
    priority: Priority | None = Field(
        default=None,
        sa_column=Column(PRIORITY_ENUM, nullable=True),
    )
    source_other: str | None = Field(
        default=None,
        sa_column=Column("source_other", nullable=True),
    )
    type_other: str | None = Field(
        default=None,
        sa_column=Column("type_other", nullable=True),
    )
    published_to_roadmap: bool = Field(
        default=False,
        sa_column=Column(
            "published_to_roadmap",
            nullable=False,
            server_default=text("false"),
        ),
    )
    published_to_changelog: bool = Field(
        default=False,
        sa_column=Column(
            "published_to_changelog",
            nullable=False,
            server_default=text("false"),
        ),
    )
    release_note: str | None = Field(
        default=None,
        sa_column=Column("release_note", nullable=True),
    )
