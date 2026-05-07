"""Pydantic schemas for the v2.0 workspace / membership / invitation surfaces.

Co-located under ``api/v1/`` rather than the v1.0 flat
:mod:`feedback_triage.schemas` module (which owns the feedback shapes)
because these schemas are tightly coupled to the v2.0 routers and
shouldn't pollute the v1.0 import surface.

Reuses :class:`feedback_triage.auth.schemas.WorkspaceResponse` for
single-workspace reads and adds the rename / member-listing /
invitation-lifecycle shapes that PR 1.8 introduces.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from feedback_triage.auth.schemas import (
    MAX_WORKSPACE_NAME_LEN,
    MIN_WORKSPACE_NAME_LEN,
)
from feedback_triage.enums import UserRole, WorkspaceRole

# ---------------------------------------------------------------------------
# Workspaces
# ---------------------------------------------------------------------------


class WorkspaceUpdateRequest(BaseModel):
    """``PATCH /api/v1/workspaces/{slug}`` body.

    ``slug`` is intentionally absent: per the v2.0 glossary the slug is
    immutable. ``name`` and ``public_submit_enabled`` are both
    optional; at least one must be supplied (the route returns 422
    otherwise). Explicit JSON ``null`` is rejected for both fields
    because the underlying columns are ``NOT NULL`` -- omit a field
    to leave it unchanged instead.
    """

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(
        default=None,
        min_length=MIN_WORKSPACE_NAME_LEN,
        max_length=MAX_WORKSPACE_NAME_LEN,
    )
    public_submit_enabled: bool | None = None

    @field_validator("name", "public_submit_enabled")
    @classmethod
    def _reject_explicit_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("must not be null; omit the field to leave it unchanged")
        return value


# ---------------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------------


class MemberUserResponse(BaseModel):
    """User shape inside a member listing.

    A subset of :class:`feedback_triage.auth.schemas.UserResponse` — we
    deliberately drop ``is_verified`` because surfacing another
    workspace member's verification state would be a small information
    leak with no UI use case in v2.0.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    role: UserRole
    created_at: datetime


class MemberResponse(BaseModel):
    """One member of a workspace."""

    user: MemberUserResponse
    role: WorkspaceRole
    joined_at: datetime


class MemberListResponse(BaseModel):
    """``GET /api/v1/workspaces/{slug}/members`` 200 body."""

    items: list[MemberResponse]
    total: int


# ---------------------------------------------------------------------------
# Invitations
# ---------------------------------------------------------------------------


class InvitationCreateRequest(BaseModel):
    """``POST /api/v1/workspaces/{slug}/invitations`` body."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    role: WorkspaceRole = Field(default=WorkspaceRole.TEAM_MEMBER)


class InvitationResponse(BaseModel):
    """One workspace invitation row, sans ``token_hash``.

    The raw token is **only** delivered via email; the JSON surface
    never echoes it. An attacker with read access to invitation
    listings must not be able to accept the invite.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    email: str
    role: WorkspaceRole
    invited_by_id: uuid.UUID
    expires_at: datetime
    accepted_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime


class InvitationListResponse(BaseModel):
    """``GET /api/v1/workspaces/{slug}/invitations`` 200 body."""

    items: list[InvitationResponse]
    total: int


class InvitationAcceptResponse(BaseModel):
    """``POST /api/v1/invitations/{token}/accept`` 200 body."""

    workspace_id: uuid.UUID
    workspace_slug: str
    workspace_name: str
    role: WorkspaceRole
