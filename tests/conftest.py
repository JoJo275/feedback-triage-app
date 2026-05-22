"""Shared pytest fixtures for the API test suite.

The tests run against a real Postgres database (no SQLite — see spec —
Testing) and are isolated from local dev data by using a dedicated
``*_test`` database URL. Unless ``TEST_DATABASE_URL`` is set
explicitly, this module derives it from ``DATABASE_URL`` by appending
``_test`` to the database name.

Each test gets a fresh ``feedback_item`` via a ``TRUNCATE`` fixture;
we don't recreate the schema per test because the migration already ran
in CI / locally via ``task migrate``.

Phase 6 will expand this with a per-test schema or transaction-rollback
strategy. For Phase 3, truncate-between-tests is enough.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Iterator
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

_VALID_DB_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

if TYPE_CHECKING:
    from feedback_triage.config import Settings


def _normalize_database_url(raw: str) -> str:
    if raw.startswith("postgres://"):
        return "postgresql+psycopg://" + raw[len("postgres://") :]
    if raw.startswith("postgresql://"):
        return "postgresql+psycopg://" + raw[len("postgresql://") :]
    return raw


def _derive_test_database_url() -> str:
    explicit = os.environ.get("TEST_DATABASE_URL")
    if explicit:
        return _normalize_database_url(explicit)

    base_url = os.environ.get("DATABASE_URL")
    if not base_url:
        # Pull from `.env` via the application's own settings loader so
        # pytest respects local credentials even when DATABASE_URL isn't
        # exported in the shell session.
        from feedback_triage.config import Settings

        base_url = Settings().database_url.get_secret_value()
    base_url = _normalize_database_url(base_url)

    parsed = make_url(base_url)
    db_name = parsed.database
    if not db_name:
        msg = (
            "DATABASE_URL must include a database name for tests. "
            "Set TEST_DATABASE_URL explicitly if needed."
        )
        raise RuntimeError(msg)

    target_name = db_name if db_name.endswith("_test") else f"{db_name}_test"
    return parsed.set(database=target_name).render_as_string(hide_password=False)


def _ensure_database_exists(database_url: str) -> None:
    parsed = make_url(database_url)
    db_name = parsed.database or ""
    if not _VALID_DB_NAME.fullmatch(db_name):
        msg = (
            "Unsafe test database name derived from URL: "
            f"{db_name!r}. Use TEST_DATABASE_URL with a simple identifier."
        )
        raise RuntimeError(msg)

    admin_engine = create_engine(
        parsed.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
        future=True,
    )
    try:
        with admin_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": db_name},
            ).scalar_one_or_none()
            if exists is None:
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    finally:
        admin_engine.dispose()


def _upgrade_database_to_head(database_url: str) -> None:
    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_cfg, "head")


def _configure_test_database() -> None:
    test_database_url = _derive_test_database_url()
    os.environ["DATABASE_URL"] = test_database_url
    _ensure_database_exists(test_database_url)
    _upgrade_database_to_head(test_database_url)


_configure_test_database()


@pytest.fixture(scope="session", autouse=True)
def ensure_test_react_manifest() -> Iterator[None]:
    """Provide a deterministic React manifest for server-side page tests.

    CI runners don't build ``web/`` before Python-only test jobs, so the
    Vite manifest may be absent on a clean checkout. Many page-route tests
    assert the React shell responses and should not fail purely because local
    build artifacts are missing.
    """
    from feedback_triage.frontend_assets import REACT_MANIFEST, reset_manifest_cache

    existed = REACT_MANIFEST.exists()
    previous_manifest = REACT_MANIFEST.read_text(encoding="utf-8") if existed else ""
    created_paths = []

    if not existed:
        REACT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        REACT_MANIFEST.write_text(
            json.dumps(
                {
                    "index.html": {
                        "file": "assets/index-test.js",
                        "css": ["assets/index-test.css"],
                    }
                }
            ),
            encoding="utf-8",
        )

        assets_dir = REACT_MANIFEST.parent / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)

        js_path = assets_dir / "index-test.js"
        if not js_path.exists():
            js_path.write_text("// pytest stub react entrypoint\n", encoding="utf-8")
            created_paths.append(js_path)

        css_path = assets_dir / "index-test.css"
        if not css_path.exists():
            css_path.write_text(
                "/* pytest stub react stylesheet */\n", encoding="utf-8"
            )
            created_paths.append(css_path)

    reset_manifest_cache()
    yield

    if existed:
        REACT_MANIFEST.write_text(previous_manifest, encoding="utf-8")
    else:
        REACT_MANIFEST.unlink(missing_ok=True)
        for path in created_paths:
            path.unlink(missing_ok=True)
        assets_dir = REACT_MANIFEST.parent / "assets"
        if assets_dir.exists() and not any(assets_dir.iterdir()):
            assets_dir.rmdir()

    reset_manifest_cache()


@pytest.fixture(scope="session")
def settings() -> Settings:
    from feedback_triage.config import Settings

    return Settings(_env_file=None)  # type: ignore[call-arg]


@pytest.fixture
def truncate_feedback() -> Iterator[None]:
    """Wipe ``feedback_item`` and reset its identity sequence per test.

    ``CASCADE`` follows the v2 join tables (``feedback_tags``,
    ``feedback_notes``) so a re-run starts with no orphan rows. Also
    re-seeds the synthetic ``signalnest-legacy`` admin + workspace
    inserted by Migration A — the v2 isolation / session canary
    fixtures truncate ``users`` + ``workspaces`` between tests, so v1
    routes (which fall back to the legacy workspace per
    ``rollout.md``) need the rows re-created defensively.
    """
    from feedback_triage.database import engine

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE feedback_item RESTART IDENTITY CASCADE"))
        # Sentinel password hash: not a valid Argon2id encoded hash, so
        # login is disabled by construction (per ADR 062).
        conn.execute(
            text(
                """
                INSERT INTO users (id, email, password_hash, is_verified, role)
                SELECT gen_random_uuid(), 'legacy@signalnest.local',
                       '!disabled-legacy-v1-admin!', false, 'admin'
                 WHERE NOT EXISTS (
                    SELECT 1 FROM users WHERE email = 'legacy@signalnest.local'
                 )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO workspaces (id, slug, name, owner_id, is_demo)
                SELECT gen_random_uuid(), 'signalnest-legacy',
                       'SignalNest (legacy)', u.id, false
                  FROM users u
                 WHERE u.email = 'legacy@signalnest.local'
                   AND NOT EXISTS (
                    SELECT 1 FROM workspaces WHERE slug = 'signalnest-legacy'
                   )
                """
            )
        )
    yield


@pytest.fixture
def client(settings: Settings, truncate_feedback: None) -> Iterator[TestClient]:
    """FastAPI TestClient bound to the live Postgres database."""
    from feedback_triage.main import create_app

    app = create_app(settings)
    with TestClient(app) as c:
        yield c


@pytest.fixture
def truncate_auth_world() -> Iterator[None]:
    """Wipe every v2 auth/tenant table between tests."""
    from feedback_triage.database import engine

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


@pytest.fixture
def auth_settings() -> Settings:
    from feedback_triage.config import Settings

    return Settings(_env_file=None)  # type: ignore[call-arg]


@pytest.fixture
def auth_client(
    auth_settings: Settings,
    truncate_auth_world: None,
) -> Iterator[TestClient]:
    """TestClient for v2 auth/workspace flow tests."""
    from feedback_triage.main import create_app

    app = create_app(auth_settings)
    with TestClient(app) as c:
        yield c
