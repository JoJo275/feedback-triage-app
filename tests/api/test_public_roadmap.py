"""PR 3.2 -- public roadmap page tests.

Covers the four guards the spec calls out:

1. Slug isolation -- unknown slug returns 404 with the standard
   ``not_found`` envelope.
2. Filtering -- only items with ``published_to_roadmap = true`` and
   a status in ``{planned, in_progress, shipped}`` appear, and the
   shipped column is bounded to the last 30 days.
3. Cache header -- the response advertises the public-page cache
   contract from ``performance-budgets.md``.
4. No auth -- a logged-out client renders the page successfully.
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


def _create_item(
    client: TestClient,
    slug: str,
    *,
    title: str,
    type_: str = "feature_request",
    description: str = "Background.",
) -> int:
    payload: dict[str, Any] = {
        "title": title,
        "description": description,
        "source": "email",
        "pain_level": 3,
        "type": type_,
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
    """Backdate ``updated_at`` for shipped-window edge tests.

    The ``feedback_item_set_updated_at`` BEFORE UPDATE trigger refreshes
    the column on every UPDATE, so we briefly disable it for the
    backdate. ``ALTER TABLE ... DISABLE TRIGGER`` is the cheapest way
    to bypass it without changing the trigger definition. The trigger
    is re-enabled in the same transaction so concurrent tests are
    unaffected.
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


def test_public_roadmap_unknown_slug_returns_404(
    auth_client: TestClient,
) -> None:
    resp = auth_client.get("/w/no-such-workspace/roadmap/public")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# No auth + cache header
# ---------------------------------------------------------------------------


def test_public_roadmap_renders_without_auth_and_sets_cache_header(
    auth_client: TestClient,
) -> None:
    slug = _signup_and_login(auth_client, "owner@example.com")
    # Drop the session cookie set by signup -- the public roadmap
    # MUST work for fully anonymous callers.
    auth_client.cookies.clear()

    resp = auth_client.get(f"/w/{slug}/roadmap/public")
    assert resp.status_code == 200
    assert (
        resp.headers["cache-control"]
        == "public, max-age=300, stale-while-revalidate=600"
    )
    assert "roadmap" in resp.text.lower()


# ---------------------------------------------------------------------------
# Filtering: published_to_roadmap = true, columns by status
# ---------------------------------------------------------------------------


def test_public_roadmap_only_shows_published_items(
    auth_client: TestClient,
) -> None:
    slug = _signup_and_login(auth_client, "owner@example.com")

    published_id = _create_item(auth_client, slug, title="Public planned item")
    _patch_item(
        auth_client,
        slug,
        published_id,
        {"status": "planned", "published_to_roadmap": True},
    )

    private_id = _create_item(auth_client, slug, title="Private planned item")
    _patch_item(
        auth_client,
        slug,
        private_id,
        {"status": "planned", "published_to_roadmap": False},
    )

    auth_client.cookies.clear()
    resp = auth_client.get(f"/w/{slug}/roadmap/public")
    assert resp.status_code == 200
    assert "Public planned item" in resp.text
    assert "Private planned item" not in resp.text


def test_public_roadmap_groups_by_status_column(
    auth_client: TestClient,
) -> None:
    slug = _signup_and_login(auth_client, "owner@example.com")

    planned_id = _create_item(auth_client, slug, title="Planned thing")
    _patch_item(
        auth_client,
        slug,
        planned_id,
        {"status": "planned", "published_to_roadmap": True},
    )
    in_progress_id = _create_item(auth_client, slug, title="WIP thing")
    _patch_item(
        auth_client,
        slug,
        in_progress_id,
        {"status": "in_progress", "published_to_roadmap": True},
    )
    shipped_id = _create_item(auth_client, slug, title="Shipped thing")
    _patch_item(
        auth_client,
        slug,
        shipped_id,
        {"status": "shipped", "published_to_roadmap": True},
    )
    # An accepted item is published-to-roadmap but not in any of the
    # three roadmap columns -- it must not appear.
    accepted_id = _create_item(auth_client, slug, title="Accepted thing")
    _patch_item(
        auth_client,
        slug,
        accepted_id,
        {"status": "accepted", "published_to_roadmap": True},
    )

    auth_client.cookies.clear()
    resp = auth_client.get(f"/w/{slug}/roadmap/public")
    assert resp.status_code == 200
    body = resp.text
    assert "Planned thing" in body
    assert "WIP thing" in body
    assert "Shipped thing" in body
    assert "Accepted thing" not in body


def test_public_roadmap_shipped_column_bounded_to_30_days(
    auth_client: TestClient,
) -> None:
    slug = _signup_and_login(auth_client, "owner@example.com")
    fresh_id = _create_item(auth_client, slug, title="Fresh ship")
    _patch_item(
        auth_client,
        slug,
        fresh_id,
        {"status": "shipped", "published_to_roadmap": True},
    )
    stale_id = _create_item(auth_client, slug, title="Ancient ship")
    _patch_item(
        auth_client,
        slug,
        stale_id,
        {"status": "shipped", "published_to_roadmap": True},
    )
    _set_updated_at(stale_id, datetime.now(UTC) - timedelta(days=45))

    auth_client.cookies.clear()
    resp = auth_client.get(f"/w/{slug}/roadmap/public")
    assert resp.status_code == 200
    assert "Fresh ship" in resp.text
    assert "Ancient ship" not in resp.text


def test_public_roadmap_empty_state_when_nothing_published(
    auth_client: TestClient,
) -> None:
    slug = _signup_and_login(auth_client, "owner@example.com")
    item_id = _create_item(auth_client, slug, title="Hidden item")
    _patch_item(auth_client, slug, item_id, {"status": "planned"})

    auth_client.cookies.clear()
    resp = auth_client.get(f"/w/{slug}/roadmap/public")
    assert resp.status_code == 200
    assert "Nothing on the public roadmap yet" in resp.text
