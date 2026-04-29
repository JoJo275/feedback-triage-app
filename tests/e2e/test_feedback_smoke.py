"""Playwright smoke suite — three critical UI paths.

These specs prove the static HTML + vanilla JS frontend is wired to the
API correctly. They intentionally do **not** drill into edge cases the
API tests already cover. See spec — Frontend Smoke Tests.
"""

from __future__ import annotations

import pytest

# Skip the entire module when Playwright is not installed (the default
# in the unit/coverage CI jobs that install only the [test] extra).
# This MUST run before the ``from playwright...`` import below.
playwright_sync_api = pytest.importorskip(
    "playwright.sync_api",
    reason="playwright is only installed for the e2e job",
)

from playwright.sync_api import Page, expect  # noqa: E402

pytestmark = pytest.mark.e2e


def _create_via_ui(page: Page, base_url: str, title: str) -> None:
    page.goto(f"{base_url}/new")
    page.get_by_label("Title").fill(title)
    page.get_by_label("Source").select_option("email")
    page.get_by_label("Pain level").select_option("4")
    page.get_by_role("button", name="Create").click()
    # new.js redirects to /feedback/{id} on success.
    page.wait_for_url(f"{base_url}/feedback/**")


def test_create_flow_lands_user_with_new_item_visible(
    live_app_url: str,
    truncate_feedback: None,
    page: Page,
) -> None:
    title = "Smoke create flow"
    _create_via_ui(page, live_app_url, title)

    page.goto(f"{live_app_url}/")
    expect(page.get_by_role("table")).to_contain_text(title)


def test_edit_flow_persists_status_change(
    live_app_url: str,
    truncate_feedback: None,
    page: Page,
) -> None:
    _create_via_ui(page, live_app_url, "Smoke edit flow")

    # Already on the detail page after _create_via_ui.
    page.get_by_label("Status").select_option("reviewing")
    page.get_by_role("button", name="Save").click()

    page.reload()
    expect(page.get_by_label("Status")).to_have_value("reviewing")


def test_delete_flow_removes_item_from_list(
    live_app_url: str,
    truncate_feedback: None,
    page: Page,
) -> None:
    title = "Smoke delete flow"
    _create_via_ui(page, live_app_url, title)

    page.goto(f"{live_app_url}/")
    expect(page.get_by_role("table")).to_contain_text(title)

    # Auto-accept the window.confirm() dialog before clicking Delete.
    page.once("dialog", lambda d: d.accept())
    page.get_by_role("button", name="Delete").first.click()

    expect(page.locator("#list-body")).not_to_contain_text(title)

    # Reload — the item must stay gone.
    page.reload()
    expect(page.locator("main")).not_to_contain_text(title)
