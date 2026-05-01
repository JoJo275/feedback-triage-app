"""SQLModel ORM models.

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

from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, SmallInteger, func, text
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlmodel import Column, Field, SQLModel

from feedback_triage.enums import Source, Status

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
