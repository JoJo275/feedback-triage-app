"""Status-change → submitter email notifier (PR 3.1).

Three cases per the implementation plan:

1. **Happy path** — a PATCH that moves the row into ``shipped`` (the
   default-configured notify status) writes an ``email_log`` row at
   ``status='sent'`` (DRY_RUN short-circuit).
2. **Fail-soft** — a transient Resend outage during the send leaves
   the PATCH committed and the email_log row at ``status='failed'``;
   the API caller never sees provider state.
3. **Opt-out** — items without a linked submitter, or whose submitter
   has ``email IS NULL`` (anonymous public submission), do not write
   an ``email_log`` row at all.
"""

from __future__ import annotations

import uuid
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text

from feedback_triage.database import SessionLocal, engine
from feedback_triage.email.client import EmailClient
from feedback_triage.enums import EmailPurpose, EmailStatus
from feedback_triage.models import EmailLog

VALID_PASSWORD = "correct horse battery staple"  # pragma: allowlist secret


def _signup(client: TestClient, email: str) -> tuple[str, uuid.UUID]:
    client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": VALID_PASSWORD},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": VALID_PASSWORD},
    )
    body = login.json()
    return (
        body["memberships"][0]["workspace_slug"],
        uuid.UUID(body["memberships"][0]["workspace_id"]),
    )


def _seed_submitter(workspace_id: uuid.UUID, email: str | None) -> uuid.UUID:
    submitter_id = uuid.uuid4()
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO submitters "
                "(id, workspace_id, email, name, submission_count) "
                "VALUES (:id, :ws, :email, :name, 1)",
            ),
            {
                "id": submitter_id,
                "ws": workspace_id,
                "email": email,
                "name": "Casey",
            },
        )
    return submitter_id


