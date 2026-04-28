"""Shared pytest fixtures for the API test suite.

The tests run against a real Postgres database (no SQLite — see spec —
Testing). Each test gets a fresh ``feedback_item`` via a ``TRUNCATE``
fixture; we don't recreate the schema per test because the migration
already ran in CI / locally via ``task migrate``.

Phase 6 will expand this with a per-test schema or transaction-rollback
strategy. For Phase 3, truncate-between-tests is enough.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from feedback_triage.config import Settings
from feedback_triage.database import engine
from feedback_triage.main import create_app


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings(_env_file=None)  # type: ignore[call-arg]


@pytest.fixture
def truncate_feedback() -> Iterator[None]:
    """Wipe ``feedback_item`` and reset its identity sequence per test."""
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE feedback_item RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture
def client(settings: Settings, truncate_feedback: None) -> Iterator[TestClient]:
    """FastAPI TestClient bound to the live Postgres database."""
    app = create_app(settings)
    with TestClient(app) as c:
        yield c
