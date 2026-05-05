"""SQLModel ORM model for the ``workspaces`` table.

Canonical schema lives in
``alembic/versions/0002_v2_a_auth_tenancy_email_log.py`` and
``docs/project/spec/v2/schema.md``. ``slug`` is ``citext`` and is the
stable URL identifier; ``id`` (UUID) is the FK target everywhere.
The synthetic ``signalnest-legacy`` workspace receives every v1.0
``feedback_item`` row during Migration B (ADR 062).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, func, text
from sqlalchemy.dialects.postgresql import CITEXT, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlmodel import Column, Field, SQLModel


class Workspace(SQLModel, table=True):
    """A tenant boundary. Every workspace-scoped row points at one."""

    __tablename__ = "workspaces"
    __table_args__ = (
        CheckConstraint(
            "slug ~ '^[a-z0-9](?:[a-z0-9-]{0,38}[a-z0-9])?$'",
            name="workspaces_slug_format",
        ),
        CheckConstraint(
            "length(name) BETWEEN 1 AND 60",
            name="workspaces_name_len",
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
    slug: str = Field(sa_column=Column(CITEXT(), nullable=False, unique=True))
    name: str = Field(sa_column=Column("name", nullable=False))
    owner_id: uuid.UUID = Field(
        sa_column=Column(
            PgUUID(as_uuid=True),
            ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
    )
    is_demo: bool = Field(
        default=False,
        sa_column=Column(
            "is_demo",
            nullable=False,
            server_default=text("false"),
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
