"""API tests for ``/api/v1/feedback`` (spec — API Tests [Must])."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient


def _valid_payload(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "title": "Login is slow",
        "description": "Takes 8 seconds on cold start.",
        "source": "email",
        "pain_level": 3,
    }
    base.update(overrides)
    return base


# --- Create ---------------------------------------------------------------


def test_create_returns_201_and_location_header(client: TestClient) -> None:
    resp = client.post("/api/v1/feedback", json=_valid_payload())
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] >= 1
    assert resp.headers["Location"] == f"/api/v1/feedback/{body['id']}"
    assert body["status"] == "new"
    assert body["created_at"].endswith("Z")


def test_create_invalid_pain_level_returns_422(client: TestClient) -> None:
    for bad in (0, 6, -1, 100):
        resp = client.post("/api/v1/feedback", json=_valid_payload(pain_level=bad))
        assert resp.status_code == 422, bad


def test_create_missing_title_returns_422(client: TestClient) -> None:
    payload = _valid_payload()
    payload.pop("title")
    resp = client.post("/api/v1/feedback", json=payload)
    assert resp.status_code == 422


def test_create_whitespace_only_title_returns_422(client: TestClient) -> None:
    resp = client.post("/api/v1/feedback", json=_valid_payload(title="   "))
    assert resp.status_code == 422


def test_create_oversized_description_returns_422(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/feedback",
        json=_valid_payload(description="x" * 5001),
    )
    assert resp.status_code == 422


def test_create_invalid_source_returns_422(client: TestClient) -> None:
    resp = client.post("/api/v1/feedback", json=_valid_payload(source="carrier-pigeon"))
    assert resp.status_code == 422


# --- List -----------------------------------------------------------------


def test_list_returns_envelope_shape(client: TestClient) -> None:
    for i in range(3):
        client.post(
            "/api/v1/feedback", json=_valid_payload(title=f"item {i}", pain_level=i + 1)
        )
    resp = client.get("/api/v1/feedback")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"items", "total", "skip", "limit"}
    assert body["total"] == 3
    assert body["skip"] == 0
    assert isinstance(body["items"], list)
    assert len(body["items"]) == 3


def test_list_skip_and_limit_returns_expected_slice(client: TestClient) -> None:
    for i in range(5):
        client.post("/api/v1/feedback", json=_valid_payload(title=f"item {i}"))
    resp = client.get("/api/v1/feedback?skip=2&limit=2")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 5
    assert body["skip"] == 2
    assert body["limit"] == 2
    assert len(body["items"]) == 2


def test_list_invalid_sort_by_returns_422(client: TestClient) -> None:
    resp = client.get("/api/v1/feedback?sort_by=evil")
    assert resp.status_code == 422


def test_list_filter_by_status_and_source(client: TestClient) -> None:
    client.post("/api/v1/feedback", json=_valid_payload(source="email"))
    client.post("/api/v1/feedback", json=_valid_payload(source="reddit"))
    client.post(
        "/api/v1/feedback", json=_valid_payload(source="reddit", status="planned")
    )

    resp = client.get("/api/v1/feedback?source=reddit")
    assert resp.json()["total"] == 2

    resp = client.get("/api/v1/feedback?status=planned")
    assert resp.json()["total"] == 1

    resp = client.get("/api/v1/feedback?status=planned&source=reddit")
    assert resp.json()["total"] == 1


# --- Get one --------------------------------------------------------------


def test_get_one_existing_returns_200(client: TestClient) -> None:
    created = client.post("/api/v1/feedback", json=_valid_payload()).json()
    resp = client.get(f"/api/v1/feedback/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_get_nonexistent_returns_404(client: TestClient) -> None:
    resp = client.get("/api/v1/feedback/99999")
    assert resp.status_code == 404
    body = resp.json()
    assert body["detail"] == "Feedback item not found"
    assert body["request_id"] == resp.headers["X-Request-ID"]


# --- Patch ----------------------------------------------------------------


def test_patch_single_field_returns_200_and_bumps_updated_at(
    client: TestClient,
) -> None:
    created = client.post("/api/v1/feedback", json=_valid_payload()).json()
    resp = client.patch(
        f"/api/v1/feedback/{created['id']}", json={"status": "reviewing"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "reviewing"
    assert body["updated_at"] >= created["updated_at"]


def test_patch_empty_body_bumps_updated_at(client: TestClient) -> None:
    created = client.post("/api/v1/feedback", json=_valid_payload()).json()
    resp = client.patch(f"/api/v1/feedback/{created['id']}", json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == created["title"]
    assert body["updated_at"] >= created["updated_at"]


def test_patch_then_get_returns_fresh_state(client: TestClient) -> None:
    """Canary for the session-reuse / stale-read bug.

    PATCH in one request, GET in the next. If a session ever leaks
    across requests with ``expire_on_commit=False``, the GET sees stale
    state and this test fails. See spec — Database session lifecycle.
    """
    created = client.post("/api/v1/feedback", json=_valid_payload()).json()
    item_id = created["id"]
    patched = client.patch(
        f"/api/v1/feedback/{item_id}",
        json={"status": "planned", "pain_level": 5},
    ).json()
    fetched = client.get(f"/api/v1/feedback/{item_id}").json()
    assert fetched["status"] == "planned"
    assert fetched["pain_level"] == 5
    assert fetched["updated_at"] == patched["updated_at"]


# --- Delete ---------------------------------------------------------------


def test_delete_returns_204(client: TestClient) -> None:
    created = client.post("/api/v1/feedback", json=_valid_payload()).json()
    resp = client.delete(f"/api/v1/feedback/{created['id']}")
    assert resp.status_code == 204
    assert resp.content == b""
    follow = client.get(f"/api/v1/feedback/{created['id']}")
    assert follow.status_code == 404


def test_delete_missing_returns_404(client: TestClient) -> None:
    resp = client.delete("/api/v1/feedback/99999")
    assert resp.status_code == 404
