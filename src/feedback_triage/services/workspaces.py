"""Service-layer helpers for workspace, membership, and invitation writes.

The ``/api/v1/workspaces/...`` and ``/api/v1/invitations/...`` route
handlers stay thin and call into this module for anything that
touches more than one row.

The transaction boundary is the caller's ``get_db`` session — every
helper here only stages writes via ``db.add`` / ``db.execute`` and
relies on the request-scoped commit/rollback in ``get_db``.

Cross-tenant isolation (ADR 060): the route layer guards entry with
``WorkspaceContextDep`` and ``require_workspace_role``; helpers here
trust the workspace id passed in and never re-resolve the slug.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import update
from sqlalchemy.orm import Session as DbSession
from sqlmodel import col, select

from feedback_triage.enums import WorkspaceRole
from feedback_triage.models import (
    User,
    Workspace,
    WorkspaceInvitation,
    WorkspaceMembership,
)


def _now() -> datetime:
    return datetime.now(tz=UTC)


# ---------------------------------------------------------------------------
# Workspaces
# ---------------------------------------------------------------------------


def rename_workspace(
    db: DbSession,
    *,
    workspace_id: uuid.UUID,
    new_name: str,
) -> Workspace:
    """Update ``workspaces.name`` and return the refreshed row.

    The ``slug`` column is intentionally **not** mutable in v2.0
    (``glossary.md`` — Workspace addressing). The trigger
    ``workspaces_set_updated_at`` bumps ``updated_at`` for us.
    """
    workspace = db.get(Workspace, workspace_id)
    assert workspace is not None, "rename_workspace: id not in this tx"
    workspace.name = new_name
    db.add(workspace)
    db.flush()
    return workspace


def update_workspace_settings(
    db: DbSession,
    *,
    workspace_id: uuid.UUID,
    changes: dict[str, object],
) -> Workspace:
    """Apply a partial update to a workspace.

    ``changes`` is a pre-validated dict of column-name → new-value
    pairs. Callers must guarantee no immutable column (``slug``,
    ``id``, ``owner_id``) is included; the request schema in
    ``api/v1/_schemas.py`` enforces that today.
    """
    workspace = db.get(Workspace, workspace_id)
    assert workspace is not None, "update_workspace_settings: id not in this tx"
    for field, value in changes.items():
        setattr(workspace, field, value)
    db.add(workspace)
    db.flush()
    return workspace


# ---------------------------------------------------------------------------
# Memberships
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class MemberRow:
    """Joined ``(membership, user)`` pair for the members listing."""

    membership: WorkspaceMembership
    user: User


def list_workspace_members(
    db: DbSession,
    *,
    workspace_id: uuid.UUID,
) -> list[MemberRow]:
    """Return every membership for ``workspace_id`` joined with its user."""
    rows: Sequence[tuple[WorkspaceMembership, User]] = db.execute(
        select(WorkspaceMembership, User)
        .join(User, col(User.id) == col(WorkspaceMembership.user_id))
        .where(col(WorkspaceMembership.workspace_id) == workspace_id),
    ).all()  # type: ignore[assignment]
    return [MemberRow(membership=m, user=u) for m, u in rows]


def count_owners(db: DbSession, *, workspace_id: uuid.UUID) -> int:
    """Return how many ``OWNER``-role memberships the workspace has.

    Used by :func:`remove_member` to refuse the last-owner removal.
    """
    rows = db.execute(
        select(WorkspaceMembership).where(
            col(WorkspaceMembership.workspace_id) == workspace_id,
            col(WorkspaceMembership.role) == WorkspaceRole.OWNER,
        ),
    ).all()
    return len(rows)


def get_membership(
    db: DbSession,
    *,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
) -> WorkspaceMembership | None:
    """Return the membership row or ``None``."""
    return db.execute(
        select(WorkspaceMembership).where(
            col(WorkspaceMembership.workspace_id) == workspace_id,
            col(WorkspaceMembership.user_id) == user_id,
        ),
    ).scalar_one_or_none()


def remove_member(
    db: DbSession,
    *,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    """Delete a membership row.

    Returns ``True`` on success, ``False`` when there was no such
    membership. Refuses to remove the last remaining owner; the route
    layer maps that to ``409``.
    """
    membership = get_membership(db, workspace_id=workspace_id, user_id=user_id)
    if membership is None:
        return False
    if (
        membership.role == WorkspaceRole.OWNER
        and count_owners(db, workspace_id=workspace_id) <= 1
    ):
        raise LastOwnerError("cannot remove the last owner")
    db.delete(membership)
    db.flush()
    return True


class LastOwnerError(Exception):
    """Raised when :func:`remove_member` would orphan a workspace."""


# ---------------------------------------------------------------------------
# Invitations
# ---------------------------------------------------------------------------


def list_open_invitations(
    db: DbSession,
    *,
    workspace_id: uuid.UUID,
) -> list[WorkspaceInvitation]:
    """Return all not-yet-accepted, not-yet-revoked invitations.

    Mirrors the partial unique index ``workspace_invitations_open_idx``
    so a "list open" call shows exactly the rows that block a re-invite.
    """
    rows = db.execute(
        select(WorkspaceInvitation)
        .where(
            col(WorkspaceInvitation.workspace_id) == workspace_id,
            col(WorkspaceInvitation.accepted_at).is_(None),
            col(WorkspaceInvitation.revoked_at).is_(None),
        )
        .order_by(col(WorkspaceInvitation.created_at).desc()),
    ).scalars()
    return list(rows)


def get_invitation(
    db: DbSession,
    *,
    invitation_id: uuid.UUID,
) -> WorkspaceInvitation | None:
    """Fetch one invitation row by primary key."""
    return db.get(WorkspaceInvitation, invitation_id)


def revoke_open_invitations_for_email(
    db: DbSession,
    *,
    workspace_id: uuid.UUID,
    email: str,
) -> int:
    """Revoke any open invitation matching ``(workspace_id, email)``.

    Re-inviting the same email is "revoke + mint" — this helper is
    the *revoke* half. Returns how many rows it touched. The match is
    case-insensitive because ``email`` is stored as ``citext``.
    """
    when = _now()
    result = db.execute(
        update(WorkspaceInvitation)
        .where(
            col(WorkspaceInvitation.workspace_id) == workspace_id,
            col(WorkspaceInvitation.email) == email,
            col(WorkspaceInvitation.accepted_at).is_(None),
            col(WorkspaceInvitation.revoked_at).is_(None),
        )
        .values(revoked_at=when),
    )
    return int(result.rowcount or 0)  # type: ignore[attr-defined]


def revoke_invitation(
    db: DbSession,
    *,
    invitation_id: uuid.UUID,
) -> bool:
    """Mark one invitation revoked. Returns ``True`` on a state change.

    Idempotent: a second call on an already-revoked or already-accepted
    row returns ``False`` and the route maps that to ``404`` so the
    response cannot be used to enumerate invitation ids.
    """
    when = _now()
    result = db.execute(
        update(WorkspaceInvitation)
        .where(
            col(WorkspaceInvitation.id) == invitation_id,
            col(WorkspaceInvitation.accepted_at).is_(None),
            col(WorkspaceInvitation.revoked_at).is_(None),
        )
        .values(revoked_at=when),
    )
    return bool(result.rowcount)  # type: ignore[attr-defined]


def add_membership(
    db: DbSession,
    *,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    role: WorkspaceRole,
) -> WorkspaceMembership:
    """Insert a membership row, no-op if one already exists."""
    existing = get_membership(db, workspace_id=workspace_id, user_id=user_id)
    if existing is not None:
        return existing
    membership = WorkspaceMembership(
        workspace_id=workspace_id,
        user_id=user_id,
        role=role,
    )
    db.add(membership)
    db.flush()
    return membership
