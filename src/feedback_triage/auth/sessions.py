"""Session creation, lookup, sliding renewal, and revocation.

Sessions are stored in the ``sessions`` table (PR 1.3b). The DB column
``token_hash`` holds ``sha256(raw_token)``; the raw token lives only in
the ``signalnest_session`` cookie on the client. See
``docs/project/spec/v2/auth.md`` — Session cookie / TTLs / last_seen
cadence.

Naming: this module deliberately uses :class:`UserSession` (the ORM
class re-exported from :mod:`feedback_triage.models`) rather than
``Session`` to avoid colliding with :class:`sqlalchemy.orm.Session`.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import update
from sqlalchemy.orm import Session as DbSession
from sqlmodel import col, select

from feedback_triage.models import UserSession

# Sliding-window cadence (auth.md — last_seen_at write cadence). Writes
# at most once per 5 minutes per session to keep WAL traffic down.
SESSION_TTL = timedelta(days=7)
LAST_SEEN_WRITE_INTERVAL = timedelta(minutes=5)

# 256 bits per spec — Session cookie. ``token_urlsafe(32)`` returns a
# 43-character base64-url string (32 bytes of entropy).
_RAW_TOKEN_BYTES = 32


@dataclass(frozen=True, slots=True)
class IssuedSession:
    """Return value of :func:`create_session`.

    Carries the raw token so the route can hand it to
    :func:`feedback_triage.auth.cookies.set_session_cookie`. Never
    persisted; the DB stores only :attr:`token_hash`.
    """

    session_id: uuid.UUID
    raw_token: str
    expires_at: datetime


def _hash_token(raw_token: str) -> str:
    """Return the canonical storage form of a session/token value.

    SHA-256 hex digest. Per ``auth.md`` — Token TTLs: "All tokens are
    stored as SHA-256 of the raw value."
    """
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime.now(tz=UTC)


def create_session(
    db: DbSession,
    *,
    user_id: uuid.UUID,
    user_agent: str | None = None,
    ip_inet: str | None = None,
    now: datetime | None = None,
) -> IssuedSession:
    """Mint a new session row and return the raw cookie token.

    The caller (PR 1.7's login route) is responsible for setting the
    cookie via :mod:`feedback_triage.auth.cookies`.
    """
    when = now or _now()
    raw_token = secrets.token_urlsafe(_RAW_TOKEN_BYTES)
    row = UserSession(
        user_id=user_id,
        token_hash=_hash_token(raw_token),
        user_agent=user_agent,
        ip_inet=ip_inet,
        created_at=when,
        last_seen_at=when,
        expires_at=when + SESSION_TTL,
    )
    db.add(row)
    db.flush()  # populate ``row.id`` without ending the transaction
    assert row.id is not None
    return IssuedSession(
        session_id=row.id,
        raw_token=raw_token,
        expires_at=row.expires_at,
    )


def lookup_session(
    db: DbSession,
    *,
    raw_token: str,
    now: datetime | None = None,
) -> UserSession | None:
    """Return the live :class:`UserSession` for ``raw_token`` or ``None``.

    "Live" means: row exists, ``revoked_at IS NULL``, and ``expires_at
    > now``. Expired-but-not-revoked rows return ``None`` and are left
    in place; a sweeper job (Phase 3) trims them.
    """
    when = now or _now()
    token_hash = _hash_token(raw_token)
    row = db.execute(
        select(UserSession).where(col(UserSession.token_hash) == token_hash),
    ).scalar_one_or_none()
    if row is None or row.revoked_at is not None or row.expires_at <= when:
        return None
    return row


def renew_if_stale(
    db: DbSession,
    session: UserSession,
    *,
    now: datetime | None = None,
) -> bool:
    """Update ``last_seen_at`` + ``expires_at`` if past the cadence window.

    Returns ``True`` if the row was written. Per
    ``auth.md`` — last_seen_at write cadence: at most one write per
    5 minutes per session.
    """
    when = now or _now()
    if when - session.last_seen_at < LAST_SEEN_WRITE_INTERVAL:
        return False
    db.execute(
        update(UserSession)
        .where(col(UserSession.id) == session.id)
        .values(last_seen_at=when, expires_at=when + SESSION_TTL),
    )
    # Mirror the write into the in-memory object so the same request's
    # later code paths see fresh values.
    session.last_seen_at = when
    session.expires_at = when + SESSION_TTL
    return True


def revoke_session(
    db: DbSession,
    *,
    session_id: uuid.UUID,
    now: datetime | None = None,
) -> None:
    """Mark one session row revoked.

    Used by ``/logout`` (PR 1.7).
    """
    when = now or _now()
    db.execute(
        update(UserSession)
        .where(col(UserSession.id) == session_id)
        .where(col(UserSession.revoked_at).is_(None))
        .values(revoked_at=when),
    )


def revoke_all_sessions_for_user(
    db: DbSession,
    *,
    user_id: uuid.UUID,
    now: datetime | None = None,
    except_session_id: uuid.UUID | None = None,
) -> int:
    """Revoke every live session for ``user_id``.

    Returns the number of rows touched. ``except_session_id`` is used
    by the change-password flow (auth.md state machine: change-password
    revokes every session **other than** the one the request came
    from). ``reset-password`` and ``logout-everywhere`` pass ``None``.
    """
    when = now or _now()
    stmt = (
        update(UserSession)
        .where(col(UserSession.user_id) == user_id)
        .where(col(UserSession.revoked_at).is_(None))
        .values(revoked_at=when)
    )
    if except_session_id is not None:
        stmt = stmt.where(col(UserSession.id) != except_session_id)
    result = db.execute(stmt)
    return int(result.rowcount or 0)  # type: ignore[attr-defined]
