"""Single-use auth tokens — verification, password reset, invitation.

The three token surfaces share an identical shape on disk
(``email_verification_tokens``, ``password_reset_tokens``,
``workspace_invitations``) and an identical lifecycle (mint → consume
once → reuse → 410 Gone). This module owns the mint + consume
primitives so the route handlers (PR 1.7) stay thin.

TTLs come straight from ``docs/project/spec/v2/auth.md`` — Token TTLs:

| Token                | TTL      |
| -------------------- | -------- |
| Email verification   | 24 hours |
| Password reset       | 1 hour   |
| Workspace invitation | 7 days   |

All tokens are stored as ``sha256(raw)`` per the same spec section.

The module exposes a :class:`TokenStatus` enum so the routes can map
mint/consume outcomes to HTTP shapes without re-deriving the rules:

- ``OK``       — token consumed, side effects can proceed.
- ``EXPIRED``  — past TTL; ``410 Gone`` per spec.
- ``CONSUMED`` — replay of an already-consumed token; ``410 Gone``.
- ``UNKNOWN``  — no row matches; ``410 Gone`` (no enumeration).
"""

from __future__ import annotations

import enum
import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import update
from sqlalchemy.orm import Session as DbSession
from sqlmodel import col, select

from feedback_triage.models import (
    EmailVerificationToken,
    PasswordResetToken,
    WorkspaceInvitation,
)

VERIFICATION_TTL = timedelta(hours=24)
PASSWORD_RESET_TTL = timedelta(hours=1)
INVITATION_TTL = timedelta(days=7)

# 256 bits of entropy, base64-url. Same shape as session tokens; kept
# separate so the surfaces can rotate independently if either one ever
# needs a different size.
_RAW_TOKEN_BYTES = 32


class TokenStatus(enum.Enum):
    """Outcome of a :func:`consume_*_token` call."""

    OK = "ok"
    EXPIRED = "expired"
    CONSUMED = "consumed"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class IssuedToken:
    """Return value of every ``mint_*`` function.

    The raw value is what gets emailed; only :attr:`token_hash` ever
    lives in the database.
    """

    raw_token: str
    token_hash: str
    expires_at: datetime


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _mint(ttl: timedelta, *, now: datetime | None = None) -> IssuedToken:
    when = now or _now()
    raw = secrets.token_urlsafe(_RAW_TOKEN_BYTES)
    return IssuedToken(
        raw_token=raw,
        token_hash=_hash_token(raw),
        expires_at=when + ttl,
    )


# ---------------------------------------------------------------------------
# Email verification
# ---------------------------------------------------------------------------


def mint_verification_token(
    db: DbSession,
    *,
    user_id: uuid.UUID,
    now: datetime | None = None,
) -> IssuedToken:
    """Persist a new email-verification token row and return the raw value."""
    when = now or _now()
    issued = _mint(VERIFICATION_TTL, now=when)
    db.add(
        EmailVerificationToken(
            user_id=user_id,
            token_hash=issued.token_hash,
            expires_at=issued.expires_at,
            created_at=when,
        ),
    )
    db.flush()
    return issued


def consume_verification_token(
    db: DbSession,
    *,
    raw_token: str,
    now: datetime | None = None,
) -> tuple[TokenStatus, uuid.UUID | None]:
    """Mark a verification token consumed; return the status + user id.

    On :class:`TokenStatus.OK` the caller is responsible for flipping
    ``users.is_verified = true``. The split keeps the token primitive
    storage-agnostic.
    """
    when = now or _now()
    row = db.execute(
        select(EmailVerificationToken).where(
            col(EmailVerificationToken.token_hash) == _hash_token(raw_token),
        ),
    ).scalar_one_or_none()
    if row is None:
        return TokenStatus.UNKNOWN, None
    if row.consumed_at is not None:
        return TokenStatus.CONSUMED, row.user_id
    if row.expires_at <= when:
        return TokenStatus.EXPIRED, row.user_id
    db.execute(
        update(EmailVerificationToken)
        .where(col(EmailVerificationToken.id) == row.id)
        .values(consumed_at=when),
    )
    return TokenStatus.OK, row.user_id


