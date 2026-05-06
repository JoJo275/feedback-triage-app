"""Unit tests for :mod:`feedback_triage.email.client`.

Covers the four invariants from ADR 061 - Test strategy:

1. ``RESEND_DRY_RUN=1`` short-circuits before any HTTP call but
   still writes a ``status='sent'`` row with a synthetic
   ``provider_id``.
2. The provider-down canary — every attempt raises
   :class:`httpx.ConnectError` — leaves the row at ``status='failed'``
   after retries and never re-raises into the caller.
3. A 5xx response triggers retry; a 4xx auth/validation response is
   terminal on the first attempt.
4. Boot fails fast when ``RESEND_API_KEY`` is missing in production
   while the auth surface is on.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import httpx
import pytest
from pydantic import SecretStr
from pydantic_core import ValidationError
from sqlalchemy import select

from feedback_triage.config import Settings
from feedback_triage.database import SessionLocal
from feedback_triage.email.client import EmailClient
from feedback_triage.enums import EmailPurpose, EmailStatus
from feedback_triage.models import EmailLog


def _settings(**overrides: Any) -> Settings:
    base: dict[str, Any] = {
        "app_env": "test",
        "feature_auth": True,
        "resend_api_key": SecretStr("test-key"),
        "resend_dry_run": False,
        "resend_max_retries": 2,
        "resend_timeout_seconds": 1.0,
    }
    base.update(overrides)
    return Settings(_env_file=None, **base)  # type: ignore[call-arg]


def _no_sleep(_seconds: float) -> None:
    return None


def _read_log(log_id: Any) -> EmailLog:
    with SessionLocal() as session:
        row = session.scalar(select(EmailLog).where(EmailLog.id == log_id))
    assert row is not None
    return row


# ---------------------------------------------------------------------------
# 1. DRY_RUN short-circuit
# ---------------------------------------------------------------------------
@pytest.mark.usefixtures("truncate_email_log")
def test_dry_run_marks_sent_and_skips_network() -> None:
    """``RESEND_DRY_RUN=1`` must not call httpx at all."""

    def _factory_should_never_run() -> httpx.Client:
        msg = "DRY_RUN=1 must not construct an HTTP client"
        raise AssertionError(msg)

    client = EmailClient(
        _settings(resend_dry_run=True),
        http_client_factory=_factory_should_never_run,
        sleep=_no_sleep,
    )

    result = client.send(
        purpose=EmailPurpose.VERIFICATION,
        to="alice@example.com",
        context={
            "recipient_name": "Alice",
            "verify_url": "https://signalnest.app/verify-email?token=abc",
            "expires_in_hours": 24,
        },
    )

    assert result.status is EmailStatus.SENT
    assert result.provider_id is not None
    assert result.provider_id.startswith("dry-run-")

    row = _read_log(result.log_id)
    assert row.status is EmailStatus.SENT
    assert row.provider_id == result.provider_id
    assert row.attempt_count == 1
    assert row.sent_at is not None
    assert row.purpose is EmailPurpose.VERIFICATION
    assert row.template == "verification.html"
    assert row.to_address == "alice@example.com"


# ---------------------------------------------------------------------------
# 2. Provider-down canary
# ---------------------------------------------------------------------------
@pytest.mark.usefixtures("truncate_email_log")
def test_provider_down_canary_returns_failed_after_retries() -> None:
    """Connection errors on every attempt → terminal ``failed`` row,
    never an exception in the caller's request thread."""
    attempts: list[httpx.Request] = []

    def _always_connect_error(request: httpx.Request) -> httpx.Response:
        attempts.append(request)
        msg = "simulated provider outage"
        raise httpx.ConnectError(msg, request=request)

    transport = httpx.MockTransport(_always_connect_error)

    def _factory() -> httpx.Client:
        return httpx.Client(transport=transport, timeout=1.0)

    client = EmailClient(
        _settings(resend_max_retries=2),
        http_client_factory=_factory,
        sleep=_no_sleep,
    )

    result = client.send(
        purpose=EmailPurpose.PASSWORD_RESET,
        to="bob@example.com",
        context={
            "recipient_name": "Bob",
            "reset_url": "https://signalnest.app/reset?token=xyz",
            "expires_in_minutes": 30,
        },
    )

    assert result.status is EmailStatus.FAILED
    assert result.provider_id is None
    # 1 initial attempt + 2 retries = 3 calls into the transport.
    assert len(attempts) == 3

    row = _read_log(result.log_id)
    assert row.status is EmailStatus.FAILED
    assert row.attempt_count == 3
    assert row.error_code == "network"
    assert row.sent_at is None
    assert row.provider_id is None


