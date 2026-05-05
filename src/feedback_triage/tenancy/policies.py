"""Workspace-role gates and demo read-only policy.

Two FastAPI-dependency factories live here:

- :func:`require_writable` — short, single-purpose: rejects any
  caller whose :class:`WorkspaceContext.is_read_only` is `True`.
  Mounted on every `POST` / `PATCH` / `DELETE` route in
  ``docs/project/spec/v2/api.md`` — *Demo users are read-only*.
- :func:`require_workspace_role` — factory returning a dep that
  rejects callers whose effective workspace role is not in the
  allow-list. Site-wide admins (``ctx.role == "admin"``) always
  pass, per ``docs/project/spec/v2/multi-tenancy.md`` — Admin posture.

Both raise `403` when the user *is* a member of the workspace but
lacks the required privilege. That is **not** a tenant-leak: the
caller already proved membership in
:func:`feedback_triage.tenancy.context.get_current_workspace`, so a
`403` here only confirms what the cookie + slug already established.
The cross-tenant `404`-vs-`403` invariant lives one layer up in the
context resolver (see
``tests/api/test_isolation.py``).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Literal

from fastapi import HTTPException, status

from feedback_triage.enums import WorkspaceRole
from feedback_triage.tenancy.context import (
    WorkspaceContext,
    WorkspaceContextDep,
)


def require_writable(ctx: WorkspaceContextDep) -> WorkspaceContext:
    """Reject the demo user on any write route.

    Wraps :func:`get_current_workspace` and re-emits the resolved
    context unchanged for normal callers. Demo users (``role='demo'``
    on `users`, surfaced as ``ctx.is_read_only=True``) get
    ``403 Forbidden`` with the documented ``code=demo_read_only``
    error code from
    ``docs/project/spec/v2/error-catalog.md``.
    """
    if ctx.is_read_only:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "demo_read_only",
                "message": ("Demo workspaces are read-only. Sign up to make changes."),
            },
        )
    return ctx


def _coerce_roles(
    roles: Iterable[WorkspaceRole | str],
) -> Iterable[WorkspaceRole]:
    """Accept either ``WorkspaceRole`` members or their string values.

    Mirror of :func:`feedback_triage.auth.deps._coerce_roles` so a
    role list pulled from config is readable at the call site.
    """
    for r in roles:
        yield r if isinstance(r, WorkspaceRole) else WorkspaceRole(r)


def require_workspace_role(
    *allowed: WorkspaceRole | str,
) -> Callable[[WorkspaceContext], WorkspaceContext]:
    """Return a dependency that 403s callers outside ``allowed``.

    Usage::

        @router.delete(
            "/api/v1/workspaces/{slug}/members/{user_id}",
            dependencies=[Depends(require_workspace_role(WorkspaceRole.OWNER))],
        )

    Site-wide admins (``ctx.role == "admin"``) always pass — see
    ``docs/project/spec/v2/multi-tenancy.md`` — Admin posture.
    """
    allowed_set: frozenset[WorkspaceRole] = frozenset(_coerce_roles(allowed))

    def _dep(ctx: WorkspaceContextDep) -> WorkspaceContext:
        role: WorkspaceRole | Literal["admin"] = ctx.role
        if role == "admin":
            return ctx
        if role not in allowed_set:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "forbidden",
                    "message": "Insufficient workspace privileges.",
                },
            )
        return ctx

    return _dep


__all__ = [
    "require_workspace_role",
    "require_writable",
]
