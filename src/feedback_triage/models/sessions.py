"""SQLModel ORM model for the ``sessions`` table.

Holds the rolling session cookies issued by the auth module (PR 1.4).
Canonical schema in
``alembic/versions/0002_v2_a_auth_tenancy_email_log.py`` and
``docs/project/spec/v2/auth.md`` (Token TTL matrix).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, func, text
from sqlalchemy.dialects.postgresql import INET, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlmodel import Column, Field, SQLModel


class UserSession(SQLModel, table=True):
    """A live (or revoked / expired) browser session for a user."""

    __tablename__ = "sessions"
    __table_args__ = (
        CheckConstraint(
            "length(token_hash) <= 256",
            name="sessions_token_hash_max_len",
        ),
        CheckConstraint(
            "user_agent IS NULL OR length(user_agent) <= 512",
            name="sessions_user_agent_max_len",
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
    token_hash: str = Field(sa_column=Column("token_hash", nullable=False))
    user_agent: str | None = Field(
        default=None,
        sa_column=Column("user_agent", nullable=True),
    )
    ip_inet: str | None = Field(
        default=None,
        sa_column=Column(INET(), nullable=True),
    )
    created_at: datetime = Field(
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
    expires_at: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
    )
    revoked_at: datetime | None = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True),
    )
