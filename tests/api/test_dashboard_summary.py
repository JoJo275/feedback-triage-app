"""Dashboard summary aggregator tests (PR 3.4).

Pins the per-workspace TTL cache contract from
``docs/project/spec/v2/performance-budgets.md`` -- *Dashboard cache*:

* a fresh workspace misses the cache and triggers DB work,
* a second call inside the TTL returns the same object (cache hit),
* expiring the cache forces a re-read with current data,
* the cache key is workspace-scoped (one workspace's writes do not
  shadow another's summary).
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from feedback_triage.database import SessionLocal
from feedback_triage.enums import Status, WorkspaceRole
from feedback_triage.services import dashboard_aggregator

VALID_PASSWORD = "correct horse battery staple"  # pragma: allowlist secret


def _signup_and_login(client: TestClient, email: str) -> dict[str, Any]:
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


def _workspace_id(membership: dict[str, Any]) -> uuid.UUID:
    return uuid.UUID(membership["workspace_id"])


def _post_feedback(
    client: TestClient,
    slug: str,
    title: str,
    *,
    source: str = "email",
    pain_level: int = 3,
    assignee_user_id: str | None = None,
) -> dict[str, Any]:
    resp = client.post(
        "/api/v1/feedback",
        json={
            "title": title,
            "description": "body",
            "source": source,
            "pain_level": pain_level,
            "assignee_user_id": assignee_user_id,
        },
        headers={"X-Workspace-Slug": slug},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _patch_feedback(
    client: TestClient,
    slug: str,
    item_id: int,
    payload: dict[str, object],
) -> dict[str, Any]:
    resp = client.patch(
        f"/api/v1/feedback/{item_id}",
        json=payload,
        headers={"X-Workspace-Slug": slug},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest.fixture(autouse=True)
def _reset_dashboard_cache() -> Iterator[None]:
    dashboard_aggregator.reset_cache()
    yield
    dashboard_aggregator.reset_cache()


def test_summary_cache_hit_returns_same_object(
    auth_client: TestClient,
    truncate_auth_world: None,
) -> None:
    body = _signup_and_login(auth_client, "owner@example.com")
    workspace_id = _workspace_id(body["memberships"][0])

    with SessionLocal() as db:
        first = dashboard_aggregator.get_summary(
            db,
            workspace_id=workspace_id,
            role=WorkspaceRole.OWNER,
        )
        second = dashboard_aggregator.get_summary(
            db,
            workspace_id=workspace_id,
            role=WorkspaceRole.OWNER,
        )

    # Same identity proves the cached object was returned, not just an
    # equal-valued recomputation.
    assert first is second


def test_summary_cache_miss_after_ttl_expires(
    auth_client: TestClient,
    truncate_auth_world: None,
) -> None:
    body = _signup_and_login(auth_client, "owner@example.com")
    slug = body["memberships"][0]["workspace_slug"]
    workspace_id = _workspace_id(body["memberships"][0])

    with SessionLocal() as db:
        first = dashboard_aggregator.get_summary(
            db,
            workspace_id=workspace_id,
            role=WorkspaceRole.OWNER,
        )
        # Add work; cache still serves the stale value because writes
        # do not bust it (the documented trade-off).
        _post_feedback(auth_client, slug, "fresh item")
        cached = dashboard_aggregator.get_summary(
            db,
            workspace_id=workspace_id,
            role=WorkspaceRole.OWNER,
        )
        assert cached is first

        # Simulate TTL expiry (``cachetools.TTLCache`` evicts on read
        # once ``timer() - inserted_at > ttl``). ``reset_cache`` is the
        # production-safe knob the service exposes for exactly this.
        dashboard_aggregator.reset_cache()
        refreshed = dashboard_aggregator.get_summary(
            db,
            workspace_id=workspace_id,
            role=WorkspaceRole.OWNER,
        )

    assert refreshed is not first
    assert refreshed.total_items == first.total_items + 1


def test_summary_cache_is_per_workspace(
    auth_client: TestClient,
    truncate_auth_world: None,
) -> None:
    """Two workspaces never share a cache entry (canary against leak)."""
    first_body = _signup_and_login(auth_client, "alice@example.com")
    auth_client.cookies.clear()
    second_body = _signup_and_login(auth_client, "bob@example.com")

    alice_id = _workspace_id(first_body["memberships"][0])
    bob_id = _workspace_id(second_body["memberships"][0])
    alice_slug = first_body["memberships"][0]["workspace_slug"]

    # Bob is logged in; create one item in Bob's workspace.
    _post_feedback(
        auth_client, second_body["memberships"][0]["workspace_slug"], "bob 1"
    )

    # Switch back to Alice and add two items in Alice's workspace.
    auth_client.cookies.clear()
    _signup_and_login(auth_client, "alice@example.com")
    _post_feedback(auth_client, alice_slug, "alice 1")
    _post_feedback(auth_client, alice_slug, "alice 2")

    with SessionLocal() as db:
        alice_summary = dashboard_aggregator.get_summary(
            db,
            workspace_id=alice_id,
            role=WorkspaceRole.OWNER,
        )
        bob_summary = dashboard_aggregator.get_summary(
            db,
            workspace_id=bob_id,
            role=WorkspaceRole.OWNER,
        )

    assert alice_summary.total_items == 2
    assert bob_summary.total_items == 1
    # And neither summary is the other (no key collision).
    assert alice_summary is not bob_summary


def test_summary_includes_source_breakdown(
    auth_client: TestClient,
    truncate_auth_world: None,
) -> None:
    body = _signup_and_login(auth_client, "owner@example.com")
    slug = body["memberships"][0]["workspace_slug"]
    workspace_id = _workspace_id(body["memberships"][0])

    _post_feedback(auth_client, slug, "email one", source="email")
    _post_feedback(auth_client, slug, "email two", source="email")
    _post_feedback(auth_client, slug, "support one", source="support")

    with SessionLocal() as db:
        summary = dashboard_aggregator.get_summary(
            db,
            workspace_id=workspace_id,
            role=WorkspaceRole.OWNER,
        )

    breakdown = {item.source: item for item in summary.source_breakdown}
    assert breakdown["email"].count == 2
    assert breakdown["support"].count == 1
    assert breakdown["email"].percent == 67
    assert breakdown["support"].percent == 33


def test_summary_exposes_kpis_and_urgency_queue(
    auth_client: TestClient,
    truncate_auth_world: None,
) -> None:
    body = _signup_and_login(auth_client, "owner@example.com")
    slug = body["memberships"][0]["workspace_slug"]
    workspace_id = _workspace_id(body["memberships"][0])

    low = _post_feedback(auth_client, slug, "low pain item", pain_level=2)
    _patch_feedback(
        auth_client,
        slug,
        int(low["id"]),
        {"status": Status.REVIEWING.value},
    )
    _post_feedback(auth_client, slug, "high pain item", pain_level=5)

    with SessionLocal() as db:
        summary = dashboard_aggregator.get_summary(
            db,
            workspace_id=workspace_id,
            role=WorkspaceRole.OWNER,
        )

    assert summary.kpi.total_signals == 2
    assert summary.kpi.needs_action == 2
    assert summary.kpi.high_pain_signals == 1
    assert summary.action_queue.default_rows == dashboard_aggregator.ACTION_QUEUE_LIMIT
    assert summary.action_queue.urgency_rules[0] == "high_pain"
    assert summary.action_queue.entries[0].title == "high pain item"
    assert summary.action_queue.entries[0].is_high_pain is True
    assert summary.team_workload.unassigned_open == 2

    canonical = [slice_.status.value for slice_ in summary.status_mix]
    assert canonical == [
        "new",
        "needs_info",
        "reviewing",
        "accepted",
        "planned",
        "in_progress",
        "shipped",
        "closed",
        "spam",
    ]


def test_summary_team_workload_and_queue_use_assignee(
    auth_client: TestClient,
    truncate_auth_world: None,
) -> None:
    body = _signup_and_login(auth_client, "owner@example.com")
    slug = body["memberships"][0]["workspace_slug"]
    workspace_id = _workspace_id(body["memberships"][0])
    assignee_user_id = body["user"]["id"]
    assignee_email = body["user"]["email"]

    _post_feedback(
        auth_client,
        slug,
        "assigned high pain",
        pain_level=5,
        assignee_user_id=assignee_user_id,
    )
    _post_feedback(auth_client, slug, "unassigned item", pain_level=2)

    with SessionLocal() as db:
        summary = dashboard_aggregator.get_summary(
            db,
            workspace_id=workspace_id,
            role=WorkspaceRole.OWNER,
        )

    assigned_row = next(
        row for row in summary.team_workload.rows if row.owner == assignee_email
    )
    assert assigned_row.open_count == 1
    assert assigned_row.high_pain_count == 1
    assert summary.team_workload.unassigned_open == 1

    queue_by_title = {entry.title: entry for entry in summary.action_queue.entries}
    assert queue_by_title["assigned high pain"].owner == assignee_email
    assert queue_by_title["assigned high pain"].is_unassigned is False
    assert queue_by_title["unassigned item"].owner == "Unassigned"
    assert queue_by_title["unassigned item"].is_unassigned is True
