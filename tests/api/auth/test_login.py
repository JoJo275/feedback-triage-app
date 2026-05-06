"""``POST /api/v1/auth/login`` flow tests.

Covers the happy path (200 + ``Set-Cookie``), the wrong-password path
(400 with no enumeration), and the unknown-email path (also 400).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from feedback_triage.auth.cookies import SESSION_COOKIE_NAME

VALID_PASSWORD = "correct horse battery staple"


def _signup(client: TestClient, email: str = "bob@example.com") -> None:
    resp = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": VALID_PASSWORD},
    )
    assert resp.status_code == 201


def test_login_success_sets_session_cookie(auth_client: TestClient) -> None:
    _signup(auth_client)
    resp = auth_client.post(
        "/api/v1/auth/login",
        json={"email": "bob@example.com", "password": VALID_PASSWORD},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["user"]["email"] == "bob@example.com"
    assert len(body["memberships"]) == 1
    assert body["memberships"][0]["role"] == "owner"
    # The httpx ``TestClient`` exposes Set-Cookie via ``cookies``.
    assert auth_client.cookies.get(SESSION_COOKIE_NAME)


def test_login_wrong_password_returns_400(auth_client: TestClient) -> None:
    _signup(auth_client)
    resp = auth_client.post(
        "/api/v1/auth/login",
        json={"email": "bob@example.com", "password": "wrong-but-long-enough"},
    )
    assert resp.status_code == 400
    assert auth_client.cookies.get(SESSION_COOKIE_NAME) is None


def test_login_unknown_email_returns_400(auth_client: TestClient) -> None:
    resp = auth_client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": VALID_PASSWORD},
    )
    assert resp.status_code == 400


def test_me_returns_user_for_signed_in_caller(auth_client: TestClient) -> None:
    _signup(auth_client)
    auth_client.post(
        "/api/v1/auth/login",
        json={"email": "bob@example.com", "password": VALID_PASSWORD},
    )
    resp = auth_client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    assert resp.json()["user"]["email"] == "bob@example.com"


def test_me_returns_401_when_anonymous(auth_client: TestClient) -> None:
    resp = auth_client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_logout_clears_session(auth_client: TestClient) -> None:
    _signup(auth_client)
    auth_client.post(
        "/api/v1/auth/login",
        json={"email": "bob@example.com", "password": VALID_PASSWORD},
    )
    resp = auth_client.post("/api/v1/auth/logout")
    assert resp.status_code == 204
    # Subsequent /me must be unauthenticated.
    me = auth_client.get("/api/v1/auth/me")
    assert me.status_code == 401
