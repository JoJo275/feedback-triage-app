"""SQLModel ORM model for the ``feedback_tags`` join table.

Many-to-many bridge between ``feedback_item`` and ``tags``. Composite
primary key (``feedback_id``, ``tag_id``); both legs cascade. The
``feedback_id`` column type intentionally tracks ``feedback_item.id``
(``BigInteger``) — the schema spec sketch shows ``uuid``, but
v2.0 keeps the v1 identity primary key (out of scope for PR 2.1).
Canonical schema in
``alembic/versions/0003_v2_b_workflow_tables.py``.
"""

from __future__ import annotations

import uuid

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlmodel import Column, Field, SQLModel


class FeedbackTag(SQLModel, table=True):
    """One row per (feedback item, tag) pairing."""

    __tablename__ = "feedback_tags"

    feedback_id: int = Field(
        sa_column=Column(
            BigInteger,
            ForeignKey("feedback_item.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
    )
    tag_id: uuid.UUID = Field(
        sa_column=Column(
            PgUUID(as_uuid=True),
            ForeignKey("tags.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
    )
