"""Playwright smoke for the public roadmap + public changelog (PR 3.2).

The smoke seeds the data through the live JSON API (signup -> create
-> patch to shipped + published) and then opens the two unauthenticated
pages in the browser. The browser page never carries the signup
session cookie because we navigate to the public URLs in a fresh
session-less request flow; the spec's requirement is that the pages
work for fully anonymous callers.
"""

from __future__ import annotations

from collections.abc import Iterator

import httpx
import pytest
from sqlalchemy import text

from feedback_triage.database import engine

playwright_sync_api = pytest.importorskip(
    "playwright.sync_api",
    reason="playwright is only installed for the e2e job",
)

from playwright.sync_api import Page, expect  # noqa: E402

pytestmark = pytest.mark.e2e

VALID_PASSWORD = "correct horse battery staple"  # pragma: allowlist secret


@pytest.fixture
def truncate_auth_world_e2e() -> Iterator[None]:
    with engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE TABLE "
                "users, workspaces, workspace_memberships, "
                "workspace_invitations, sessions, "
                "email_verification_tokens, password_reset_tokens, "
                "auth_rate_limits, email_log "
                "RESTART IDENTITY CASCADE",
            ),
        )
    yield


def _seed_shipped_item(base_url: str, title: str) -> str:
    """Sign up, create a feedback row, ship + publish it. Returns slug."""
    with httpx.Client(base_url=base_url, timeout=10.0) as api:
        resp = api.post(
            "/api/v1/auth/signup",
            json={"email": "smoke@example.com", "password": VALID_PASSWORD},
        )
        assert resp.status_code == 201, resp.text
        login = api.post(
            "/api/v1/auth/login",
            json={"email": "smoke@example.com", "password": VALID_PASSWORD},
        )
        assert login.status_code == 200, login.text
        slug = str(login.json()["memberships"][0]["workspace_slug"])
        headers = {"X-Workspace-Slug": slug}
        created = api.post(
            "/api/v1/feedback",
            json={
                "title": title,
                "description": "Background.",
                "source": "email",
                "pain_level": 3,
                "type": "feature_request",
            },
            headers=headers,
        )
        assert created.status_code == 201, created.text
        item_id = created.json()["id"]
        patched = api.patch(
            f"/api/v1/feedback/{item_id}",
            json={
                "status": "shipped",
                "published_to_roadmap": True,
                "published_to_changelog": True,
                "release_note": "Shipped during smoke test.",
            },
            headers=headers,
        )
        assert patched.status_code == 200, patched.text
    return slug


def test_public_roadmap_renders_anonymous(
    live_app_url: str,
    truncate_auth_world_e2e: None,
    page: Page,
) -> None:
    slug = _seed_shipped_item(live_app_url, "Roadmap smoke item")

    page.goto(f"{live_app_url}/w/{slug}/roadmap/public")
    expect(page.get_by_role("heading", name="Recently shipped")).to_be_visible()
    expect(page.get_by_text("Roadmap smoke item")).to_be_visible()


def test_public_changelog_renders_anonymous(
    live_app_url: str,
    truncate_auth_world_e2e: None,
    page: Page,
) -> None:
    slug = _seed_shipped_item(live_app_url, "Changelog smoke item")

    page.goto(f"{live_app_url}/w/{slug}/changelog/public")
    expect(page.get_by_text("Changelog smoke item")).to_be_visible()
    expect(page.get_by_text("Shipped during smoke test.")).to_be_visible()
