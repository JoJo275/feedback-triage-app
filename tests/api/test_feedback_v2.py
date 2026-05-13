"""API flow tests for ``/api/v1/feedback`` on the v2 workspace-scoped contract.

Replaces the v1 anonymous suite that lived at ``tests/test_feedback_api.py``
before PR 2.2. Every request carries a session cookie + an
``X-Workspace-Slug`` header; the workspace is the one auto-created
by ``POST /api/v1/auth/signup``. The session-reuse canary
(``test_patch_then_get_returns_fresh_state``) is preserved.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

VALID_PASSWORD = "correct horse battery staple"  # pragma: allowlist secret


def _signup_and_login(client: TestClient, email: str) -> dict[str, Any]:
    """Sign up + log in. Return the login response body."""
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
    return login.json()


def _current_user_id(client: TestClient) -> str:
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 200, resp.text
    return str(resp.json()["user"]["id"])


@pytest.fixture
def workspace_slug(auth_client: TestClient) -> str:
    login = _signup_and_login(auth_client, "alice@example.com")
    return str(login["memberships"][0]["workspace_slug"])


@pytest.fixture
def headers(workspace_slug: str) -> dict[str, str]:
    return {"X-Workspace-Slug": workspace_slug}


def _valid_payload(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "title": "Login is slow",
        "description": "Takes 8 seconds on cold start.",
        "source": "email",
        "pain_level": 3,
    }
    base.update(overrides)
    return base


# --- Auth/tenant gating ---------------------------------------------------


def test_anonymous_request_returns_401(auth_client: TestClient) -> None:
    resp = auth_client.post("/api/v1/feedback", json=_valid_payload())
    assert resp.status_code == 401


def test_missing_workspace_header_returns_404(
    auth_client: TestClient, workspace_slug: str
) -> None:
    # Authenticated, but no slug in header or path → cross-tenant 404.
    resp = auth_client.post("/api/v1/feedback", json=_valid_payload())
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "not_found"


def test_unknown_workspace_slug_returns_404(auth_client: TestClient) -> None:
    _signup_and_login(auth_client, "bob@example.com")
    resp = auth_client.get(
        "/api/v1/feedback",
        headers={"X-Workspace-Slug": "no-such-workspace"},
    )
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "not_found"


# --- Create ---------------------------------------------------------------


def test_create_returns_201_and_location_header(
    auth_client: TestClient, headers: dict[str, str]
) -> None:
    resp = auth_client.post("/api/v1/feedback", json=_valid_payload(), headers=headers)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["id"] >= 1
    assert resp.headers["Location"] == f"/api/v1/feedback/{body['id']}"
    assert body["status"] == "new"
    assert body["type"] == "other"
    assert body["created_at"].endswith("Z")


def test_create_invalid_pain_level_returns_422(
    auth_client: TestClient, headers: dict[str, str]
) -> None:
    for bad in (0, 6, -1, 100):
        resp = auth_client.post(
            "/api/v1/feedback",
            json=_valid_payload(pain_level=bad),
            headers=headers,
        )
        assert resp.status_code == 422, bad


def test_create_missing_title_returns_422(
    auth_client: TestClient, headers: dict[str, str]
) -> None:
    payload = _valid_payload()
    payload.pop("title")
    resp = auth_client.post("/api/v1/feedback", json=payload, headers=headers)
    assert resp.status_code == 422


def test_create_whitespace_only_title_returns_422(
    auth_client: TestClient, headers: dict[str, str]
) -> None:
    resp = auth_client.post(
        "/api/v1/feedback",
        json=_valid_payload(title="   "),
        headers=headers,
    )
    assert resp.status_code == 422


def test_create_oversized_description_returns_422(
    auth_client: TestClient, headers: dict[str, str]
) -> None:
    resp = auth_client.post(
        "/api/v1/feedback",
        json=_valid_payload(description="x" * 5001),
        headers=headers,
    )
    assert resp.status_code == 422


def test_create_invalid_source_returns_422(
    auth_client: TestClient, headers: dict[str, str]
) -> None:
    resp = auth_client.post(
        "/api/v1/feedback",
        json=_valid_payload(source="carrier-pigeon"),
        headers=headers,
    )
    assert resp.status_code == 422


def test_create_rejected_status_returns_422(
    auth_client: TestClient, headers: dict[str, str]
) -> None:
    """``rejected`` is forbidden on writes (DB CHECK + early reject)."""
    resp = auth_client.post(
        "/api/v1/feedback",
        json=_valid_payload(status="rejected"),
        headers=headers,
    )
    assert resp.status_code == 422


def test_create_with_assignee_in_workspace_returns_201(
    auth_client: TestClient, headers: dict[str, str]
) -> None:
    assignee_user_id = _current_user_id(auth_client)
    resp = auth_client.post(
        "/api/v1/feedback",
        json=_valid_payload(assignee_user_id=assignee_user_id),
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["assignee_user_id"] == assignee_user_id


def test_create_assignee_outside_workspace_returns_422(auth_client: TestClient) -> None:
    owner_login = _signup_and_login(auth_client, "owner@example.com")
    owner_slug = str(owner_login["memberships"][0]["workspace_slug"])

    auth_client.cookies.clear()
    outsider_login = _signup_and_login(auth_client, "outsider@example.com")
    outsider_user_id = str(outsider_login["user"]["id"])

    auth_client.cookies.clear()
    _signup_and_login(auth_client, "owner@example.com")
    resp = auth_client.post(
        "/api/v1/feedback",
        json=_valid_payload(assignee_user_id=outsider_user_id),
        headers={"X-Workspace-Slug": owner_slug},
    )
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert detail[0]["loc"] == ["body", "assignee_user_id"]


# --- List -----------------------------------------------------------------


def test_list_returns_envelope_shape(
    auth_client: TestClient, headers: dict[str, str]
) -> None:
    for i in range(3):
        auth_client.post(
            "/api/v1/feedback",
            json=_valid_payload(title=f"item {i}", pain_level=i + 1),
            headers=headers,
        )
    resp = auth_client.get("/api/v1/feedback", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert set(body.keys()) == {"items", "total", "skip", "limit"}
    assert body["total"] == 3
    assert body["skip"] == 0
    assert isinstance(body["items"], list)
    assert len(body["items"]) == 3


def test_list_skip_and_limit_returns_expected_slice(
    auth_client: TestClient, headers: dict[str, str]
) -> None:
    for i in range(5):
        auth_client.post(
            "/api/v1/feedback",
            json=_valid_payload(title=f"item {i}"),
            headers=headers,
        )
    resp = auth_client.get("/api/v1/feedback?skip=2&limit=2", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 5
    assert body["skip"] == 2
    assert body["limit"] == 2
    assert len(body["items"]) == 2


def test_list_invalid_sort_by_returns_422(
    auth_client: TestClient, headers: dict[str, str]
) -> None:
    resp = auth_client.get("/api/v1/feedback?sort_by=evil", headers=headers)
    assert resp.status_code == 422


def test_list_filter_by_status_and_source(
    auth_client: TestClient, headers: dict[str, str]
) -> None:
    auth_client.post(
        "/api/v1/feedback",
        json=_valid_payload(source="email"),
        headers=headers,
    )
    auth_client.post(
        "/api/v1/feedback",
        json=_valid_payload(source="reddit"),
        headers=headers,
    )
    auth_client.post(
        "/api/v1/feedback",
        json=_valid_payload(source="reddit", status="planned"),
        headers=headers,
    )

    resp = auth_client.get("/api/v1/feedback?source=reddit", headers=headers)
    assert resp.json()["total"] == 2

    resp = auth_client.get("/api/v1/feedback?status=planned", headers=headers)
    assert resp.json()["total"] == 1

    resp = auth_client.get(
        "/api/v1/feedback?status=planned&source=reddit", headers=headers
    )
    assert resp.json()["total"] == 1


def test_list_q_searches_title_and_description(
    auth_client: TestClient, headers: dict[str, str]
) -> None:
    auth_client.post(
        "/api/v1/feedback",
        json=_valid_payload(title="Slow checkout", description="..."),
        headers=headers,
    )
    auth_client.post(
        "/api/v1/feedback",
        json=_valid_payload(title="Fast", description="checkout flows are nice"),
        headers=headers,
    )
    auth_client.post(
        "/api/v1/feedback",
        json=_valid_payload(title="Other", description="unrelated"),
        headers=headers,
    )
    resp = auth_client.get("/api/v1/feedback?q=checkout", headers=headers)
    assert resp.json()["total"] == 2


def test_list_filter_by_assignee_user_id(
    auth_client: TestClient, headers: dict[str, str]
) -> None:
    assignee_user_id = _current_user_id(auth_client)
    auth_client.post(
        "/api/v1/feedback",
        json=_valid_payload(title="assigned", assignee_user_id=assignee_user_id),
        headers=headers,
    )
    auth_client.post(
        "/api/v1/feedback",
        json=_valid_payload(title="unassigned"),
        headers=headers,
    )

    resp = auth_client.get(
        f"/api/v1/feedback?assignee_user_id={assignee_user_id}",
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "assigned"


# --- Get one --------------------------------------------------------------


def test_get_one_existing_returns_200(
    auth_client: TestClient, headers: dict[str, str]
) -> None:
    created = auth_client.post(
        "/api/v1/feedback", json=_valid_payload(), headers=headers
    ).json()
    resp = auth_client.get(f"/api/v1/feedback/{created['id']}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_get_nonexistent_returns_404(
    auth_client: TestClient, headers: dict[str, str]
) -> None:
    resp = auth_client.get("/api/v1/feedback/99999", headers=headers)
    assert resp.status_code == 404


# --- Patch ----------------------------------------------------------------


def test_patch_single_field_returns_200_and_bumps_updated_at(
    auth_client: TestClient, headers: dict[str, str]
) -> None:
    created = auth_client.post(
        "/api/v1/feedback", json=_valid_payload(), headers=headers
    ).json()
    resp = auth_client.patch(
        f"/api/v1/feedback/{created['id']}",
        json={"status": "reviewing"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "reviewing"
    assert body["updated_at"] >= created["updated_at"]


def test_patch_empty_body_bumps_updated_at(
    auth_client: TestClient, headers: dict[str, str]
) -> None:
    created = auth_client.post(
        "/api/v1/feedback", json=_valid_payload(), headers=headers
    ).json()
    resp = auth_client.patch(
        f"/api/v1/feedback/{created['id']}", json={}, headers=headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == created["title"]
    assert body["updated_at"] >= created["updated_at"]


def test_patch_then_get_returns_fresh_state(
    auth_client: TestClient, headers: dict[str, str]
) -> None:
    """Canary for the session-reuse / stale-read bug.

    PATCH in one request, GET in the next. If a session ever leaks
    across requests with ``expire_on_commit=False``, the GET sees stale
    state and this test fails.
    """
    created = auth_client.post(
        "/api/v1/feedback", json=_valid_payload(), headers=headers
    ).json()
    item_id = created["id"]
    patched = auth_client.patch(
        f"/api/v1/feedback/{item_id}",
        json={"status": "planned", "pain_level": 5},
        headers=headers,
    ).json()
    fetched = auth_client.get(f"/api/v1/feedback/{item_id}", headers=headers).json()
    assert fetched["status"] == "planned"
    assert fetched["pain_level"] == 5
    assert fetched["updated_at"] == patched["updated_at"]


def test_patch_v2_fields(auth_client: TestClient, headers: dict[str, str]) -> None:
    created = auth_client.post(
        "/api/v1/feedback", json=_valid_payload(), headers=headers
    ).json()
    resp = auth_client.patch(
        f"/api/v1/feedback/{created['id']}",
        json={
            "type": "bug",
            "priority": "high",
            "published_to_roadmap": True,
            "release_note": "Fixed cold-start latency.",
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["type"] == "bug"
    assert body["priority"] == "high"
    assert body["published_to_roadmap"] is True
    assert body["release_note"] == "Fixed cold-start latency."


def test_patch_assignee_and_clear_assignee(
    auth_client: TestClient, headers: dict[str, str]
) -> None:
    assignee_user_id = _current_user_id(auth_client)
    created = auth_client.post(
        "/api/v1/feedback", json=_valid_payload(), headers=headers
    ).json()

    assign = auth_client.patch(
        f"/api/v1/feedback/{created['id']}",
        json={"assignee_user_id": assignee_user_id},
        headers=headers,
    )
    assert assign.status_code == 200, assign.text
    assert assign.json()["assignee_user_id"] == assignee_user_id

    clear = auth_client.patch(
        f"/api/v1/feedback/{created['id']}",
        json={"assignee_user_id": None},
        headers=headers,
    )
    assert clear.status_code == 200, clear.text
    assert clear.json()["assignee_user_id"] is None


# --- Delete ---------------------------------------------------------------


def test_delete_returns_204(auth_client: TestClient, headers: dict[str, str]) -> None:
    created = auth_client.post(
        "/api/v1/feedback", json=_valid_payload(), headers=headers
    ).json()
    resp = auth_client.delete(f"/api/v1/feedback/{created['id']}", headers=headers)
    assert resp.status_code == 204
    assert resp.content == b""
    follow = auth_client.get(f"/api/v1/feedback/{created['id']}", headers=headers)
    assert follow.status_code == 404


def test_delete_missing_returns_404(
    auth_client: TestClient, headers: dict[str, str]
) -> None:
    resp = auth_client.delete("/api/v1/feedback/99999", headers=headers)
    assert resp.status_code == 404
