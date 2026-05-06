"""``/api/v1/workspaces/*`` JSON endpoints.

Every route depends on ``current_user_required``; routes scoped to a
specific workspace also depend on
:class:`feedback_triage.tenancy.context.WorkspaceContextDep` (which
404s on cross-tenant probes — see ADR 060 and
``tests/api/test_isolation.py``).

Owner-only routes layer ``require_workspace_role(WorkspaceRole.OWNER)``
on top; site-wide ``admin`` users bypass that check via the
``WorkspaceContext.role == "admin"`` short-circuit in
:mod:`feedback_triage.tenancy.policies`.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from feedback_triage.api.v1._schemas import (
    MemberListResponse,
    MemberResponse,
    MemberUserResponse,
    WorkspaceUpdateRequest,
)
from feedback_triage.auth.deps import CurrentUserDep
from feedback_triage.auth.schemas import MembershipResponse, WorkspaceResponse
from feedback_triage.auth.service import list_memberships
from feedback_triage.database import get_db
from feedback_triage.enums import WorkspaceRole
from feedback_triage.models import Workspace
from feedback_triage.services import workspaces as ws_svc
from feedback_triage.tenancy import (
    WorkspaceContextDep,
    require_workspace_role,
)

router = APIRouter(prefix="/api/v1/workspaces", tags=["workspaces"])

DbDep = Annotated[DbSession, Depends(get_db)]


@router.get(
    "",
    response_model=list[MembershipResponse],
    summary="List the caller's workspaces",
)
def list_my_workspaces(
    user: CurrentUserDep,
    db: DbDep,
) -> list[MembershipResponse]:
    """Return one entry per workspace the caller has a membership for."""
    assert user.id is not None
    rows = list_memberships(db, user_id=user.id)
    return [
        MembershipResponse(
            workspace_id=ws.id,  # type: ignore[arg-type]
            workspace_slug=ws.slug,
            workspace_name=ws.name,
            role=m.role,
        )
        for m, ws in rows
    ]


@router.get(
    "/{slug}",
    response_model=WorkspaceResponse,
    summary="Get one workspace",
)
def get_workspace(
    ctx: WorkspaceContextDep,
    db: DbDep,
) -> WorkspaceResponse:
    """Return the workspace identified by ``slug`` in the URL."""
    workspace = db.get(Workspace, ctx.id)
    # ``WorkspaceContextDep`` already loaded the row to build the
    # context, but it does not hand it back. The re-fetch is cheap
    # (PK + the row is in the session identity map) and keeps the
    # response shape decoupled from the dep contract.
    assert workspace is not None, "context resolved to a missing workspace"
    return WorkspaceResponse.model_validate(workspace)


@router.patch(
    "/{slug}",
    response_model=WorkspaceResponse,
    summary="Update workspace settings (owner only)",
    dependencies=[Depends(require_workspace_role(WorkspaceRole.OWNER))],
)
def update_workspace(
    payload: WorkspaceUpdateRequest,
    ctx: WorkspaceContextDep,
    db: DbDep,
) -> WorkspaceResponse:
    """Update mutable workspace fields.

    ``slug`` is immutable (rejected by the request schema). Both
    ``name`` and ``public_submit_enabled`` are optional but the body
    must contain at least one of them.
    """
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="At least one field must be supplied.",
        )
    workspace = ws_svc.update_workspace_settings(
        db,
        workspace_id=ctx.id,
        changes=changes,
    )
    return WorkspaceResponse.model_validate(workspace)


# ---------------------------------------------------------------------------
# Members (sub-resource)
# ---------------------------------------------------------------------------
# The members listing is membership-gated; removal is owner-only. Both
# are mounted under ``/workspaces/{slug}/...`` so they share the same
# path-param-driven slug resolution as the workspace routes above.


@router.get(
    "/{slug}/members",
    response_model=MemberListResponse,
    summary="List members of a workspace",
)
def list_members(
    ctx: WorkspaceContextDep,
    db: DbDep,
) -> MemberListResponse:
    """Return every member of the workspace plus their role."""
    rows = ws_svc.list_workspace_members(db, workspace_id=ctx.id)
    items = [
        MemberResponse(
            user=MemberUserResponse.model_validate(row.user),
            role=row.membership.role,
            joined_at=row.membership.joined_at,
        )
        for row in rows
    ]
    return MemberListResponse(items=items, total=len(items))


@router.delete(
    "/{slug}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a member from a workspace (owner only)",
    dependencies=[Depends(require_workspace_role(WorkspaceRole.OWNER))],
)
def remove_member_route(
    user_id: str,
    ctx: WorkspaceContextDep,
    user: CurrentUserDep,
    db: DbDep,
) -> None:
    """Delete a membership row.

    - ``404`` if no such membership in this workspace.
    - ``409`` if the target is the last owner.
    - ``409`` if the caller tries to remove themselves (forces the
      caller to promote a co-owner first; documented in api.md).
    """
    try:
        target_id = uuid.UUID(user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found.",
        ) from exc

    if target_id == user.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot remove yourself; promote another owner first.",
        )

    try:
        deleted = ws_svc.remove_member(
            db,
            workspace_id=ctx.id,
            user_id=target_id,
        )
    except ws_svc.LastOwnerError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot remove the last owner.",
        ) from exc

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found.",
        )
