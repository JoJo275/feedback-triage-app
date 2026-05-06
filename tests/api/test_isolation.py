"""Cross-tenant isolation canary (PR 1.5 / v2.0-alpha).

Every workspace-scoped route depends on
:func:`feedback_triage.tenancy.context.get_current_workspace`. The
contract — see ``docs/project/spec/v2/multi-tenancy.md`` — Tenant-
isolation invariants — is:

- A signed-in user who is **not** a member of the requested workspace
  always gets ``404 Not Found`` (with ``code=not_found``), **never**
  ``403``. Returning ``403`` would leak the existence of the slug.
- A response body for a cross-tenant request must never echo any row
  id from the other workspace.

This file ships the **initial six** canary cases. Three of them
(submitters, tags, notes) are placeholders skipped until PR 2.1
adds those tables; the remaining three (feedback_item, memberships,
invitations) exercise the dependency directly today. New cases are
appended as PR 1.8 and PR 2.x add tenant-scoped tables.

The dependency is exercised through a minimal ad-hoc FastAPI app
mounted in :func:`_make_test_app` rather than the real auth/feedback
routes (which do not exist until PR 1.7+). Once those routes ship,
the same invariant is also covered end-to-end by their flow tests;
this canary stays as the single-purpose regression guard.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from feedback_triage.auth import sessions as auth_sessions
from feedback_triage.auth.cookies import (
    SESSION_COOKIE_NAME,
    set_session_cookie,
)
from feedback_triage.auth.hashing import hash_password
from feedback_triage.config import Settings
from feedback_triage.database import SessionLocal, engine
from feedback_triage.enums import UserRole, WorkspaceRole
from feedback_triage.errors import register_exception_handlers
from feedback_triage.models import (
    FeedbackNote,
    Submitter,
    Tag,
    User,
    Workspace,
    WorkspaceInvitation,
    WorkspaceMembership,
)
from feedback_triage.tenancy import (
    WorkspaceContext,
    WorkspaceContextDep,
)

# ---------------------------------------------------------------------------
# Fixture infrastructure
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _Tenant:
    """Bundle a workspace + its sole owning user + raw session token."""

    user_id: uuid.UUID
    workspace_id: uuid.UUID
    workspace_slug: str
    raw_token: str


@pytest.fixture
def truncate_tenancy_tables() -> Iterator[None]:
    """Wipe every table the canary touches.

    ``CASCADE`` follows FKs into ``sessions`` etc. The
    ``feedback_item`` row added in :func:`_seed_feedback_for` is also
    cleared so a re-run of the suite starts clean.
    """
    with engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE TABLE "
                "feedback_item, "
                "users, workspaces, workspace_memberships, "
                "workspace_invitations, sessions, "
                "email_verification_tokens, password_reset_tokens, "
                "auth_rate_limits, email_log, "
                "submitters, tags, feedback_tags, feedback_notes "
                "RESTART IDENTITY CASCADE"
            )
        )
    yield


def _make_tenant(*, slug: str, email_local: str) -> _Tenant:
    """Create a user, a workspace they own, a membership, and a session."""
    db = SessionLocal()
    try:
        user = User(
            email=f"{email_local}@example.com",
            password_hash=hash_password("not-used-in-canary"),
            is_verified=True,
            role=UserRole.TEAM_MEMBER,
        )
        db.add(user)
        db.flush()
        assert user.id is not None

        workspace = Workspace(slug=slug, name=slug.capitalize(), owner_id=user.id)
        db.add(workspace)
        db.flush()
        assert workspace.id is not None

        db.add(
            WorkspaceMembership(
                workspace_id=workspace.id,
                user_id=user.id,
                role=WorkspaceRole.OWNER,
            ),
        )

        issued = auth_sessions.create_session(db, user_id=user.id)
        db.commit()
        return _Tenant(
            user_id=user.id,
            workspace_id=workspace.id,
            workspace_slug=workspace.slug,
            raw_token=issued.raw_token,
        )
    finally:
        db.close()


def _make_test_app() -> FastAPI:
    """Build a tiny app that exercises ``get_current_workspace``.

    Two routes:

    - ``GET /probe/header`` — slug carried by ``X-Workspace-Slug``.
    - ``GET /probe/{slug}`` — slug carried by the URL path.

    Both return the resolved workspace id and slug so a test can
    assert on the value (or its absence on a 404).
    """
    app = FastAPI()
    register_exception_handlers(app)

    def _payload(ctx: WorkspaceContext) -> dict[str, str]:
        return {"workspace_id": str(ctx.id), "slug": ctx.slug}

    @app.get("/probe/header")
    def probe_header(ctx: WorkspaceContextDep) -> dict[str, str]:
        return _payload(ctx)

    @app.get("/probe/{slug}")
    def probe_path(ctx: WorkspaceContextDep) -> dict[str, str]:
        return _payload(ctx)

    return app


@pytest.fixture
def settings() -> Settings:
    return Settings(_env_file=None, feature_auth=True)  # type: ignore[call-arg]


@pytest.fixture
def two_tenants(truncate_tenancy_tables: None) -> tuple[_Tenant, _Tenant]:
    """Two unrelated workspaces, owned by two unrelated users."""
    t1 = _make_tenant(slug="acme", email_local="alice")
    t2 = _make_tenant(slug="globex", email_local="bob")
    return t1, t2


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    app = _make_test_app()
    with TestClient(app) as c:
        yield c


def _set_cookie(client: TestClient, raw_token: str) -> None:
    """Attach ``raw_token`` as the session cookie on ``client``.

    ``TestClient.cookies`` is a ``httpx.Cookies`` jar; setting the
    same key as :func:`set_session_cookie` would write keeps the test
    aligned with what the production browser sees.
    """
    client.cookies.set(SESSION_COOKIE_NAME, raw_token)
    # Reference ``set_session_cookie`` so a future rename of the cookie
    # writer also forces a rename here. Cheap and self-documenting.
    _ = set_session_cookie


# ---------------------------------------------------------------------------
# Canary case 1 — feedback (the v1.0 table, retrofitted with workspace_id)
# ---------------------------------------------------------------------------


def _seed_feedback_for(workspace_id: uuid.UUID) -> int:
    """Insert one ``feedback_item`` row tagged to ``workspace_id``.

    Migration A added ``workspace_id`` as nullable; PR 2.1 will flip
    it to ``NOT NULL``. We populate it here so the row is unambiguously
    associated with one tenant.
    """
    db = SessionLocal()
    try:
        result = db.execute(
            text(
                "INSERT INTO feedback_item "
                "(title, description, source, pain_level, status, workspace_id) "
                "VALUES (:title, :description, 'email', 3, 'new', :wid) "
                "RETURNING id"
            ),
            {
                "title": f"canary-{workspace_id}",
                "description": "tenant-isolation canary row",
                "wid": str(workspace_id),
            },
        )
        row_id = int(result.scalar_one())
        db.commit()
        return row_id
    finally:
        db.close()


def test_feedback_cross_tenant_returns_404(
    client: TestClient,
    two_tenants: tuple[_Tenant, _Tenant],
) -> None:
    """User in tenant A asking for tenant B's slug → 404, not 403.

    Also asserts the response body never echoes tenant B's workspace
    id, which is the leak path the spec explicitly forbids.
    """
    t1, t2 = two_tenants
    _seed_feedback_for(t2.workspace_id)
    _set_cookie(client, t1.raw_token)

    # Path-encoded slug
    resp = client.get(f"/probe/{t2.workspace_slug}")
    assert resp.status_code == 404, (
        f"cross-tenant must 404 (never 403); got {resp.status_code}"
    )
    body = resp.text
    assert str(t2.workspace_id) not in body
    assert t2.workspace_slug not in body or "not_found" in body

    # Header-encoded slug
    resp = client.get("/probe/header", headers={"X-Workspace-Slug": t2.workspace_slug})
    assert resp.status_code == 404
    assert str(t2.workspace_id) not in resp.text


def test_feedback_same_tenant_returns_200(
    client: TestClient,
    two_tenants: tuple[_Tenant, _Tenant],
) -> None:
    """Positive control: user in tenant A reading tenant A succeeds.

    Without this, a `get_current_workspace` that always raises 404
    would silently pass the negative cases above. This is the
    "the canary actually catches the regression" guard called out in
    the PR 1.5 DoD.
    """
    t1, _t2 = two_tenants
    _set_cookie(client, t1.raw_token)

    resp = client.get(f"/probe/{t1.workspace_slug}")
    assert resp.status_code == 200, resp.text
    assert resp.json() == {
        "workspace_id": str(t1.workspace_id),
        "slug": t1.workspace_slug,
    }


# ---------------------------------------------------------------------------
# Canary case 2 — workspace_memberships
# ---------------------------------------------------------------------------


def test_memberships_cross_tenant_returns_404(
    client: TestClient,
    two_tenants: tuple[_Tenant, _Tenant],
) -> None:
    """User in tenant A asking for tenant B's slug → 404.

    Memberships are addressed under ``/api/v1/workspaces/{slug}/members``
    in PR 1.8; the cross-tenant guard is the same `get_current_workspace`
    dependency. Asserting it here means the 1.8 routes inherit the
    invariant for free.
    """
    t1, t2 = two_tenants
    _set_cookie(client, t1.raw_token)

    resp = client.get(f"/probe/{t2.workspace_slug}")
    assert resp.status_code == 404
    assert str(t2.workspace_id) not in resp.text


# ---------------------------------------------------------------------------
# Canary case 3 — workspace_invitations
# ---------------------------------------------------------------------------


def _seed_invitation_for(
    workspace_id: uuid.UUID, invited_by_id: uuid.UUID
) -> uuid.UUID:
    """Insert one open invitation row tagged to ``workspace_id``."""
    db = SessionLocal()
    try:
        invite = WorkspaceInvitation(
            workspace_id=workspace_id,
            email="invitee@example.com",
            role=WorkspaceRole.TEAM_MEMBER,
            token_hash=uuid.uuid4().hex,  # canary-only; not a real token
            invited_by_id=invited_by_id,
            expires_at=datetime.now(tz=UTC) + timedelta(days=7),
        )
        db.add(invite)
        db.commit()
        assert invite.id is not None
        return invite.id
    finally:
        db.close()


def test_invitations_cross_tenant_returns_404(
    client: TestClient,
    two_tenants: tuple[_Tenant, _Tenant],
) -> None:
    """User in tenant A asking for tenant B's slug → 404.

    Same shape as the memberships case; included as its own test so a
    future regression in invitation handling fails with a precise
    name.
    """
    t1, t2 = two_tenants
    invitation_id = _seed_invitation_for(t2.workspace_id, t2.user_id)
    _set_cookie(client, t1.raw_token)

    resp = client.get(
        "/probe/header",
        headers={"X-Workspace-Slug": t2.workspace_slug},
    )
    assert resp.status_code == 404
    assert str(invitation_id) not in resp.text
    assert str(t2.workspace_id) not in resp.text


# ---------------------------------------------------------------------------
# Canary cases 4-6 — submitters / tags / notes (PR 2.1)
# ---------------------------------------------------------------------------
# These tables landed in PR 2.1 (Migration B / B2). The canary asserts
# the same invariant as cases 1-3: a signed-in user asking for a slug
# they're not a member of gets ``404`` and the response body never
# leaks any row id from the other workspace.


def _seed_submitter_for(workspace_id: uuid.UUID) -> uuid.UUID:
    """Insert one ``submitter`` row tagged to ``workspace_id``."""
    submitter = Submitter(
        workspace_id=workspace_id,
        email=f"submitter-{uuid.uuid4().hex[:8]}@example.com",
        name="Canary Submitter",
    )
    db = SessionLocal()
    try:
        db.add(submitter)
        db.commit()
        assert submitter.id is not None
        return submitter.id
    finally:
        db.close()


def _seed_tag_for(workspace_id: uuid.UUID) -> uuid.UUID:
    """Insert one ``tag`` row tagged to ``workspace_id``."""
    slug = f"canary-{uuid.uuid4().hex[:6]}"
    tag = Tag(workspace_id=workspace_id, name="Canary", slug=slug)
    db = SessionLocal()
    try:
        db.add(tag)
        db.commit()
        assert tag.id is not None
        return tag.id
    finally:
        db.close()


def _seed_note_for(workspace_id: uuid.UUID, author_user_id: uuid.UUID) -> uuid.UUID:
    """Insert one ``feedback_notes`` row tied to a feedback item in
    ``workspace_id`` and authored by ``author_user_id``."""
    feedback_id = _seed_feedback_for(workspace_id)
    note = FeedbackNote(
        feedback_id=feedback_id,
        author_user_id=author_user_id,
        body="canary note",
    )
    db = SessionLocal()
    try:
        db.add(note)
        db.commit()
        assert note.id is not None
        return note.id
    finally:
        db.close()


def test_submitters_cross_tenant_returns_404(
    client: TestClient,
    two_tenants: tuple[_Tenant, _Tenant],
) -> None:
    """User in tenant A asking for tenant B's slug → 404 with no leak."""
    t1, t2 = two_tenants
    submitter_id = _seed_submitter_for(t2.workspace_id)
    _set_cookie(client, t1.raw_token)

    resp = client.get(f"/probe/{t2.workspace_slug}")
    assert resp.status_code == 404
    assert str(submitter_id) not in resp.text
    assert str(t2.workspace_id) not in resp.text


