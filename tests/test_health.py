"""Tests for `/health` and `/ready` plus request-ID middleware behaviour.

The readiness probe is exercised against a real engine in Phase 2; here
we patch the engine's ``connect`` method to keep the test hermetic.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from feedback_triage.config import Settings
from feedback_triage.main import create_app


@pytest.fixture
def client() -> Iterator[TestClient]:
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    app = create_app(settings)
    with TestClient(app) as c:
        yield c


def test_health_returns_ok(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_every_response_has_request_id_header(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.headers.get("X-Request-ID")


def test_inbound_request_id_is_echoed(client: TestClient) -> None:
    rid = "abc123-fixed-id"
    resp = client.get("/health", headers={"X-Request-ID": rid})
    assert resp.headers["X-Request-ID"] == rid


def test_ready_returns_ok_when_db_reachable(client: TestClient) -> None:
    fake_conn = MagicMock()
    fake_conn.execute.return_value = None
    fake_ctx = MagicMock()
    fake_ctx.__enter__.return_value = fake_conn
    fake_ctx.__exit__.return_value = False
    with patch("feedback_triage.routes.health.engine.connect", return_value=fake_ctx):
        resp = client.get("/ready")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_ready_returns_503_when_db_unreachable(client: TestClient) -> None:
    def boom(*_args: Any, **_kwargs: Any) -> None:
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    with patch("feedback_triage.routes.health.engine.connect", side_effect=boom):
        resp = client.get("/ready")
    assert resp.status_code == 503
    assert resp.json() == {"status": "degraded"}
