"""Tests for the static HTML page routes (Phase 4)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_index_page_serves_html(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "<title>SignalNest</title>" in response.text
    assert "/static/js/index.js" in response.text


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


def test_static_js_modules_are_served(client: TestClient) -> None:
    for path in (
        "/static/js/api.js",
        "/static/js/index.js",
        "/static/js/new.js",
        "/static/js/detail.js",
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
