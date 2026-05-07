"""PR 3.2 -- public changelog page tests.

Covers the spec's DoD bullets:

1. Slug isolation -- unknown slug returns 404 with the standard
   ``not_found`` envelope.
2. Filtering -- only ``status='shipped' AND published_to_changelog=true``
   appears (the spec calls this out explicitly: a row with
   ``published_to_changelog=false`` does not show up).
3. Ordering -- entries reverse-chronological by updated_at.
4. Cache header -- response advertises the public-page cache contract.
5. No auth -- the page renders for anonymous callers.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import text

from feedback_triage.database import engine

VALID_PASSWORD = "correct horse battery staple"  # pragma: allowlist secret


def _signup_and_login(client: TestClient, email: str) -> str:
    resp = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": VALID_PASSWORD},
    )
    assert resp.status_code == 201, resp.text
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": VALID_PASSWORD},
    )
    assert login.status_code == 200, login.text
    return str(login.json()["memberships"][0]["workspace_slug"])


def _create_item(client: TestClient, slug: str, title: str) -> int:
    payload: dict[str, Any] = {
        "title": title,
        "description": "Background.",
        "source": "email",
        "pain_level": 3,
        "type": "feature_request",
    }
    resp = client.post(
        "/api/v1/feedback",
        json=payload,
        headers={"X-Workspace-Slug": slug},
    )
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


def _patch_item(
    client: TestClient,
    slug: str,
    item_id: int,
    body: dict[str, Any],
) -> None:
    resp = client.patch(
        f"/api/v1/feedback/{item_id}",
        json=body,
        headers={"X-Workspace-Slug": slug},
    )
    assert resp.status_code == 200, resp.text


def _set_updated_at(item_id: int, when: datetime) -> None:
    """Force a specific ``updated_at`` for ordering tests.

    Bypasses the BEFORE UPDATE trigger so the timestamp written here
    survives the statement.
    """
    with engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE feedback_item "
                "DISABLE TRIGGER feedback_item_set_updated_at",
            ),
        )
        conn.execute(
            text("UPDATE feedback_item SET updated_at = :ts WHERE id = :id"),
            {"ts": when, "id": item_id},
        )
        conn.execute(
            text(
                "ALTER TABLE feedback_item ENABLE TRIGGER feedback_item_set_updated_at",
            ),
        )


# ---------------------------------------------------------------------------
# Slug isolation
# ---------------------------------------------------------------------------


def test_public_changelog_unknown_slug_returns_404(
    auth_client: TestClient,
) -> None:
    resp = auth_client.get("/w/no-such-workspace/changelog/public")
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "not_found"


# ---------------------------------------------------------------------------
# No auth + cache header
# ---------------------------------------------------------------------------


def test_public_changelog_renders_without_auth_and_sets_cache_header(
    auth_client: TestClient,
) -> None:
    slug = _signup_and_login(auth_client, "owner@example.com")
    auth_client.cookies.clear()

    resp = auth_client.get(f"/w/{slug}/changelog/public")
    assert resp.status_code == 200
    assert (
        resp.headers["cache-control"]
        == "public, max-age=300, stale-while-revalidate=600"
    )
    assert "changelog" in resp.text.lower()


# ---------------------------------------------------------------------------
# Filtering and ordering
# ---------------------------------------------------------------------------


def test_public_changelog_only_lists_published_shipped_items(
    auth_client: TestClient,
) -> None:
    slug = _signup_and_login(auth_client, "owner@example.com")

    # Shipped + published -> appears.
    visible_id = _create_item(auth_client, slug, "Visible release")
    _patch_item(
        auth_client,
        slug,
        visible_id,
        {
            "status": "shipped",
            "published_to_changelog": True,
            "release_note": "Made it faster.",
        },
    )
    # Shipped but unpublished -> hidden (the spec's named guarantee).
    hidden_id = _create_item(auth_client, slug, "Hidden release")
    _patch_item(
        auth_client,
        slug,
        hidden_id,
        {"status": "shipped", "published_to_changelog": False},
    )
    # Published but not shipped -> hidden.
    planned_id = _create_item(auth_client, slug, "Planned not shipped")
    _patch_item(
        auth_client,
        slug,
        planned_id,
        {"status": "planned", "published_to_changelog": True},
    )

    auth_client.cookies.clear()
    resp = auth_client.get(f"/w/{slug}/changelog/public")
    assert resp.status_code == 200
    body = resp.text
    assert "Visible release" in body
    assert "Made it faster." in body
    assert "Hidden release" not in body
    assert "Planned not shipped" not in body


def test_public_changelog_orders_newest_first(
    auth_client: TestClient,
) -> None:
    slug = _signup_and_login(auth_client, "owner@example.com")

    older_id = _create_item(auth_client, slug, "Older release")
    _patch_item(
        auth_client,
        slug,
        older_id,
        {"status": "shipped", "published_to_changelog": True},
    )
    newer_id = _create_item(auth_client, slug, "Newer release")
    _patch_item(
        auth_client,
        slug,
        newer_id,
        {"status": "shipped", "published_to_changelog": True},
    )
    # Force an unambiguous ordering (the trigger writes one timestamp
    # per UPDATE and tests can land within the same microsecond).
    now = datetime.now(UTC)
    _set_updated_at(older_id, now - timedelta(days=10))
    _set_updated_at(newer_id, now)

    auth_client.cookies.clear()
    resp = auth_client.get(f"/w/{slug}/changelog/public")
    body = resp.text
    assert resp.status_code == 200
    assert body.index("Newer release") < body.index("Older release")


def test_public_changelog_empty_state(auth_client: TestClient) -> None:
    slug = _signup_and_login(auth_client, "owner@example.com")
    auth_client.cookies.clear()
    resp = auth_client.get(f"/w/{slug}/changelog/public")
    assert resp.status_code == 200
    assert "Nothing shipped yet" in resp.text
