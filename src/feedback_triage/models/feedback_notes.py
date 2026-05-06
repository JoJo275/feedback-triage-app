"""SQLModel ORM model for the ``feedback_notes`` table.

Internal team-only notes attached to a ``feedback_item``. The
``author_user_id`` FK uses ``ON DELETE RESTRICT`` so deleting a user
forces an explicit decision about what to do with their notes;
deleting the feedback item cascades. Canonical schema in
``alembic/versions/0003_v2_b_workflow_tables.py`` and
``docs/project/spec/v2/schema.md``.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, func, text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlmodel import Column, Field, SQLModel


class FeedbackNote(SQLModel, table=True):
    """One internal note attached to a feedback item."""

    __tablename__ = "feedback_notes"
    __table_args__ = (
        CheckConstraint(
            "length(body) BETWEEN 1 AND 4000",
            name="feedback_notes_body_len",
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
    feedback_id: int = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey("feedback_item.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    author_user_id: uuid.UUID = Field(
        sa_column=Column(
            PgUUID(as_uuid=True),
            ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
    )
    body: str = Field(sa_column=Column("body", nullable=False))
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
