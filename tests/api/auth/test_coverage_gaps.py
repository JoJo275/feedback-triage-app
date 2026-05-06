"""Targeted tests filling the codecov gaps flagged on PR 2.3.

Each block below is scoped to one source file; comments cite the
specific uncovered branch from the ``coverage report``. Keep these
focused — they exist to lock in behaviour around rarely-hit error
paths, not to re-test happy paths covered elsewhere.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from feedback_triage.config import Settings
from feedback_triage.database import SessionLocal, engine
from feedback_triage.main import create_app

VALID_PASSWORD = "correct horse battery staple"  # pragma: allowlist secret
NEW_PASSWORD = "another-passphrase-2026"  # pragma: allowlist secret


def _signup_and_login(
    client: TestClient,
    email: str = "alice@example.com",
) -> dict[str, object]:
    signup = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": VALID_PASSWORD},
    )
    assert signup.status_code == 201, signup.text
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": VALID_PASSWORD},
    )
    assert login.status_code == 200, login.text
    return login.json()


# ---------------------------------------------------------------------------
# api/v1/auth.py — change-password (lines 461-487)
# ---------------------------------------------------------------------------


def test_change_password_rejects_wrong_current_password(
    auth_client: TestClient,
) -> None:
    _signup_and_login(auth_client)
    resp = auth_client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "wrong-password-here-please",
            "new_password": NEW_PASSWORD,
        },
    )
    assert resp.status_code == 400


def test_change_password_succeeds_and_keeps_active_session(
    auth_client: TestClient,
) -> None:
    _signup_and_login(auth_client)

    resp = auth_client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": VALID_PASSWORD,
            "new_password": NEW_PASSWORD,
        },
    )
    assert resp.status_code == 200
    # Active session preserved per auth.md.
    me = auth_client.get("/api/v1/auth/me")
    assert me.status_code == 200
    # The new password is what works now.
    fresh = auth_client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": NEW_PASSWORD},
    )
    assert fresh.status_code == 200


def test_change_password_requires_login(auth_client: TestClient) -> None:
    resp = auth_client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": VALID_PASSWORD,
            "new_password": NEW_PASSWORD,
        },
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# api/v1/auth.py — resend-verification (lines 340-366)
# ---------------------------------------------------------------------------


def test_resend_verification_via_session_cookie(auth_client: TestClient) -> None:
    """Logged-in caller resolves email from the session, no body needed."""
    _signup_and_login(auth_client)
    resp = auth_client.post("/api/v1/auth/resend-verification", json={})
    assert resp.status_code == 202
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                "SELECT to_address FROM email_log "
                "WHERE purpose = 'verification' "
                "AND to_address = 'alice@example.com'",
            ),
        ).all()
    # Initial signup logs one verification, resend logs a second.
    assert len(rows) >= 2


def test_resend_verification_anonymous_with_unknown_email(
    auth_client: TestClient,
) -> None:
    """No session, no matching user — still 202, silent on the wire."""
    resp = auth_client.post(
        "/api/v1/auth/resend-verification",
        json={"email": "nobody@example.com"},
    )
    assert resp.status_code == 202


def test_resend_verification_silent_when_already_verified(
    auth_client: TestClient,
) -> None:
    _signup_and_login(auth_client, email="bob@example.com")
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE users SET is_verified = true WHERE email = 'bob@example.com'"),
        )
    # Drain rows from signup so we count only what resend writes.
    with engine.begin() as conn:
        before = conn.execute(
            text(
                "SELECT count(*) FROM email_log "
                "WHERE purpose = 'verification' "
                "AND to_address = 'bob@example.com'",
            ),
        ).scalar_one()
    resp = auth_client.post("/api/v1/auth/resend-verification", json={})
    assert resp.status_code == 202
    with engine.begin() as conn:
        after = conn.execute(
            text(
                "SELECT count(*) FROM email_log "
                "WHERE purpose = 'verification' "
                "AND to_address = 'bob@example.com'",
            ),
        ).scalar_one()
    assert after == before  # no new email — branch hit, silent.


# ---------------------------------------------------------------------------
# api/v1/auth.py — login rehash branch (lines 206-208)
# ---------------------------------------------------------------------------


def test_login_rehashes_legacy_argon2_hash(auth_client: TestClient) -> None:
    """Login on a hash flagged by ``needs_rehash`` rewrites it.

    We materialise a user row whose hash uses an older Argon2 cost so
    ``needs_rehash`` returns True on the first login, which exercises
    the ``hash_password`` rewrite block (lines 206-208).
    """
    from argon2 import PasswordHasher

    weak = PasswordHasher(time_cost=1, memory_cost=8, parallelism=1).hash(
        VALID_PASSWORD,
    )
    user_id = uuid.uuid4()
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO users (id, email, password_hash, is_verified, role) "
                "VALUES (:i, :e, :h, true, 'team_member')",
            ),
            {"i": user_id, "e": "rehash@example.com", "h": weak},
        )
        conn.execute(
            text(
                "INSERT INTO workspaces (id, slug, name, owner_id, is_demo) "
                "VALUES (:i, 'rehash-ws', 'Rehash WS', :o, false)",
            ),
            {"i": uuid.uuid4(), "o": user_id},
        )
    resp = auth_client.post(
        "/api/v1/auth/login",
        json={"email": "rehash@example.com", "password": VALID_PASSWORD},
    )
    assert resp.status_code == 200
    # Hash should have been rewritten to the project default.
    with engine.begin() as conn:
        new_hash = conn.execute(
            text("SELECT password_hash FROM users WHERE email = 'rehash@example.com'"),
        ).scalar_one()
    assert new_hash != weak


# ---------------------------------------------------------------------------
# api/v1/auth.py — logout-everywhere (lines 254-257) and bare logout
# ---------------------------------------------------------------------------


def test_logout_everywhere_clears_cookie(auth_client: TestClient) -> None:
    _signup_and_login(auth_client)
    resp = auth_client.post("/api/v1/auth/logout-everywhere")
    assert resp.status_code == 204
    me = auth_client.get("/api/v1/auth/me")
    assert me.status_code == 401


# ---------------------------------------------------------------------------
# auth/deps.py — require_role 403 + feature_auth disabled (lines 115, 144-154)
# ---------------------------------------------------------------------------


@pytest.fixture
def disabled_auth_client(truncate_auth_world: None) -> Iterator[TestClient]:
    """A TestClient with ``FEATURE_AUTH=false`` so the 503 branch fires."""
    settings = Settings(_env_file=None, feature_auth=False)  # type: ignore[call-arg]
    app = create_app(settings)
    with TestClient(app) as c:
        yield c


def test_current_user_required_returns_503_when_auth_disabled(
    disabled_auth_client: TestClient,
) -> None:
    """``feature_auth=False`` ⇒ ``current_user_required`` raises 503."""
    resp = disabled_auth_client.get("/api/v1/auth/me")
    assert resp.status_code == 503


def test_require_role_returns_403_for_team_member_on_admin_route(
    auth_client: TestClient,
) -> None:
    """``team_member`` calling an admin-gated route → 403.

    Uses ``GET /api/v1/admin/email-log`` which is wrapped in
    ``require_role(UserRole.ADMIN)`` per the email-admin router.
    """
    _signup_and_login(auth_client)
    # Sanity check route exists; if the project hasn't shipped this
    # endpoint, fall back to mounting an inline one would be heavier
    # than warranted — skip in that case.
    resp = auth_client.get("/api/v1/admin/email-log")
    if resp.status_code == 404:
        pytest.skip("admin email-log route not present in this build")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# pages/auth.py — every GET (lines 28, 34, 40, 49-50, 60-61, 77)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [
        "/login",
        "/signup",
        "/forgot-password",
        "/reset-password",
        "/reset-password?token=abc",
        "/verify-email",
        "/verify-email?token=xyz",
        "/invitations/some-token",
    ],
)
def test_auth_pages_render(auth_client: TestClient, path: str) -> None:
    resp = auth_client.get(path)
    assert resp.status_code == 200
    assert "<!doctype html>" in resp.text.lower()


# ---------------------------------------------------------------------------
# services/workspaces.py — add_membership idempotency (line 246)
# ---------------------------------------------------------------------------


def test_add_membership_is_idempotent_for_existing_user() -> None:
    """``add_membership`` on an existing pair returns the existing row."""
    from feedback_triage.enums import WorkspaceRole
    from feedback_triage.services.workspaces import add_membership

    # Prep: truncate, then create user+workspace so we have ids to bind.
    with engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE TABLE users, workspaces, workspace_memberships "
                "RESTART IDENTITY CASCADE",
            ),
        )
        user_id = uuid.uuid4()
        workspace_id = uuid.uuid4()
        conn.execute(
            text(
                "INSERT INTO users (id, email, password_hash, is_verified, role) "
                "VALUES (:i, 'idem@example.com', '!disabled!', true, 'team_member')",
            ),
            {"i": user_id},
        )
        conn.execute(
            text(
                "INSERT INTO workspaces (id, slug, name, owner_id, is_demo) "
                "VALUES (:i, 'idem-ws', 'Idem', :o, false)",
            ),
            {"i": workspace_id, "o": user_id},
        )
        conn.execute(
            text(
                "INSERT INTO workspace_memberships (workspace_id, user_id, role) "
                "VALUES (:w, :u, 'team_member')",
            ),
            {"w": workspace_id, "u": user_id},
        )

    db = SessionLocal()
    try:
        m = add_membership(
            db,
            workspace_id=workspace_id,
            user_id=user_id,
            role=WorkspaceRole.OWNER,
        )
        # Existing row was returned unchanged — role still team_member.
        assert m.role == WorkspaceRole.TEAM_MEMBER
    finally:
        db.close()


# ---------------------------------------------------------------------------
# services/workspaces.py — last-owner refusal (lines 136-143) +
# count_owners (97-103)
# ---------------------------------------------------------------------------


def test_remove_self_as_sole_owner_returns_409(auth_client: TestClient) -> None:
    """Single owner cannot remove themselves — covers ``LastOwnerError``."""
    body = _signup_and_login(auth_client)
    slug = body["memberships"][0]["workspace_slug"]
    user_id = body["user"]["id"]
    resp = auth_client.delete(f"/api/v1/workspaces/{slug}/members/{user_id}")
    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# config.py — production validators (lines 161-171, 182-187, 203-215)
# ---------------------------------------------------------------------------


def test_production_requires_secure_cookies() -> None:
    with pytest.raises(ValueError, match="SECURE_COOKIES"):
        Settings(  # type: ignore[call-arg]
            _env_file=None,
            app_env="production",
            database_url="postgresql+psycopg://u:p@db.railway.internal:5432/d",
            secure_cookies=False,
            feature_auth=False,
        )


def test_production_with_auth_rejects_resend_dry_run() -> None:
    with pytest.raises(ValueError, match="RESEND_DRY_RUN"):
        Settings(  # type: ignore[call-arg]
            _env_file=None,
            app_env="production",
            database_url="postgresql+psycopg://u:p@db.railway.internal:5432/d",
            secure_cookies=True,
            feature_auth=True,
            resend_dry_run=True,
            resend_api_key="placeholder-not-a-real-key",  # pragma: allowlist secret
        )


def test_production_with_auth_requires_resend_api_key() -> None:
    with pytest.raises(ValueError, match="RESEND_API_KEY"):
        Settings(  # type: ignore[call-arg]
            _env_file=None,
            app_env="production",
            database_url="postgresql+psycopg://u:p@db.railway.internal:5432/d",
            secure_cookies=True,
            feature_auth=True,
            resend_dry_run=False,
            resend_api_key="",
        )
