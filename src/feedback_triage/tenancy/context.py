"""`WorkspaceContext` dependency: resolve `<slug>` to a tenant boundary.

Every workspace-scoped route depends on :func:`get_current_workspace`,
which:

1. Reads the slug from the route's ``{slug}`` path parameter, falling
   back to the ``X-Workspace-Slug`` header on JSON-API routes that do
   not encode the slug in the URL (see
   ``docs/project/spec/v2/multi-tenancy.md`` — Workspace addressing
   and ``docs/project/spec/v2/api.md`` — header semantics).
2. Looks up the :class:`Workspace` row by slug.
3. Confirms the requesting :class:`User` either has a
   :class:`WorkspaceMembership` for that workspace **or** holds the
   site-wide ``admin`` role (per
   ``docs/project/spec/v2/multi-tenancy.md`` — Admin posture).
4. Returns a frozen :class:`WorkspaceContext` carrying the workspace
   id + slug, the caller's effective role, and the read-only flag
   that demo accounts trip on every write route.

**Cross-tenant isolation rule (ADR 060, ``multi-tenancy.md`` -
Tenant-isolation invariants):** any failure mode in steps 1-3
returns ``404 Not Found`` with ``code=not_found``. We never return
``403`` for a missing membership, because that would leak the
existence of another workspace's slug. The canary at
``tests/api/test_isolation.py`` asserts this explicitly.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Annotated, Literal

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session as DbSession
from sqlmodel import col, select

from feedback_triage.auth.deps import CurrentUserDep
from feedback_triage.database import get_db
from feedback_triage.enums import UserRole, WorkspaceRole
from feedback_triage.models import Workspace, WorkspaceMembership

DbDep = Annotated[DbSession, Depends(get_db)]
# ``Annotated[..., Header(...)]`` forbids ``default=...`` inside the
# FieldInfo; the per-parameter ``= None`` on the route signature below
# is what makes the header optional.
WorkspaceSlugHeaderDep = Annotated[
    str | None,
    Header(alias="X-Workspace-Slug"),
]


@dataclass(frozen=True, slots=True)
class WorkspaceContext:
    """Per-request tenant boundary.

    `id` and `slug` identify the workspace; `role` is the caller's
    effective role within it (the literal string ``"admin"`` for
    site-wide admins, who do not need a membership row); `is_read_only`
    is `True` iff the caller is a `demo` user, which the
    :func:`feedback_triage.tenancy.policies.require_writable` policy
    consumes.
    """

    id: uuid.UUID
    slug: str
    role: WorkspaceRole | Literal["admin"]
    is_read_only: bool


def _not_found() -> HTTPException:
    """Build the canonical cross-tenant 404.

    Centralised so the response shape (`code=not_found`) cannot drift
    between the slug-missing, slug-unknown, and not-a-member branches.
    """
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "not_found", "message": "Workspace not found."},
    )


def _resolve_slug(request: Request, header_slug: str | None) -> str:
    """Pick the slug from the URL path, falling back to the header.

    Path param wins: dashboard pages and public routes always carry
    `/w/<slug>/...`, and a path-vs-header mismatch on those routes is
    almost certainly a misbuilt `fetch` call rather than a deliberate
    cross-tenant probe.
    """
    path_slug = request.path_params.get("slug")
    slug = path_slug or header_slug
    if not slug:
        raise _not_found()
    return slug


def get_current_workspace(
    request: Request,
    user: CurrentUserDep,
    db: DbDep,
    header_slug: WorkspaceSlugHeaderDep = None,
) -> WorkspaceContext:
    """Resolve `<slug>` + the current user to a `WorkspaceContext`.

    Raises a `404` (never a `403`) on every failure mode — see the
    module docstring and ``tests/api/test_isolation.py``.
    """
    slug = _resolve_slug(request, header_slug)
    workspace = db.execute(
        select(Workspace).where(col(Workspace.slug) == slug),
    ).scalar_one_or_none()
    if workspace is None or workspace.id is None:
        raise _not_found()

    is_admin = user.role == UserRole.ADMIN
    if is_admin:
        # Admins still scope to the requested slug; they don't see
        # cross-workspace data merged. Membership lookup skipped on
        # purpose so an admin can switch into any workspace without
        # being added as a member first (multi-tenancy.md — Admin
        # posture).
        return WorkspaceContext(
            id=workspace.id,
            slug=workspace.slug,
            role="admin",
            is_read_only=False,
        )

    membership = db.execute(
        select(WorkspaceMembership)
        .where(col(WorkspaceMembership.workspace_id) == workspace.id)
        .where(col(WorkspaceMembership.user_id) == user.id),
    ).scalar_one_or_none()
    if membership is None:
        # Cross-tenant probe: caller is signed in but is not a member
        # of this workspace. Return 404 — never 403 — so the response
        # cannot be used to enumerate workspace slugs.
        raise _not_found()

    return WorkspaceContext(
        id=workspace.id,
        slug=workspace.slug,
        role=membership.role,
        is_read_only=user.role == UserRole.DEMO,
    )


WorkspaceContextDep = Annotated[WorkspaceContext, Depends(get_current_workspace)]


__all__ = [
    "WorkspaceContext",
    "WorkspaceContextDep",
    "get_current_workspace",
]
