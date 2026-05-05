"""SQLModel ORM model for the ``auth_rate_limits`` table.

Backs the per-bucket login / sign-up / token-mint rate limiters that
the auth module (PR 1.4) consults. Canonical schema in
``alembic/versions/0002_v2_a_auth_tenancy_email_log.py`` and
``docs/project/spec/v2/auth.md`` (Rate limits).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlmodel import Column, Field, SQLModel


class AuthRateLimit(SQLModel, table=True):
    """One row per ``(bucket_key, window_start)`` counter."""

    __tablename__ = "auth_rate_limits"
    __table_args__ = (
        CheckConstraint(
            "length(bucket_key) <= 128",
            name="auth_rate_limits_bucket_key_max_len",
        ),
        CheckConstraint(
            "count >= 0",
            name="auth_rate_limits_count_nonneg",
        ),
    )

    bucket_key: str = Field(
        sa_column=Column("bucket_key", primary_key=True, nullable=False),
    )
    window_start: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            primary_key=True,
            nullable=False,
        ),
    )
    count: int = Field(
        default=0,
        sa_column=Column(
            "count",
            nullable=False,
            server_default=text("0"),
        ),
    )
