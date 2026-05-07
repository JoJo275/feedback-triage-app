"""Integration test for ``EmailClient.replay`` / ``task email:replay``.

Simulates the PR 3.1 DoD scenario:

1. Provider is down → status-change PATCH commits, email_log row
   lands at ``status='failed'`` (covered by
   ``tests/api/test_status_change_email.py``).
2. Operator runs ``task email:replay <log-id>`` once Resend is back
   → row transitions ``failed → sent`` and a fresh ``provider_id``
   is recorded.

Marked ``integration`` because it exercises the full client + DB +
HTTP-mock path end-to-end.
"""

from __future__ import annotations

import uuid

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import select, text

from feedback_triage.config import Settings
from feedback_triage.database import SessionLocal, engine
from feedback_triage.email.client import EmailClient
from feedback_triage.enums import EmailPurpose, EmailStatus
from feedback_triage.models import EmailLog

pytestmark = pytest.mark.integration


def _settings(**overrides: object) -> Settings:
    base: dict[str, object] = {
        "app_env": "test",
        "feature_auth": True,
        "resend_api_key": SecretStr("test-key"),
        "resend_dry_run": False,
        "resend_max_retries": 1,
        "resend_timeout_seconds": 1.0,
    }
    base.update(overrides)
    return Settings(_env_file=None, **base)  # type: ignore[call-arg]


@pytest.fixture(autouse=True)
def _truncate_email_log() -> None:
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE email_log RESTART IDENTITY CASCADE"))


def _read(log_id: uuid.UUID) -> EmailLog:
    with SessionLocal() as session:
        row = session.scalar(select(EmailLog).where(EmailLog.id == log_id))
    assert row is not None
    return row


def _factory_for(handler: object) -> object:
    transport = httpx.MockTransport(handler)  # type: ignore[arg-type]

    def _make() -> httpx.Client:
        return httpx.Client(transport=transport, timeout=1.0)

    return _make


def test_failed_row_can_be_replayed_once_provider_is_back() -> None:
    """End-to-end: outage → failed row → replay → sent."""

    # --- Phase 1: provider is down. Send → failed. -----------------
    def _down(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="upstream busy")

    client_down = EmailClient(
        _settings(),
        http_client_factory=_factory_for(_down),  # type: ignore[arg-type]
        sleep=lambda _s: None,
    )
    first = client_down.send(
        purpose=EmailPurpose.STATUS_CHANGE,
        to="casey@example.com",
        context={
            "workspace_name": "Acme",
            "feedback_title": "Login is slow",
            "status_label": "shipped",
        },
        subject_override="Your feedback is now shipped",
    )
    assert first.status is EmailStatus.FAILED

    row = _read(first.log_id)
    assert row.status is EmailStatus.FAILED
    assert row.provider_id is None
    assert row.error_code == "http_503"

    # --- Phase 2: provider is back. Replay → sent. -----------------
    def _up(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"id": "msg_replayed"})

    client_up = EmailClient(
        _settings(),
        http_client_factory=_factory_for(_up),  # type: ignore[arg-type]
        sleep=lambda _s: None,
    )
    second = client_up.replay(first.log_id)
    assert second.status is EmailStatus.SENT
    assert second.provider_id == "msg_replayed"
    assert second.log_id == first.log_id  # same row, not a duplicate

    refreshed = _read(first.log_id)
    assert refreshed.status is EmailStatus.SENT
    assert refreshed.provider_id == "msg_replayed"
    assert refreshed.error_code is None
    assert refreshed.error_detail is None
    assert refreshed.sent_at is not None
    assert refreshed.attempt_count == 1  # counter reset on replay


def test_replay_rejects_already_sent_row() -> None:
    """Replaying a ``sent`` row is a programming error → ValueError."""
    client = EmailClient(
        _settings(resend_dry_run=True),
        sleep=lambda _s: None,
    )
    sent = client.send(
        purpose=EmailPurpose.STATUS_CHANGE,
        to="casey@example.com",
        context={"workspace_name": "Acme"},
        subject_override="ok",
    )
    assert sent.status is EmailStatus.SENT

    with pytest.raises(ValueError, match="failed/retrying"):
        client.replay(sent.log_id)


def test_replay_unknown_id_raises() -> None:
    client = EmailClient(_settings(resend_dry_run=True), sleep=lambda _s: None)
    with pytest.raises(ValueError, match="not found"):
        client.replay(uuid.uuid4())
