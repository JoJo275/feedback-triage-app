#!/usr/bin/env python3
"""Check docs/known-issues.md for stale Resolved entries.

Scans the "Resolved" table in ``docs/known-issues.md`` and flags entries
whose resolution date is older than a configurable threshold (default:
90 days — roughly one release cycle). Intended for CI to remind the team
to clean up resolved entries after they've been shipped.

Flags::

    --days N             Max age in days before a resolved entry is stale
                         (default: 90)
    --issues-path PATH   Path to known-issues.md
                         (default: docs/known-issues.md)
    --json               Output results as JSON (for CI integration)
    -q, --quiet          Suppress output; exit code only
    --version            Print version and exit

Exit codes::

    0  — No stale entries (or no resolved entries at all)
    1  — One or more stale resolved entries found
    2  — File not found or parse error

Usage::

    python scripts/check_known_issues.py
    python scripts/check_known_issues.py --days 60
    python scripts/check_known_issues.py --quiet
    python scripts/check_known_issues.py --json

    Task runner shortcuts for this script are defined in ``Taskfile.yml``.

Portability:
    Can be used in any repo with a ``docs/known-issues.md`` that follows
    the same Resolved table format.  Requires shared modules:
    ``_colors.py``, ``_imports.py``, ``_ui.py``.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from datetime import date, timedelta
from pathlib import Path

# -- Local script modules (not third-party; live in scripts/) ----------------
from _colors import Colors, unicode_symbols
from _imports import find_repo_root
from _ui import UI

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ROOT = find_repo_root()
SCRIPT_VERSION = "1.3.0"

# Theme color for this script's dashboard output.
THEME = "red"
# TODO (template users): If you move or rename docs/known-issues.md, update
#   this default path and the --issues-path help text below.
DEFAULT_ISSUES_PATH = ROOT / "docs" / "known-issues.md"
DEFAULT_MAX_AGE_DAYS = 90

# Matches a Markdown table row with 4 cells: | Area | Issue | Resolution | Date |
# The date cell is expected to contain an ISO date (YYYY-MM-DD) or be empty.
# TODO: This regex does not handle escaped pipes (\|) inside cells.
#   In practice this is rare in known-issues.md, but if you see false
#   negatives in CI, consider switching to a proper Markdown table parser.
_TABLE_ROW_RE = re.compile(
    r"^\|"
    r"\s*(?P<area>[^|]*?)\s*\|"
    r"\s*(?P<issue>[^|]*?)\s*\|"
    r"\s*(?P<resolution>[^|]*?)\s*\|"
    r"\s*(?P<date>[^|]*?)\s*\|",
)
_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")

# Accept common heading variants:
#   ## Resolved   |   ## Resolved Issues   |   ## Resolved Known Issues
_RESOLVED_HEADING_RE = re.compile(r"^##\s+Resolved", re.IGNORECASE)

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


def parse_resolved_entries(text: str) -> list[dict[str, str]]:
    """Extract rows from the Resolved table in known-issues.md.

    Args:
        text: Full file content of known-issues.md.

    Returns:
        List of dicts with keys: area, issue, resolution, date.
        Only rows with non-empty area AND a parseable date are returned.
    """
    in_resolved = False
    entries: list[dict[str, str]] = []

    for line in text.splitlines():
        stripped = line.strip()

        # Detect the "## Resolved" heading (and common variants)
        if _RESOLVED_HEADING_RE.match(stripped):
            in_resolved = True
            continue

        # Stop at the next heading
        if in_resolved and stripped.startswith("## "):
            break

        if not in_resolved:
            continue

        # Skip separator rows (| :--- | :--- | ... |) and header rows
        if not stripped.startswith("|"):
            continue
        if re.match(r"^\|\s*:?-+", stripped):
            continue

        match = _TABLE_ROW_RE.match(stripped)
        if not match:
            continue

        area = match.group("area").strip()
        issue = match.group("issue").strip()
        resolution = match.group("resolution").strip()
        date_str = match.group("date").strip()

        # Skip empty rows (template placeholder) and header row
        if not area or area.lower() == "area":
            continue

        entries.append(
            {
                "area": area,
                "issue": issue,
                "resolution": resolution,
                "date": date_str,
            }
        )

    return entries


def find_stale_entries(
    entries: list[dict[str, str]],
    max_age_days: int,
    today: date | None = None,
) -> list[dict[str, object]]:
    """Find resolved entries older than the threshold.

    Args:
        entries: Parsed resolved entries from ``parse_resolved_entries()``.
        max_age_days: Number of days after which an entry is stale.
        today: Override for the current date (for testing).

    Returns:
        List of stale entries, each augmented with ``age_days`` and
        ``parsed_date`` fields.
    """
    if today is None:
        today = date.today()

    threshold = today - timedelta(days=max_age_days)
    stale: list[dict[str, object]] = []

    for entry in entries:
        date_match = _DATE_RE.search(entry["date"])
        if not date_match:
            log.debug("Skipping entry with unparsable date: %s", entry)
            continue

        try:
            resolved_date = date.fromisoformat(date_match.group())
        except ValueError:
            log.warning("Invalid date format in entry: %s", entry["date"])
            continue

        if resolved_date < threshold:
            stale.append(
                {
                    **entry,
                    "parsed_date": resolved_date.isoformat(),
                    "age_days": (today - resolved_date).days,
                }
            )

    return stale


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Check docs/known-issues.md for stale resolved entries. "
            "Exits non-zero if any entry has been in the Resolved table "
            "longer than --days."
        ),
    )
    parser.add_argument(
        "--days",
        type=int,
        default=DEFAULT_MAX_AGE_DAYS,
        metavar="N",
        help=f"Max age in days for resolved entries (default: {DEFAULT_MAX_AGE_DAYS})",
    )
    parser.add_argument(
        "--issues-path",
        type=Path,
        default=DEFAULT_ISSUES_PATH,
        metavar="PATH",
        help="Path to known-issues.md (default: docs/known-issues.md)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results as JSON",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress output; exit code only",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {SCRIPT_VERSION}",
    )
    # TODO: Consider adding a --warn flag that exits 0 but prints
    #   warnings instead of failing.  Useful for advisory CI checks
    #   that shouldn't block merges.
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Quick import and arg-parse health check; exit 0 immediately",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the known-issues checker.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code: 0 = clean, 1 = stale entries found, 2 = error.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.smoke:
        print(f"check_known_issues {SCRIPT_VERSION}: smoke ok")
        return 0

    logging.basicConfig(
        level=logging.WARNING if args.quiet else logging.INFO,
        format="%(message)s",
    )

    issues_path: Path = args.issues_path
    if not issues_path.exists():
        log.error("File not found: %s", issues_path)
        return 2

    try:
        text = issues_path.read_text(encoding="utf-8")
    except OSError as exc:
        log.error("Cannot read %s: %s", issues_path, exc)
        return 2

    entries = parse_resolved_entries(text)
    if not entries:
        c = Colors()
        sym = unicode_symbols()
        print(c.green(f"No resolved entries found {sym['dash']} nothing to check."))
        return 0

    stale = find_stale_entries(entries, max_age_days=args.days)

    if args.json_output:
        result = {
            "total_resolved": len(entries),
            "stale_count": len(stale),
            "max_age_days": args.days,
            "stale_entries": stale,
        }
        print(json.dumps(result, indent=2, default=str))
    elif not args.quiet:
        c = Colors()
        sym = unicode_symbols()
        ui = UI(title="Known Issues Check", version=SCRIPT_VERSION, theme=THEME)
        ui.header()
        # All human-readable output goes to stdout so that callers
        # (e.g. Taskfile, PowerShell) don't treat it as an error.
        if stale:
            noun = "entry" if len(stale) == 1 else "entries"
            ui.section(
                f"Found {len(stale)} stale resolved {noun} "
                f"(older than {args.days} days)"
            )
            for entry in stale:
                print(
                    f"    {c.red(sym['cross'])} [{c.cyan(str(entry['area']))}] "
                    f"{entry['issue']} {sym['dash']} resolved "
                    f"{c.dim(str(entry['parsed_date']))} "
                    f"({c.yellow(str(entry['age_days']))} days ago)"
                )
            ui.footer(
                passed=len(entries) - len(stale),
                failed=len(stale),
            )
        else:
            ui.section("Results")
            ui.status_line(
                "check",
                f"All {len(entries)} resolved entries are within "
                f"the {args.days}-day window.",
                "green",
            )
            ui.footer(passed=len(entries), failed=0)

    return 1 if stale else 0


if __name__ == "__main__":
    raise SystemExit(main())
