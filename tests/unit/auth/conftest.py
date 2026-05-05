"""Shared fixtures for the auth unit tests.

These tests exercise the auth primitives against the live Postgres DB
(no SQLite, per spec — Testing). The v2 table cluster is truncated
before each test so token/session row IDs don't leak between cases.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import text

from feedback_triage.database import engine


@pytest.fixture
def truncate_auth_tables() -> Iterator[None]:
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
