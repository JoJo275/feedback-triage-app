"""Smoke tests for the submitters list / detail pages (PR 2.6).

Pages are server-rendered shells; the UI hydration is covered in
e2e. Here we assert the shell loads for an authorized member, that
cross-tenant requests 404 (ADR 060), and that an unknown submitter
id 404s instead of leaking existence.
"""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from sqlalchemy import text

from feedback_triage.database import engine

VALID_PASSWORD = "correct horse battery staple"  # pragma: allowlist secret


def _signup_and_login(client: TestClient, email: str) -> dict[str, object]:
    client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": VALID_PASSWORD},
    )
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": VALID_PASSWORD},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _create_submitter(workspace_id: uuid.UUID, email: str) -> uuid.UUID:
    new_id = uuid.uuid4()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO submitters (id, workspace_id, email, name)
                VALUES (:id, :ws, :email, :name)
                """,
            ),
            {"id": new_id, "ws": workspace_id, "email": email, "name": "Test User"},
        )
    return new_id


def test_submitters_list_renders_for_member(auth_client: TestClient) -> None:
    body = _signup_and_login(auth_client, "owner@example.com")
    slug = body["memberships"][0]["workspace_slug"]

    resp = auth_client.get(f"/w/{slug}/submitters")
    assert resp.status_code == 200, resp.text
    assert "submitters" in resp.text.lower()
    assert "submitters.js" in resp.text


def test_submitters_list_anonymous_returns_401(auth_client: TestClient) -> None:
    resp = auth_client.get("/w/whatever/submitters")
    assert resp.status_code == 401


def test_submitters_list_cross_tenant_returns_404(auth_client: TestClient) -> None:
    _signup_and_login(auth_client, "owner@example.com")
    resp = auth_client.get("/w/some-other-slug/submitters")
    assert resp.status_code == 404


def test_submitter_detail_renders_for_owned_row(auth_client: TestClient) -> None:
    body = _signup_and_login(auth_client, "owner@example.com")
    slug = body["memberships"][0]["workspace_slug"]
    workspace_id = uuid.UUID(body["memberships"][0]["workspace_id"])
    submitter_id = _create_submitter(workspace_id, "user@example.com")

    resp = auth_client.get(f"/w/{slug}/submitters/{submitter_id}")
    assert resp.status_code == 200, resp.text
    assert "submitter_detail.js" in resp.text
    assert str(submitter_id) in resp.text


def test_submitter_detail_unknown_id_returns_404(auth_client: TestClient) -> None:
    body = _signup_and_login(auth_client, "owner@example.com")
    slug = body["memberships"][0]["workspace_slug"]

    resp = auth_client.get(f"/w/{slug}/submitters/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_submitter_detail_cross_tenant_returns_404(auth_client: TestClient) -> None:
    # Owner A creates a submitter; owner B tries to fetch it.
    body_a = _signup_and_login(auth_client, "owner-a@example.com")
    workspace_a_id = uuid.UUID(body_a["memberships"][0]["workspace_id"])
    submitter_id = _create_submitter(workspace_a_id, "shared@example.com")

    # Log out and into a second account.
    auth_client.post("/api/v1/auth/logout")
    body_b = _signup_and_login(auth_client, "owner-b@example.com")
    slug_b = body_b["memberships"][0]["workspace_slug"]

    resp = auth_client.get(f"/w/{slug_b}/submitters/{submitter_id}")
    assert resp.status_code == 404
