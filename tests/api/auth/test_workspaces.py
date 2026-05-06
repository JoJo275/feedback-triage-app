"""Flow tests for ``/api/v1/workspaces/...``.

Reuses the auth-world conftest (``auth_client`` + ``truncate_auth_world``)
because every workspace route requires a logged-in caller. The
signup → login pair is the cheapest way to land a known user with a
known workspace and an OWNER membership.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

VALID_PASSWORD = "correct horse battery staple"  # pragma: allowlist secret


def _signup_and_login(
    client: TestClient,
    email: str = "alice@example.com",
) -> dict[str, object]:
    """Create a user + workspace, log in, return the login body."""
    signup = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": VALID_PASSWORD},
    )
    assert signup.status_code == 201, signup.text
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": VALID_PASSWORD},
    )
    assert login.status_code == 200, login.text
    return login.json()


def test_list_workspaces_returns_callers_memberships(
    auth_client: TestClient,
) -> None:
    body = _signup_and_login(auth_client)
    slug = body["memberships"][0]["workspace_slug"]

    resp = auth_client.get("/api/v1/workspaces")
    assert resp.status_code == 200, resp.text
    items = resp.json()
    assert len(items) == 1
    assert items[0]["workspace_slug"] == slug
    assert items[0]["role"] == "owner"


def test_list_workspaces_anonymous_returns_401(auth_client: TestClient) -> None:
    resp = auth_client.get("/api/v1/workspaces")
    assert resp.status_code == 401


def test_get_workspace_by_slug(auth_client: TestClient) -> None:
    body = _signup_and_login(auth_client)
    slug = body["memberships"][0]["workspace_slug"]

    resp = auth_client.get(f"/api/v1/workspaces/{slug}")
    assert resp.status_code == 200, resp.text
    assert resp.json()["slug"] == slug


def test_get_unknown_workspace_returns_404(auth_client: TestClient) -> None:
    _signup_and_login(auth_client)
    # A slug the caller is not a member of (and which doesn't exist)
    # must 404 with the canonical not_found shape — never 403.
    resp = auth_client.get("/api/v1/workspaces/nope-not-here")
    assert resp.status_code == 404
    # ``register_exception_handlers`` wraps HTTPException details into
    # the envelope; the ``code=not_found`` payload from the tenancy
    # dep lives under ``detail`` either flattened or nested.
    assert "not_found" in resp.text


def test_patch_workspace_renames_owner_only(auth_client: TestClient) -> None:
    body = _signup_and_login(auth_client)
    slug = body["memberships"][0]["workspace_slug"]

    resp = auth_client.patch(
        f"/api/v1/workspaces/{slug}",
        json={"name": "Renamed"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["name"] == "Renamed"


def test_patch_workspace_rejects_unknown_field(auth_client: TestClient) -> None:
    body = _signup_and_login(auth_client)
    slug = body["memberships"][0]["workspace_slug"]

    # ``slug`` is immutable; the request schema forbids extra fields.
    resp = auth_client.patch(
        f"/api/v1/workspaces/{slug}",
        json={"name": "ok", "slug": "new-slug"},
    )
    assert resp.status_code == 422


def test_list_members_returns_owner(auth_client: TestClient) -> None:
    body = _signup_and_login(auth_client)
    slug = body["memberships"][0]["workspace_slug"]

    resp = auth_client.get(f"/api/v1/workspaces/{slug}/members")
    assert resp.status_code == 200, resp.text
    payload = resp.json()
    assert payload["total"] == 1
    assert payload["items"][0]["role"] == "owner"
    assert payload["items"][0]["user"]["email"] == "alice@example.com"


def test_remove_self_returns_409(auth_client: TestClient) -> None:
    body = _signup_and_login(auth_client)
    slug = body["memberships"][0]["workspace_slug"]
    user_id = body["user"]["id"]

    resp = auth_client.delete(f"/api/v1/workspaces/{slug}/members/{user_id}")
    assert resp.status_code == 409


def test_remove_unknown_member_returns_404(auth_client: TestClient) -> None:
    body = _signup_and_login(auth_client)
    slug = body["memberships"][0]["workspace_slug"]

    # A well-formed UUID that is not a member.
    resp = auth_client.delete(
        f"/api/v1/workspaces/{slug}/members/00000000-0000-0000-0000-000000000001",
    )
    assert resp.status_code == 404


def test_remove_member_with_garbage_id_returns_404(
    auth_client: TestClient,
) -> None:
    body = _signup_and_login(auth_client)
    slug = body["memberships"][0]["workspace_slug"]

    resp = auth_client.delete(f"/api/v1/workspaces/{slug}/members/not-a-uuid")
    assert resp.status_code == 404
