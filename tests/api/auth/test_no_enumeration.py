"""Email-enumeration canary for the auth surface (PR 1.7).

Per ``docs/project/spec/v2/auth.md`` — Email enumeration posture, the
following endpoints must be byte-equivalent for known and unknown
addresses (apart from row ids that already existed):

- ``POST /api/v1/auth/signup`` — duplicate email → same 201 shape; the
  difference shows up only in ``email_log`` (template differs).
- ``POST /api/v1/auth/forgot-password`` — always 202.
- ``POST /api/v1/auth/login`` — wrong password vs. unknown email both
  return the same 400 body. (Asserted in ``test_login.py``; included
  here too for the doc-of-truth.)
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import text

from feedback_triage.database import engine

VALID_PASSWORD = "correct horse battery staple"


def _signup(client: TestClient, email: str = "duplicate@example.com") -> dict:
    resp = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": VALID_PASSWORD},
    )
    assert resp.status_code == 201
    return resp.json()


def _strip_volatile(body: dict) -> dict:
    """Remove fields that legitimately differ between fresh + duplicate.

    ``id`` and ``created_at`` of the *user* and *workspace* are always
    going to differ when the row already existed; the contract is that
    *the shape* — and the keys present — are identical.
    """
    return {
        "user_keys": sorted(body["user"].keys()),
        "user_email": body["user"]["email"],
        "user_is_verified": body["user"]["is_verified"],
        "workspace_keys": sorted(body["workspace"].keys()),
    }


def test_signup_duplicate_returns_same_shape(auth_client: TestClient) -> None:
    first = _signup(auth_client)
    second = auth_client.post(
        "/api/v1/auth/signup",
        json={"email": "duplicate@example.com", "password": VALID_PASSWORD},
    )
    assert second.status_code == 201
    assert _strip_volatile(first) == _strip_volatile(second.json())


def test_signup_duplicate_uses_already_template(auth_client: TestClient) -> None:
    _signup(auth_client)
    # Second signup with the same email picks a different email template.
    auth_client.post(
        "/api/v1/auth/signup",
        json={"email": "duplicate@example.com", "password": VALID_PASSWORD},
    )
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                "SELECT template FROM email_log "
                "WHERE to_address = 'duplicate@example.com' "
                "ORDER BY created_at",
            ),
        ).all()
    templates_used = [r[0] for r in rows]
    assert templates_used == ["verification.html", "verification_already.html"]


def test_forgot_password_always_returns_202(auth_client: TestClient) -> None:
    # Known email
    _signup(auth_client, email="known@example.com")
    known = auth_client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "known@example.com"},
    )
    # Unknown email
    unknown = auth_client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "ghost@example.com"},
    )
    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json() == {"status": "accepted"}


def test_forgot_password_logs_email_only_for_known_address(
    auth_client: TestClient,
) -> None:
    _signup(auth_client, email="known@example.com")
    auth_client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "known@example.com"},
    )
    auth_client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "ghost@example.com"},
    )
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                "SELECT to_address FROM email_log WHERE purpose = 'password_reset'",
            ),
        ).all()
    addresses = {r[0] for r in rows}
    assert addresses == {"known@example.com"}


def test_login_unknown_and_wrong_password_return_same_body(
    auth_client: TestClient,
) -> None:
    _signup(auth_client, email="real@example.com")
    wrong_pw = auth_client.post(
        "/api/v1/auth/login",
        json={"email": "real@example.com", "password": "wrong-but-long-enough"},
    )
    unknown = auth_client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@example.com", "password": VALID_PASSWORD},
    )
    assert wrong_pw.status_code == unknown.status_code == 400
    # ``request_id`` is per-request and intentionally differs; the
    # ``detail`` message is the part the attacker would see.
    assert wrong_pw.json()["detail"] == unknown.json()["detail"]
