"""Phase 3 React public-page route tests.

Covers per-page feature flags for public routes, legacy fallback via
``?view=legacy``, and cache-header parity on cached public pages.
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


def _first_slug(login_body: dict[str, object]) -> str:
    memberships = login_body["memberships"]
    assert isinstance(memberships, list) and memberships
    return str(memberships[0]["workspace_slug"])


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
    ("flag_name", "route_template", "page_key"),
    [
        ("feature_react_landing", "/", "landing"),
        ("feature_react_public_submit", "/w/{slug}/submit", "public_submit"),
        (
            "feature_react_public_roadmap",
            "/w/{slug}/roadmap/public",
            "public_roadmap",
        ),
        (
            "feature_react_public_changelog",
            "/w/{slug}/changelog/public",
            "public_changelog",
        ),
    ],
)
def test_public_page_route_renders_react_shell_when_flag_enabled(
    truncate_auth_world: None,
    flag_name: str,
    route_template: str,
    page_key: str,
) -> None:
    manifest_payload = {
        "index.html": {
            "file": "assets/index-phase3.js",
            "css": ["assets/index-phase3.css"],
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
            route = route_template
            if "{slug}" in route_template:
                body = _signup_and_login(client, f"{page_key}@example.com")
                slug = _first_slug(body)
                route = route_template.format(slug=slug)
                client.cookies.clear()

            resp = client.get(route)

        assert resp.status_code == 200, resp.text
        text = resp.text
        assert 'id="sn-react-app-root"' in text
        assert f'data-page-key="{page_key}"' in text
        assert "Open classic page" in text
        assert "/static/app/assets/index-phase3.js" in text
        assert "/static/app/assets/index-phase3.css" in text
    finally:
        _restore_manifest(existed, previous)


@pytest.mark.parametrize(
    ("flag_name", "route_template", "expected_fragment"),
    [
        ("feature_react_landing", "/", 'id="landing-demo"'),
        (
            "feature_react_public_submit",
            "/w/{slug}/submit",
            'id="submit-form"',
        ),
        (
            "feature_react_public_roadmap",
            "/w/{slug}/roadmap/public",
            "Nothing on the public roadmap yet.",
        ),
        (
            "feature_react_public_changelog",
            "/w/{slug}/changelog/public",
            "Nothing shipped yet.",
        ),
    ],
)
def test_public_page_route_honors_legacy_view_query_param(
    truncate_auth_world: None,
    flag_name: str,
    route_template: str,
    expected_fragment: str,
) -> None:
    manifest_payload = {
        "index.html": {
            "file": "assets/index-phase3.js",
            "css": ["assets/index-phase3.css"],
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
            route = route_template
            if "{slug}" in route_template:
                body = _signup_and_login(client, f"legacy-{flag_name}@example.com")
                slug = _first_slug(body)
                route = route_template.format(slug=slug)
                client.cookies.clear()

            resp = client.get(f"{route}?view=legacy")

        assert resp.status_code == 200, resp.text
        assert 'id="sn-react-app-root"' not in resp.text
        assert expected_fragment in resp.text
    finally:
        _restore_manifest(existed, previous)


@pytest.mark.parametrize(
    ("flag_name", "route_template"),
    [
        ("feature_react_public_roadmap", "/w/{slug}/roadmap/public"),
        ("feature_react_public_changelog", "/w/{slug}/changelog/public"),
    ],
)
def test_react_public_cached_routes_preserve_cache_headers(
    truncate_auth_world: None,
    flag_name: str,
    route_template: str,
) -> None:
    manifest_payload = {
        "index.html": {
            "file": "assets/index-phase3.js",
            "css": ["assets/index-phase3.css"],
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
            body = _signup_and_login(client, f"cache-{flag_name}@example.com")
            slug = _first_slug(body)
            client.cookies.clear()

            resp = client.get(route_template.format(slug=slug))

        assert resp.status_code == 200, resp.text
        assert (
            resp.headers["cache-control"]
            == "public, max-age=300, stale-while-revalidate=600"
        )
    finally:
        _restore_manifest(existed, previous)
