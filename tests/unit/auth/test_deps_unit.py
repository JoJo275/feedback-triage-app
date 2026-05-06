"""Unit tests for :mod:`feedback_triage.auth.deps` (codecov backfill, PR 2.2).

Targets the role-gate factory and the ``current_user_required`` 503
branch — both lines that the auth flow tests don't reach because they
either depend on a real session or always run with ``feature_auth=True``.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi import HTTPException, status

from feedback_triage.auth.deps import current_user_required, require_role
from feedback_triage.config import Settings
from feedback_triage.enums import UserRole
from feedback_triage.models import User


def _user(role: UserRole) -> User:
    """Build an in-memory :class:`User` (never persisted)."""
    return User(
        id=uuid.uuid4(),
        email=f"{role.value}@example.com",
        password_hash="!disabled!",
        is_verified=True,
        role=role,
    )


def test_require_role_allows_admin() -> None:
    dep = require_role(UserRole.ADMIN)
    user = _user(UserRole.ADMIN)
    assert dep(user) is user


def test_require_role_allows_member_in_allowlist() -> None:
    dep = require_role(UserRole.ADMIN, UserRole.TEAM_MEMBER)
    user = _user(UserRole.TEAM_MEMBER)
    assert dep(user) is user


def test_require_role_rejects_role_outside_allowlist() -> None:
    dep = require_role(UserRole.ADMIN)
    user = _user(UserRole.TEAM_MEMBER)
    with pytest.raises(HTTPException) as exc:
        dep(user)
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN


def test_require_role_accepts_string_values() -> None:
    """The factory coerces plain strings to :class:`UserRole` for config use."""
    dep = require_role("admin")
    user = _user(UserRole.ADMIN)
    assert dep(user) is user


def test_current_user_required_returns_503_when_feature_auth_off() -> None:
    """When ``FEATURE_AUTH=false`` even a logged-in caller gets 503."""
    settings = Settings(feature_auth=False, _env_file=None)  # type: ignore[call-arg]
    with pytest.raises(HTTPException) as exc:
        current_user_required(user=None, settings=settings)
    assert exc.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


def test_current_user_required_returns_401_when_anonymous() -> None:
    settings = Settings(feature_auth=True, _env_file=None)  # type: ignore[call-arg]
    with pytest.raises(HTTPException) as exc:
        current_user_required(user=None, settings=settings)
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_current_user_required_returns_user_when_present() -> None:
    settings = Settings(feature_auth=True, _env_file=None)  # type: ignore[call-arg]
    user = _user(UserRole.TEAM_MEMBER)
    assert current_user_required(user=user, settings=settings) is user