# ---------------------------------------------------------------------------
# Password reset
# ---------------------------------------------------------------------------


def mint_password_reset_token(
    db: DbSession,
    *,
    user_id: uuid.UUID,
    now: datetime | None = None,
) -> IssuedToken:
    """Persist a new password-reset token row and return the raw value."""
    when = now or _now()
    issued = _mint(PASSWORD_RESET_TTL, now=when)
    db.add(
        PasswordResetToken(
            user_id=user_id,
            token_hash=issued.token_hash,
            expires_at=issued.expires_at,
            created_at=when,
        ),
    )
    db.flush()
    return issued


def consume_password_reset_token(
    db: DbSession,
    *,
    raw_token: str,
    now: datetime | None = None,
) -> tuple[TokenStatus, uuid.UUID | None]:
    """Mark a password-reset token consumed; return the status + user id.

    On :class:`TokenStatus.OK` the caller writes the new password hash
    **and** revokes every session for the user (auth.md state machine:
    "reset-password revokes every session including the active one").
    """
    when = now or _now()
    row = db.execute(
        select(PasswordResetToken).where(
            col(PasswordResetToken.token_hash) == _hash_token(raw_token),
        ),
    ).scalar_one_or_none()
    if row is None:
        return TokenStatus.UNKNOWN, None
    if row.consumed_at is not None:
        return TokenStatus.CONSUMED, row.user_id
    if row.expires_at <= when:
        return TokenStatus.EXPIRED, row.user_id
    db.execute(
        update(PasswordResetToken)
        .where(col(PasswordResetToken.id) == row.id)
        .values(consumed_at=when),
    )
    return TokenStatus.OK, row.user_id


# ---------------------------------------------------------------------------
# Workspace invitation
# ---------------------------------------------------------------------------


def mint_invitation_token(
    db: DbSession,
    *,
    workspace_id: uuid.UUID,
    email: str,
    invited_by_id: uuid.UUID,
    role: str = "team_member",
    now: datetime | None = None,
) -> IssuedToken:
    """Persist a new workspace-invitation row and return the raw value.

    The migration's partial unique index
    ``workspace_invitations_open_idx`` enforces "at most one open
    invite per (workspace, email)"; the route is responsible for
    revoking any prior open invite before calling this primitive (a
    fresh re-invite is a revoke + mint).
    """
    when = now or _now()
    issued = _mint(INVITATION_TTL, now=when)
    db.add(
        WorkspaceInvitation(
            workspace_id=workspace_id,
            email=email,
            role=role,
            token_hash=issued.token_hash,
            invited_by_id=invited_by_id,
            expires_at=issued.expires_at,
            created_at=when,
        ),
    )
    db.flush()
    return issued


def consume_invitation_token(
    db: DbSession,
    *,
    raw_token: str,
    now: datetime | None = None,
) -> tuple[TokenStatus, WorkspaceInvitation | None]:
    """Mark an invitation accepted; return the status + invitation row.

    On :class:`TokenStatus.OK` the caller inserts a
    :class:`feedback_triage.models.WorkspaceMembership` row binding
    the accepting user to ``invitation.workspace_id`` with
    ``invitation.role``.
    """
    when = now or _now()
    row = db.execute(
        select(WorkspaceInvitation).where(
            col(WorkspaceInvitation.token_hash) == _hash_token(raw_token),
        ),
    ).scalar_one_or_none()
    if row is None:
        return TokenStatus.UNKNOWN, None
    if row.revoked_at is not None:
        # A revoked invite reads like a replay — same 410 outcome.
        return TokenStatus.CONSUMED, row
    if row.accepted_at is not None:
        return TokenStatus.CONSUMED, row
    if row.expires_at <= when:
        return TokenStatus.EXPIRED, row
    db.execute(
        update(WorkspaceInvitation)
        .where(col(WorkspaceInvitation.id) == row.id)
        .values(accepted_at=when),
    )
    return TokenStatus.OK, row
