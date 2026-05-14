"""PR 3.3 -- management changelog page tests.

Like the roadmap page, this is a thin shell: auth-required, tenant-
scoped, seeds the workspace slug for ``static/js/changelog.js``. Edit
flow is exercised through the v2 PATCH endpoint covered elsewhere.
"""

from __future__ import annotations

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


def test_changelog_page_requires_auth(
    auth_client: TestClient,
    truncate_auth_world: None,
) -> None:
    slug = _signup_and_login(auth_client, "owner@example.com")
    auth_client.cookies.clear()

    resp = auth_client.get(f"/w/{slug}/changelog")

    assert resp.status_code == 401


def test_changelog_page_unknown_slug_returns_404(
    auth_client: TestClient,
    truncate_auth_world: None,
) -> None:
    _signup_and_login(auth_client, "owner@example.com")

    resp = auth_client.get("/w/no-such-workspace/changelog")

    assert resp.status_code == 404


def test_changelog_page_cross_tenant_returns_404(
    auth_client: TestClient,
    truncate_auth_world: None,
) -> None:
    other_slug = _signup_and_login(auth_client, "stranger@example.com")
    auth_client.cookies.clear()
    _signup_and_login(auth_client, "owner@example.com")

    resp = auth_client.get(f"/w/{other_slug}/changelog")

    assert resp.status_code == 404


def test_changelog_page_renders_shell(
    auth_client: TestClient,
    truncate_auth_world: None,
) -> None:
    slug = _signup_and_login(auth_client, "owner@example.com")

    resp = auth_client.get(f"/w/{slug}/changelog")

    assert resp.status_code == 200
    body = resp.text
    assert f'data-workspace-slug="{slug}"' in body
    assert 'id="changelog-list"' in body
    assert 'id="release-note-template"' in body
    assert "/static/js/changelog.js" in body
