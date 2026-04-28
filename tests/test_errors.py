"""Tests for global exception handlers and the error envelope shape.

Covers Phase 5 deliverables: 404 / 422 / 500 bodies all include the
request ID, validation rules from the spec are enforced, and unhandled
exceptions never leak stack traces to the client.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from feedback_triage.config import Settings
from feedback_triage.main import create_app


def _valid_payload(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "title": "Login is slow",
        "description": "Takes 8 seconds on cold start.",
        "source": "email",
        "pain_level": 3,
    }
    base.update(overrides)
    return base


# --- 404 envelope ---------------------------------------------------------


def test_404_body_contains_detail_and_request_id(client: TestClient) -> None:
    resp = client.get("/api/v1/feedback/99999")
    body = resp.json()
    assert resp.status_code == 404
    assert body["detail"] == "Feedback item not found"
    assert body["request_id"] == resp.headers["X-Request-ID"]


def test_404_echoes_inbound_request_id(client: TestClient) -> None:
    rid = "fixed-test-rid"
    resp = client.get("/api/v1/feedback/99999", headers={"X-Request-ID": rid})
    assert resp.json()["request_id"] == rid


# --- 422 / validation rules -----------------------------------------------


def test_validation_error_body_has_request_id(client: TestClient) -> None:
    resp = client.post("/api/v1/feedback", json=_valid_payload(pain_level=0))
    assert resp.status_code == 422
    body = resp.json()
    assert body["request_id"] == resp.headers["X-Request-ID"]
    assert isinstance(body["detail"], list)


@pytest.mark.parametrize(
    "overrides",
    [
        {"pain_level": 0},
        {"pain_level": 6},
        {"pain_level": -1},
        {"title": ""},
        {"title": "   "},
        {"title": "x" * 201},
        {"description": "x" * 5001},
        {"source": "carrier-pigeon"},
        {"status": "bogus"},
    ],
)
def test_validation_rules_reject_bad_input(
    client: TestClient,
    overrides: dict[str, object],
) -> None:
    resp = client.post("/api/v1/feedback", json=_valid_payload(**overrides))
    assert resp.status_code == 422, overrides


# --- 500 / unhandled exceptions -------------------------------------------


@pytest.fixture
def boom_client() -> Iterator[TestClient]:
    """A client whose app has an extra route that always blows up."""
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    app: FastAPI = create_app(settings)

    @app.get("/__boom__")
    def boom() -> None:
        raise RuntimeError("intentional explosion for tests")

    # raise_server_exceptions=False so TestClient lets the handler run
    # instead of re-raising the exception in our face.
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
    # No leaked exception text in the body.
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
