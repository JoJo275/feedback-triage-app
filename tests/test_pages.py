"""Tests for the static HTML page routes (Phase 4)."""

from __future__ import annotations

import html

import pytest
from fastapi.testclient import TestClient

VALID_PASSWORD = "correct horse battery staple"  # pragma: allowlist secret


def _signup_and_login(client: TestClient, email: str) -> str:
    signup = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": VALID_PASSWORD},
    )
    assert signup.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": VALID_PASSWORD},
    )
    assert login.status_code == 200
    return str(login.json()["memberships"][0]["workspace_slug"])


def test_index_page_serves_landing(client: TestClient) -> None:
    """ "/" now renders the v2 Jinja landing page (PR 3.4)."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    body = response.text
    assert "SignalNest" in body
    assert "Capture the noise. Find the signal." in body
    assert 'id="landing-demo"' in body
    assert "/static/js/landing_demo.js" in body
    assert response.headers.get("cache-control", "").startswith("public, max-age=300")


def test_landing_redirects_authenticated_users_to_dashboard(
    auth_client: TestClient,
) -> None:
    slug = _signup_and_login(auth_client, "owner@example.com")

    response = auth_client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == f"/w/{slug}/dashboard"
    assert response.headers.get("cache-control") == "private, no-store"


@pytest.mark.parametrize("path", ["/login", "/signup"])
def test_login_and_signup_redirect_authenticated_users_to_dashboard(
    auth_client: TestClient,
    path: str,
) -> None:
    slug = _signup_and_login(auth_client, "owner@example.com")

    response = auth_client.get(path, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == f"/w/{slug}/dashboard"
    assert response.headers.get("cache-control") == "private, no-store"


def test_new_page_serves_html(client: TestClient) -> None:
    response = client.get("/new")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Create feedback" in response.text
    assert "/static/js/new.js" in response.text


def test_detail_page_serves_html(client: TestClient) -> None:
    response = client.get("/feedback/1")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Edit feedback" in response.text
    assert "/static/js/detail.js" in response.text


def test_detail_page_rejects_non_integer_id(client: TestClient) -> None:
    # Path parameter is typed as ``int`` so non-numeric IDs 422.
    response = client.get("/feedback/not-a-number")
    assert response.status_code == 422


def test_static_css_is_served(client: TestClient) -> None:
    response = client.get("/static/css/styles.css")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/css")


def test_styleguide_page_renders(client: TestClient) -> None:
    """v2.0 styleguide stub: confirms Jinja + Tailwind link wiring.

    The actual hashed app.<hash>.css comes from `task build:css`. When
    the manifest is missing (clean clone before first build), the
    fallback resolves to ``/static/css/app.css`` — both forms count
    as "wiring works" for this smoke.
    """
    response = client.get("/styleguide")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    body = response.text
    assert "<title>Style guide" in body
    # Either the hashed (post-build) or unhashed (pre-build) link.
    assert "/static/css/app." in body
    # Skip-link present per accessibility floor.
    assert 'class="sn-skip-link"' in body
    # PR 4.2: preset switcher present and main element carries the
    # default `preset-production` token block.
    assert 'data-theme="preset-production"' in body
    assert 'id="sg-preset-switcher"' in body
    for preset in ("production", "basic", "unique", "crazy"):
        assert f'value="{preset}"' in body
    assert "/static/js/styleguide.js" in body


@pytest.mark.parametrize(
    ("path", "status_code", "expected_copy"),
    [
        ("/404", 404, "Not found."),
        ("/403", 403, "You don't have access to that."),
        ("/500", 500, "Something went wrong. The team has been notified."),
    ],
)
def test_system_error_pages_render(
    client: TestClient,
    path: str,
    status_code: int,
    expected_copy: str,
) -> None:
    response = client.get(path, headers={"X-Request-ID": "rid-test-123"})
    assert response.status_code == status_code
    assert response.headers["content-type"].startswith("text/html")
    assert expected_copy in html.unescape(response.text)
    if path == "/500":
        assert "rid-test-123" in response.text


def test_404_page_links_to_dashboard_when_authenticated(
    auth_client: TestClient,
) -> None:
    slug = _signup_and_login(auth_client, "owner@example.com")

    response = auth_client.get("/404")
    assert response.status_code == 404
    assert f'href="/w/{slug}/dashboard"' in response.text


def test_static_js_modules_are_served(client: TestClient) -> None:
    for path in (
        "/static/js/api.js",
        "/static/js/index.js",
        "/static/js/new.js",
        "/static/js/detail.js",
        "/static/js/landing_demo.js",
        "/static/js/styleguide.js",
    ):
        response = client.get(path)
        assert response.status_code == 200, path
        assert response.headers["content-type"].startswith(
            ("application/javascript", "text/javascript")
        ), path


def test_pages_excluded_from_openapi_schema(client: TestClient) -> None:
    schema = client.get("/api/v1/openapi.json").json()
    paths = schema.get("paths", {})
    assert "/" not in paths
    assert "/new" not in paths
    assert "/feedback/{item_id}" not in paths
    assert "/404" not in paths
    assert "/403" not in paths
    assert "/500" not in paths
    assert "/privacy" not in paths
    assert "/terms" not in paths


def test_privacy_page_renders(client: TestClient) -> None:
    response = client.get("/privacy")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    body = response.text
    assert "<h1>Privacy</h1>" in body
    assert 'href="/terms"' in body


def test_terms_page_renders(client: TestClient) -> None:
    response = client.get("/terms")
    assert response.status_code == 200
    body = response.text
    assert "Terms of service" in body
    assert 'href="/privacy"' in body


def test_landing_links_to_legal_pages(client: TestClient) -> None:
    response = client.get("/")
    body = response.text
    assert 'href="/privacy"' in body
    assert 'href="/terms"' in body
