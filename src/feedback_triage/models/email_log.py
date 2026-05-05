"""SQLModel ORM model for the ``email_log`` table.

Records every outbound transactional email and its delivery status.
Canonical schema in
``alembic/versions/0002_v2_a_auth_tenancy_email_log.py``, ADR 061,
and ``docs/project/spec/v2/email.md``. ``workspace_id`` and
``user_id`` are nullable because verification sends predate either
record being committed; ``ON DELETE SET NULL`` keeps the audit trail
intact when a user / workspace is later removed.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, func, text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlmodel import Column, Field, SQLModel

from feedback_triage.enums import (
    EMAIL_PURPOSE_ENUM,
    EMAIL_STATUS_ENUM,
    EmailPurpose,
    EmailStatus,
)


class EmailLog(SQLModel, table=True):
    """One row per transactional-email send attempt."""

    __tablename__ = "email_log"
    __table_args__ = (
        CheckConstraint(
            "length(to_address) <= 320",
            name="email_log_to_address_max_len",
        ),
        CheckConstraint(
            "length(template) <= 64",
            name="email_log_template_max_len",
        ),
        CheckConstraint(
            "length(subject) <= 256",
            name="email_log_subject_max_len",
        ),
        CheckConstraint(
            "provider_id IS NULL OR length(provider_id) <= 128",
            name="email_log_provider_id_max_len",
        ),
        CheckConstraint(
            "error_code IS NULL OR length(error_code) <= 64",
            name="email_log_error_code_max_len",
        ),
        CheckConstraint(
            "error_detail IS NULL OR length(error_detail) <= 1024",
            name="email_log_error_detail_max_len",
        ),
        CheckConstraint(
            "attempt_count >= 0",
            name="email_log_attempt_count_nonneg",
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
    workspace_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            PgUUID(as_uuid=True),
            ForeignKey("workspaces.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    user_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            PgUUID(as_uuid=True),
            ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    to_address: str = Field(sa_column=Column("to_address", nullable=False))
    purpose: EmailPurpose = Field(
        sa_column=Column(EMAIL_PURPOSE_ENUM, nullable=False),
    )
    template: str = Field(sa_column=Column("template", nullable=False))
    subject: str = Field(sa_column=Column("subject", nullable=False))
    status: EmailStatus = Field(
        default=EmailStatus.QUEUED,
        sa_column=Column(
            EMAIL_STATUS_ENUM,
            nullable=False,
            server_default=text("'queued'::email_status_enum"),
        ),
    )
    provider_id: str | None = Field(
        default=None,
        sa_column=Column("provider_id", nullable=True),
    )
    error_code: str | None = Field(
        default=None,
        sa_column=Column("error_code", nullable=True),
    )
    error_detail: str | None = Field(
        default=None,
        sa_column=Column("error_detail", nullable=True),
    )
    attempt_count: int = Field(
        default=0,
        sa_column=Column(
            "attempt_count",
            nullable=False,
            server_default=text("0"),
        ),
    )
    created_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=func.now(),
        ),
    )
    sent_at: datetime | None = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True),
    )
    updated_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=func.now(),
        ),
    )
