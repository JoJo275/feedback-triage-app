"""API flow tests for ``/api/v1/feedback/{id}/notes`` (PR 2.2)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import text

from feedback_triage.database import engine

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


def _new_feedback(client: TestClient, headers: dict[str, str]) -> dict[str, Any]:
    return client.post(
        "/api/v1/feedback",
        json={
            "title": "Login is slow",
            "source": "email",
            "pain_level": 3,
        },
        headers=headers,
    ).json()


def test_create_and_list_notes(auth_client: TestClient) -> None:
    slug = _signup(auth_client, "alice@example.com")
    headers = {"X-Workspace-Slug": slug}
    item = _new_feedback(auth_client, headers)

    resp = auth_client.post(
        f"/api/v1/feedback/{item['id']}/notes",
        json={"body": "First triage note."},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    note = resp.json()
    assert note["body"] == "First triage note."

    listing = auth_client.get(f"/api/v1/feedback/{item['id']}/notes", headers=headers)
    assert listing.status_code == 200
    body = listing.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == note["id"]


def test_create_note_oversize_returns_422(auth_client: TestClient) -> None:
    slug = _signup(auth_client, "alice@example.com")
    headers = {"X-Workspace-Slug": slug}
    item = _new_feedback(auth_client, headers)
    resp = auth_client.post(
        f"/api/v1/feedback/{item['id']}/notes",
        json={"body": "x" * 4001},
        headers=headers,
    )
    assert resp.status_code == 422


def test_patch_note_within_window(auth_client: TestClient) -> None:
    slug = _signup(auth_client, "alice@example.com")
    headers = {"X-Workspace-Slug": slug}
    item = _new_feedback(auth_client, headers)
    note = auth_client.post(
        f"/api/v1/feedback/{item['id']}/notes",
        json={"body": "first"},
        headers=headers,
    ).json()
    resp = auth_client.patch(
        f"/api/v1/feedback/{item['id']}/notes/{note['id']}",
        json={"body": "edited"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["body"] == "edited"


def test_patch_note_after_window_returns_409(auth_client: TestClient) -> None:
    slug = _signup(auth_client, "alice@example.com")
    headers = {"X-Workspace-Slug": slug}
    item = _new_feedback(auth_client, headers)
    note = auth_client.post(
        f"/api/v1/feedback/{item['id']}/notes",
        json={"body": "first"},
        headers=headers,
    ).json()
    # Backdate created_at past the 15-minute window.
    past = datetime.now(tz=UTC) - timedelta(minutes=20)
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE feedback_notes SET created_at = :ts WHERE id = :id"),
            {"ts": past, "id": note["id"]},
        )
    resp = auth_client.patch(
        f"/api/v1/feedback/{item['id']}/notes/{note['id']}",
        json={"body": "edited late"},
        headers=headers,
    )
    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "edit_window_closed"


def test_delete_note_by_author(auth_client: TestClient) -> None:
    slug = _signup(auth_client, "alice@example.com")
    headers = {"X-Workspace-Slug": slug}
    item = _new_feedback(auth_client, headers)
    note = auth_client.post(
        f"/api/v1/feedback/{item['id']}/notes",
        json={"body": "ephemeral"},
        headers=headers,
    ).json()
    resp = auth_client.delete(
        f"/api/v1/feedback/{item['id']}/notes/{note['id']}",
        headers=headers,
    )
    assert resp.status_code == 204
