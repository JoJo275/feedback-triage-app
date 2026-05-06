"""Playwright smoke for the auth sign-up flow (PR 1.7).

Drives `/signup` end-to-end: a user fills the form, submits, and the
page swaps to the "check your inbox" success message. This proves the
static HTML, ``auth.js``, and ``/api/v1/auth/signup`` are wired up.

The signup endpoint also writes an ``email_log`` row via
``EmailClient`` with ``RESEND_DRY_RUN=1`` (the package default in
non-production envs), so no outbound HTTP call is made.

See spec — Frontend Smoke Tests; ADRs 059/061.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import text

from feedback_triage.database import engine

# Skip the entire module when Playwright is not installed (the unit /
# coverage CI jobs install only the [test] extra). MUST run before the
# ``from playwright...`` import below.
playwright_sync_api = pytest.importorskip(
    "playwright.sync_api",
    reason="playwright is only installed for the e2e job",
)

from playwright.sync_api import Page, expect  # noqa: E402

pytestmark = pytest.mark.e2e


@pytest.fixture
def truncate_auth_world_e2e() -> Iterator[None]:
    """Wipe the auth-cluster tables for an isolated signup spec."""
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


def test_signup_flow_shows_success_message(
    live_app_url: str,
    truncate_auth_world_e2e: None,
    page: Page,
) -> None:
    page.goto(f"{live_app_url}/signup")
    page.get_by_label("Email").fill("smoke@example.com")
    # Whitespace is intentional — keeps the value above the 12-char
    # minimum without tripping the no-secrets-patterns hook (see
    # tests/api/auth/test_tokens.py).
    page.get_by_label("Password").fill("smoke test passphrase")
    page.get_by_label("Workspace name").fill("Smoke Co")
    page.get_by_role("button", name="Create account").click()

    # On success, ``auth.js`` hides the form and reveals the
    # ``#signup-success`` paragraph. ``expect`` retries until the
    # element becomes visible or the default timeout expires.
    success = page.locator("#signup-success")
    expect(success).to_be_visible()
    expect(success).to_contain_text("Check your inbox")

    # The email_log row is the audit boundary the back-end commits
    # before invoking EmailClient — see signup() in api/v1/auth.py.
    with engine.begin() as conn:
        row = conn.execute(
            text(
                "SELECT to_address, purpose, status FROM email_log",
            ),
        ).one()
    assert row.to_address == "smoke@example.com"
    assert row.purpose == "verification"
    assert row.status == "sent"  # DRY_RUN short-circuits to ``sent``.
