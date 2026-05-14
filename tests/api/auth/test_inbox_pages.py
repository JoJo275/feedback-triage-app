"""Smoke tests for the v2 inbox / feedback list / feedback detail pages.

These are server-side tests against the page routes shipped in PR
2.3. The actual UI hydration runs client-side; the e2e Playwright
suite covers the rendered behaviour. Here we only assert that the
shell loads, that the workspace context resolver is in front of
every route (auth / cross-tenant 404), and that the detail route
404s on a feedback id from another workspace.
"""

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


def _create_feedback(client: TestClient, slug: str, title: str = "T") -> int:
    resp = client.post(
        "/api/v1/feedback",
        headers={"X-Workspace-Slug": slug},
        json={
            "title": title,
            "description": "d",
            "source": "web_form",
            "pain_level": 3,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


# ---------------------------------------------------------------------------
# Inbox + feedback list
# ---------------------------------------------------------------------------


def test_inbox_renders_for_member(auth_client: TestClient) -> None:
    body = _signup_and_login(auth_client, "owner@example.com")
    slug = body["memberships"][0]["workspace_slug"]

    resp = auth_client.get(f"/w/{slug}/inbox")
    assert resp.status_code == 200, resp.text
    assert "inbox" in resp.text.lower()
    assert slug in resp.text
    # The inbox JS bundle must be referenced.
    assert "inbox.js" in resp.text


def test_feedback_list_renders_for_member(auth_client: TestClient) -> None:
    body = _signup_and_login(auth_client, "owner@example.com")
    slug = body["memberships"][0]["workspace_slug"]

    resp = auth_client.get(f"/w/{slug}/feedback")
    assert resp.status_code == 200, resp.text
    assert "feedback" in resp.text.lower()
    # Feedback list shares the inbox shell + script.
    assert "inbox.js" in resp.text


def test_feedback_new_renders_for_member(auth_client: TestClient) -> None:
    body = _signup_and_login(auth_client, "owner@example.com")
    slug = body["memberships"][0]["workspace_slug"]

    resp = auth_client.get(f"/w/{slug}/feedback/new")
    assert resp.status_code == 200, resp.text
    assert "create feedback" in resp.text.lower()


def test_inbox_anonymous_returns_401(auth_client: TestClient) -> None:
    resp = auth_client.get("/w/whatever/inbox")
    assert resp.status_code == 401


def test_inbox_cross_tenant_returns_404(auth_client: TestClient) -> None:
    _signup_and_login(auth_client, "owner@example.com")
    resp = auth_client.get("/w/some-other-slug/inbox")
    assert resp.status_code == 404


def test_feedback_list_cross_tenant_returns_404(auth_client: TestClient) -> None:
    _signup_and_login(auth_client, "owner@example.com")
    resp = auth_client.get("/w/some-other-slug/feedback")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Feedback detail
# ---------------------------------------------------------------------------


def test_feedback_detail_renders_for_member(auth_client: TestClient) -> None:
    body = _signup_and_login(auth_client, "owner@example.com")
    slug = body["memberships"][0]["workspace_slug"]
    item_id = _create_feedback(auth_client, slug, title="Pagination is slow")

    resp = auth_client.get(f"/w/{slug}/feedback/{item_id}")
    assert resp.status_code == 200, resp.text
    assert "Pagination is slow" in resp.text
    assert "feedback_detail.js" in resp.text


def test_feedback_detail_unknown_id_returns_404(auth_client: TestClient) -> None:
    body = _signup_and_login(auth_client, "owner@example.com")
    slug = body["memberships"][0]["workspace_slug"]

    resp = auth_client.get(f"/w/{slug}/feedback/99999999")
    assert resp.status_code == 404


def test_feedback_detail_cross_tenant_returns_404(auth_client: TestClient) -> None:
    """An item that exists in workspace A is invisible from workspace B."""
    a = _signup_and_login(auth_client, "alice@example.com")
    a_slug = a["memberships"][0]["workspace_slug"]
    item_id = _create_feedback(auth_client, a_slug, title="Hidden")

    # Sign out + sign up as a different user with their own workspace.
    auth_client.post("/api/v1/auth/logout")
    b = _signup_and_login(auth_client, "bob@example.com")
    b_slug = b["memberships"][0]["workspace_slug"]
    assert b_slug != a_slug

    resp = auth_client.get(f"/w/{b_slug}/feedback/{item_id}")
    assert resp.status_code == 404


def test_feedback_detail_anonymous_returns_401(auth_client: TestClient) -> None:
    resp = auth_client.get("/w/whatever/feedback/1")
    assert resp.status_code == 401
