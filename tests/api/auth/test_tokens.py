"""Verify-email + password-reset flow tests."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import text

from feedback_triage.auth import tokens as auth_tokens
from feedback_triage.database import SessionLocal, engine

VALID_PASSWORD = "correct horse battery staple"
NEW_PASSWORD = "another-passphrase-2026"  # pragma: allowlist secret


def _signup(client: TestClient, email: str = "carol@example.com") -> str:
    resp = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": VALID_PASSWORD},
    )
    assert resp.status_code == 201
    return resp.json()["user"]["id"]


def _user_id_for(email: str) -> str:
    with engine.begin() as conn:
        return conn.execute(
            text("SELECT id FROM users WHERE email = :e"),
            {"e": email},
        ).scalar_one()


def test_verify_email_flips_is_verified(auth_client: TestClient) -> None:
    _signup(auth_client)
    user_id = _user_id_for("carol@example.com")
    # Mint a token directly so we don't have to scrape an outbound email.
    db = SessionLocal()
    try:
        issued = auth_tokens.mint_verification_token(db, user_id=user_id)
        db.commit()
    finally:
        db.close()

    resp = auth_client.post(
        "/api/v1/auth/verify-email",
        json={"token": issued.raw_token},
    )
    assert resp.status_code == 200
    assert resp.json() == {"status": "verified"}

    with engine.begin() as conn:
        verified = conn.execute(
            text("SELECT is_verified FROM users WHERE email = 'carol@example.com'"),
        ).scalar_one()
    assert verified is True


def test_verify_email_rejects_replay(auth_client: TestClient) -> None:
    _signup(auth_client)
    user_id = _user_id_for("carol@example.com")
    db = SessionLocal()
    try:
        issued = auth_tokens.mint_verification_token(db, user_id=user_id)
        db.commit()
    finally:
        db.close()
    first = auth_client.post(
        "/api/v1/auth/verify-email",
        json={"token": issued.raw_token},
    )
    assert first.status_code == 200
    second = auth_client.post(
        "/api/v1/auth/verify-email",
        json={"token": issued.raw_token},
    )
    assert second.status_code == 410


def test_verify_email_unknown_token_returns_410(auth_client: TestClient) -> None:
    resp = auth_client.post(
        "/api/v1/auth/verify-email",
        json={"token": "not-a-real-token"},
    )
    assert resp.status_code == 410


def test_reset_password_consumes_token_and_revokes_sessions(
    auth_client: TestClient,
) -> None:
    _signup(auth_client)
    auth_client.post(
        "/api/v1/auth/login",
        json={"email": "carol@example.com", "password": VALID_PASSWORD},
    )
    user_id = _user_id_for("carol@example.com")
    db = SessionLocal()
    try:
        issued = auth_tokens.mint_password_reset_token(db, user_id=user_id)
        db.commit()
    finally:
        db.close()

    resp = auth_client.post(
        "/api/v1/auth/reset-password",
        json={"token": issued.raw_token, "new_password": NEW_PASSWORD},
    )
    assert resp.status_code == 200, resp.text

    # Old session is revoked — /me on the existing client must 401.
    me_after = auth_client.get("/api/v1/auth/me")
    assert me_after.status_code == 401

    # New password works.
    fresh = auth_client.post(
        "/api/v1/auth/login",
        json={"email": "carol@example.com", "password": NEW_PASSWORD},
    )
    assert fresh.status_code == 200


def test_reset_password_rejects_replay(auth_client: TestClient) -> None:
    _signup(auth_client)
    user_id = _user_id_for("carol@example.com")
    db = SessionLocal()
    try:
        issued = auth_tokens.mint_password_reset_token(db, user_id=user_id)
        db.commit()
    finally:
        db.close()
    first = auth_client.post(
        "/api/v1/auth/reset-password",
        json={"token": issued.raw_token, "new_password": NEW_PASSWORD},
    )
    assert first.status_code == 200
    second = auth_client.post(
        "/api/v1/auth/reset-password",
        json={"token": issued.raw_token, "new_password": NEW_PASSWORD},
    )
    assert second.status_code == 410
