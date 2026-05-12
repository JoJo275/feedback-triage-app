"""axe-core accessibility scan over the v2 page surface (PR 2.6).

Runs axe-core (vendored from the CDN at runtime) against the
authenticated and public pages we care about: inbox, feedback
detail, settings, submitters list, public-submit form. Any
*serious* or *critical* violation fails the suite. Color-contrast
is opt-in because the live theme is verified separately in design
review.

The suite is opt-in via ``task test:e2e`` like the rest of the
Playwright pack. We pull axe.min.js from the cdnjs mirror so the
test does not require ``npm`` on the runner; the URL is pinned to
a specific version so a CDN-side compromise can't silently change
the rule set under us.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import pytest
from sqlalchemy import text

from feedback_triage.database import engine

# Axe-core, pinned. Hash of this version is in the package-lock
# upstream; pulling at runtime keeps the e2e job from needing npm.
AXE_CDN_URL = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js"

# Skip the entire module when Playwright is not installed.
playwright_sync_api = pytest.importorskip(
    "playwright.sync_api",
    reason="playwright is only installed for the e2e job",
)

from playwright.sync_api import Page  # noqa: E402

pytestmark = pytest.mark.e2e

VALID_PASSWORD = "smoke test passphrase"  # pragma: allowlist secret


@pytest.fixture
def truncate_world() -> Iterator[None]:
    """Wipe every table the smoke run touches."""
    with engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE TABLE "
                "users, workspaces, workspace_memberships, "
                "workspace_invitations, sessions, "
                "email_verification_tokens, password_reset_tokens, "
                "auth_rate_limits, email_log, "
                "feedback_item, tags, submitters "
                "RESTART IDENTITY CASCADE",
            ),
        )
    yield


def _signup(page: Page, base_url: str, email: str) -> str:
    """Sign up a fresh user and return the workspace slug."""
    page.goto(f"{base_url}/signup")
    page.get_by_label("Email").fill(email)
    page.get_by_label("Password").fill(VALID_PASSWORD)
    page.get_by_label("Workspace name").fill("Axe Co")
    page.get_by_role("button", name="Create account").click()
    page.locator("#signup-success").wait_for()

    # Look up the slug directly; the success message doesn't expose it.
    with engine.begin() as conn:
        slug = conn.execute(
            text(
                "SELECT slug FROM workspaces ORDER BY created_at DESC LIMIT 1",
            ),
        ).scalar_one()
    # Bypass email verification: mark the user verified and log in.
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE users SET is_verified = true WHERE email = :e"),
            {"e": email},
        )
    page.goto(f"{base_url}/login")
    page.get_by_label("Email").fill(email)
    page.get_by_label("Password").fill(VALID_PASSWORD)
    page.get_by_role("button", name="Sign in").click()
    # Login lands the user on their workspace dashboard.
    page.wait_for_url(f"{base_url}/w/*/dashboard")
    return str(slug)


def _seed_submitter(workspace_slug: str) -> uuid.UUID:
    sub_id = uuid.uuid4()
    with engine.begin() as conn:
        ws_id = conn.execute(
            text("SELECT id FROM workspaces WHERE slug = :s"),
            {"s": workspace_slug},
        ).scalar_one()
        conn.execute(
            text(
                """
                INSERT INTO submitters (id, workspace_id, email, name)
                VALUES (:id, :ws, 'a11y@example.com', 'Axe User')
                """,
            ),
            {"id": sub_id, "ws": ws_id},
        )
    return sub_id


def _run_axe(page: Page) -> list[dict[str, object]]:
    """Inject axe.min.js and return ``serious``/``critical`` violations."""
    page.add_script_tag(url=AXE_CDN_URL)
    result = page.evaluate(
        # `axe.run()` returns a Promise; Playwright awaits it.
        "async () => await axe.run(document, "
        "{ resultTypes: ['violations'], "
        "runOnly: { type: 'tag', "
        "values: ['wcag2a', 'wcag2aa'] } })",
    )
    violations = [
        v
        for v in result.get("violations", [])
        if v.get("impact") in {"serious", "critical"}
    ]
    return violations


def _assert_clean(page: Page, label: str) -> None:
    violations = _run_axe(page)
    formatted = [
        f"  - [{v.get('impact')}] {v.get('id')}: {v.get('help')}" for v in violations
    ]
    assert not violations, (
        f"axe-core reported {len(violations)} serious/critical "
        f"violations on {label}:\n" + "\n".join(formatted)
    )


def test_axe_inbox(
    live_app_url: str,
    truncate_world: None,
    page: Page,
) -> None:
    slug = _signup(page, live_app_url, "axe-inbox@example.com")
    page.goto(f"{live_app_url}/w/{slug}/inbox")
    page.wait_for_load_state("networkidle")
    _assert_clean(page, "/w/<slug>/inbox")


def test_axe_feedback_detail(
    live_app_url: str,
    truncate_world: None,
    page: Page,
) -> None:
    slug = _signup(page, live_app_url, "axe-detail@example.com")
    # Create a feedback item via the API (cookie is set after login).
    response = page.context.request.post(
        f"{live_app_url}/api/v1/feedback",
        headers={"X-Workspace-Slug": slug},
        data={
            "title": "axe-target",
            "description": "Body.",
            "source": "email",
            "pain_level": 2,
        },
    )
    assert response.status == 201, response.text()
    item_id = response.json()["id"]
    page.goto(f"{live_app_url}/w/{slug}/feedback/{item_id}")
    page.wait_for_load_state("networkidle")
    _assert_clean(page, "/w/<slug>/feedback/<id>")


def test_axe_settings(
    live_app_url: str,
    truncate_world: None,
    page: Page,
) -> None:
    slug = _signup(page, live_app_url, "axe-settings@example.com")
    page.goto(f"{live_app_url}/w/{slug}/settings")
    page.wait_for_load_state("networkidle")
    _assert_clean(page, "/w/<slug>/settings")


def test_axe_submitters_list(
    live_app_url: str,
    truncate_world: None,
    page: Page,
) -> None:
    slug = _signup(page, live_app_url, "axe-subs@example.com")
    _seed_submitter(slug)
    page.goto(f"{live_app_url}/w/{slug}/submitters")
    page.wait_for_load_state("networkidle")
    _assert_clean(page, "/w/<slug>/submitters")


def test_axe_public_submit(
    live_app_url: str,
    truncate_world: None,
    page: Page,
) -> None:
    slug = _signup(page, live_app_url, "axe-public@example.com")
    page.goto(f"{live_app_url}/w/{slug}/submit")
    page.wait_for_load_state("networkidle")
    _assert_clean(page, "/w/<slug>/submit")
