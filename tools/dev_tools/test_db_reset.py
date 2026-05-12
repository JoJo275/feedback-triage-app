#!/usr/bin/env python3
"""Rebuild the isolated pytest database and apply migrations.

This utility mirrors the test DB derivation strategy in
`tests/conftest.py`: if `TEST_DATABASE_URL` is set, use it;
otherwise derive a sibling database name by appending `_test`
to `DATABASE_URL`'s database.

Typical use:

    uv run python tools/dev_tools/test_db_reset.py
"""

from __future__ import annotations

import argparse
import logging
import os
import re

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from feedback_triage.config import Settings

SCRIPT_VERSION = "1.0.0"
_VALID_DB_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

logger = logging.getLogger(__name__)


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
        base_url = Settings().database_url.get_secret_value()
    base_url = _normalize_database_url(base_url)

    parsed = make_url(base_url)
    db_name = parsed.database
    if not db_name:
        msg = (
            "DATABASE_URL must include a database name for test DB reset. "
            "Set TEST_DATABASE_URL explicitly if needed."
        )
        raise RuntimeError(msg)

    target_name = db_name if db_name.endswith("_test") else f"{db_name}_test"
    return parsed.set(database=target_name).render_as_string(hide_password=False)


def _validate_db_name(db_name: str) -> None:
    if _VALID_DB_NAME.fullmatch(db_name):
        return
    msg = (
        "Unsafe test database name derived from URL: "
        f"{db_name!r}. Use TEST_DATABASE_URL with a simple identifier."
    )
    raise RuntimeError(msg)


def _drop_and_create_database(database_url: str) -> None:
    parsed = make_url(database_url)
    db_name = parsed.database or ""
    _validate_db_name(db_name)

    admin_engine = create_engine(
        parsed.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
        future=True,
    )
    try:
        with admin_engine.connect() as conn:
            conn.execute(
                text(
                    "SELECT pg_terminate_backend(pid) "
                    "FROM pg_stat_activity "
                    "WHERE datname = :name "
                    "AND pid <> pg_backend_pid()",
                ),
                {"name": db_name},
            )
            conn.execute(text(f'DROP DATABASE IF EXISTS "{db_name}"'))
            conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    finally:
        admin_engine.dispose()


def _upgrade_database_to_head(database_url: str) -> None:
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_cfg, "head")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="test_db_reset",
        description="Drop/recreate pytest database and run alembic upgrade head.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {SCRIPT_VERSION}",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="count",
        default=0,
        help="Decrease log verbosity.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase log verbosity.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the test DB reset flow and return a shell-friendly exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    level = logging.INFO - (10 * args.verbose) + (10 * args.quiet)
    logging.basicConfig(level=max(level, logging.DEBUG), format="%(message)s")

    database_url = _derive_test_database_url()
    database_name = make_url(database_url).database
    logger.info("Resetting pytest database: %s", database_name)

    _drop_and_create_database(database_url)
    _upgrade_database_to_head(database_url)

    logger.info("Pytest database is ready: %s", database_name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
