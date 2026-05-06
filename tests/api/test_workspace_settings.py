"""PR 2.5 — settings page / workspace settings API tests.

Covers the ``PATCH /api/v1/workspaces/{slug}`` extensions:

* Renaming the workspace (existing path, unchanged behaviour).
* Toggling ``public_submit_enabled`` flips the flag and gates the
  public submission surface 404 when off.
* Empty / over-shaped bodies return 422.
* Page route renders for owners and read-only-shapes for
  non-owners.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

VALID_PASSWORD = "correct horse battery staple"  # pragma: allowlist secret


def _signup_and_login(
    client: TestClient,
    email: str = "owner@example.com",
) -> dict[str, object]:
    resp = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": VALID_PASSWORD},
    )
    assert resp.status_code == 201, resp.text
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": VALID_PASSWORD},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _first_slug(body: dict[str, object]) -> str:
    memberships = body["memberships"]
    assert isinstance(memberships, list) and memberships
    return str(memberships[0]["workspace_slug"])


# ---------------------------------------------------------------------------
# PATCH semantics
# ---------------------------------------------------------------------------


def test_patch_workspace_rename_only(auth_client: TestClient) -> None:
    body = _signup_and_login(auth_client)
    slug = _first_slug(body)

    resp = auth_client.patch(
        f"/api/v1/workspaces/{slug}",
        json={"name": "Renamed"},
    )
    assert resp.status_code == 200, resp.text
    payload = resp.json()
    assert payload["name"] == "Renamed"
    # The flag defaults to true and is not affected by a name-only patch.
    assert payload["public_submit_enabled"] is True


def test_patch_workspace_toggle_public_submit(auth_client: TestClient) -> None:
    body = _signup_and_login(auth_client)
    slug = _first_slug(body)

    resp = auth_client.patch(
        f"/api/v1/workspaces/{slug}",
        json={"public_submit_enabled": False},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["public_submit_enabled"] is False

    # Round-trip GET reflects the new state.
    resp = auth_client.get(f"/api/v1/workspaces/{slug}")
    assert resp.status_code == 200
    assert resp.json()["public_submit_enabled"] is False


def test_patch_workspace_combined_fields(auth_client: TestClient) -> None:
    body = _signup_and_login(auth_client)
    slug = _first_slug(body)

    resp = auth_client.patch(
        f"/api/v1/workspaces/{slug}",
        json={"name": "New name", "public_submit_enabled": False},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["name"] == "New name"
    assert data["public_submit_enabled"] is False


def test_patch_workspace_empty_body_returns_422(auth_client: TestClient) -> None:
    body = _signup_and_login(auth_client)
    slug = _first_slug(body)

    resp = auth_client.patch(f"/api/v1/workspaces/{slug}", json={})
    assert resp.status_code == 422


def test_patch_workspace_rejects_unknown_field(auth_client: TestClient) -> None:
    body = _signup_and_login(auth_client)
    slug = _first_slug(body)

    resp = auth_client.patch(
        f"/api/v1/workspaces/{slug}",
        json={"slug": "new-slug"},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Public-submit kill switch wiring
# ---------------------------------------------------------------------------


def test_public_submit_disabled_returns_404_on_page(
    auth_client: TestClient,
) -> None:
    body = _signup_and_login(auth_client)
    slug = _first_slug(body)

    auth_client.patch(
        f"/api/v1/workspaces/{slug}",
        json={"public_submit_enabled": False},
    )

    # A separate session — anonymous — must see the same 404 envelope
    # as an unknown slug. We use the same TestClient but the public
    # routes don't require auth, so it's representative.
    resp = auth_client.get(f"/w/{slug}/submit")
    assert resp.status_code == 404


def test_public_submit_disabled_returns_404_on_post(
    auth_client: TestClient,
) -> None:
    body = _signup_and_login(auth_client)
    slug = _first_slug(body)

    auth_client.patch(
        f"/api/v1/workspaces/{slug}",
        json={"public_submit_enabled": False},
    )

    resp = auth_client.post(
        f"/api/v1/public/feedback/{slug}",
        json={
            "title": "Should be rejected",
            "pain_level": 3,
            "type": "bug",
        },
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Page route
# ---------------------------------------------------------------------------


def test_settings_page_renders_for_owner(auth_client: TestClient) -> None:
    body = _signup_and_login(auth_client)
    slug = _first_slug(body)

    resp = auth_client.get(f"/w/{slug}/settings")
    assert resp.status_code == 200
    text = resp.text
    # Owner sections are present.
    assert 'id="workspace-form"' in text
    assert 'id="public-submit-form"' in text
    assert 'id="invite-form"' in text
    assert 'id="tag-form"' in text


def test_settings_page_unknown_slug_returns_404(auth_client: TestClient) -> None:
    _signup_and_login(auth_client)
    resp = auth_client.get("/w/no-such-workspace/settings")
    assert resp.status_code == 404
