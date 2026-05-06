"""Flow tests for ``/api/v1/workspaces/{slug}/invitations`` and accept.

The mint side asserts that an email row lands on the ``email_log``
(``RESEND_DRY_RUN=1`` keeps it network-free); the accept side asserts
that consuming a token creates a membership and a second consume
returns ``410``.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import text

from feedback_triage.auth import tokens as auth_tokens
from feedback_triage.database import SessionLocal, engine

VALID_PASSWORD = "correct horse battery staple"  # pragma: allowlist secret


def _signup_and_login(
    client: TestClient,
    email: str,
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


def _slug(login_body: dict[str, object]) -> str:
    memberships = login_body["memberships"]
    assert isinstance(memberships, list) and memberships
    return str(memberships[0]["workspace_slug"])


def test_create_invitation_persists_row_and_logs_email(
    auth_client: TestClient,
) -> None:
    body = _signup_and_login(auth_client, "owner@example.com")
    slug = _slug(body)

    resp = auth_client.post(
        f"/api/v1/workspaces/{slug}/invitations",
        json={"email": "invitee@example.com", "role": "team_member"},
    )
    assert resp.status_code == 201, resp.text
    payload = resp.json()
    assert payload["email"] == "invitee@example.com"
    assert payload["role"] == "team_member"
    assert payload["accepted_at"] is None
    assert payload["revoked_at"] is None

    # `email_log` got a row in dry-run mode (no network).
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT to_address, purpose FROM email_log WHERE to_address = :addr",
            ),
            {"addr": "invitee@example.com"},
        ).all()
    assert len(rows) == 1
    assert rows[0][1] == "invitation"


def test_list_invitations_returns_open_only(auth_client: TestClient) -> None:
    body = _signup_and_login(auth_client, "owner@example.com")
    slug = _slug(body)

    auth_client.post(
        f"/api/v1/workspaces/{slug}/invitations",
        json={"email": "a@example.com"},
    )
    auth_client.post(
        f"/api/v1/workspaces/{slug}/invitations",
        json={"email": "b@example.com"},
    )

    resp = auth_client.get(f"/api/v1/workspaces/{slug}/invitations")
    assert resp.status_code == 200, resp.text
    payload = resp.json()
    assert payload["total"] == 2
    emails = {item["email"] for item in payload["items"]}
    assert emails == {"a@example.com", "b@example.com"}


def test_re_invite_revokes_prior_open_invitation(
    auth_client: TestClient,
) -> None:
    body = _signup_and_login(auth_client, "owner@example.com")
    slug = _slug(body)

    first = auth_client.post(
        f"/api/v1/workspaces/{slug}/invitations",
        json={"email": "dup@example.com"},
    )
    assert first.status_code == 201
    second = auth_client.post(
        f"/api/v1/workspaces/{slug}/invitations",
        json={"email": "dup@example.com"},
    )
    assert second.status_code == 201

    # The list endpoint shows only the *open* row.
    resp = auth_client.get(f"/api/v1/workspaces/{slug}/invitations")
    assert resp.json()["total"] == 1


def test_revoke_invitation_returns_204_and_204s_again_as_404(
    auth_client: TestClient,
) -> None:
    body = _signup_and_login(auth_client, "owner@example.com")
    slug = _slug(body)

    created = auth_client.post(
        f"/api/v1/workspaces/{slug}/invitations",
        json={"email": "revokeme@example.com"},
    ).json()
    inv_id = created["id"]

    resp = auth_client.delete(
        f"/api/v1/workspaces/{slug}/invitations/{inv_id}",
    )
    assert resp.status_code == 204

    # Second revoke is a 404 (the row is no longer open).
    resp = auth_client.delete(
        f"/api/v1/workspaces/{slug}/invitations/{inv_id}",
    )
    assert resp.status_code == 404


def test_revoke_unknown_invitation_returns_404(auth_client: TestClient) -> None:
    body = _signup_and_login(auth_client, "owner@example.com")
    slug = _slug(body)
    bogus = "00000000-0000-0000-0000-000000000001"

    resp = auth_client.delete(f"/api/v1/workspaces/{slug}/invitations/{bogus}")
    assert resp.status_code == 404


def test_accept_invitation_creates_membership(auth_client: TestClient) -> None:
    """Owner invites Bob; Bob signs up + accepts; Bob gains membership."""
    owner = _signup_and_login(auth_client, "owner@example.com")
    slug = _slug(owner)
    auth_client.post(
        f"/api/v1/workspaces/{slug}/invitations",
        json={"email": "bob@example.com", "role": "team_member"},
    )

    # Pull the raw token directly out of the DB. The route never
    # echoes it (security-by-design), so this is the only way the
    # test can play the invitee's role.
    raw_token = _mint_extra_token_for(slug, "bob-extra@example.com")

    # Log out the owner; sign Bob up + log in.
    auth_client.post("/api/v1/auth/logout")
    bob = _signup_and_login(auth_client, "bob-extra@example.com")
    assert len(bob["memberships"]) == 1  # Bob's own workspace

    resp = auth_client.post(f"/api/v1/invitations/{raw_token}/accept")
    assert resp.status_code == 200, resp.text
    payload = resp.json()
    assert payload["workspace_slug"] == slug
    assert payload["role"] == "team_member"

    # Second accept on the same token → 410 Gone.
    resp2 = auth_client.post(f"/api/v1/invitations/{raw_token}/accept")
    assert resp2.status_code == 410


def test_accept_unknown_token_returns_410(auth_client: TestClient) -> None:
    _signup_and_login(auth_client, "anyone@example.com")
    resp = auth_client.post("/api/v1/invitations/this-is-not-a-real-token/accept")
    assert resp.status_code == 410


def test_accept_anonymous_returns_401(auth_client: TestClient) -> None:
    resp = auth_client.post("/api/v1/invitations/anything/accept")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mint_extra_token_for(slug: str, email: str) -> str:
    """Mint an invitation token for ``email`` against workspace ``slug``.

    Used by the accept-flow test because the public POST route never
    surfaces the raw token (it goes out only by email). We bypass
    that here and call the same primitive the route would.
    """
    from sqlmodel import col, select

    from feedback_triage.models import User, Workspace

    db = SessionLocal()
    try:
        workspace = db.execute(
            select(Workspace).where(col(Workspace.slug) == slug),
        ).scalar_one()
        owner = db.execute(
            select(User).where(col(User.email) == "owner@example.com"),
        ).scalar_one()
        assert workspace.id is not None
        assert owner.id is not None
        issued = auth_tokens.mint_invitation_token(
            db,
            workspace_id=workspace.id,
            email=email,
            invited_by_id=owner.id,
            role="team_member",
        )
        db.commit()
        return issued.raw_token
    finally:
        db.close()
