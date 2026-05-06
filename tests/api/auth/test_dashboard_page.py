"""Smoke tests for the workspace dashboard page route."""

from __future__ import annotations

from fastapi.testclient import TestClient

VALID_PASSWORD = "correct horse battery staple"  # pragma: allowlist secret


def _signup_and_login(client: TestClient, email: str) -> dict[str, object]:
    client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": VALID_PASSWORD},
    )
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": VALID_PASSWORD},
    )
    assert resp.status_code == 200
    return resp.json()


def test_dashboard_renders_for_member(auth_client: TestClient) -> None:
    body = _signup_and_login(auth_client, "owner@example.com")
    slug = body["memberships"][0]["workspace_slug"]

    resp = auth_client.get(f"/w/{slug}/dashboard")
    assert resp.status_code == 200, resp.text
    assert "no feedback yet" in resp.text.lower()
    assert slug in resp.text


def test_dashboard_anonymous_returns_401(auth_client: TestClient) -> None:
    # No login → ``current_user_required`` → 401.
    resp = auth_client.get("/w/whatever/dashboard")
    assert resp.status_code == 401


def test_dashboard_cross_tenant_returns_404(auth_client: TestClient) -> None:
    """Authenticated, but slug belongs to a different tenant → 404."""
    _signup_and_login(auth_client, "owner@example.com")

    resp = auth_client.get("/w/some-other-slug/dashboard")
    assert resp.status_code == 404
