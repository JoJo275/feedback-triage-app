"""Playwright parity matrix for Phase 3 public React routes.

This suite boots a dedicated app with React public routes enabled, then
verifies shell rendering and anonymous submit/public-read behavior.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import uuid
from collections.abc import Iterator
from urllib.error import URLError
from urllib.request import urlopen

import httpx
import pytest
from sqlalchemy import text

from feedback_triage.database import engine
from feedback_triage.frontend_assets import REACT_MANIFEST, reset_manifest_cache

playwright_sync_api = pytest.importorskip(
    "playwright.sync_api",
    reason="playwright is only installed for the e2e job",
)

from playwright.sync_api import Page, expect  # noqa: E402

pytestmark = pytest.mark.e2e

VALID_PASSWORD = "smoke test passphrase"  # pragma: allowlist secret

_PHASE3_ROUTE_MATRIX = [
    ("landing", "/", "landing"),
    ("public_submit", "/w/{slug}/submit", "public_submit"),
    ("public_roadmap", "/w/{slug}/roadmap/public", "public_roadmap"),
    (
        "public_changelog",
        "/w/{slug}/changelog/public",
        "public_changelog",
    ),
]

_PHASE3_REACT_ENV = {
    "REACT_DASHBOARD_ENTRYPOINT": "index.html",
    "REACT_MANIFEST_VALIDATE_ON_STARTUP": "1",
}


def _manifest_payload() -> dict[str, object]:
    """Build a manifest payload from checked-in Vite bundle assets."""
    assets_dir = REACT_MANIFEST.parent / "assets"
    js_entries = sorted(assets_dir.glob("index-*.js"))
    css_entries = sorted(assets_dir.glob("index-*.css"))

    assert js_entries, (
        "Expected at least one built React JS bundle under "
        f"{assets_dir}; run 'task web:build' to refresh static/app artifacts."
    )

    return {
        "index.html": {
            "file": f"assets/{js_entries[-1].name}",
            "css": [f"assets/{entry.name}" for entry in css_entries],
        }
    }


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_health(url: str, timeout_s: float = 30.0) -> None:
    deadline = time.monotonic() + timeout_s
    last_err: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=1.0) as response:
                if response.status == 200:
                    return
        except (URLError, OSError) as exc:
            last_err = exc
        time.sleep(0.25)

    raise RuntimeError(f"App did not become healthy at {url}: {last_err!r}")


@pytest.fixture(scope="session")
def _seed_react_manifest() -> Iterator[None]:
    existed = REACT_MANIFEST.exists()
    previous = REACT_MANIFEST.read_text(encoding="utf-8") if existed else ""

    REACT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    REACT_MANIFEST.write_text(
        json.dumps(_manifest_payload(), sort_keys=True),
        encoding="utf-8",
    )
    reset_manifest_cache()

    try:
        yield
    finally:
        if existed:
            REACT_MANIFEST.write_text(previous, encoding="utf-8")
        else:
            REACT_MANIFEST.unlink(missing_ok=True)
        reset_manifest_cache()


@pytest.fixture(scope="session")
def live_phase3_public_url(_seed_react_manifest: None) -> Iterator[str]:
    """Run a dedicated live app with React public routes enabled."""
    port = _free_port()
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "feedback_triage.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--log-level",
        "warning",
    ]

    env = os.environ.copy()
    env.update(_PHASE3_REACT_ENV)

    proc = subprocess.Popen(cmd, env=env)
    base_url = f"http://127.0.0.1:{port}"

    try:
        _wait_for_health(f"{base_url}/health")
        yield base_url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


@pytest.fixture
def truncate_world() -> Iterator[None]:
    """Wipe auth + tenancy + triage tables touched by this matrix."""
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


def _signup_and_login(page: Page, base_url: str, email: str) -> str:
    """Create an account, verify it in DB, sign in, and return workspace slug."""
    page.goto(f"{base_url}/signup")
    page.get_by_label("Email").fill(email)
    page.get_by_label("Password").fill(VALID_PASSWORD)
    page.get_by_label("Workspace name").fill("React Phase3 Public Co")
    page.get_by_role("button", name="Create account").click()
    page.locator("#signup-success").wait_for()

    with engine.begin() as conn:
        conn.execute(
            text("UPDATE users SET is_verified = true WHERE email = :email"),
            {"email": email},
        )
        slug = conn.execute(
            text(
                """
                SELECT w.slug
                FROM workspaces AS w
                JOIN workspace_memberships AS wm ON wm.workspace_id = w.id
                JOIN users AS u ON u.id = wm.user_id
                WHERE u.email = :email
                ORDER BY w.created_at DESC
                LIMIT 1
                """,
            ),
            {"email": email},
        ).scalar_one()

    page.goto(f"{base_url}/login")
    page.get_by_label("Email").fill(email)
    page.get_by_label("Password").fill(VALID_PASSWORD)
    page.get_by_role("button", name="Sign in").click()
    page.wait_for_url(f"{base_url}/w/*/dashboard")

    return str(slug)


def _seed_shipped_item(base_url: str, title: str, email: str) -> str:
    """Create a shipped+published item and return the workspace slug."""
    with httpx.Client(base_url=base_url, timeout=10.0) as api:
        signup = api.post(
            "/api/v1/auth/signup",
            json={"email": email, "password": VALID_PASSWORD},
        )
        assert signup.status_code == 201, signup.text

        with engine.begin() as conn:
            conn.execute(
                text("UPDATE users SET is_verified = true WHERE email = :email"),
                {"email": email},
            )

        login = api.post(
            "/api/v1/auth/login",
            json={"email": email, "password": VALID_PASSWORD},
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
                "release_note": "Shipped during phase3 public smoke.",
            },
            headers=headers,
        )
        assert patched.status_code == 200, patched.text

    return slug


@pytest.mark.parametrize(
    ("route_template", "page_key"),
    [(route[1], route[2]) for route in _PHASE3_ROUTE_MATRIX],
)
def test_phase3_public_routes_render_react_shell(
    live_phase3_public_url: str,
    truncate_world: None,
    page: Page,
    route_template: str,
    page_key: str,
) -> None:
    route = route_template
    if "{slug}" in route_template:
        slug = _signup_and_login(
            page,
            live_phase3_public_url,
            f"phase3-{page_key}-{uuid.uuid4().hex[:8]}@example.com",
        )
        route = route_template.format(slug=slug)
        page.context.clear_cookies()

    page.goto(f"{live_phase3_public_url}{route}")
    page.wait_for_load_state("networkidle")

    root = page.locator("#sn-react-app-root")
    expect(root).to_have_count(1)
    expect(root).to_have_attribute("data-page-key", page_key)


def test_phase3_public_submit_route_keeps_anonymous_submit_flow(
    live_phase3_public_url: str,
    truncate_world: None,
    page: Page,
) -> None:
    slug = _signup_and_login(
        page,
        live_phase3_public_url,
        f"phase3-submit-{uuid.uuid4().hex[:8]}@example.com",
    )
    page.context.clear_cookies()

    page.goto(f"{live_phase3_public_url}/w/{slug}/submit")
    page.get_by_label("Title").fill("React phase 3 submit smoke")
    page.get_by_label("How painful is this? (1 = minor, 5 = blocking)").fill("4")
    page.get_by_role("button", name="Submit feedback").click()

    expect(page.get_by_role("heading", name="Thanks!")).to_be_visible()

    with engine.begin() as conn:
        count = conn.execute(
            text(
                "SELECT count(*) FROM feedback_item WHERE title = :title",
            ),
            {"title": "React phase 3 submit smoke"},
        ).scalar_one()
    assert count == 1


def test_phase3_public_roadmap_and_changelog_render_seeded_items(
    live_phase3_public_url: str,
    truncate_world: None,
    page: Page,
) -> None:
    slug = _seed_shipped_item(
        live_phase3_public_url,
        "Phase3 shipped item",
        f"phase3-seed-{uuid.uuid4().hex[:8]}@example.com",
    )
    page.context.clear_cookies()

    page.goto(f"{live_phase3_public_url}/w/{slug}/roadmap/public")
    expect(page.get_by_text("Phase3 shipped item")).to_be_visible()

    page.goto(f"{live_phase3_public_url}/w/{slug}/changelog/public")
    expect(page.get_by_text("Phase3 shipped item")).to_be_visible()
    expect(page.get_by_text("Shipped during phase3 public smoke.")).to_be_visible()


def test_phase3_public_routes_ignore_legacy_query_param(
    live_phase3_public_url: str,
    truncate_world: None,
    page: Page,
) -> None:
    slug = _signup_and_login(
        page,
        live_phase3_public_url,
        f"phase3-legacy-{uuid.uuid4().hex[:8]}@example.com",
    )
    page.context.clear_cookies()

    page.goto(f"{live_phase3_public_url}/w/{slug}/roadmap/public?view=legacy")
    page.wait_for_load_state("networkidle")

    expect(page.locator("#sn-react-app-root")).to_have_count(1)
