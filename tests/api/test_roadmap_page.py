"""PR 3.3 -- management roadmap kanban page tests.

The kanban page itself is a thin shell: it requires auth, resolves the
workspace through ``WorkspaceContextDep`` (so unknown / cross-tenant
slugs 404), and seeds the workspace slug into the DOM for
``static/js/roadmap.js`` to read. The actual data flow goes through
the v2 list + PATCH endpoints already covered by their own tests --
here we only assert the page-level guards.
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
    # Slug is seeded into the DOM for the JS module.
    assert f'data-workspace-slug="{slug}"' in body
    # All three columns render server-side.
    assert 'data-column="planned"' in body
    assert 'data-column="in_progress"' in body
    assert 'data-column="shipped"' in body
    # Inert template is present so the JS can clone cards.
    assert 'id="kanban-card-template"' in body
    # The roadmap.js module is wired.
    assert "/static/js/roadmap.js" in body
