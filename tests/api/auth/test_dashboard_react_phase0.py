"""Phase 0 React dashboard route tests.

Covers manifest fail-closed startup validation, route fallback behavior,
and CSP/header handling for the Vite-backed React shell route.
"""

from __future__ import annotations

import json
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from feedback_triage.config import Settings
from feedback_triage.frontend_assets import REACT_MANIFEST, reset_manifest_cache
from feedback_triage.main import create_app
from feedback_triage.services import dashboard_aggregator

VALID_PASSWORD = "correct horse battery staple"  # pragma: allowlist secret


@pytest.fixture(autouse=True)
def _reset_dashboard_cache() -> Iterator[None]:
    dashboard_aggregator.reset_cache()
    reset_manifest_cache()
    yield
    dashboard_aggregator.reset_cache()
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


def test_react_route_startup_fails_closed_when_required_manifest_key_missing(
    truncate_auth_world: None,
) -> None:
    settings = Settings(
        _env_file=None,
        feature_react_dashboard=True,
        react_manifest_required_entries="missing-entry.html",
    )
    app = create_app(settings)

    with (
        pytest.raises(
            RuntimeError,
            match="React manifest validation failed",
        ),
        TestClient(app),
    ):
        pass


def test_react_route_falls_back_to_legacy_dashboard_when_entry_missing(
    truncate_auth_world: None,
) -> None:
    settings = Settings(
        _env_file=None,
        feature_react_dashboard=True,
        react_manifest_validate_on_startup=False,
        react_dashboard_entrypoint="missing-entry.html",
    )
    app = create_app(settings)

    with TestClient(app) as client:
        body = _signup_and_login(client, "owner@example.com")
        slug = body["memberships"][0]["workspace_slug"]

        resp = client.get(
            f"/w/{slug}/dashboard/react",
            follow_redirects=False,
        )

    assert resp.status_code == 307
    assert resp.headers.get("location") == f"/w/{slug}/dashboard"


def test_react_route_renders_vite_assets_and_csp_header_when_manifest_exists(
    truncate_auth_world: None,
) -> None:
    manifest_payload = {
        "index.html": {
            "file": "assets/index-phase0.js",
            "css": ["assets/index-phase0.css"],
        }
    }
    existed, previous = _write_manifest(manifest_payload)

    settings = Settings(
        _env_file=None,
        feature_react_dashboard=True,
        react_manifest_required_entries="index.html",
        react_dashboard_entrypoint="index.html",
        react_csp_enabled=True,
    )
    app = create_app(settings)

    try:
        with TestClient(app) as client:
            body = _signup_and_login(client, "owner@example.com")
            slug = body["memberships"][0]["workspace_slug"]

            resp = client.get(f"/w/{slug}/dashboard/react")

        assert resp.status_code == 200, resp.text
        assert 'id="sn-react-app-root"' in resp.text
        assert "/static/app/assets/index-phase0.css" in resp.text
        assert "/static/app/assets/index-phase0.js" in resp.text
        assert resp.headers.get("content-security-policy") == settings.react_csp_policy
    finally:
        _restore_manifest(existed, previous)
