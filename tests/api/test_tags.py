"""API flow tests for ``/api/v1/tags`` (PR 2.2).

Owner-only writes, workspace-scoped reads. Reuses the auth-world
fixtures from ``tests/conftest.py``.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

VALID_PASSWORD = "correct horse battery staple"  # pragma: allowlist secret


def _signup(client: TestClient, email: str) -> str:
    client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": VALID_PASSWORD},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": VALID_PASSWORD},
    )
    return login.json()["memberships"][0]["workspace_slug"]


def test_create_tag_returns_201(auth_client: TestClient) -> None:
    slug = _signup(auth_client, "alice@example.com")
    headers = {"X-Workspace-Slug": slug}
    resp = auth_client.post(
        "/api/v1/tags",
        json={"name": "Bug", "slug": "bug", "color": "rose"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["name"] == "Bug"
    assert body["slug"] == "bug"
    assert body["color"] == "rose"


def test_create_tag_duplicate_slug_returns_409(auth_client: TestClient) -> None:
    slug = _signup(auth_client, "alice@example.com")
    headers = {"X-Workspace-Slug": slug}
    auth_client.post(
        "/api/v1/tags",
        json={"name": "Bug", "slug": "bug"},
        headers=headers,
    )
    resp = auth_client.post(
        "/api/v1/tags",
        json={"name": "Another", "slug": "bug"},
        headers=headers,
    )
    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "tag_slug_taken"


def test_invalid_slug_returns_422(auth_client: TestClient) -> None:
    slug = _signup(auth_client, "alice@example.com")
    headers = {"X-Workspace-Slug": slug}
    resp = auth_client.post(
        "/api/v1/tags",
        json={"name": "Bug", "slug": "Bad Slug!"},
        headers=headers,
    )
    assert resp.status_code == 422


def test_invalid_color_returns_422(auth_client: TestClient) -> None:
    slug = _signup(auth_client, "alice@example.com")
    headers = {"X-Workspace-Slug": slug}
    resp = auth_client.post(
        "/api/v1/tags",
        json={"name": "Bug", "slug": "bug", "color": "neon-pink"},
        headers=headers,
    )
    assert resp.status_code == 422


def test_list_tags_envelope(auth_client: TestClient) -> None:
    slug = _signup(auth_client, "alice@example.com")
    headers = {"X-Workspace-Slug": slug}
    auth_client.post(
        "/api/v1/tags",
        json={"name": "Bug", "slug": "bug"},
        headers=headers,
    )
    resp = auth_client.get("/api/v1/tags", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"items", "total", "skip", "limit"}
    assert body["total"] == 1


def test_patch_and_delete_tag(auth_client: TestClient) -> None:
    slug = _signup(auth_client, "alice@example.com")
    headers = {"X-Workspace-Slug": slug}
    created = auth_client.post(
        "/api/v1/tags",
        json={"name": "Bug", "slug": "bug"},
        headers=headers,
    ).json()
    patched = auth_client.patch(
        f"/api/v1/tags/{created['id']}",
        json={"name": "Defect"},
        headers=headers,
    )
    assert patched.status_code == 200
    assert patched.json()["name"] == "Defect"
    deleted = auth_client.delete(f"/api/v1/tags/{created['id']}", headers=headers)
    assert deleted.status_code == 204


def test_cross_tenant_tag_lookup_returns_404(auth_client: TestClient) -> None:
    """A tag id from workspace A must 404 when fetched from workspace B."""
    slug_a = _signup(auth_client, "alice@example.com")
    headers_a = {"X-Workspace-Slug": slug_a}
    tag = auth_client.post(
        "/api/v1/tags",
        json={"name": "Bug", "slug": "bug"},
        headers=headers_a,
    ).json()

    # log out + sign up second user
    auth_client.post("/api/v1/auth/logout")
    slug_b = _signup(auth_client, "bob@example.com")
    headers_b = {"X-Workspace-Slug": slug_b}

    resp = auth_client.patch(
        f"/api/v1/tags/{tag['id']}",
        json={"name": "Stolen"},
        headers=headers_b,
    )
    assert resp.status_code == 404
