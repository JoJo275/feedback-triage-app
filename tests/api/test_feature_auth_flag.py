"""``FEATURE_AUTH=false`` gate tests (PR 1.9).

Covers the production-rollout flag from
``docs/project/spec/v2/implementation.md`` — when ``FEATURE_AUTH`` is
false, ``/api/v1/auth/*`` short-circuits with ``503 Service
Unavailable`` and the auth page routes render a "coming soon"
notice instead of the live form. Routes outside the auth surface
keep working.

The settings object is read once at app construction (the flag is
not hot-reloaded), so each test builds its own ``TestClient`` from
``create_app(settings)`` rather than reusing the shared
``auth_client`` fixture.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from feedback_triage.config import Settings
from feedback_triage.main import create_app


@pytest.fixture
def disabled_client() -> TestClient:
    settings = Settings(_env_file=None, feature_auth=False)  # type: ignore[call-arg]
    app = create_app(settings)
    return TestClient(app)


@pytest.fixture
def enabled_client() -> TestClient:
    settings = Settings(_env_file=None, feature_auth=True)  # type: ignore[call-arg]
    app = create_app(settings)
    return TestClient(app)


# ---------------------------------------------------------------------------
# API surface — gated 503


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", "/api/v1/auth/signup"),
        ("post", "/api/v1/auth/login"),
        ("post", "/api/v1/auth/logout"),
        ("post", "/api/v1/auth/forgot-password"),
        ("post", "/api/v1/auth/reset-password"),
        ("post", "/api/v1/auth/verify-email"),
        ("post", "/api/v1/auth/resend-verification"),
        ("get", "/api/v1/auth/me"),
    ],
)
def test_auth_api_returns_503_when_disabled(
    disabled_client: TestClient,
    method: str,
    path: str,
) -> None:
    resp = disabled_client.request(method, path, json={})
    assert resp.status_code == 503
    body = resp.json()
    assert "FEATURE_AUTH" in body["detail"]


def test_auth_api_short_circuits_before_validation(
    disabled_client: TestClient,
) -> None:
    """Empty body would normally 422; the gate returns 503 first."""
    resp = disabled_client.post("/api/v1/auth/signup", json={})
    assert resp.status_code == 503


# ---------------------------------------------------------------------------
# Page surface — coming-soon notice


@pytest.mark.parametrize(
    "path",
    [
        "/login",
        "/signup",
        "/forgot-password",
        "/reset-password",
        "/verify-email",
        "/invitations/some-token",
    ],
)
def test_auth_page_renders_coming_soon_when_disabled(
    disabled_client: TestClient,
    path: str,
) -> None:
    resp = disabled_client.get(path)
    assert resp.status_code == 503
    assert "text/html" in resp.headers["content-type"]
    assert "Coming soon" in resp.text


# ---------------------------------------------------------------------------
# Non-auth surface keeps working


def test_health_route_unaffected_when_disabled(
    disabled_client: TestClient,
) -> None:
    resp = disabled_client.get("/health")
    assert resp.status_code == 200


def test_feedback_route_unaffected_when_disabled(
    disabled_client: TestClient,
) -> None:
    # The feedback list endpoint is unaffected by the gate; whether
    # it 200s on an empty DB or errors on a missing table is not the
    # subject of this test — just that it isn't intercepted with 503.
    resp = disabled_client.get("/api/v1/feedback")
    assert resp.status_code != 503


# ---------------------------------------------------------------------------
# Enabled flag preserves the live surface


def test_auth_pages_render_form_when_enabled(
    enabled_client: TestClient,
) -> None:
    resp = enabled_client.get("/login")
    assert resp.status_code == 200
    assert "Coming soon" not in resp.text
