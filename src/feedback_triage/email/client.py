"""Resend HTTP client with fail-soft retry + ``email_log`` writes.

This module is the **only** code path that calls the Resend API. Every
transactional send (verification, password reset, invitation, future
status-change notification) goes through :meth:`EmailClient.send`,
which:

1. Renders the named Jinja template + a hard-coded subject for the
   given :class:`EmailPurpose`.
2. Writes a ``email_log`` row at ``status='queued'`` on a *separate*
   SQLAlchemy session — the row survives even if the request that
   triggered the send rolls back.
3. Either short-circuits (``RESEND_DRY_RUN=true``) and marks the row
   ``sent`` with a synthetic ``provider_id``, or POSTs to Resend with
   in-process retries on 429 / 5xx / network errors.
4. Maps the final outcome to one of ``sent`` / ``failed`` (terminal)
   per the ADR 061 fail-soft contract; any exception inside ``send``
   is swallowed after the row is written so the user-facing flow
   never sees provider state.

Canonical contracts:

- :doc:`/docs/adr/061-resend-email-fail-soft` — provider, retry
  semantics, ``email_log`` shape.
- ``docs/project/spec/v2/email.md`` — surface, sender addresses,
  per-flow failure handling.
- ``docs/project/spec/v2/auth.md`` — no-enumeration copy that the
  fail-soft contract enables.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx
from jinja2 import Environment, FileSystemLoader, select_autoescape

from feedback_triage.config import Settings, get_settings
from feedback_triage.database import SessionLocal
from feedback_triage.enums import EmailPurpose, EmailStatus
from feedback_triage.models import EmailLog

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)

_RESEND_ENDPOINT = "https://api.resend.com/emails"
_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

# Subject + template name per purpose. Subjects are intentionally
# short and provider-state-independent so the no-enumeration copy on
# the auth pages stays consistent with what hits the inbox.
_PURPOSE_TEMPLATES: dict[EmailPurpose, tuple[str, str]] = {
    EmailPurpose.VERIFICATION: ("verification.html", "Confirm your email"),
    EmailPurpose.PASSWORD_RESET: (
        "password_reset.html",
        "Reset your SignalNest password",
    ),
    EmailPurpose.INVITATION: (
        "invitation.html",
        "You're invited to a SignalNest workspace",
    ),
    # Subject for status_change is always overridden at the call site
    # (``services/status_change_notifier.py``) so the recipient inbox
    # carries the new status; the literal here is the safe fallback
    # used by ``EmailClient.replay`` when the original context is no
    # longer reconstructable.
    EmailPurpose.STATUS_CHANGE: (
        "status_change.html",
        "Update on your feedback",
    ),
}

# HTTP statuses where retry has any chance of helping. Auth (401/403)
# and validation (422) errors are terminal — retrying spends quota
# without changing the outcome.
_RETRYABLE_STATUSES = frozenset({408, 429, 500, 502, 503, 504})


@dataclass(frozen=True, slots=True)
class EmailSendResult:
    """Outcome of :meth:`EmailClient.send`.

    ``log_id`` is always set — the row is written before the network
    call, so callers can quote it back to a user (or to ``loguru``)
    even on failure. ``status`` is the terminal state; ``provider_id``
    is the Resend message id when ``status='sent'``.
    """

    log_id: uuid.UUID
    status: EmailStatus
    provider_id: str | None


class EmailClient:
    """Resend HTTP wrapper. One instance per process.

    Constructed via :func:`get_email_client`; tests can pass a custom
    ``http_client_factory`` to inject :class:`httpx.MockTransport` or
    a transport that raises :class:`httpx.ConnectError` for the
    provider-down canary (ADR 061 - Test strategy).
    """

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        http_client_factory: Callable[[], httpx.Client] | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        """Build an :class:`EmailClient`. See module docstring."""
        self._settings = settings or get_settings()
        self._http_client_factory = http_client_factory
        self._sleep = sleep
        self._jinja = Environment(
            loader=FileSystemLoader(str(_TEMPLATE_DIR)),
            autoescape=select_autoescape(["html"]),
            keep_trailing_newline=True,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def send(
        self,
        *,
        purpose: EmailPurpose,
        to: str,
        context: dict[str, Any],
        workspace_id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
        template_override: str | None = None,
        subject_override: str | None = None,
    ) -> EmailSendResult:
        """Send a transactional email and log the attempt.

        Never raises. Network and provider errors are swallowed after
        the ``email_log`` row reaches a terminal state, so the calling
        request thread cannot leak provider state into its response.

        ``template_override`` / ``subject_override`` let the caller
        substitute a sibling template that shares a DB-enum purpose.
        Used by the no-enumeration signup path (``EmailPurpose.VERIFICATION``
        + ``verification_already.html``); see ``auth.md`` — Email
        enumeration posture.
        """
        default_template, default_subject = _PURPOSE_TEMPLATES[purpose]
        template_name = template_override or default_template
        subject = subject_override or default_subject
        body = self._render(template_name, context)

        log_id = self._write_initial_log(
            to=to,
            purpose=purpose,
            template=template_name,
            subject=subject,
            workspace_id=workspace_id,
            user_id=user_id,
        )

        if self._settings.resend_dry_run:
            provider_id = f"dry-run-{uuid.uuid4()}"
            self._mark_sent(log_id, provider_id=provider_id, attempt_count=1)
            return EmailSendResult(
                log_id=log_id,
                status=EmailStatus.SENT,
                provider_id=provider_id,
            )

        try:
            return self._send_with_retry(
                log_id=log_id,
                to=to,
                subject=subject,
                body=body,
            )
        except Exception:  # pragma: no cover - defensive
            logger.exception(
                "email.send unexpected error log_id=%s purpose=%s",
                log_id,
                purpose.value,
            )
            self._mark_failed(
                log_id,
                error_code="unexpected",
                error_detail="unexpected exception in send loop",
                attempt_count=self._settings.resend_max_retries + 1,
            )
            return EmailSendResult(
                log_id=log_id,
                status=EmailStatus.FAILED,
                provider_id=None,
            )

    # ------------------------------------------------------------------
    # Replay — re-issue a previously failed/retrying send
    # ------------------------------------------------------------------
    def replay(self, log_id: uuid.UUID) -> EmailSendResult:
        """Re-send a ``failed`` (or stuck ``retrying``) email_log row.

        Used by :mod:`scripts.email_replay` (``task email:replay <id>``)
        to drain rows that landed terminal during a Resend outage.

        Limitations: the original render context is not stored on
        ``email_log`` (no ``context_json`` column in v2.0), so replay
        re-renders the row's template with an empty context. The
        templates ship with safe defaults so the body still parses;
        the inbox copy is generic ("Update on your feedback…") rather
        than the original detail. Status / verification links are not
        recoverable on replay — that's a v3.0 deliverable, tracked
        alongside the dead-letter queue.

        Raises:
            ValueError: if ``log_id`` does not refer to an
                ``email_log`` row, or if the row is in a status other
                than ``failed`` / ``retrying`` (only those two are
                replayable).

        For all *send-time* errors — provider outage, transport
        failure, unexpected exceptions inside the retry loop — the
        same fail-soft contract as :meth:`send` applies: the row is
        marked ``failed`` and a normal :class:`EmailSendResult` is
        returned (no exception escapes).
        """
        with SessionLocal() as session:
            row = session.get(EmailLog, log_id)
        if row is None:
            msg = f"email_log row {log_id} not found"
            raise ValueError(msg)
        if row.status not in {EmailStatus.FAILED, EmailStatus.RETRYING}:
            msg = (
                f"email_log row {log_id} is in status {row.status.value!r}; "
                "only failed/retrying rows can be replayed"
            )
            raise ValueError(msg)

        body = self._render(row.template, {})
        # Reset attempt_count + clear prior error fields before retry.
        with SessionLocal() as session, session.begin():
            target = session.get(EmailLog, log_id)
            if target is None:  # pragma: no cover - defensive
                msg = f"email_log row {log_id} vanished mid-replay"
                raise ValueError(msg)
            target.status = EmailStatus.QUEUED
            target.error_code = None
            target.error_detail = None
            target.attempt_count = 0
            target.provider_id = None
            target.sent_at = None

        if self._settings.resend_dry_run:
            provider_id = f"dry-run-{uuid.uuid4()}"
            self._mark_sent(log_id, provider_id=provider_id, attempt_count=1)
            return EmailSendResult(
                log_id=log_id,
                status=EmailStatus.SENT,
                provider_id=provider_id,
            )

        try:
            return self._send_with_retry(
                log_id=log_id,
                to=row.to_address,
                subject=row.subject,
                body=body,
            )
        except Exception:  # pragma: no cover - defensive
            logger.exception("email.replay unexpected error log_id=%s", log_id)
            self._mark_failed(
                log_id,
                error_code="unexpected",
                error_detail="unexpected exception in replay loop",
                attempt_count=self._settings.resend_max_retries + 1,
            )
            return EmailSendResult(
                log_id=log_id,
                status=EmailStatus.FAILED,
                provider_id=None,
            )

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def _render(self, template_name: str, context: dict[str, Any]) -> str:
        template = self._jinja.get_template(template_name)
        return template.render(**context)

    # ------------------------------------------------------------------
    # email_log writes (own session — fail-soft & request-independent)
    # ------------------------------------------------------------------
    def _write_initial_log(
        self,
        *,
        to: str,
        purpose: EmailPurpose,
        template: str,
        subject: str,
        workspace_id: uuid.UUID | None,
        user_id: uuid.UUID | None,
    ) -> uuid.UUID:
        with SessionLocal() as session, session.begin():
            row = EmailLog(
                workspace_id=workspace_id,
                user_id=user_id,
                to_address=to,
                purpose=purpose,
                template=template,
                subject=subject,
                status=EmailStatus.QUEUED,
                attempt_count=0,
            )
            session.add(row)
            session.flush()
            assert row.id is not None  # populated by gen_random_uuid()
            return row.id

    def _mark_sent(
        self,
        log_id: uuid.UUID,
        *,
        provider_id: str,
        attempt_count: int,
    ) -> None:
        self._update_log(
            log_id,
            status=EmailStatus.SENT,
            provider_id=provider_id,
            attempt_count=attempt_count,
            sent_at=datetime.now(tz=UTC),
        )

    def _mark_retrying(self, log_id: uuid.UUID, *, attempt_count: int) -> None:
        self._update_log(
            log_id,
            status=EmailStatus.RETRYING,
            attempt_count=attempt_count,
        )

    def _mark_failed(
        self,
        log_id: uuid.UUID,
        *,
        error_code: str,
        error_detail: str,
        attempt_count: int,
    ) -> None:
        self._update_log(
            log_id,
            status=EmailStatus.FAILED,
            error_code=error_code[:64],
            error_detail=error_detail[:1024],
            attempt_count=attempt_count,
        )

    def _update_log(self, log_id: uuid.UUID, **fields: Any) -> None:
        with SessionLocal() as session, session.begin():
            row = session.get(EmailLog, log_id)
            if row is None:  # pragma: no cover - defensive
                logger.warning("email_log row vanished log_id=%s", log_id)
                return
            for key, value in fields.items():
                setattr(row, key, value)

    # ------------------------------------------------------------------
    # HTTP send with retry
    # ------------------------------------------------------------------
    def _send_with_retry(
        self,
        *,
        log_id: uuid.UUID,
        to: str,
        subject: str,
        body: str,
    ) -> EmailSendResult:
        max_attempts = self._settings.resend_max_retries + 1
        last_error_code = "unknown"
        last_error_detail = ""

        for attempt in range(1, max_attempts + 1):
            try:
                provider_id = self._post_to_resend(
                    to=to,
                    subject=subject,
                    body=body,
                )
            except _TerminalProviderError as exc:
                self._mark_failed(
                    log_id,
                    error_code=exc.error_code,
                    error_detail=exc.detail,
                    attempt_count=attempt,
                )
                return EmailSendResult(
                    log_id=log_id,
                    status=EmailStatus.FAILED,
                    provider_id=None,
                )
            except _RetryableProviderError as exc:
                last_error_code = exc.error_code
                last_error_detail = exc.detail
                if attempt < max_attempts:
                    self._mark_retrying(log_id, attempt_count=attempt)
                    self._sleep(_backoff_seconds(attempt))
                    continue
            else:
                self._mark_sent(
                    log_id,
                    provider_id=provider_id,
                    attempt_count=attempt,
                )
                return EmailSendResult(
                    log_id=log_id,
                    status=EmailStatus.SENT,
                    provider_id=provider_id,
                )

        # All retries exhausted on a retryable error.
        self._mark_failed(
            log_id,
            error_code=last_error_code,
            error_detail=last_error_detail,
            attempt_count=max_attempts,
        )
        return EmailSendResult(
            log_id=log_id,
            status=EmailStatus.FAILED,
            provider_id=None,
        )

    def _post_to_resend(self, *, to: str, subject: str, body: str) -> str:
        api_key = self._settings.resend_api_key.get_secret_value()
        if not api_key:
            # Hit when ``feature_auth=true``, ``resend_dry_run=false``,
            # and the operator forgot to set the secret. Treated as
            # terminal — retrying won't conjure a key.
            raise _TerminalProviderError(
                error_code="missing_api_key",
                detail="RESEND_API_KEY is not configured",
            )

        client = (
            self._http_client_factory()
            if self._http_client_factory is not None
            else httpx.Client(timeout=self._settings.resend_timeout_seconds)
        )
        try:
            with client:
                response = client.post(
                    _RESEND_ENDPOINT,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": self._settings.resend_from_address,
                        "to": [to],
                        "subject": subject,
                        "html": body,
                    },
                )
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            raise _RetryableProviderError(
                error_code="network",
                detail=f"{type(exc).__name__}: {exc}",
            ) from exc

        if 200 <= response.status_code < 300:
            payload = _safe_json(response)
            provider_id = str(payload.get("id", ""))[:128] or "unknown"
            return provider_id

        detail = (response.text or "")[:1024]
        if response.status_code in _RETRYABLE_STATUSES:
            raise _RetryableProviderError(
                error_code=f"http_{response.status_code}",
                detail=detail,
            )
        raise _TerminalProviderError(
            error_code=f"http_{response.status_code}",
            detail=detail,
        )


# ---------------------------------------------------------------------------
# Internal exception types — never escape the module
# ---------------------------------------------------------------------------
class _ProviderError(Exception):
    def __init__(self, *, error_code: str, detail: str) -> None:
        super().__init__(f"{error_code}: {detail}")
        self.error_code = error_code
        self.detail = detail


class _RetryableProviderError(_ProviderError):
    """429, 5xx, timeout, connection error — try again."""


class _TerminalProviderError(_ProviderError):
    """401, 403, 422, missing key — retry won't help."""


def _backoff_seconds(attempt: int) -> float:
    """Bounded exponential backoff: 0.5 s, 1.0 s, 2.0 s, capped at 4 s."""
    return float(min(0.5 * (2 ** (attempt - 1)), 4.0))


def _safe_json(response: httpx.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError:
        return {}
    return payload if isinstance(payload, dict) else {}


# ---------------------------------------------------------------------------
# Module-level accessor
# ---------------------------------------------------------------------------
_client: EmailClient | None = None


def get_email_client() -> EmailClient:
    """Return the process-wide :class:`EmailClient` (lazy-singleton).

    Tests should construct :class:`EmailClient` directly with an
    injected ``http_client_factory`` rather than calling this; the
    singleton exists so request handlers can grab the client in one
    line without an explicit DI wire-up.
    """
    global _client  # lazy singleton
    if _client is None:
        _client = EmailClient()
    return _client
