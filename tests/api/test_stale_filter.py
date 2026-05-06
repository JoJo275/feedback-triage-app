"""Tests for the ``stale=true`` filter on ``GET /api/v1/feedback`` (PR 2.6).

Stale = ``created_at < now() - 14 days AND status IN ('new', 'needs_info')``
(see ``services/stale_detector.py`` and ``docs/project/spec/v2/glossary.md``).

The filter is the source of truth for the *Stale* summary card on the
Inbox; the JS row badge mirrors the same predicate client-side. These
tests pin both the SQL clause and the API surface.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from feedback_triage.database import engine

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
    return login.json()["memberships"][0]["workspace_slug"]


@pytest.fixture
def workspace_slug(auth_client: TestClient) -> str:
    return _signup_and_login(auth_client, "alice@example.com")


@pytest.fixture
def headers(workspace_slug: str) -> dict[str, str]:
    return {"X-Workspace-Slug": workspace_slug}


def _payload(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "title": "Subject",
        "description": "Body.",
        "source": "email",
        "pain_level": 2,
    }
    base.update(overrides)
    return base


@pytest.fixture
def freeze_created_at() -> Iterator[None]:
    """No-op fixture; we manipulate ``created_at`` directly via SQL."""
    yield


def _set_created_at(item_id: int, days_ago: int) -> None:
    cutoff = datetime.now(UTC) - timedelta(days=days_ago)
    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE feedback_item SET created_at = :ts WHERE id = :id",
            ),
            {"ts": cutoff, "id": item_id},
        )


def test_stale_filter_returns_only_old_items_in_stale_statuses(
    auth_client: TestClient,
    headers: dict[str, str],
) -> None:
    # Three items, three different ages/statuses.
    fresh = auth_client.post(
        "/api/v1/feedback", json=_payload(title="fresh new"), headers=headers
    ).json()
    old_new = auth_client.post(
        "/api/v1/feedback", json=_payload(title="old new"), headers=headers
    ).json()
    old_reviewing = auth_client.post(
        "/api/v1/feedback",
        json=_payload(title="old reviewing", status="reviewing"),
        headers=headers,
    ).json()

    # Backdate two of the three. Only ``old_new`` should match the
    # stale predicate; ``old_reviewing`` is old enough but its status
    # excludes it.
    _set_created_at(old_new["id"], days_ago=20)
    _set_created_at(old_reviewing["id"], days_ago=20)

    resp = auth_client.get("/api/v1/feedback?stale=true", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == old_new["id"]

    # Sanity: stale=false is the complement of stale=true relative to
    # the workspace.
    resp = auth_client.get("/api/v1/feedback?stale=false", headers=headers)
    assert resp.status_code == 200
    ids = {item["id"] for item in resp.json()["items"]}
    assert ids == {fresh["id"], old_reviewing["id"]}


def test_stale_filter_includes_needs_info(
    auth_client: TestClient,
    headers: dict[str, str],
) -> None:
    item = auth_client.post(
        "/api/v1/feedback",
        json=_payload(title="needs info, old", status="needs_info"),
        headers=headers,
    ).json()
    _set_created_at(item["id"], days_ago=15)

    resp = auth_client.get("/api/v1/feedback?stale=true", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
