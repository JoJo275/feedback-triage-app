"""SQLModel ORM model for the ``workspace_memberships`` table.

Composite-PK join table that records each user's per-workspace role.
Canonical schema in
``alembic/versions/0002_v2_a_auth_tenancy_email_log.py`` and
``docs/project/spec/v2/schema.md``.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, func
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlmodel import Column, Field, SQLModel

from feedback_triage.enums import WORKSPACE_ROLE_ENUM, WorkspaceRole


class WorkspaceMembership(SQLModel, table=True):
    """A user's role inside one workspace."""

    __tablename__ = "workspace_memberships"

    workspace_id: uuid.UUID = Field(
        sa_column=Column(
            PgUUID(as_uuid=True),
            ForeignKey("workspaces.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
    )
    user_id: uuid.UUID = Field(
        sa_column=Column(
            PgUUID(as_uuid=True),
            ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
    )
    role: WorkspaceRole = Field(
        sa_column=Column(WORKSPACE_ROLE_ENUM, nullable=False),
    )
    joined_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=func.now(),
        ),
    )
