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

Exit codes (see ``scripts/_ui.py::ExitCode``):
    0  OK       — dump written
    2  FAIL     — pg_dump or docker compose failed, or not in a repo
    64 USAGE    — docker not on PATH
"""

from __future__ import annotations

import argparse
import contextlib
import logging
import shutil
import subprocess  # nosec B404 — argv-only invocations below
import sys
from datetime import UTC, datetime
from pathlib import Path

# -- Local script modules (not third-party; live in scripts/) ----------------
from _colors import Colors, unicode_symbols
from _imports import find_repo_root
from _ui import UI, ExitCode

logger = logging.getLogger(__name__)

# --- Constants ---
SCRIPT_VERSION = "1.1.0"
THEME = "blue"


def _docker() -> str | None:
    return shutil.which("docker")


def _default_output(backups_dir: Path) -> Path:
    ts = datetime.now(tz=UTC).strftime("%Y%m%d-%H%M%S")
    return backups_dir / f"feedback-{ts}.sql"


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
        out = _default_output(Path("backups"))
        assert out.parent.name == "backups"
        assert out.suffix == ".sql"
        print(f"db_dump {SCRIPT_VERSION}: smoke ok")
        return int(ExitCode.OK)

    try:
        root = find_repo_root()
    except FileNotFoundError:
        logger.error(
            "Not inside a git repository. Run this command from the "
            "feedback-triage-app working tree."
        )
        return int(ExitCode.FAIL)

    backups_dir = root / "backups"

    docker = _docker()
    if docker is None:
        logger.error("docker not found in PATH")
        return int(ExitCode.USAGE)

    output = args.output or _default_output(backups_dir)
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
        return int(ExitCode.OK)

    ui.section("Running")
    # Stream pg_dump stdout straight to disk to avoid buffering large
    # dumps in memory; capture stderr for error reporting only.
    with output.open("wb") as fh:
        proc = subprocess.Popen(  # nosec B603 — argv list, no shell
            cmd,
            cwd=root,
            stdout=fh,
            stderr=subprocess.PIPE,
        )
        _, stderr = proc.communicate()
    if proc.returncode != 0:
        # Remove the partial dump so a stale file isn't mistaken for a
        # successful backup.
        with contextlib.suppress(OSError):
            output.unlink()
        logger.error(
            "%s pg_dump failed (rc=%d)\n%s",
            c.red(sym["cross"]),
            proc.returncode,
            stderr.decode("utf-8", errors="replace"),
        )
        return int(ExitCode.FAIL)

    bytes_written = output.stat().st_size
    print(
        f"  {c.green(sym['check'])} wrote "
        f"{c.cyan(str(output))} ({bytes_written:,} bytes)"
    )
    return int(ExitCode.OK)


if __name__ == "__main__":
    sys.exit(main())