# ---------------------------------------------------------------------------
# 3. 5xx retries → success on second attempt
# ---------------------------------------------------------------------------
@pytest.mark.usefixtures("truncate_email_log")
def test_retries_on_5xx_then_succeeds() -> None:
    responses: Iterator[httpx.Response] = iter(
        [
            httpx.Response(503, text="upstream busy"),
            httpx.Response(200, json={"id": "msg_abc123"}),
        ],
    )

    def _handler(_request: httpx.Request) -> httpx.Response:
        return next(responses)

    transport = httpx.MockTransport(_handler)

    def _factory() -> httpx.Client:
        return httpx.Client(transport=transport, timeout=1.0)

    client = EmailClient(
        _settings(resend_max_retries=2),
        http_client_factory=_factory,
        sleep=_no_sleep,
    )

    result = client.send(
        purpose=EmailPurpose.INVITATION,
        to="carol@example.com",
        context={
            "workspace_name": "Acme",
            "inviter_name": "Alice",
            "role": "team_member",
            "accept_url": "https://signalnest.app/invitations/tok",
            "expires_in_days": 7,
        },
    )

    assert result.status is EmailStatus.SENT
    assert result.provider_id == "msg_abc123"

    row = _read_log(result.log_id)
    assert row.status is EmailStatus.SENT
    assert row.attempt_count == 2
    assert row.provider_id == "msg_abc123"


# ---------------------------------------------------------------------------
# 3b. 4xx auth error is terminal — no retry
# ---------------------------------------------------------------------------
@pytest.mark.usefixtures("truncate_email_log")
def test_auth_error_is_terminal_no_retry() -> None:
    calls = 0

    def _handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(401, text="invalid api key")

    transport = httpx.MockTransport(_handler)

    def _factory() -> httpx.Client:
        return httpx.Client(transport=transport, timeout=1.0)

    client = EmailClient(
        _settings(resend_max_retries=5),
        http_client_factory=_factory,
        sleep=_no_sleep,
    )

    result = client.send(
        purpose=EmailPurpose.VERIFICATION,
        to="dave@example.com",
        context={
            "recipient_name": "Dave",
            "verify_url": "https://signalnest.app/verify-email?token=t",
            "expires_in_hours": 24,
        },
    )

    assert result.status is EmailStatus.FAILED
    assert calls == 1, "401 must not retry"

    row = _read_log(result.log_id)
    assert row.status is EmailStatus.FAILED
    assert row.error_code == "http_401"
    assert row.attempt_count == 1


# ---------------------------------------------------------------------------
# 4. Boot-time validation
# ---------------------------------------------------------------------------
def test_production_boot_fails_without_resend_api_key() -> None:
    """``APP_ENV=production`` + ``FEATURE_AUTH=true`` + DRY_RUN=false
    → boot must fail when ``RESEND_API_KEY`` is empty."""
    with pytest.raises(ValidationError) as excinfo:
        Settings(  # type: ignore[call-arg]
            _env_file=None,
            app_env="production",
            feature_auth=True,
            secure_cookies=True,
            database_url=SecretStr(
                "postgresql+psycopg://u:p@db.example.com:5432/x",
            ),
            resend_dry_run=False,
            resend_api_key=SecretStr(""),
        )
    assert "RESEND_API_KEY" in str(excinfo.value)


def test_production_boot_fails_when_dry_run_left_on() -> None:
    """Production with ``RESEND_DRY_RUN=true`` would silently never
    send mail. Boot must refuse."""
    with pytest.raises(ValidationError) as excinfo:
        Settings(  # type: ignore[call-arg]
            _env_file=None,
            app_env="production",
            feature_auth=True,
            secure_cookies=True,
            database_url=SecretStr(
                "postgresql+psycopg://u:p@db.example.com:5432/x",
            ),
            resend_dry_run=True,
            resend_api_key=SecretStr("re_xxx"),
        )
    assert "RESEND_DRY_RUN" in str(excinfo.value)
