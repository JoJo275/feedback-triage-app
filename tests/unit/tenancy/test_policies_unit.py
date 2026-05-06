"""Unit tests for :mod:`feedback_triage.tenancy.policies` (codecov backfill, PR 2.2).

Targets the ``require_writable`` demo gate and the
``require_workspace_role`` factory's allow / reject branches. The
v2 isolation canary covers cross-tenant 404; this file covers the
intra-tenant 403 paths.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi import HTTPException, status

from feedback_triage.enums import WorkspaceRole
from feedback_triage.tenancy.context import WorkspaceContext
from feedback_triage.tenancy.policies import (
    require_workspace_role,
    require_writable,
)


def _ctx(
    role: WorkspaceRole | str = WorkspaceRole.TEAM_MEMBER, *, demo: bool = False
) -> WorkspaceContext:
    return WorkspaceContext(
        id=uuid.uuid4(),
        slug="acme",
        role=role,  # type: ignore[arg-type]
        is_read_only=demo,
    )


def test_require_writable_allows_normal_user() -> None:
    ctx = _ctx()
    assert require_writable(ctx) is ctx


def test_require_writable_rejects_demo_user() -> None:
    ctx = _ctx(demo=True)
    with pytest.raises(HTTPException) as exc:
        require_writable(ctx)
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc.value.detail["code"] == "demo_read_only"  # type: ignore[index]


def test_require_workspace_role_allows_admin_bypass() -> None:
    """Site-wide admins (``ctx.role == 'admin'``) always pass."""
    dep = require_workspace_role(WorkspaceRole.OWNER)
    ctx = _ctx(role="admin")
    assert dep(ctx) is ctx


def test_require_workspace_role_allows_role_in_set() -> None:
    dep = require_workspace_role(WorkspaceRole.OWNER, WorkspaceRole.TEAM_MEMBER)
    ctx = _ctx(role=WorkspaceRole.TEAM_MEMBER)
    assert dep(ctx) is ctx


def test_require_workspace_role_rejects_role_outside_set() -> None:
    dep = require_workspace_role(WorkspaceRole.OWNER)
    ctx = _ctx(role=WorkspaceRole.TEAM_MEMBER)
    with pytest.raises(HTTPException) as exc:
        dep(ctx)
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc.value.detail["code"] == "forbidden"  # type: ignore[index]


def test_require_workspace_role_accepts_string_values() -> None:
    """The factory coerces plain strings into :class:`WorkspaceRole`."""
    dep = require_workspace_role("owner")
    ctx = _ctx(role=WorkspaceRole.OWNER)
    assert dep(ctx) is ctx
