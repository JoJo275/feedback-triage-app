"""Phase 2 React authenticated page route tests.

Covers per-page feature flags on existing authenticated routes, legacy
fallback via ``?view=legacy``, and frontend telemetry ingestion.
"""

from __future__ import annotations

import json
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from feedback_triage.config import Settings
from feedback_triage.frontend_assets import REACT_MANIFEST, reset_manifest_cache
from feedback_triage.main import create_app

VALID_PASSWORD = "correct horse battery staple"  # pragma: allowlist secret


@pytest.fixture(autouse=True)
def _reset_manifest_cache() -> Iterator[None]:
    reset_manifest_cache()
    yield
    reset_manifest_cache()


def _signup_and_login(client: TestClient, email: str) -> dict[str, object]:
    signup = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": VALID_PASSWORD},
    )
    assert signup.status_code == 201, signup.text

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": VALID_PASSWORD},
    )
    assert login.status_code == 200, login.text
    return login.json()


def _write_manifest(payload: dict[str, object]) -> tuple[bool, str]:
    existed = REACT_MANIFEST.exists()
    previous = REACT_MANIFEST.read_text(encoding="utf-8") if existed else ""

    REACT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    REACT_MANIFEST.write_text(json.dumps(payload), encoding="utf-8")
    reset_manifest_cache()

    return existed, previous


def _restore_manifest(existed: bool, previous: str) -> None:
    if existed:
        REACT_MANIFEST.write_text(previous, encoding="utf-8")
    else:
        REACT_MANIFEST.unlink(missing_ok=True)
    reset_manifest_cache()


@pytest.mark.parametrize(
    ("flag_name", "route_template", "page_key", "active_section"),
    [
        ("feature_react_dashboard", "/w/{slug}/dashboard", "dashboard", "dashboard"),
        ("feature_react_inbox", "/w/{slug}/inbox", "inbox", "inbox"),
        ("feature_react_inbox", "/w/{slug}/feedback", "feedback", "feedback"),
        ("feature_react_roadmap", "/w/{slug}/roadmap", "roadmap", "roadmap"),
        (
            "feature_react_changelog",
            "/w/{slug}/changelog",
            "changelog",
            "changelog",
        ),
        (
            "feature_react_submitters",
            "/w/{slug}/submitters",
            "submitters",
            "submitters",
        ),
        ("feature_react_insights", "/w/{slug}/insights", "insights", "insights"),
        ("feature_react_settings", "/w/{slug}/settings", "settings", "settings"),
    ],
)
def test_authenticated_page_route_renders_react_shell_when_flag_enabled(
    truncate_auth_world: None,
    flag_name: str,
    route_template: str,
    page_key: str,
    active_section: str,
) -> None:
    manifest_payload = {
        "index.html": {
            "file": "assets/index-phase2.js",
            "css": ["assets/index-phase2.css"],
        }
    }
    existed, previous = _write_manifest(manifest_payload)

    settings = Settings(
        _env_file=None,
        react_manifest_validate_on_startup=False,
        **{flag_name: True},
    )
    app = create_app(settings)

    try:
        with TestClient(app) as client:
            body = _signup_and_login(client, f"{page_key}@example.com")
            slug = body["memberships"][0]["workspace_slug"]

            resp = client.get(route_template.format(slug=slug))

        assert resp.status_code == 200, resp.text
        text = resp.text
        assert 'id="sn-react-app-root"' in text
        assert f'data-page-key="{page_key}"' in text
        assert f'data-active-section="{active_section}"' in text
        assert "Open classic page" in text
        assert "/static/app/assets/index-phase2.js" in text
        assert "/static/app/assets/index-phase2.css" in text
    finally:
        _restore_manifest(existed, previous)


def test_react_authenticated_route_honors_legacy_view_query_param(
    truncate_auth_world: None,
) -> None:
    manifest_payload = {
        "index.html": {
            "file": "assets/index-phase2.js",
            "css": ["assets/index-phase2.css"],
        }
    }
    existed, previous = _write_manifest(manifest_payload)

    settings = Settings(
        _env_file=None,
        react_manifest_validate_on_startup=False,
        feature_react_inbox=True,
    )
    app = create_app(settings)

    try:
        with TestClient(app) as client:
            body = _signup_and_login(client, "owner@example.com")
            slug = body["memberships"][0]["workspace_slug"]

            resp = client.get(f"/w/{slug}/inbox?view=legacy")

        assert resp.status_code == 200, resp.text
        assert "inbox.js" in resp.text
        assert 'id="sn-react-app-root"' not in resp.text
    finally:
        _restore_manifest(existed, previous)


def test_frontend_telemetry_endpoint_accepts_authenticated_events(
    truncate_auth_world: None,
) -> None:
    app = create_app(Settings(_env_file=None))

    with TestClient(app) as client:
        _signup_and_login(client, "owner@example.com")

        resp = client.post(
            "/api/v1/frontend-events",
            json={
                "event": "api_failure",
                "route": "/w/demo-owner/inbox",
                "client_release": "assets/index-phase2.js",
                "path": "/api/v1/feedback",
                "method": "GET",
                "status_code": 500,
                "code": "internal_error",
                "request_id": "req-123",
                "message": "Something broke",
            },
        )

    assert resp.status_code == 202


def test_frontend_telemetry_endpoint_requires_auth(
    truncate_auth_world: None,
) -> None:
    app = create_app(Settings(_env_file=None))

    with TestClient(app) as client:
        resp = client.post(
            "/api/v1/frontend-events",
            json={
                "event": "api_failure",
                "route": "/w/demo-owner/inbox",
                "client_release": "assets/index-phase2.js",
            },
        )

    assert resp.status_code == 401
