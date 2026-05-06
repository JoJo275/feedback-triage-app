"""``/api/v1/workspaces/{slug}/invitations`` and ``/api/v1/invitations`` endpoints.

Three sets of routes live here:

- Owner-only management of a workspace's invitations (create, list,
  revoke). These mount under ``/api/v1/workspaces/{slug}/invitations``
  so they share slug resolution and the membership/owner guard with
  :mod:`feedback_triage.api.v1.workspaces`.
- Authenticated acceptance of an invitation by the *invitee* (the
  token holder). This route mounts under ``/api/v1/invitations`` —
  it deliberately does not carry a workspace slug so a recipient can
  accept without knowing the slug ahead of time.

Email send pattern (ADR 061): :class:`EmailClient` writes its
``email_log`` row on its **own** ``SessionLocal``, so callers must
``db.commit()`` before invoking ``send`` — otherwise the FK from
``email_log.user_id`` to a not-yet-committed ``users`` row fails.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from feedback_triage.api.v1._schemas import (
    InvitationAcceptResponse,
    InvitationCreateRequest,
    InvitationListResponse,
    InvitationResponse,
)
from feedback_triage.auth import tokens as auth_tokens
from feedback_triage.auth.deps import CurrentUserDep
from feedback_triage.config import Settings, get_settings
from feedback_triage.database import get_db
from feedback_triage.email import get_email_client
from feedback_triage.enums import EmailPurpose, WorkspaceRole
from feedback_triage.models import Workspace
from feedback_triage.services import workspaces as ws_svc
from feedback_triage.tenancy import (
    WorkspaceContextDep,
    require_workspace_role,
)

# Two routers so the OpenAPI tag and prefix split cleanly.
ws_invitations_router = APIRouter(
    prefix="/api/v1/workspaces/{slug}/invitations",
    tags=["invitations"],
)
accept_router = APIRouter(prefix="/api/v1/invitations", tags=["invitations"])


DbDep = Annotated[DbSession, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]

_NOT_FOUND_DETAIL = "Invitation not found."


# ---------------------------------------------------------------------------
# Owner-only management
# ---------------------------------------------------------------------------


@ws_invitations_router.post(
    "",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite a user to the workspace (owner only)",
    dependencies=[Depends(require_workspace_role(WorkspaceRole.OWNER))],
)
def create_invitation(
    payload: InvitationCreateRequest,
    ctx: WorkspaceContextDep,
    user: CurrentUserDep,
    db: DbDep,
    settings: SettingsDep,
) -> InvitationResponse:
    """Mint an invitation token, persist the row, and send the email.

    Re-inviting an email that already has an open invitation revokes
    the prior row first ("revoke + mint" — the partial unique index
    ``workspace_invitations_open_idx`` enforces at-most-one-open).
    """
    assert user.id is not None
    # Revoke any pre-existing open invitation for the same email so we
    # never trip the partial unique index.
    ws_svc.revoke_open_invitations_for_email(
        db,
        workspace_id=ctx.id,
        email=payload.email,
    )
    issued = auth_tokens.mint_invitation_token(
        db,
        workspace_id=ctx.id,
        email=payload.email,
        invited_by_id=user.id,
        role=payload.role.value,
    )

    # Look up the just-inserted row by token_hash to return its id +
    # timestamps. The `mint_*` primitive flushes but does not return
    # the ORM row.
    invitation = next(
        (
            inv
            for inv in ws_svc.list_open_invitations(db, workspace_id=ctx.id)
            if inv.token_hash == issued.token_hash
        ),
        None,
    )
    assert invitation is not None, "minted invitation missing from open list"

    workspace = db.get(Workspace, ctx.id)
    assert workspace is not None

    # Commit BEFORE sending the email: EmailClient writes ``email_log``
    # on its own SessionLocal, so an in-flight transaction here is
    # invisible to it. Without this commit the user_id/workspace_id
    # FKs on ``email_log`` would fail (ADR 061 - Test strategy).
    db.commit()

    accept_url = f"{settings.app_base_url.rstrip('/')}/invitations/{issued.raw_token}"
    email_client = get_email_client()
    email_client.send(
        purpose=EmailPurpose.INVITATION,
        to=payload.email,
        context={
            "workspace_name": workspace.name,
            "inviter_name": user.email,
            "role": payload.role.value,
            "accept_url": accept_url,
            "expires_in_days": int(auth_tokens.INVITATION_TTL.total_seconds() // 86400),
        },
        workspace_id=ctx.id,
        user_id=user.id,
    )
    return InvitationResponse.model_validate(invitation)


@ws_invitations_router.get(
    "",
    response_model=InvitationListResponse,
    summary="List open invitations for a workspace (owner only)",
    dependencies=[Depends(require_workspace_role(WorkspaceRole.OWNER))],
)
def list_invitations(
    ctx: WorkspaceContextDep,
    db: DbDep,
) -> InvitationListResponse:
    """Return every not-yet-accepted, not-yet-revoked invitation."""
    rows = ws_svc.list_open_invitations(db, workspace_id=ctx.id)
    items = [InvitationResponse.model_validate(row) for row in rows]
    return InvitationListResponse(items=items, total=len(items))


@ws_invitations_router.delete(
    "/{invitation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke an open invitation (owner only)",
    dependencies=[Depends(require_workspace_role(WorkspaceRole.OWNER))],
)
def revoke_invitation_route(
    invitation_id: str,
    ctx: WorkspaceContextDep,
    db: DbDep,
) -> None:
    """Mark an invitation revoked.

    Cross-tenant probes are already 404'd by ``WorkspaceContextDep``;
    this handler additionally 404s if the id belongs to a *different*
    workspace's invitation, so an owner cannot probe other workspaces
    by feeding random ids into their own slug.
    """
    try:
        target_id = uuid.UUID(invitation_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_NOT_FOUND_DETAIL,
        ) from exc

    invitation = ws_svc.get_invitation(db, invitation_id=target_id)
    if invitation is None or invitation.workspace_id != ctx.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_NOT_FOUND_DETAIL,
        )

    if not ws_svc.revoke_invitation(db, invitation_id=target_id):
        # Already-accepted or already-revoked. Treat as 404 so the
        # response cannot be used to differentiate state transitions.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_NOT_FOUND_DETAIL,
        )


# ---------------------------------------------------------------------------
# Invitee-side acceptance
# ---------------------------------------------------------------------------


@accept_router.post(
    "/{token}/accept",
    response_model=InvitationAcceptResponse,
    summary="Accept a workspace invitation",
)
def accept_invitation(
    token: str,
    user: CurrentUserDep,
    db: DbDep,
) -> InvitationAcceptResponse:
    """Consume an invitation token; create the membership.

    All non-OK token states (unknown, expired, consumed, revoked) map
    to ``410 Gone`` per ``auth.md`` — Token TTLs.
    """
    assert user.id is not None
    status_, invitation = auth_tokens.consume_invitation_token(
        db,
        raw_token=token,
    )
    if status_ is not auth_tokens.TokenStatus.OK or invitation is None:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Invitation is no longer valid.",
        )

    ws_svc.add_membership(
        db,
        workspace_id=invitation.workspace_id,
        user_id=user.id,
        role=invitation.role,
    )

    workspace = db.get(Workspace, invitation.workspace_id)
    assert workspace is not None
    return InvitationAcceptResponse(
        workspace_id=workspace.id,  # type: ignore[arg-type]
        workspace_slug=workspace.slug,
        workspace_name=workspace.name,
        role=invitation.role,
    )
