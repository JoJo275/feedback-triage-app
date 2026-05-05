"""Unit tests for :mod:`feedback_triage.auth.sessions`.

Pins the contract documented in
``docs/project/spec/v2/auth.md`` — Session cookie / TTLs:

- 256-bit raw tokens stored as SHA-256.
- 7-day TTL, sliding via ``last_seen_at`` writes capped to one per
  5 minutes per session.
- Lookup ignores expired and revoked rows.
- ``revoke_all_sessions_for_user`` honours ``except_session_id`` so
  the change-password flow can preserve the active session.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from feedback_triage.auth import sessions
from feedback_triage.database import get_db
from feedback_triage.models import User


def _commit(gen) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(StopIteration):
        next(gen)


def _make_user(db) -> uuid.UUID:  # type: ignore[no-untyped-def]
    user = User(
        email=f"u-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="!disabled-test!",
    )
    db.add(user)
    db.flush()
    assert user.id is not None
    return user.id


@pytest.mark.usefixtures("truncate_auth_tables")
def test_create_session_returns_raw_token_and_persists_hash() -> None:
    gen = get_db()
    db = next(gen)
    user_id = _make_user(db)
    issued = sessions.create_session(db, user_id=user_id, user_agent="pytest")
    assert len(issued.raw_token) >= 40  # 32 bytes base64-url ~= 43 chars
    looked_up = sessions.lookup_session(db, raw_token=issued.raw_token)
    assert looked_up is not None
    assert looked_up.user_id == user_id
    assert looked_up.token_hash != issued.raw_token  # stored as hash, not raw
    _commit(gen)


@pytest.mark.usefixtures("truncate_auth_tables")
def test_lookup_session_rejects_revoked_and_expired() -> None:
    gen = get_db()
    db = next(gen)
    user_id = _make_user(db)

    # Expired row.
    long_ago = datetime.now(tz=UTC) - timedelta(days=30)
    expired = sessions.create_session(db, user_id=user_id, now=long_ago)
    assert sessions.lookup_session(db, raw_token=expired.raw_token) is None

    # Revoked row.
    live = sessions.create_session(db, user_id=user_id)
    sessions.revoke_session(db, session_id=live.session_id)
    assert sessions.lookup_session(db, raw_token=live.raw_token) is None
    _commit(gen)


@pytest.mark.usefixtures("truncate_auth_tables")
def test_renew_if_stale_respects_five_minute_cadence() -> None:
    gen = get_db()
    db = next(gen)
    user_id = _make_user(db)
    issued = sessions.create_session(db, user_id=user_id)
    row = sessions.lookup_session(db, raw_token=issued.raw_token)
    assert row is not None

    # A renewal within 5 minutes is a no-op.
    soon = row.last_seen_at + timedelta(minutes=1)
    assert sessions.renew_if_stale(db, row, now=soon) is False

    # Past the window, the row is bumped.
    later = row.last_seen_at + timedelta(minutes=10)
    assert sessions.renew_if_stale(db, row, now=later) is True
    assert row.last_seen_at == later
    assert row.expires_at == later + sessions.SESSION_TTL
    _commit(gen)


@pytest.mark.usefixtures("truncate_auth_tables")
def test_revoke_all_for_user_can_preserve_active_session() -> None:
    gen = get_db()
    db = next(gen)
    user_id = _make_user(db)
    keep = sessions.create_session(db, user_id=user_id)
    drop1 = sessions.create_session(db, user_id=user_id)
    drop2 = sessions.create_session(db, user_id=user_id)

    touched = sessions.revoke_all_sessions_for_user(
        db,
        user_id=user_id,
        except_session_id=keep.session_id,
    )
    assert touched == 2
    assert sessions.lookup_session(db, raw_token=keep.raw_token) is not None
    assert sessions.lookup_session(db, raw_token=drop1.raw_token) is None
    assert sessions.lookup_session(db, raw_token=drop2.raw_token) is None
    _commit(gen)
