"""PR 2.4 -- public submission flow tests.

Covers the four guards that ship as deliverables:

1. Slug isolation -- unknown slug returns 404 with the standard
   ``not_found`` envelope (page route + API route).
2. Happy path -- POST creates a feedback row + (optionally) a
   submitter row keyed on ``(workspace_id, email)``.
3. Honeypot -- a non-empty ``website`` field returns the same 200
   envelope a real success would, but writes nothing.
4. Rate limit -- the sixth submission inside the 60s window returns
   429 with the ``rate_limited`` envelope.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import text

from feedback_triage.database import engine

VALID_PASSWORD = "correct horse battery staple"  # pragma: allowlist secret


def _signup_and_login(client: TestClient, email: str) -> dict[str, object]:
    """Sign up + log in; return the login response body."""
    resp = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": VALID_PASSWORD},
    )
    assert resp.status_code == 201, resp.text
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": VALID_PASSWORD},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _first_slug(login_body: dict[str, object]) -> str:
    memberships = login_body["memberships"]
    assert isinstance(memberships, list) and memberships
    return str(memberships[0]["workspace_slug"])


def _valid_payload(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "title": "Login button is broken",
        "description": "Clicking it does nothing on Safari 17.",
        "pain_level": 4,
        "type": "bug",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Slug isolation
# ---------------------------------------------------------------------------


def test_public_submit_page_unknown_slug_returns_404(
    auth_client: TestClient,
) -> None:
    resp = auth_client.get("/w/no-such-workspace/submit")
    assert resp.status_code == 404


def test_public_submit_page_renders_for_known_slug(
    auth_client: TestClient,
) -> None:
    body = _signup_and_login(auth_client, "owner@example.com")
    slug = _first_slug(body)

    resp = auth_client.get(f"/w/{slug}/submit")
    assert resp.status_code == 200
    assert "Submit feedback" in resp.text
    # Honeypot field is in the markup so bots find it.
    assert 'name="website"' in resp.text


def test_public_submit_api_unknown_slug_returns_404(
    auth_client: TestClient,
) -> None:
    resp = auth_client.post(
        "/api/v1/public/feedback/no-such-workspace",
        json=_valid_payload(),
    )
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "not_found"


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_public_submit_anonymous_creates_feedback_no_submitter(
    auth_client: TestClient,
) -> None:
    body = _signup_and_login(auth_client, "owner@example.com")
    slug = _first_slug(body)

    resp = auth_client.post(
        f"/api/v1/public/feedback/{slug}",
        json=_valid_payload(),
    )
    assert resp.status_code == 201, resp.text
    payload = resp.json()
    assert payload["status"] == "accepted"
    assert isinstance(payload["id"], int)

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT title, status::text, source::text, submitter_id "
                "FROM feedback_item WHERE id = :id",
            ),
            {"id": payload["id"]},
        ).all()
    assert len(rows) == 1
    title, status_, source_, submitter_id = rows[0]
    assert title == "Login button is broken"
    assert status_ == "new"
    assert source_ == "web_form"
    assert submitter_id is None


def test_public_submit_with_email_creates_and_dedupes_submitter(
    auth_client: TestClient,
) -> None:
    body = _signup_and_login(auth_client, "owner@example.com")
    slug = _first_slug(body)

    payload = _valid_payload(
        submitter_email="reporter@example.com",
        submitter_name="Reporter Name",
    )
    first = auth_client.post(f"/api/v1/public/feedback/{slug}", json=payload)
    assert first.status_code == 201, first.text
    second = auth_client.post(f"/api/v1/public/feedback/{slug}", json=payload)
    assert second.status_code == 201, second.text

    with engine.connect() as conn:
        sub_rows = conn.execute(
            text(
                "SELECT submission_count, name FROM submitters WHERE email = :e",
            ),
            {"e": "reporter@example.com"},
        ).all()
        fb_rows = conn.execute(
            text(
                "SELECT submitter_id FROM feedback_item WHERE id IN (:a, :b)",
            ),
            {"a": first.json()["id"], "b": second.json()["id"]},
        ).all()
    assert len(sub_rows) == 1
    assert sub_rows[0][0] == 2  # submission_count incremented
    assert sub_rows[0][1] == "Reporter Name"
    submitter_ids = {r[0] for r in fb_rows}
    assert len(submitter_ids) == 1  # both feedback rows linked to same submitter


# ---------------------------------------------------------------------------
# Honeypot
# ---------------------------------------------------------------------------


def test_public_submit_honeypot_returns_ok_but_writes_nothing(
    auth_client: TestClient,
) -> None:
    body = _signup_and_login(auth_client, "owner@example.com")
    slug = _first_slug(body)

    resp = auth_client.post(
        f"/api/v1/public/feedback/{slug}",
        json=_valid_payload(website="http://spam.example"),
    )
    # Spec: never leak detection -- always return the success envelope.
    assert resp.status_code == 201
    assert resp.json() == {"status": "accepted"}

    with engine.connect() as conn:
        count = conn.execute(
            text("SELECT count(*) FROM feedback_item"),
        ).scalar_one()
    assert count == 0


# ---------------------------------------------------------------------------
# Rate limit
# ---------------------------------------------------------------------------


def test_public_submit_rate_limit_trips_on_sixth_submission(
    auth_client: TestClient,
) -> None:
    body = _signup_and_login(auth_client, "owner@example.com")
    slug = _first_slug(body)

    for i in range(5):
        resp = auth_client.post(
            f"/api/v1/public/feedback/{slug}",
            json=_valid_payload(title=f"Item {i}"),
        )
        assert resp.status_code == 201, resp.text

    sixth = auth_client.post(
        f"/api/v1/public/feedback/{slug}",
        json=_valid_payload(title="Item 6"),
    )
    assert sixth.status_code == 429, sixth.text
    assert sixth.json()["detail"]["code"] == "rate_limited"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def test_public_submit_rejects_internal_source(auth_client: TestClient) -> None:
    body = _signup_and_login(auth_client, "owner@example.com")
    slug = _first_slug(body)

    resp = auth_client.post(
        f"/api/v1/public/feedback/{slug}",
        json=_valid_payload(source="support"),
    )
    # ``support`` is a team-only source, not an allowed public source.
    assert resp.status_code == 422


def test_public_submit_rejects_extra_fields(auth_client: TestClient) -> None:
    body = _signup_and_login(auth_client, "owner@example.com")
    slug = _first_slug(body)

    resp = auth_client.post(
        f"/api/v1/public/feedback/{slug}",
        json=_valid_payload(status="accepted"),
    )
    # ``extra="forbid"`` -- public submitters can't pre-set status.
    assert resp.status_code == 422
