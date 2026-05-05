"""SQLModel ORM model for the ``workspace_invitations`` table.

Drives the membership-by-email flow exposed in PR 1.8; canonical
schema in ``alembic/versions/0002_v2_a_auth_tenancy_email_log.py``
and ``docs/project/spec/v2/schema.md``. The partial unique index
on ``(workspace_id, email) WHERE accepted_at IS NULL AND revoked_at
IS NULL`` is owned by the migration.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, func, text
from sqlalchemy.dialects.postgresql import CITEXT, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlmodel import Column, Field, SQLModel

from feedback_triage.enums import WORKSPACE_ROLE_ENUM, WorkspaceRole


class WorkspaceInvitation(SQLModel, table=True):
    """A pending / accepted / revoked invitation to join a workspace."""

    __tablename__ = "workspace_invitations"
    __table_args__ = (
        CheckConstraint(
            "length(email) <= 320",
            name="workspace_invitations_email_max_len",
        ),
        CheckConstraint(
            "length(token_hash) <= 256",
            name="workspace_invitations_token_hash_max_len",
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
    email: str = Field(sa_column=Column(CITEXT(), nullable=False))
    role: WorkspaceRole = Field(
        default=WorkspaceRole.TEAM_MEMBER,
        sa_column=Column(
            WORKSPACE_ROLE_ENUM,
            nullable=False,
            server_default=text("'team_member'::workspace_role_enum"),
        ),
    )
    token_hash: str = Field(
        sa_column=Column("token_hash", nullable=False, unique=True),
    )
    invited_by_id: uuid.UUID = Field(
        sa_column=Column(
            PgUUID(as_uuid=True),
            ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
    )
    expires_at: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
    )
    accepted_at: datetime | None = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True),
    )
    revoked_at: datetime | None = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True),
    )
    created_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=func.now(),
        ),
    )
