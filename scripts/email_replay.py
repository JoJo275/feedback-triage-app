#!/usr/bin/env python3
"""Re-send a previously failed (or stuck retrying) ``email_log`` row.

Wraps :meth:`feedback_triage.email.client.EmailClient.replay`. Used
when a transient Resend outage leaves rows at ``status='failed'`` —
once the provider is back, ``task email:replay <log-id>`` drains the
backlog one row at a time.

Usage::

    task email:replay -- <log-uuid>
    python scripts/email_replay.py <log-uuid>
    python scripts/email_replay.py <log-uuid> --dry-run
    python scripts/email_replay.py --smoke

Exit codes: see :class:`scripts._ui.ExitCode`.
"""

from __future__ import annotations

import argparse
import logging
import sys
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import select

# -- Local script modules (not third-party; live in scripts/) ----------------
from _ui import UI, ExitCode
from feedback_triage.database import SessionLocal
from feedback_triage.enums import EmailStatus

if TYPE_CHECKING:
    from feedback_triage.models import EmailLog

logger = logging.getLogger(__name__)

SCRIPT_VERSION = "1.0.0"
THEME = "magenta"


def _load_env() -> None:
    """All env reads happen via :class:`feedback_triage.config.Settings`.

    Kept here so the conventions checklist is satisfied and future
    additions stay centralized.
    """
    return None


def _load_row(log_id: uuid.UUID) -> EmailLog | None:
    # Local import: keeps ``--smoke`` from touching the DB-bound model
    # registry until it has to.
    from feedback_triage.models import EmailLog

    with SessionLocal() as session:
        return session.scalar(select(EmailLog).where(EmailLog.id == log_id))


def _build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        prog="email_replay",
        description=(
            "Re-send a failed transactional email. Loads the email_log "
            "row by id, asserts it is in a replayable terminal state, "
            "and re-issues the send via the same EmailClient that the "
            "API uses (subject to RESEND_DRY_RUN)."
        ),
        epilog=(
            "Examples:\n"
            "  task email:replay -- 11111111-2222-3333-4444-555555555555\n"
            "  python scripts/email_replay.py "
            "11111111-2222-3333-4444-555555555555 --dry-run\n"
            "  python scripts/email_replay.py --smoke\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. See :class:`scripts._ui.ExitCode`."""
    parser = _build_parser()
    parser.add_argument(
        "log_id",
        nargs="?",
        help="UUID of the email_log row to replay (omit with --smoke).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load + validate the row but do not call the client.",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Self-check (no DB / no network); exit 0 on success.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="count",
        default=0,
        help="Suppress informational output (repeatable).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="More log detail (repeatable).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {SCRIPT_VERSION}",
    )
    args = parser.parse_args(argv)

    level = logging.INFO - 10 * args.verbose + 10 * args.quiet
    logging.basicConfig(level=max(level, logging.DEBUG), format="%(message)s")

    if args.smoke:
        # No DB / no network. Validate constants + that argparse + UI
        # wiring is intact.
        assert SCRIPT_VERSION
        assert THEME
        assert ExitCode.OK == 0
        print(f"email_replay {SCRIPT_VERSION}: smoke ok")
        return int(ExitCode.OK)

    _load_env()

    if not args.log_id:
        parser.error("log_id is required (or pass --smoke)")

    try:
        log_id = uuid.UUID(args.log_id)
    except ValueError:
        logger.error("Not a valid UUID: %s", args.log_id)
        return int(ExitCode.USAGE)

    ui = UI(title="Email Replay", version=SCRIPT_VERSION, theme=THEME)
    ui.header()

    row = _load_row(log_id)
    if row is None:
        logger.error("email_log row %s not found", log_id)
        ui.footer(passed=0, failed=1)
        return int(ExitCode.FAIL)

    ui.section("Source row")
    ui.kv("id", str(log_id))
    ui.kv("purpose", row.purpose.value)
    ui.kv("template", row.template)
    ui.kv("to", row.to_address)
    ui.kv("status", row.status.value)
    ui.kv("attempts", str(row.attempt_count))

    if row.status not in {EmailStatus.FAILED, EmailStatus.RETRYING}:
        logger.error(
            "row %s is in status %r; only failed/retrying rows can be replayed",
            log_id,
            row.status.value,
        )
        ui.footer(passed=0, failed=1)
        return int(ExitCode.FAIL)

    if args.dry_run:
        ui.kv("mode", "dry-run (no send)")
        ui.footer(passed=1, failed=0)
        return int(ExitCode.OK)

    # Local import: avoids loading httpx + the Settings cache during --smoke.
    from feedback_triage.email import get_email_client

    result = get_email_client().replay(log_id)

    ui.section("Result")
    ui.kv("status", result.status.value)
    ui.kv("provider_id", result.provider_id or "—")

    if result.status is EmailStatus.SENT:
        ui.footer(passed=1, failed=0)
        return int(ExitCode.OK)

    ui.footer(passed=0, failed=1)
    return int(ExitCode.FAIL)


if __name__ == "__main__":
    sys.exit(main())
