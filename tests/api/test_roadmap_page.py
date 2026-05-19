"""PR 3.3 -- management roadmap page tests.

Phase 4 serves the route through the shared React shell. These tests
focus on auth/tenancy guards and shell metadata contract.
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

VALID_PASSWORD = "correct horse battery staple"  # pragma: allowlist secret


def _signup_and_login(client: TestClient, email: str) -> str:
    resp = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": VALID_PASSWORD},
    )
    assert resp.status_code == 201, resp.text
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": VALID_PASSWORD},
    )
    assert login.status_code == 200, login.text
    return str(login.json()["memberships"][0]["workspace_slug"])


def _create_item(client: TestClient, slug: str, *, title: str) -> int:
    payload: dict[str, Any] = {
        "title": title,
        "description": "Background.",
        "source": "email",
        "pain_level": 3,
        "type": "feature_request",
    }
    resp = client.post(
        "/api/v1/feedback",
        json=payload,
        headers={"X-Workspace-Slug": slug},
    )
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


# ---------------------------------------------------------------------------
# Auth + slug guards
# ---------------------------------------------------------------------------


def test_roadmap_page_requires_auth(
    auth_client: TestClient,
    truncate_auth_world: None,
) -> None:
    slug = _signup_and_login(auth_client, "owner@example.com")
    auth_client.cookies.clear()

    resp = auth_client.get(f"/w/{slug}/roadmap")

    assert resp.status_code == 401


def test_roadmap_page_unknown_slug_returns_404(
    auth_client: TestClient,
    truncate_auth_world: None,
) -> None:
    _signup_and_login(auth_client, "owner@example.com")

    resp = auth_client.get("/w/no-such-workspace/roadmap")

    assert resp.status_code == 404


def test_roadmap_page_cross_tenant_returns_404(
    auth_client: TestClient,
    truncate_auth_world: None,
) -> None:
    """A logged-in user from workspace A cannot probe workspace B's roadmap."""
    other_slug = _signup_and_login(auth_client, "stranger@example.com")
    auth_client.cookies.clear()
    _signup_and_login(auth_client, "owner@example.com")

    # Owner is now logged in; ``other_slug`` is a workspace they don't belong to.
    resp = auth_client.get(f"/w/{other_slug}/roadmap")

    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Shell rendering
# ---------------------------------------------------------------------------


def test_roadmap_page_renders_kanban_shell(
    auth_client: TestClient,
    truncate_auth_world: None,
) -> None:
    slug = _signup_and_login(auth_client, "owner@example.com")
    _create_item(auth_client, slug, title="Something to plan")

    resp = auth_client.get(f"/w/{slug}/roadmap")

    assert resp.status_code == 200
    body = resp.text
    assert 'id="sn-react-app-root"' in body
    assert f'data-workspace-slug="{slug}"' in body
    assert 'data-page-key="roadmap"' in body
    assert 'data-active-section="roadmap"' in body
