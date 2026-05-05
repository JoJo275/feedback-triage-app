"""Unit tests for :mod:`feedback_triage.auth.tokens`.

Pins the TTLs and the mint → consume → replay → 410 lifecycle from
``docs/project/spec/v2/auth.md`` — Token TTLs.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from feedback_triage.auth import tokens
from feedback_triage.database import get_db
from feedback_triage.models import User, Workspace


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


def _make_workspace(db, owner_id: uuid.UUID) -> uuid.UUID:  # type: ignore[no-untyped-def]
    ws = Workspace(
        slug=f"ws-{uuid.uuid4().hex[:8]}",
        name="Test",
        owner_id=owner_id,
    )
    db.add(ws)
    db.flush()
    assert ws.id is not None
    return ws.id


# ---------------------------------------------------------------------------
# TTL constants pinned to the spec.
# ---------------------------------------------------------------------------


def test_ttl_constants_match_spec() -> None:
    assert timedelta(hours=24) == tokens.VERIFICATION_TTL
    assert timedelta(hours=1) == tokens.PASSWORD_RESET_TTL
    assert timedelta(days=7) == tokens.INVITATION_TTL


# ---------------------------------------------------------------------------
# Email verification
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("truncate_auth_tables")
def test_verification_token_happy_path() -> None:
    gen = get_db()
    db = next(gen)
    user_id = _make_user(db)
    issued = tokens.mint_verification_token(db, user_id=user_id)
    status, returned_id = tokens.consume_verification_token(
        db,
        raw_token=issued.raw_token,
    )
    assert status is tokens.TokenStatus.OK
    assert returned_id == user_id
    _commit(gen)


@pytest.mark.usefixtures("truncate_auth_tables")
def test_verification_token_replay_returns_consumed() -> None:
    gen = get_db()
    db = next(gen)
    user_id = _make_user(db)
    issued = tokens.mint_verification_token(db, user_id=user_id)
    tokens.consume_verification_token(db, raw_token=issued.raw_token)
    status, _ = tokens.consume_verification_token(db, raw_token=issued.raw_token)
    assert status is tokens.TokenStatus.CONSUMED
    _commit(gen)


@pytest.mark.usefixtures("truncate_auth_tables")
def test_verification_token_expired() -> None:
    gen = get_db()
    db = next(gen)
    user_id = _make_user(db)
    long_ago = datetime.now(tz=UTC) - timedelta(days=30)
    issued = tokens.mint_verification_token(db, user_id=user_id, now=long_ago)
    status, _ = tokens.consume_verification_token(db, raw_token=issued.raw_token)
    assert status is tokens.TokenStatus.EXPIRED
    _commit(gen)


@pytest.mark.usefixtures("truncate_auth_tables")
def test_verification_token_unknown_returns_unknown() -> None:
    gen = get_db()
    db = next(gen)
    status, returned_id = tokens.consume_verification_token(
        db,
        raw_token="never-minted",
    )
    assert status is tokens.TokenStatus.UNKNOWN
    assert returned_id is None
    _commit(gen)


# ---------------------------------------------------------------------------
# Password reset
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("truncate_auth_tables")
def test_password_reset_token_happy_path() -> None:
    gen = get_db()
    db = next(gen)
    user_id = _make_user(db)
    issued = tokens.mint_password_reset_token(db, user_id=user_id)
    status, returned_id = tokens.consume_password_reset_token(
        db,
        raw_token=issued.raw_token,
    )
    assert status is tokens.TokenStatus.OK
    assert returned_id == user_id
    _commit(gen)


@pytest.mark.usefixtures("truncate_auth_tables")
def test_password_reset_token_expires_after_one_hour() -> None:
    gen = get_db()
    db = next(gen)
    user_id = _make_user(db)
    # Mint as if it were issued 2 hours ago — past the 1h window.
    two_hours_ago = datetime.now(tz=UTC) - timedelta(hours=2)
    issued = tokens.mint_password_reset_token(db, user_id=user_id, now=two_hours_ago)
    status, _ = tokens.consume_password_reset_token(db, raw_token=issued.raw_token)
    assert status is tokens.TokenStatus.EXPIRED
    _commit(gen)


# ---------------------------------------------------------------------------
# Invitations
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("truncate_auth_tables")
def test_invitation_token_happy_path() -> None:
    gen = get_db()
    db = next(gen)
    inviter_id = _make_user(db)
    workspace_id = _make_workspace(db, owner_id=inviter_id)
    issued = tokens.mint_invitation_token(
        db,
        workspace_id=workspace_id,
        email="invitee@example.com",
        invited_by_id=inviter_id,
    )
    status, row = tokens.consume_invitation_token(db, raw_token=issued.raw_token)
    assert status is tokens.TokenStatus.OK
    assert row is not None
    assert row.workspace_id == workspace_id
    assert row.email == "invitee@example.com"
    _commit(gen)


@pytest.mark.usefixtures("truncate_auth_tables")
def test_invitation_token_replay_returns_consumed() -> None:
    gen = get_db()
    db = next(gen)
    inviter_id = _make_user(db)
    workspace_id = _make_workspace(db, owner_id=inviter_id)
    issued = tokens.mint_invitation_token(
        db,
        workspace_id=workspace_id,
        email="invitee@example.com",
        invited_by_id=inviter_id,
    )
    tokens.consume_invitation_token(db, raw_token=issued.raw_token)
    status, _ = tokens.consume_invitation_token(db, raw_token=issued.raw_token)
    assert status is tokens.TokenStatus.CONSUMED
    _commit(gen)
