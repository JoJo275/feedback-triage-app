"""SQLModel ORM models for single-use token tables.

The ``email_verification_tokens`` and ``password_reset_tokens`` tables
share an identical shape; both are minted and consumed by the auth
module (PR 1.4). Canonical schema in
``alembic/versions/0002_v2_a_auth_tenancy_email_log.py`` and
``docs/project/spec/v2/auth.md`` (Token TTL matrix). Workspace
invitations live in their own table — see ``invitations.py`` —
because they have additional columns (workspace, role, inviter).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, func, text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlmodel import Column, Field, SQLModel


class EmailVerificationToken(SQLModel, table=True):
    """Single-use email-verification token (24 h TTL)."""

    __tablename__ = "email_verification_tokens"
    __table_args__ = (
        CheckConstraint(
            "length(token_hash) <= 256",
            name="email_verification_tokens_token_hash_max_len",
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
    user_id: uuid.UUID = Field(
        sa_column=Column(
            PgUUID(as_uuid=True),
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    token_hash: str = Field(
        sa_column=Column("token_hash", nullable=False, unique=True),
    )
    expires_at: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
    )
    consumed_at: datetime | None = Field(
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


class PasswordResetToken(SQLModel, table=True):
    """Single-use password-reset token (1 h TTL)."""

    __tablename__ = "password_reset_tokens"
    __table_args__ = (
        CheckConstraint(
            "length(token_hash) <= 256",
            name="password_reset_tokens_token_hash_max_len",
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
    user_id: uuid.UUID = Field(
        sa_column=Column(
            PgUUID(as_uuid=True),
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    token_hash: str = Field(
        sa_column=Column("token_hash", nullable=False, unique=True),
    )
    expires_at: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
    )
    consumed_at: datetime | None = Field(
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
