"""Targeted unit tests for auth service helper branches."""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from typing import Any

from feedback_triage.auth import service as auth_service
from feedback_triage.database import SessionLocal
from feedback_triage.enums import UserRole, WorkspaceRole
from feedback_triage.models import User, Workspace


def test_unique_slug_appends_suffix_when_base_already_exists(
    truncate_auth_world: None,
) -> None:
    with SessionLocal() as db:
        user = User(
            email="slug-owner@example.com",
            password_hash="!disabled!",
            is_verified=True,
            role=UserRole.TEAM_MEMBER,
        )
        db.add(user)
        db.flush()
        assert user.id is not None

        db.add(
            Workspace(
                slug="team-space",
                name="Team Space",
                owner_id=user.id,
                is_demo=False,
            )
        )
        db.flush()

        candidate = auth_service._unique_slug(db, "team-space")

    assert candidate != "team-space"
    assert candidate.startswith("team-space-")
    assert len(candidate) <= auth_service.SLUG_MAX_LEN


def test_primary_workspace_slug_prefers_owner_membership(
    monkeypatch: Any,
) -> None:
    rows = [
        (
            SimpleNamespace(role=WorkspaceRole.TEAM_MEMBER),
            SimpleNamespace(slug="member-z"),
        ),
        (
            SimpleNamespace(role=WorkspaceRole.OWNER),
            SimpleNamespace(slug="owner-b"),
        ),
        (
            SimpleNamespace(role=WorkspaceRole.OWNER),
            SimpleNamespace(slug="owner-a"),
        ),
    ]

    monkeypatch.setattr(auth_service, "list_memberships", lambda db, user_id: rows)

    slug = auth_service.primary_workspace_slug(db=None, user_id=uuid.uuid4())
    assert slug == "owner-a"


def test_primary_workspace_slug_falls_back_to_lexical_membership_order(
    monkeypatch: Any,
) -> None:
    rows = [
        (
            SimpleNamespace(role=WorkspaceRole.TEAM_MEMBER),
            SimpleNamespace(slug="workspace-z"),
        ),
        (
            SimpleNamespace(role=WorkspaceRole.TEAM_MEMBER),
            SimpleNamespace(slug="workspace-a"),
        ),
    ]

    monkeypatch.setattr(auth_service, "list_memberships", lambda db, user_id: rows)

    slug = auth_service.primary_workspace_slug(db=None, user_id=uuid.uuid4())
    assert slug == "workspace-a"
