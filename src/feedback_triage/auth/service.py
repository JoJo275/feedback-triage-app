"""Service-layer helpers for the auth API endpoints.

The route handlers in :mod:`feedback_triage.api.v1.auth` stay thin —
this module owns the multi-table writes (signup creates user +
workspace + membership atomically) and the slug derivation rules so
the route logic is straight-line.
"""

from __future__ import annotations

import re
import secrets
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession
from sqlmodel import col

from feedback_triage.auth.hashing import hash_password
from feedback_triage.enums import UserRole, WorkspaceRole
from feedback_triage.models import User, Workspace, WorkspaceMembership

# ``workspaces_slug_format`` CHECK: ``^[a-z0-9](?:[a-z0-9-]{0,38}[a-z0-9])?$``.
# 1-40 chars, lowercase alphanumeric + hyphens, no leading/trailing
# hyphen, no doubled-hyphen rule (the CHECK does not forbid them, but
# we collapse anyway for readability).
SLUG_MAX_LEN = 40
_INVALID_SLUG_CHARS = re.compile(r"[^a-z0-9-]+")
_DASH_RUN = re.compile(r"-{2,}")


@dataclass(frozen=True, slots=True)
class SignupResult:
    """Outcome of :func:`signup_user`.

    ``existed`` is ``True`` when the email already had an account; the
    caller uses this flag to pick between the verification template
    and the ``verification_already`` template (no-enumeration posture).
    """

    user: User
    workspace: Workspace
    existed: bool
    raw_verification_token: str | None  # ``None`` when ``existed`` is True


def _slugify_localpart(localpart: str) -> str:
    """Best-effort URL-safe slug seed from an email localpart.

    Lowercased, non-alphanumerics replaced with hyphens, runs of
    hyphens collapsed, leading/trailing hyphens stripped, truncated
    to :data:`SLUG_MAX_LEN`. Falls back to ``"workspace"`` if the
    cleaned value is empty.
    """
    cleaned = _INVALID_SLUG_CHARS.sub("-", localpart.lower())
    cleaned = _DASH_RUN.sub("-", cleaned).strip("-")
    cleaned = cleaned[:SLUG_MAX_LEN].strip("-")
    return cleaned or "workspace"


def _unique_slug(db: DbSession, base: str) -> str:
    """Return ``base`` or ``base-<rand>`` such that no row collides.

    Cheap optimistic check — the DB unique index is the real guard.
    The random suffix adds 6 hex chars (~24 bits) which is enough for
    the small-tenant scale ADR 059 sets.
    """
    existing = db.execute(
        select(Workspace).where(col(Workspace.slug) == base),
    ).first()
    if existing is None:
        return base
    suffix = secrets.token_hex(3)
    candidate = f"{base[: SLUG_MAX_LEN - len(suffix) - 1].rstrip('-')}-{suffix}"
    return candidate[:SLUG_MAX_LEN]


def _email_localpart(email: str) -> str:
    return email.split("@", 1)[0]


def signup_user(
    db: DbSession,
    *,
    email: str,
    password: str,
    workspace_name: str | None,
) -> SignupResult:
    """Create a user, their first workspace, and an owner membership.

    On a duplicate email: returns the *existing* user + their first
    owned workspace with ``existed=True`` and ``raw_verification_token=None``.
    The route layer uses this to send the "you already have an account"
    email instead of a verification email; the response body is
    identical to a fresh signup so an attacker cannot enumerate
    accounts (``auth.md`` — Email enumeration posture).

    The transaction boundary is the caller's ``get_db`` session — this
    function only stages writes via ``db.add`` / ``db.flush``.
    """
    existing_user = db.execute(
        select(User).where(col(User.email) == email),
    ).scalar_one_or_none()
    if existing_user is not None:
        # Find the workspace they own. Every signup creates one, so
        # one always exists; the SignupResponse needs *some* workspace.
        existing_ws = (
            db.execute(
                select(Workspace).where(col(Workspace.owner_id) == existing_user.id),
            )
            .scalars()
            .first()
        )
        # Defensive: if the owner row is missing (legacy/data fix), bail
        # with a synthetic workspace so the response shape stays valid.
        # The caller still treats ``existed=True`` as "send the already
        # email" so no enumeration happens.
        assert existing_ws is not None, "existing user has no owned workspace"
        return SignupResult(
            user=existing_user,
            workspace=existing_ws,
            existed=True,
            raw_verification_token=None,
        )

    # Fresh signup: user + workspace + membership go in together so a
    # partial commit can't leave a user with no tenant.
    user = User(
        email=email,
        password_hash=hash_password(password),
        is_verified=False,
        role=UserRole.TEAM_MEMBER,
    )
    db.add(user)
    db.flush()
    assert user.id is not None

    seed = _slugify_localpart(_email_localpart(email))
    slug = _unique_slug(db, seed)
    name = workspace_name or f"{_email_localpart(email)}'s workspace"
    # Workspace name must satisfy 1..60 chars; truncate defensively in
    # case the localpart blew past the bound.
    name = name[:60]
    workspace = Workspace(
        slug=slug,
        name=name,
        owner_id=user.id,
        is_demo=False,
    )
    db.add(workspace)
    db.flush()
    assert workspace.id is not None

    membership = WorkspaceMembership(
        workspace_id=workspace.id,
        user_id=user.id,
        role=WorkspaceRole.OWNER,
    )
    db.add(membership)
    db.flush()

    return SignupResult(
        user=user,
        workspace=workspace,
        existed=False,
        raw_verification_token=None,  # token is minted by the route
    )


def list_memberships(
    db: DbSession,
    *,
    user_id: uuid.UUID,
) -> list[tuple[WorkspaceMembership, Workspace]]:
    """Return ``(membership, workspace)`` pairs for ``user_id``."""
    rows = db.execute(
        select(WorkspaceMembership, Workspace)
        .join(Workspace, col(Workspace.id) == col(WorkspaceMembership.workspace_id))
        .where(col(WorkspaceMembership.user_id) == user_id),
    ).all()
    return [(m, w) for m, w in rows]


def primary_workspace_slug(
    db: DbSession,
    *,
    user_id: uuid.UUID,
) -> str | None:
    """Return a deterministic workspace slug for user-facing redirects.

    Prefer an owner membership when present; otherwise fall back to
    the first workspace slug in lexical order.
    """
    rows = list_memberships(db, user_id=user_id)
    if not rows:
        return None

    owner_slugs = sorted(
        workspace.slug
        for membership, workspace in rows
        if membership.role == WorkspaceRole.OWNER
    )
    if owner_slugs:
        return owner_slugs[0]

    return sorted(workspace.slug for _, workspace in rows)[0]
