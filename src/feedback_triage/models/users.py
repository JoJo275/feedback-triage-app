"""SQLModel ORM model for the ``users`` table.

The model defines the shape; the canonical schema is owned by Alembic
(see ``alembic/versions/0002_v2_a_auth_tenancy_email_log.py``). Both
must agree with the Postgres specification in
``docs/project/spec/v2/schema.md``.

Key choices:

- ``email`` and ``slug``-shaped citext columns are typed as plain
  ``str`` on the Python side; the underlying column type is
  ``citext`` (case-insensitive comparison) created by the migration.
- ``role`` is a native ``user_role_enum``; ``create_type=False`` keeps
  ``metadata.create_all()`` from trying to manage the type.
- ``updated_at`` is bumped by a ``BEFORE UPDATE`` trigger, not ORM
  ``onupdate``.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, func, text
from sqlalchemy.dialects.postgresql import CITEXT, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlmodel import Column, Field, SQLModel

from feedback_triage.enums import USER_ROLE_ENUM, UserRole


class User(SQLModel, table=True):
    """A registered human user (or the synthetic legacy admin)."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "length(email) <= 320",
            name="users_email_max_len",
        ),
        CheckConstraint(
            "length(password_hash) <= 256",
            name="users_password_hash_max_len",
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
    email: str = Field(sa_column=Column(CITEXT(), nullable=False, unique=True))
    password_hash: str = Field(sa_column=Column("password_hash", nullable=False))
    is_verified: bool = Field(
        default=False,
        sa_column=Column(
            "is_verified",
            nullable=False,
            server_default=text("false"),
        ),
    )
    role: UserRole = Field(
        default=UserRole.TEAM_MEMBER,
        sa_column=Column(
            USER_ROLE_ENUM,
            nullable=False,
            server_default=text("'team_member'::user_role_enum"),
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
