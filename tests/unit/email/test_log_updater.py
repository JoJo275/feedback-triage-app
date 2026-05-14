"""Unit tests for the email log status updater.

These tests target branches that the webhook integration tests do not
reach directly, especially validation on invalid post-send statuses.
"""

from __future__ import annotations

import uuid

import pytest

from feedback_triage.database import SessionLocal
from feedback_triage.enums import EmailPurpose, EmailStatus
from feedback_triage.models import EmailLog
from feedback_triage.services.email_log_updater import (
    EmailLogUpdateOutcome,
    apply_provider_event,
)


def _seed_log(provider_id: str, *, status: EmailStatus) -> uuid.UUID:
    log_id = uuid.uuid4()
    with SessionLocal() as session, session.begin():
        session.add(
            EmailLog(
                id=log_id,
                to_address="recipient@example.com",
                purpose=EmailPurpose.VERIFICATION,
                template="verification.html",
                subject="Confirm your email",
                status=status,
                provider_id=provider_id,
                attempt_count=1,
            )
        )
    return log_id


def _read_status(log_id: uuid.UUID) -> EmailStatus:
    with SessionLocal() as session:
        row = session.get(EmailLog, log_id)
    assert row is not None
    return row.status


def test_apply_provider_event_rejects_non_post_send_status(
    truncate_email_log: None,
) -> None:
    with (
        SessionLocal() as db,
        pytest.raises(
            ValueError,
            match="non-post-send status",
        ),
    ):
        apply_provider_event(
            db,
            provider_id="msg_invalid_status",
            new_status=EmailStatus.SENT,
        )


def test_apply_provider_event_returns_not_found_for_missing_row(
    truncate_email_log: None,
) -> None:
    with SessionLocal() as db:
        outcome = apply_provider_event(
            db,
            provider_id="msg_missing",
            new_status=EmailStatus.DELIVERED,
        )
    assert outcome is EmailLogUpdateOutcome.NOT_FOUND


def test_apply_provider_event_updates_when_incoming_has_higher_precedence(
    truncate_email_log: None,
) -> None:
    provider_id = "msg_update"
    log_id = _seed_log(provider_id, status=EmailStatus.DELIVERED)

    with SessionLocal() as db:
        outcome = apply_provider_event(
            db,
            provider_id=provider_id,
            new_status=EmailStatus.COMPLAINED,
        )
        db.commit()

    assert outcome is EmailLogUpdateOutcome.UPDATED
    assert _read_status(log_id) is EmailStatus.COMPLAINED


def test_apply_provider_event_ignores_lower_precedence_updates(
    truncate_email_log: None,
) -> None:
    provider_id = "msg_ignore"
    log_id = _seed_log(provider_id, status=EmailStatus.BOUNCED)

    with SessionLocal() as db:
        outcome = apply_provider_event(
            db,
            provider_id=provider_id,
            new_status=EmailStatus.DELIVERED,
        )

    assert outcome is EmailLogUpdateOutcome.IGNORED
    assert _read_status(log_id) is EmailStatus.BOUNCED
