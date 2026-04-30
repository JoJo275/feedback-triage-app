#!/usr/bin/env python3
"""Seed the database with demo feedback items.

Used by ``task seed`` (locally and as a one-shot against production).
The seed set is deterministic: ~20 items covering every ``Source`` and
every ``Status`` value so the README screenshots and `/api/v1/docs`
examples have realistic data to display.

Idempotent: by default the script bails out if ``feedback_item`` is
non-empty. Pass ``--force`` to insert anyway (creates duplicates), or
``--reset`` to truncate first.
"""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass

from sqlalchemy import text

# -- Local script modules (not third-party; live in scripts/) ----------------
from _imports import import_sibling
from _ui import UI
from feedback_triage.crud import create_item
from feedback_triage.database import SessionLocal
from feedback_triage.enums import Source, Status
from feedback_triage.schemas import FeedbackCreate

_progress = import_sibling("_progress")
ProgressBar = _progress.ProgressBar

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCRIPT_VERSION = "1.0.0"

# Theme color for this script's dashboard output.
THEME = "green"


@dataclass(frozen=True)
class Demo:
    """A single demo row, kept terse so the seed list reads as a table."""

    title: str
    source: Source
    pain_level: int
    status: Status
    description: str | None = None


# 20 items. Every Source and every Status is represented at least once.
# Pain levels span the full 1-5 range. Wording is realistic-but-tame so
# the README screenshots are shareable.
DEMO_ITEMS: tuple[Demo, ...] = (
    Demo(
        "Login button hidden on mobile Safari",
        Source.SUPPORT,
        4,
        Status.NEW,
        "Reported by three customers on iOS 17 — button is below the fold "
        "with no scroll affordance.",
    ),
    Demo(
        "CSV export silently truncates at 1000 rows",
        Source.EMAIL,
        5,
        Status.REVIEWING,
        "Power user hit the cap exporting a quarterly report; no warning shown.",
    ),
    Demo(
        "Dark mode would be lovely",
        Source.TWITTER,
        2,
        Status.PLANNED,
    ),
    Demo(
        "Onboarding tour is too long",
        Source.INTERVIEW,
        3,
        Status.REVIEWING,
        "Five users in a row clicked Skip on step two of seven.",
    ),
    Demo(
        "Add Slack integration",
        Source.REDDIT,
        3,
        Status.PLANNED,
    ),
    Demo(
        "App crashes when offline for >10 minutes",
        Source.APP_STORE,
        5,
        Status.NEW,
        "One-star review citing data loss on flight mode.",
    ),
    Demo(
        "Settings page typo: 'colour' should be 'color'",
        Source.OTHER,
        1,
        Status.NEW,
    ),
    Demo(
        "Keyboard shortcut for new item",
        Source.SUPPORT,
        2,
        Status.PLANNED,
    ),
    Demo(
        "Email notifications arrive 30 min late",
        Source.EMAIL,
        4,
        Status.REVIEWING,
        "Suspect SMTP retry queue is misconfigured.",
    ),
    Demo(
        "Bring back the old icon",
        Source.TWITTER,
        1,
        Status.REJECTED,
    ),
    Demo(
        "Bulk archive button on list page",
        Source.INTERVIEW,
        3,
        Status.NEW,
    ),
    Demo(
        "Search returns deleted items",
        Source.SUPPORT,
        4,
        Status.REVIEWING,
        "Tombstone rows still indexed; cleanup job not running.",
    ),
    Demo(
        "Native Windows app",
        Source.REDDIT,
        2,
        Status.REJECTED,
        "Out of scope for v1; documented in spec — Future Improvements.",
    ),
    Demo(
        "Two-factor auth via TOTP",
        Source.EMAIL,
        4,
        Status.PLANNED,
    ),
    Demo(
        "Charts render slowly with >5k items",
        Source.APP_STORE,
        3,
        Status.NEW,
        "p95 paint time climbs from 200ms to 2.4s above 5k rows.",
    ),
    Demo(
        "Allow markdown in descriptions",
        Source.OTHER,
        2,
        Status.PLANNED,
    ),
    Demo(
        "Timezone displayed in UTC, not local",
        Source.SUPPORT,
        2,
        Status.NEW,
    ),
    Demo(
        "Accessibility: focus ring missing on tabs",
        Source.INTERVIEW,
        3,
        Status.REVIEWING,
        "Found in WCAG audit; reproduces in Firefox 124+.",
    ),
    Demo(
        "Export to JSON, not just CSV",
        Source.REDDIT,
        2,
        Status.PLANNED,
    ),
    Demo(
        "Make pain_level optional",
        Source.OTHER,
        1,
        Status.REJECTED,
        "Required by design — pain_level is the primary triage signal.",
    ),
)


