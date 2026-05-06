"""API flow tests for ``/api/v1/submitters`` (PR 2.2).

PR 2.2 only ships the read + edit-metadata surface for submitters;
the auto-create path lands in PR 2.4 (``services/submitter_link``).
We seed submitter rows directly via SQL so this slice stays
hermetic.
"""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from sqlalchemy import text

from feedback_triage.database import engine

VALID_PASSWORD = "correct horse battery staple"  # pragma: allowlist secret


def _signup(client: TestClient, email: str) -> tuple[str, uuid.UUID]:
    client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": VALID_PASSWORD},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": VALID_PASSWORD},
    )
    body = login.json()
    workspace_id = uuid.UUID(body["memberships"][0]["workspace_id"])
    return body["memberships"][0]["workspace_slug"], workspace_id


def _seed_submitter(
    workspace_id: uuid.UUID, email: str | None, name: str = "Person"
) -> uuid.UUID:
    submitter_id = uuid.uuid4()
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO submitters "
                "(id, workspace_id, email, name, submission_count) "
                "VALUES (:id, :ws, :email, :name, 1)"
            ),
            {
                "id": submitter_id,
                "ws": workspace_id,
                "email": email,
                "name": name,
            },
        )
    return submitter_id


def test_list_submitters_envelope(auth_client: TestClient) -> None:
    slug, ws_id = _signup(auth_client, "alice@example.com")
    _seed_submitter(ws_id, "casey@example.com", "Casey Customer")
    resp = auth_client.get("/api/v1/submitters", headers={"X-Workspace-Slug": slug})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert set(body.keys()) == {"items", "total", "skip", "limit"}
    assert body["total"] == 1
    assert body["items"][0]["email"] == "casey@example.com"


def test_list_submitters_q_filter(auth_client: TestClient) -> None:
    slug, ws_id = _signup(auth_client, "alice@example.com")
    _seed_submitter(ws_id, "casey@example.com", "Casey Customer")
    _seed_submitter(ws_id, "dale@example.com", "Dale Different")
    headers = {"X-Workspace-Slug": slug}
    resp = auth_client.get("/api/v1/submitters?q=casey", headers=headers)
    assert resp.json()["total"] == 1


def test_get_submitter(auth_client: TestClient) -> None:
    slug, ws_id = _signup(auth_client, "alice@example.com")
    sid = _seed_submitter(ws_id, "casey@example.com", "Casey Customer")
    resp = auth_client.get(
        f"/api/v1/submitters/{sid}",
        headers={"X-Workspace-Slug": slug},
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == str(sid)


def test_patch_submitter_name(auth_client: TestClient) -> None:
    slug, ws_id = _signup(auth_client, "alice@example.com")
    sid = _seed_submitter(ws_id, "casey@example.com", "Casey Customer")
    resp = auth_client.patch(
        f"/api/v1/submitters/{sid}",
        json={"name": "Casey Renamed"},
        headers={"X-Workspace-Slug": slug},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Casey Renamed"


def test_cross_tenant_submitter_returns_404(auth_client: TestClient) -> None:
    _slug_a, ws_a = _signup(auth_client, "alice@example.com")
    sid = _seed_submitter(ws_a, "casey@example.com", "Casey Customer")
    auth_client.post("/api/v1/auth/logout")
    slug_b, _ = _signup(auth_client, "bob@example.com")
    resp = auth_client.get(
        f"/api/v1/submitters/{sid}",
        headers={"X-Workspace-Slug": slug_b},
    )
    assert resp.status_code == 404
