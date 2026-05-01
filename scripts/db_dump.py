#!/usr/bin/env python3
"""Dump the local docker-compose Postgres to a timestamped SQL file.

Replaces the cross-platform-fragile PowerShell one-liner that used to
live under the ``db:dump`` task in ``Taskfile.yml``. Calls
``docker compose exec -T db pg_dump`` and writes the output to
``backups/feedback-<UTC-timestamp>.sql``.

Production backups are handled by Railway. This script targets the
``db`` service in the local ``docker-compose.yml`` only.

Flags::

    --output PATH   Write to PATH instead of backups/feedback-<ts>.sql
    --service NAME  Compose service name (default: db)
    --user NAME     Postgres user (default: feedback)
    --db NAME       Database name (default: feedback)
    --dry-run       Print the command without executing
    --version       Print version and exit
    --smoke         Self-check (no docker calls); exit 0 on success

Usage::

    python scripts/db_dump.py
    python scripts/db_dump.py --output backups/manual.sql

Exit codes:
    0 = dump written
    1 = pg_dump or docker compose failed
    2 = docker not on PATH
"""

from __future__ import annotations

import argparse
import logging
import shutil
import subprocess  # nosec B404 — argv-only invocations below
import sys
from datetime import UTC, datetime
from pathlib import Path

# -- Local script modules (not third-party; live in scripts/) ----------------
from _colors import Colors, unicode_symbols
from _imports import find_repo_root
from _ui import UI

logger = logging.getLogger(__name__)

# --- Constants ---
SCRIPT_VERSION = "1.0.0"
THEME = "blue"
ROOT = find_repo_root()
BACKUPS_DIR = ROOT / "backups"


def _docker() -> str | None:
    return shutil.which("docker")


def _default_output() -> Path:
    ts = datetime.now(tz=UTC).strftime("%Y%m%d-%H%M%S")
    return BACKUPS_DIR / f"feedback-{ts}.sql"


def _build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        prog="db_dump",
        description="Dump local docker-compose Postgres to a SQL file.",
        epilog=(
            "Examples:\n"
            "  python scripts/db_dump.py\n"
            "  python scripts/db_dump.py --output backups/manual.sql\n"
            "  python scripts/db_dump.py --dry-run\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns the exit code."""
    parser = _build_parser()
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {SCRIPT_VERSION}"
    )
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--service", default="db")
    parser.add_argument("--user", default="feedback")
    parser.add_argument("--db", default="feedback")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(format="%(message)s", level=logging.INFO)

    if args.smoke:
        assert SCRIPT_VERSION
        assert THEME
        out = _default_output()
        assert out.parent.name == "backups"
        assert out.suffix == ".sql"
        print(f"db_dump {SCRIPT_VERSION}: smoke ok")
        return 0

    docker = _docker()
    if docker is None:
        logger.error("docker not found in PATH")
        return 2

    output = args.output or _default_output()
    output.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        docker,
        "compose",
        "exec",
        "-T",
        args.service,
        "pg_dump",
        "-U",
        args.user,
        "-d",
        args.db,
        "--clean",
        "--if-exists",
    ]

    c = Colors()
    sym = unicode_symbols()
    ui = UI(title="DB Dump", version=SCRIPT_VERSION, theme=THEME)
    ui.header()
    ui.section("Plan")
    print(f"  {c.dim('command:')} {' '.join(cmd)}")
    print(f"  {c.dim('output: ')} {output}")

    if args.dry_run:
        print(f"\n  {c.yellow('[dry-run]')} not executing")
        return 0

    ui.section("Running")
    proc = subprocess.run(  # nosec B603 — argv list, no shell
        cmd, cwd=ROOT, capture_output=True, check=False
    )
    if proc.returncode != 0:
        logger.error(
            "%s pg_dump failed (rc=%d)\n%s",
            c.red(sym["cross"]),
            proc.returncode,
            proc.stderr.decode("utf-8", errors="replace"),
        )
        return 1

    output.write_bytes(proc.stdout)
    print(
        f"  {c.green(sym['check'])} wrote "
        f"{c.cyan(str(output))} ({len(proc.stdout):,} bytes)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
