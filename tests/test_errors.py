"""Tests for global exception handlers and the error envelope shape.

Covers Phase 5 deliverables: 404 / 422 / 500 bodies all include the
request ID, and unhandled exceptions never leak stack traces to the
client. The detailed v2 feedback validation matrix (pain_level,
title, description, source, status) is exercised in
``tests/api/test_feedback_v2.py``; this file keeps the
envelope-shape coverage that the parametrised matrix used to share.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from feedback_triage.config import Settings
from feedback_triage.main import create_app

VALID_PASSWORD = "correct horse battery staple"  # pragma: allowlist secret


# --- 404 envelope ---------------------------------------------------------


def test_404_body_contains_detail_and_request_id(client: TestClient) -> None:
    # Any unmatched route returns the generic 404 envelope; this no
    # longer touches the now-authenticated /api/v1/feedback surface.
    resp = client.get("/no-such-page")
    body = resp.json()
    assert resp.status_code == 404
    assert "detail" in body
    assert body["request_id"] == resp.headers["X-Request-ID"]


def test_404_echoes_inbound_request_id(client: TestClient) -> None:
    rid = "fixed-test-rid"
    resp = client.get("/no-such-page", headers={"X-Request-ID": rid})
    assert resp.json()["request_id"] == rid


# --- 422 / validation envelope --------------------------------------------


def test_validation_error_body_has_request_id(
    auth_client: TestClient,
) -> None:
    """A 422 from an authenticated route still carries ``request_id``."""
    auth_client.post(
        "/api/v1/auth/signup",
        json={"email": "alice@example.com", "password": VALID_PASSWORD},
    )
    login = auth_client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": VALID_PASSWORD},
    )
    slug = login.json()["memberships"][0]["workspace_slug"]
    resp = auth_client.post(
        "/api/v1/feedback",
        json={
            "title": "Login is slow",
            "source": "email",
            "pain_level": 0,  # out of range -> 422
        },
        headers={"X-Workspace-Slug": slug},
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["request_id"] == resp.headers["X-Request-ID"]
    assert isinstance(body["detail"], list)


# --- 500 / unhandled exceptions -------------------------------------------


@pytest.fixture
def boom_client() -> Iterator[TestClient]:
    """A client whose app has an extra route that always blows up."""
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    app: FastAPI = create_app(settings)

    @app.get("/__boom__")
    def boom() -> None:
        raise RuntimeError("intentional explosion for tests")

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def test_unhandled_exception_returns_generic_500(boom_client: TestClient) -> None:
    resp = boom_client.get("/__boom__")
    assert resp.status_code == 500
    body = resp.json()
    assert body == {
        "detail": "Internal server error",
        "request_id": resp.headers["X-Request-ID"],
    }
    assert "intentional explosion" not in resp.text
    assert "RuntimeError" not in resp.text


def test_unhandled_exception_logs_stack_trace(
    boom_client: TestClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level("ERROR", logger="feedback_triage.errors"):
        resp = boom_client.get("/__boom__")
    assert resp.status_code == 500
    matching = [r for r in caplog.records if "Unhandled exception" in r.getMessage()]
    assert matching, "expected an unhandled-exception log record"
    record = matching[0]
    assert record.exc_info is not None
    assert record.exc_info[0] is RuntimeError
