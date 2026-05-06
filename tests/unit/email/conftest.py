"""Shared fixtures for the email-client unit tests.

The client writes ``email_log`` rows on its own ``SessionLocal`` —
test isolation is therefore a TRUNCATE between cases, same pattern
as ``tests/unit/auth/conftest.py``.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import text

from feedback_triage.database import engine


@pytest.fixture
def truncate_email_log() -> Iterator[None]:
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE email_log RESTART IDENTITY CASCADE"))
    yield
