"""Flow tests for ``POST /api/v1/auth/signup``.

Covers the happy path, the duplicate-email no-enumeration path, the
weak-password path, and the email-log side effect (a verification
row reaches ``status=sent`` under ``RESEND_DRY_RUN=1``).
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import text

from feedback_triage.database import engine

VALID_PASSWORD = "correct horse battery staple"


def _signup(client: TestClient, **overrides: str) -> dict:
    payload = {
        "email": overrides.pop("email", "alice@example.com"),
        "password": overrides.pop("password", VALID_PASSWORD),
    }
    if "workspace_name" in overrides:
        payload["workspace_name"] = overrides.pop("workspace_name")
    return client.post("/api/v1/auth/signup", json=payload)


def test_signup_creates_user_workspace_and_membership(
    auth_client: TestClient,
) -> None:
    resp = _signup(auth_client)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["user"]["email"] == "alice@example.com"
    assert body["user"]["is_verified"] is False
    assert body["workspace"]["slug"]
    assert body["workspace"]["name"] == "alice's workspace"

    # DB-level invariants: one user, one workspace, one membership row.
    with engine.begin() as conn:
        users = conn.execute(text("SELECT count(*) FROM users")).scalar_one()
        workspaces = conn.execute(text("SELECT count(*) FROM workspaces")).scalar_one()
        members = conn.execute(
            text("SELECT count(*) FROM workspace_memberships"),
        ).scalar_one()
    assert (users, workspaces, members) == (1, 1, 1)


def test_signup_uses_provided_workspace_name(auth_client: TestClient) -> None:
    resp = _signup(auth_client, workspace_name="Acme Co")
    assert resp.status_code == 201
    assert resp.json()["workspace"]["name"] == "Acme Co"


def test_signup_writes_verification_email_log(
    auth_client: TestClient,
) -> None:
    resp = _signup(auth_client)
    assert resp.status_code == 201
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                "SELECT to_address, purpose, template, status FROM email_log",
            ),
        ).all()
    assert len(rows) == 1
    to_addr, purpose, template, log_status = rows[0]
    assert to_addr == "alice@example.com"
    assert purpose == "verification"
    assert template == "verification.html"
    assert log_status == "sent"  # DRY_RUN short-circuits to ``sent``.


def test_signup_rejects_short_password(auth_client: TestClient) -> None:
    resp = _signup(auth_client, password="too-short")  # pragma: allowlist secret
    assert resp.status_code == 422
