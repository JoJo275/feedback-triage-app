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
    """Wipe ``feedback_item`` and reset its identity sequence per test.

    ``CASCADE`` follows the v2 join tables (``feedback_tags``,
    ``feedback_notes``) so a re-run starts with no orphan rows. Also
    re-seeds the synthetic ``signalnest-legacy`` admin + workspace
    inserted by Migration A — the v2 isolation / session canary
    fixtures truncate ``users`` + ``workspaces`` between tests, so v1
    routes (which fall back to the legacy workspace per
    ``rollout.md``) need the rows re-created defensively.
    """
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE feedback_item RESTART IDENTITY CASCADE"))
        # Sentinel password hash: not a valid Argon2id encoded hash, so
        # login is disabled by construction (per ADR 062).
        conn.execute(
            text(
                """
                INSERT INTO users (id, email, password_hash, is_verified, role)
                SELECT gen_random_uuid(), 'legacy@signalnest.local',
                       '!disabled-legacy-v1-admin!', false, 'admin'
                 WHERE NOT EXISTS (
                    SELECT 1 FROM users WHERE email = 'legacy@signalnest.local'
                 )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO workspaces (id, slug, name, owner_id, is_demo)
                SELECT gen_random_uuid(), 'signalnest-legacy',
                       'SignalNest (legacy)', u.id, false
                  FROM users u
                 WHERE u.email = 'legacy@signalnest.local'
                   AND NOT EXISTS (
                    SELECT 1 FROM workspaces WHERE slug = 'signalnest-legacy'
                   )
                """
            )
        )
    yield


@pytest.fixture
def client(settings: Settings, truncate_feedback: None) -> Iterator[TestClient]:
    """FastAPI TestClient bound to the live Postgres database."""
    app = create_app(settings)
    with TestClient(app) as c:
        yield c


@pytest.fixture
def truncate_auth_world() -> Iterator[None]:
    """Wipe every v2 auth/tenant table between tests."""
    with engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE TABLE "
                "users, workspaces, workspace_memberships, "
                "workspace_invitations, sessions, "
                "email_verification_tokens, password_reset_tokens, "
                "auth_rate_limits, email_log "
                "RESTART IDENTITY CASCADE",
            ),
        )
    yield


@pytest.fixture
def auth_settings() -> Settings:
    return Settings(_env_file=None)  # type: ignore[call-arg]


@pytest.fixture
def auth_client(
    auth_settings: Settings,
    truncate_auth_world: None,
) -> Iterator[TestClient]:
    """TestClient for v2 auth/workspace flow tests."""
    app = create_app(auth_settings)
    with TestClient(app) as c:
        yield c