def test_tags_cross_tenant_returns_404(
    client: TestClient,
    two_tenants: tuple[_Tenant, _Tenant],
) -> None:
    """User in tenant A asking for tenant B's slug → 404 with no leak."""
    t1, t2 = two_tenants
    tag_id = _seed_tag_for(t2.workspace_id)
    _set_cookie(client, t1.raw_token)

    resp = client.get(f"/probe/{t2.workspace_slug}")
    assert resp.status_code == 404
    assert str(tag_id) not in resp.text
    assert str(t2.workspace_id) not in resp.text


def test_notes_cross_tenant_returns_404(
    client: TestClient,
    two_tenants: tuple[_Tenant, _Tenant],
) -> None:
    """User in tenant A asking for tenant B's slug → 404 with no leak."""
    t1, t2 = two_tenants
    note_id = _seed_note_for(t2.workspace_id, t2.user_id)
    _set_cookie(client, t1.raw_token)

    resp = client.get(f"/probe/{t2.workspace_slug}")
    assert resp.status_code == 404
    assert str(note_id) not in resp.text
    assert str(t2.workspace_id) not in resp.text


# ---------------------------------------------------------------------------
# Anonymous + missing-slug guard
# ---------------------------------------------------------------------------


def test_anonymous_caller_gets_401_not_404(
    client: TestClient,
    two_tenants: tuple[_Tenant, _Tenant],
) -> None:
    """No session cookie → 401 from ``current_user_required``.

    The 404-for-cross-tenant rule applies *after* we know who the
    caller is. An unauthenticated probe must not be told whether the
    slug exists, but it also must not look like a tenant 404 in the
    logs — keeping the 401 here is what makes the 404 cases above
    meaningful.
    """
    _t1, t2 = two_tenants
    resp = client.get(f"/probe/{t2.workspace_slug}")
    assert resp.status_code == 401


def test_missing_slug_returns_404(
    client: TestClient,
    two_tenants: tuple[_Tenant, _Tenant],
) -> None:
    """Authenticated request with no slug at all → 404, not 500.

    Catches the "we forgot to pass a slug" misbuild at the dep layer
    rather than letting it bubble to a 500.
    """
    t1, _t2 = two_tenants
    _set_cookie(client, t1.raw_token)
    resp = client.get("/probe/header")
    assert resp.status_code == 404
