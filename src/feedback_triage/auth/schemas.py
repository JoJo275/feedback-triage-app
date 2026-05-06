"""Pydantic schemas for the ``/api/v1/auth/*`` JSON surface.

Request bodies use ``extra='forbid'`` so unknown fields fail validation
loudly rather than silently being ignored. Response shapes mirror what
the spec calls out in ``docs/project/spec/v2/api.md`` — Auth.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from feedback_triage.enums import UserRole, WorkspaceRole

# Password length bounds — minimum is the bottom rung of NIST SP 800-63B
# Memorized Secret guidance; the upper bound exists so we don't burn
# server CPU hashing megabyte payloads.
MIN_PASSWORD_LEN = 12
MAX_PASSWORD_LEN = 128

# Workspace-name bounds match ``workspaces_name_len`` CHECK constraint.
MIN_WORKSPACE_NAME_LEN = 1
MAX_WORKSPACE_NAME_LEN = 60


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------


class SignupRequest(BaseModel):
    """``POST /api/v1/auth/signup`` body."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=MIN_PASSWORD_LEN, max_length=MAX_PASSWORD_LEN)
    workspace_name: str | None = Field(
        default=None,
        min_length=MIN_WORKSPACE_NAME_LEN,
        max_length=MAX_WORKSPACE_NAME_LEN,
    )


class LoginRequest(BaseModel):
    """``POST /api/v1/auth/login`` body."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1, max_length=MAX_PASSWORD_LEN)


class VerifyEmailRequest(BaseModel):
    """``POST /api/v1/auth/verify-email`` body."""

    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=1, max_length=512)


class ResendVerificationRequest(BaseModel):
    """``POST /api/v1/auth/resend-verification`` body.

    Either an ``email`` is provided (anonymous re-request) or the
    request is authenticated; the route handles both shapes.
    """

    model_config = ConfigDict(extra="forbid")

    email: EmailStr | None = None


class ForgotPasswordRequest(BaseModel):
    """``POST /api/v1/auth/forgot-password`` body."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """``POST /api/v1/auth/reset-password`` body."""

    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=1, max_length=512)
    new_password: str = Field(min_length=MIN_PASSWORD_LEN, max_length=MAX_PASSWORD_LEN)


class ChangePasswordRequest(BaseModel):
    """``POST /api/v1/auth/change-password`` body."""

    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(min_length=1, max_length=MAX_PASSWORD_LEN)
    new_password: str = Field(min_length=MIN_PASSWORD_LEN, max_length=MAX_PASSWORD_LEN)


# ---------------------------------------------------------------------------
# Response bodies
# ---------------------------------------------------------------------------


class UserResponse(BaseModel):
    """User shape returned by signup / login / me."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    is_verified: bool
    role: UserRole
    created_at: datetime


class WorkspaceResponse(BaseModel):
    """Workspace shape returned by signup."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    is_demo: bool
    created_at: datetime


class MembershipResponse(BaseModel):
    """One workspace the caller belongs to + their role."""

    model_config = ConfigDict(from_attributes=True)

    workspace_id: uuid.UUID
    workspace_slug: str
    workspace_name: str
    role: WorkspaceRole


class SignupResponse(BaseModel):
    """``POST /api/v1/auth/signup`` 201 body.

    The shape is identical for fresh and duplicate signups so the
    response cannot be used to enumerate accounts (``auth.md`` —
    Email enumeration posture).
    """

    user: UserResponse
    workspace: WorkspaceResponse


class LoginResponse(BaseModel):
    """``POST /api/v1/auth/login`` 200 body."""

    user: UserResponse
    memberships: list[MembershipResponse]


class MeResponse(BaseModel):
    """``GET /api/v1/auth/me`` 200 body."""

    user: UserResponse
    memberships: list[MembershipResponse]
