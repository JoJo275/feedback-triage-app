"""SQLModel ORM model for the ``tags`` table.

Per-workspace categorisation chips. ``slug`` is unique per workspace
so two workspaces can independently use the same label; ``color``
is a named palette tone (mapped to Tailwind shades in CSS, not the
DB). Canonical schema in
``alembic/versions/0003_v2_b_workflow_tables.py`` and
``docs/project/spec/v2/schema.md``.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlmodel import Column, Field, SQLModel


class Tag(SQLModel, table=True):
    """A workspace-scoped tag chip applied to feedback items."""

    __tablename__ = "tags"
    __table_args__ = (
        UniqueConstraint("workspace_id", "slug", name="tags_workspace_slug_uq"),
        CheckConstraint(
            "length(name) BETWEEN 1 AND 40",
            name="tags_name_len",
        ),
        CheckConstraint(
            "slug ~ '^[a-z0-9](?:[a-z0-9-]{0,38}[a-z0-9])?$'",
            name="tags_slug_format",
        ),
        CheckConstraint(
            "color IN ('slate','teal','amber','rose','indigo','sky','green','violet')",
            name="tags_color_palette",
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
    name: str = Field(sa_column=Column("name", nullable=False))
    slug: str = Field(sa_column=Column("slug", nullable=False))
    color: str = Field(
        default="slate",
        sa_column=Column(
            "color",
            nullable=False,
            server_default=text("'slate'"),
        ),
    )
    created_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=func.now(),
        ),
    )
