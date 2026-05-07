"""``PATCH /api/v1/users/me`` preference tests (PR 4.1).

Covers theme persistence: happy path for each enum value, the
401 path for anonymous callers, the 422 path for an invalid value,
and the no-op path with an empty body. ``GET /api/v1/auth/me`` is
asserted to surface the new ``theme_preference`` field so the
client-side reconcile loop in ``static/js/theme.js`` has something
to read.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

VALID_PASSWORD = "correct horse battery staple"


def _signup_and_login(
    client: TestClient,
    email: str = "themer@example.com",
) -> None:
    resp = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": VALID_PASSWORD},
    )
    assert resp.status_code == 201
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": VALID_PASSWORD},
    )
    assert resp.status_code == 200


def test_default_theme_is_system(auth_client: TestClient) -> None:
    _signup_and_login(auth_client)
    resp = auth_client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    assert resp.json()["user"]["theme_preference"] == "system"


@pytest.mark.parametrize("value", ["light", "dark", "system"])
def test_patch_me_sets_theme_preference(
    auth_client: TestClient,
    value: str,
) -> None:
    _signup_and_login(auth_client)
    resp = auth_client.patch(
        "/api/v1/users/me",
        json={"theme_preference": value},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["theme_preference"] == value
    # Round-trip via /auth/me to prove the change persisted.
    me = auth_client.get("/api/v1/auth/me")
    assert me.json()["user"]["theme_preference"] == value


def test_patch_me_requires_authentication(auth_client: TestClient) -> None:
    resp = auth_client.patch(
        "/api/v1/users/me",
        json={"theme_preference": "dark"},
    )
    assert resp.status_code == 401


def test_patch_me_rejects_invalid_theme_value(
    auth_client: TestClient,
) -> None:
    _signup_and_login(auth_client)
    resp = auth_client.patch(
        "/api/v1/users/me",
        json={"theme_preference": "neon"},
    )
    assert resp.status_code == 422


def test_patch_me_rejects_unknown_field(auth_client: TestClient) -> None:
    _signup_and_login(auth_client)
    resp = auth_client.patch(
        "/api/v1/users/me",
        json={"locale": "en-US"},
    )
    assert resp.status_code == 422


def test_patch_me_empty_body_is_noop(auth_client: TestClient) -> None:
    _signup_and_login(auth_client)
    resp = auth_client.patch("/api/v1/users/me", json={})
    assert resp.status_code == 200
    assert resp.json()["theme_preference"] == "system"