def _row_count(session: object) -> int:
    """Return the current row count of ``feedback_item``."""
    # ``session`` is intentionally untyped here so the script doesn't
    # leak SQLAlchemy types into its narrow CLI surface.
    result = session.execute(  # type: ignore[attr-defined]
        text("SELECT count(*) FROM feedback_item"),
    )
    return int(result.scalar_one())


def _truncate(session: object) -> None:
    """Wipe the table (RESTART IDENTITY so ids stay tidy)."""
    session.execute(  # type: ignore[attr-defined]
        text("TRUNCATE TABLE feedback_item RESTART IDENTITY CASCADE"),
    )


def _insert_all(session: object) -> int:
    """Insert every demo row; return the count inserted."""
    with ProgressBar(
        total=len(DEMO_ITEMS),
        label="Seeding feedback_item",
        color=THEME,
    ) as bar:
        for demo in DEMO_ITEMS:
            payload = FeedbackCreate(
                title=demo.title,
                description=demo.description,
                source=demo.source,
                pain_level=demo.pain_level,
                status=demo.status,
            )
            create_item(session, payload)
            bar.update()
    return len(DEMO_ITEMS)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for ``task seed``."""
    parser = argparse.ArgumentParser(
        description="Seed the feedback_item table with ~20 demo rows.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Insert even if the table is non-empty (creates duplicates).",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="TRUNCATE the table first, then seed. Mutually exclusive with --force.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Connect to the DB and report what would happen, but do not write.",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run a self-check (no DB access) and exit.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {SCRIPT_VERSION}",
    )
    args = parser.parse_args(argv)

    if args.force and args.reset:
        parser.error("--force and --reset are mutually exclusive")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    if args.smoke:
        # No DB access: validate that the demo set is well-formed.
        assert len(DEMO_ITEMS) >= 1
        sources = {d.source for d in DEMO_ITEMS}
        statuses = {d.status for d in DEMO_ITEMS}
        assert sources == set(Source), "demo set missing a Source value"
        assert statuses == set(Status), "demo set missing a Status value"
        print(f"seed {SCRIPT_VERSION}: smoke ok ({len(DEMO_ITEMS)} rows)")
        return 0

    ui = UI(title="Seed Demo Data", version=SCRIPT_VERSION, theme=THEME)
    ui.header()

    session = SessionLocal()
    try:
        existing = _row_count(session)
        ui.section("Status")
        ui.kv("feedback_item rows", str(existing))
        ui.kv("demo rows available", str(len(DEMO_ITEMS)))

        if args.dry_run:
            ui.kv("mode", "dry-run (no writes)")
            ui.footer(passed=1, failed=0)
            return 0

        if existing > 0 and not (args.force or args.reset):
            logger.warning(
                "feedback_item is non-empty; refusing to seed. "
                "Pass --force to insert anyway, or --reset to truncate first.",
            )
            ui.footer(passed=0, failed=0, warned=1)
            return 1

        if args.reset and existing > 0:
            logger.info("--reset: truncating feedback_item")
            _truncate(session)

        inserted = _insert_all(session)
        session.commit()
        ui.section("Result")
        ui.kv("rows inserted", str(inserted))
        ui.footer(passed=inserted, failed=0)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
