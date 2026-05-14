"""Smoke tests for the workspace dashboard page route."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from feedback_triage.services import dashboard_aggregator

VALID_PASSWORD = "correct horse battery staple"  # pragma: allowlist secret


@pytest.fixture(autouse=True)
def _reset_dashboard_cache() -> Iterator[None]:
    dashboard_aggregator.reset_cache()
    yield
    dashboard_aggregator.reset_cache()


def _signup_and_login(client: TestClient, email: str) -> dict[str, object]:
    client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": VALID_PASSWORD},
    )
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": VALID_PASSWORD},
    )
    assert resp.status_code == 200
    return resp.json()


def test_dashboard_renders_empty_state_for_new_workspace(
    auth_client: TestClient,
) -> None:
    body = _signup_and_login(auth_client, "owner@example.com")
    slug = body["memberships"][0]["workspace_slug"]

    resp = auth_client.get(f"/w/{slug}/dashboard")
    assert resp.status_code == 200, resp.text
    assert "no feedback yet" in resp.text.lower()
    assert slug in resp.text


def test_dashboard_renders_populated_view_when_items_exist(
    auth_client: TestClient,
) -> None:
    body = _signup_and_login(auth_client, "owner@example.com")
    slug = body["memberships"][0]["workspace_slug"]

    create = auth_client.post(
        "/api/v1/feedback",
        json={
            "title": "Logging stalls in safari",
            "description": "long body",
            "source": "email",
            "pain_level": 4,
        },
        headers={"X-Workspace-Slug": slug},
    )
    assert create.status_code == 201, create.text

    resp = auth_client.get(f"/w/{slug}/dashboard")
    assert resp.status_code == 200, resp.text
    body_text = resp.text
    # Summary cards plus main dashboard sections appear.
    assert "Total signals" in body_text
    assert "Needs action" in body_text
    assert "High pain signals" in body_text
    assert "Median time to triage" in body_text
    assert "Net backlog change" in body_text
    assert "Signals over time" in body_text
    assert "Status mix" in body_text
    assert "Aging / SLA" in body_text
    assert "Backlog / Needs attention" in body_text
    assert "Action queue" in body_text
    assert "Top tags" in body_text
    assert "Pain distribution" in body_text
    assert "Segment impact" in body_text
    assert "Team workload" in body_text
    assert "Source breakdown" in body_text
    assert "Edit widgets" in body_text
    assert "Edit widgets in React" not in body_text
    assert "data-react-editor-url" not in body_text
    assert "data-dashboard-edit-toggle" in body_text
    assert "Reset layout" in body_text
    assert "data-dashboard-canvas" in body_text
    assert 'data-widget-id="signals-over-time"' in body_text
    assert 'data-widget-id="action-queue"' in body_text
    assert "Logging stalls in safari" in body_text


def test_dashboard_anonymous_returns_401(auth_client: TestClient) -> None:
    # No login → ``current_user_required`` → 401.
    resp = auth_client.get("/w/whatever/dashboard")
    assert resp.status_code == 401


def test_dashboard_cross_tenant_returns_404(auth_client: TestClient) -> None:
    """Authenticated, but slug belongs to a different tenant → 404."""
    _signup_and_login(auth_client, "owner@example.com")

    resp = auth_client.get("/w/some-other-slug/dashboard")
    assert resp.status_code == 404
    assert "Not found." in resp.text


def test_dashboard_react_widgets_page_renders_for_member(
    auth_client: TestClient,
) -> None:
    body = _signup_and_login(auth_client, "owner@example.com")
    slug = body["memberships"][0]["workspace_slug"]

    resp = auth_client.get(f"/w/{slug}/dashboard/react")
    assert resp.status_code == 200, resp.text
    assert "React widgets pilot" in resp.text
    assert 'id="sn-react-widget-root"' in resp.text
    assert "/static/js/dashboard_react_widgets.js" in resp.text


def test_dashboard_react_widgets_page_anonymous_returns_401(
    auth_client: TestClient,
) -> None:
    resp = auth_client.get("/w/whatever/dashboard/react")
    assert resp.status_code == 401


def test_dashboard_react_widgets_page_cross_tenant_returns_404(
    auth_client: TestClient,
) -> None:
    _signup_and_login(auth_client, "owner@example.com")

    resp = auth_client.get("/w/some-other-slug/dashboard/react")
    assert resp.status_code == 404
    assert "Not found." in resp.text