def _create_item(
    client: TestClient,
    *,
    headers: dict[str, str],
    submitter_id: uuid.UUID | None,
) -> int:
    payload: dict[str, Any] = {
        "title": "Login is slow",
        "description": "Cold start ~8s.",
        "source": "support",
        "pain_level": 3,
    }
    resp = client.post("/api/v1/feedback", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    item_id = int(resp.json()["id"])
    if submitter_id is not None:
        # submitter_id is not part of FeedbackCreateV2 (it's set by the
        # public-submit / backfill paths). Wire it directly so the
        # notifier's submitter resolution has something to walk.
        with engine.begin() as conn:
            conn.execute(
                text(
                    "UPDATE feedback_item SET submitter_id = :sid WHERE id = :id",
                ),
                {"sid": submitter_id, "id": item_id},
            )
    return item_id


def _read_logs(workspace_id: uuid.UUID) -> list[EmailLog]:
    with SessionLocal() as session:
        return list(
            session.scalars(
                select(EmailLog).where(EmailLog.workspace_id == workspace_id),
            ),
        )


# ---------------------------------------------------------------------------
# 1. Happy path
# ---------------------------------------------------------------------------
def test_patch_to_shipped_writes_email_log_row(
    auth_client: TestClient,
) -> None:
    """Marking an item ``shipped`` writes a ``status='sent'`` email_log
    row (DRY_RUN short-circuit) for an item with a linked submitter."""
    slug, ws_id = _signup(auth_client, "alice@example.com")
    headers = {"X-Workspace-Slug": slug}
    submitter_id = _seed_submitter(ws_id, "casey@example.com")
    item_id = _create_item(auth_client, headers=headers, submitter_id=submitter_id)

    resp = auth_client.patch(
        f"/api/v1/feedback/{item_id}",
        json={"status": "shipped"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "shipped"

    logs = _read_logs(ws_id)
    status_logs = [r for r in logs if r.purpose is EmailPurpose.STATUS_CHANGE]
    assert len(status_logs) == 1
    row = status_logs[0]
    assert row.status is EmailStatus.SENT
    assert row.to_address == "casey@example.com"
    assert row.template == "status_change.html"
    assert "shipped" in row.subject.lower()


def test_patch_without_status_change_writes_no_email(
    auth_client: TestClient,
) -> None:
    """Editing other fields must not fire a status-change email."""
    slug, ws_id = _signup(auth_client, "alice@example.com")
    headers = {"X-Workspace-Slug": slug}
    submitter_id = _seed_submitter(ws_id, "casey@example.com")
    item_id = _create_item(auth_client, headers=headers, submitter_id=submitter_id)

    auth_client.patch(
        f"/api/v1/feedback/{item_id}",
        json={"priority": "high"},
        headers=headers,
    )
    assert _read_logs(ws_id) == []


def test_patch_to_non_notify_status_writes_no_email(
    auth_client: TestClient,
) -> None:
    """Default config notifies on ``shipped`` only; ``planned`` is silent."""
    slug, ws_id = _signup(auth_client, "alice@example.com")
    headers = {"X-Workspace-Slug": slug}
    submitter_id = _seed_submitter(ws_id, "casey@example.com")
    item_id = _create_item(auth_client, headers=headers, submitter_id=submitter_id)

    auth_client.patch(
        f"/api/v1/feedback/{item_id}",
        json={"status": "planned"},
        headers=headers,
    )
    logs = [r for r in _read_logs(ws_id) if r.purpose is EmailPurpose.STATUS_CHANGE]
    assert logs == []


# ---------------------------------------------------------------------------
# 2. Fail-soft on Resend outage
# ---------------------------------------------------------------------------
def test_patch_to_shipped_survives_provider_outage(
    auth_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Provider 503 on every retry → PATCH still 200, status_change row
    lands at ``failed``, the originating feedback row is committed."""
    slug, ws_id = _signup(auth_client, "alice@example.com")
    headers = {"X-Workspace-Slug": slug}
    submitter_id = _seed_submitter(ws_id, "casey@example.com")
    item_id = _create_item(auth_client, headers=headers, submitter_id=submitter_id)

    def _always_503(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="upstream busy")

    transport = httpx.MockTransport(_always_503)

    def _factory() -> httpx.Client:
        return httpx.Client(transport=transport, timeout=1.0)

    # Build a non-DRY_RUN client that talks to the mock transport,
    # and substitute it for the cached singleton.
    from feedback_triage import email as email_pkg

    real_settings = email_pkg.get_email_client()._settings  # type: ignore[attr-defined]
    overridden = type(real_settings)(
        _env_file=None,
        **{
            **real_settings.model_dump(),
            "resend_dry_run": False,
            "resend_api_key": "test-key",
            "resend_max_retries": 1,
        },
    )
    fake_client = EmailClient(
        overridden,
        http_client_factory=_factory,
        sleep=lambda _s: None,
    )
    monkeypatch.setattr(email_pkg, "get_email_client", lambda: fake_client)
    # The notifier imports the symbol directly; patch it there too.
    import feedback_triage.services.status_change_notifier as notifier_mod

    monkeypatch.setattr(notifier_mod, "get_email_client", lambda: fake_client)

    resp = auth_client.patch(
        f"/api/v1/feedback/{item_id}",
        json={"status": "shipped"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "shipped"  # PATCH committed despite outage

    logs = [r for r in _read_logs(ws_id) if r.purpose is EmailPurpose.STATUS_CHANGE]
    assert len(logs) == 1
    assert logs[0].status is EmailStatus.FAILED
    assert logs[0].error_code == "http_503"


# ---------------------------------------------------------------------------
# 3. Opt-out paths
# ---------------------------------------------------------------------------
def test_no_submitter_no_email(auth_client: TestClient) -> None:
    """Team-authored items (no submitter_id) silently skip the send."""
    slug, ws_id = _signup(auth_client, "alice@example.com")
    headers = {"X-Workspace-Slug": slug}
    item_id = _create_item(auth_client, headers=headers, submitter_id=None)

    auth_client.patch(
        f"/api/v1/feedback/{item_id}",
        json={"status": "shipped"},
        headers=headers,
    )
    logs = [r for r in _read_logs(ws_id) if r.purpose is EmailPurpose.STATUS_CHANGE]
    assert logs == []


def test_anonymous_submitter_no_email(auth_client: TestClient) -> None:
    """Submitter rows with ``email IS NULL`` (anonymous public submit)
    do not receive a status-change email."""
    slug, ws_id = _signup(auth_client, "alice@example.com")
    headers = {"X-Workspace-Slug": slug}
    submitter_id = _seed_submitter(ws_id, email=None)
    item_id = _create_item(auth_client, headers=headers, submitter_id=submitter_id)

    auth_client.patch(
        f"/api/v1/feedback/{item_id}",
        json={"status": "shipped"},
        headers=headers,
    )
    logs = [r for r in _read_logs(ws_id) if r.purpose is EmailPurpose.STATUS_CHANGE]
    assert logs == []


# ---------------------------------------------------------------------------
# Should-tier: configurable EMAIL_NOTIFY_ON_STATUSES
# ---------------------------------------------------------------------------
def test_extra_notify_status_fires_email(
    auth_client: TestClient,
) -> None:
    """When the operator opts into ``planned`` notifications via
    ``EMAIL_NOTIFY_ON_STATUSES``, transitions into ``planned`` fire."""
    slug, ws_id = _signup(auth_client, "alice@example.com")
    headers = {"X-Workspace-Slug": slug}
    submitter_id = _seed_submitter(ws_id, "casey@example.com")
    item_id = _create_item(auth_client, headers=headers, submitter_id=submitter_id)

    # Override the FastAPI ``get_settings`` dependency with one that
    # opts into the wider notify set. ``dependency_overrides`` is
    # restored in ``finally`` so adjacent tests are unaffected.
    from feedback_triage import config as config_mod

    base = config_mod.Settings(_env_file=None)  # type: ignore[call-arg]
    expanded = type(base)(
        _env_file=None,
        **{
            **base.model_dump(),
            "email_notify_on_statuses": "shipped,planned",
        },
    )
    auth_client.app.dependency_overrides[config_mod.get_settings] = lambda: expanded
    try:
        resp = auth_client.patch(
            f"/api/v1/feedback/{item_id}",
            json={"status": "planned"},
            headers=headers,
        )
        assert resp.status_code == 200
    finally:
        auth_client.app.dependency_overrides.pop(config_mod.get_settings, None)

    logs = [r for r in _read_logs(ws_id) if r.purpose is EmailPurpose.STATUS_CHANGE]
    assert len(logs) == 1
    assert "planned" in logs[0].subject.lower()
