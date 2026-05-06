"""SQLModel ORM model for the ``submitters`` table.

A ``submitter`` row collapses repeat senders (matched by
``workspace_id`` + ``email``) into one identity for triage and
follow-up. Anonymous public submissions store ``email IS NULL`` —
the per-workspace ``UNIQUE (workspace_id, email)`` constraint
permits any number of NULL-email rows. Canonical schema in
``alembic/versions/0003_v2_b_workflow_tables.py`` and
``docs/project/spec/v2/schema.md``.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import CITEXT, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlmodel import Column, Field, SQLModel


class Submitter(SQLModel, table=True):
    """A workspace-scoped, deduplicated feedback submitter."""

    __tablename__ = "submitters"
    __table_args__ = (
        UniqueConstraint("workspace_id", "email", name="submitters_workspace_email_uq"),
        CheckConstraint(
            "name IS NULL OR length(name) <= 120",
            name="submitters_name_max_len",
        ),
        CheckConstraint(
            "internal_notes IS NULL OR length(internal_notes) <= 4000",
            name="submitters_internal_notes_max_len",
        ),
        CheckConstraint(
            "submission_count >= 0",
            name="submitters_submission_count_nonneg",
        ),
    )

    id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            PgUUID(as_uuid=True),
            primary_key=True,
            server_default=text("gen_random_uuid()"),
            nullable=False,
        ),
    )
    workspace_id: uuid.UUID = Field(
        sa_column=Column(
            PgUUID(as_uuid=True),
            ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    email: str | None = Field(
        default=None,
        sa_column=Column(CITEXT(), nullable=True),
    )
    name: str | None = Field(
        default=None,
        sa_column=Column("name", nullable=True),
    )
    internal_notes: str | None = Field(
        default=None,
        sa_column=Column("internal_notes", nullable=True),
    )
    first_seen_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=func.now(),
        ),
    )
    last_seen_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=func.now(),
        ),
    )
    submission_count: int = Field(
        default=0,
        sa_column=Column(
            "submission_count",
            nullable=False,
            server_default=text("0"),
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
