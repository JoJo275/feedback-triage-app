#!/usr/bin/env python3
"""Restore a SQL dump into the local docker-compose Postgres.

Replaces the cross-platform-fragile PowerShell one-liner that used to
live under the ``db:restore`` task in ``Taskfile.yml``. Streams the
dump file into ``docker compose exec -T db psql``.

DESTRUCTIVE: by design, the dumps written by ``db_dump.py`` use
``--clean --if-exists`` and will drop tables before recreating them.
Requires ``--yes`` to actually execute (Taskfile prompts for confirmation
before passing it through).

Flags::

    DUMP_PATH       Positional path to the .sql file to restore
    --service NAME  Compose service name (default: db)
    --user NAME     Postgres user (default: feedback)
    --db NAME       Database name (default: feedback)
    --yes           Confirm destructive restore (required)
    --dry-run       Print the plan without executing
    --version       Print version and exit
    --smoke         Self-check; exit 0 on success

Usage::

    python scripts/db_restore.py backups/feedback-20260501-120000.sql --yes

Exit codes (see ``scripts/_ui.py::ExitCode``):
    0  OK     — restore succeeded
    2  FAIL   — psql/docker failed, dump missing, or not in a repo
    64 USAGE  — missing path, missing --yes, or docker not on PATH
"""

from __future__ import annotations

import argparse
import logging
import shutil
import subprocess  # nosec B404 — argv-only invocations below
import sys
from pathlib import Path

# -- Local script modules (not third-party; live in scripts/) ----------------
from _colors import Colors, unicode_symbols
from _imports import find_repo_root
from _ui import UI, ExitCode

logger = logging.getLogger(__name__)

# --- Constants ---
SCRIPT_VERSION = "1.1.0"
THEME = "red"


def _docker() -> str | None:
    return shutil.which("docker")


def _build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        prog="db_restore",
        description=(
            "Restore a SQL dump into the local docker-compose Postgres. "
            "DESTRUCTIVE — requires --yes."
        ),
        epilog=(
            "Examples:\n"
            "  python scripts/db_restore.py backups/feedback-<ts>.sql --yes\n"
            "  python scripts/db_restore.py backups/x.sql --dry-run\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns the exit code."""
    parser = _build_parser()
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {SCRIPT_VERSION}"
    )
    parser.add_argument(
        "dump_path", type=Path, nargs="?", help="Path to the .sql dump file"
    )
    parser.add_argument("--service", default="db")
    parser.add_argument("--user", default="feedback")
    parser.add_argument("--db", default="feedback")
    parser.add_argument(
        "--yes", action="store_true", help="Confirm destructive restore"
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(format="%(message)s", level=logging.INFO)

    c = Colors()
    sym = unicode_symbols()
    ui = UI(title="DB Restore", version=SCRIPT_VERSION, theme=THEME)

    if args.smoke:
        assert SCRIPT_VERSION
        assert THEME
        print(f"db_restore {SCRIPT_VERSION}: smoke ok")
        return int(ExitCode.OK)

    if args.dump_path is None:
        logger.error(
            "%s missing dump path. Usage: db_restore.py <path.sql> --yes",
            c.red(sym["cross"]),
        )
        return int(ExitCode.USAGE)

    if not args.dump_path.exists():
        logger.error("%s dump file not found: %s", c.red(sym["cross"]), args.dump_path)
        return int(ExitCode.FAIL)

    if not args.yes and not args.dry_run:
        logger.error(
            "%s refusing destructive restore without --yes. "
            "(The Taskfile wrapper prompts; CLI users must pass it explicitly.)",
            c.red(sym["cross"]),
        )
        return int(ExitCode.USAGE)

    try:
        root = find_repo_root()
    except FileNotFoundError:
        logger.error(
            "Not inside a git repository. Run this command from the "
            "feedback-triage-app working tree."
        )
        return int(ExitCode.FAIL)

    docker = _docker()
    if docker is None:
        logger.error("docker not found in PATH")
        return int(ExitCode.USAGE)

    cmd = [
        docker,
        "compose",
        "exec",
        "-T",
        args.service,
        "psql",
        "-U",
        args.user,
        "-d",
        args.db,
    ]

    ui.header()
    ui.section("Plan")
    size = args.dump_path.stat().st_size
    print(f"  {c.dim('command:')} {' '.join(cmd)}")
    print(f"  {c.dim('input:  ')} {args.dump_path} ({size:,} bytes)")

    if args.dry_run:
        print(f"\n  {c.yellow('[dry-run]')} not executing")
        return int(ExitCode.OK)

    ui.section("Running")
    with args.dump_path.open("rb") as fh:
        proc = subprocess.run(  # nosec B603 — argv list, no shell
            cmd, cwd=root, stdin=fh, capture_output=True, check=False
        )

    if proc.returncode != 0:
        logger.error(
            "%s psql failed (rc=%d)\n%s",
            c.red(sym["cross"]),
            proc.returncode,
            proc.stderr.decode("utf-8", errors="replace"),
        )
        return int(ExitCode.FAIL)

    print(f"  {c.green(sym['check'])} restore complete")
    return int(ExitCode.OK)


if __name__ == "__main__":
    sys.exit(main())
