"""Shared fixtures for the auth API flow tests.

The auth routes write to many tables (users, workspaces,
memberships, sessions, ``*_tokens``, ``email_log``); we truncate the
full v2 cluster between cases — same pattern as
``tests/unit/auth/conftest.py``. ``RESEND_DRY_RUN=1`` is the package
default, so the email client never makes a network call here.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from feedback_triage.config import Settings
from feedback_triage.database import engine
from feedback_triage.main import create_app


@pytest.fixture
def truncate_auth_world() -> Iterator[None]:
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
    app = create_app(auth_settings)
    with TestClient(app) as c:
        yield c
