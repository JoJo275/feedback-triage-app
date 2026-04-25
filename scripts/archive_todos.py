#!/usr/bin/env python3
"""Archive completed TODO items from docs/notes/todo.md.

Moves checked items (``- [x]``) — including any indented sub-items beneath
them — from todo.md to archive.md, organized by month.  Creates a ``.bak``
backup of both files before writing unless ``--no-backup`` is passed.

This is a dev utility for personal note management, not distributed with
the package.

Flags::

    --dry-run         Show what would change without modifying files
    --no-backup       Skip creating .bak files before writing
    --todo-file PATH  Path to todo file (default: docs/notes/todo.md)
    --archive-file PATH  Path to archive file (default: docs/notes/archive.md)
    -q, --quiet       Suppress informational output (errors still shown)
    --version         Print version and exit

Usage::

    python scripts/archive_todos.py
    python scripts/archive_todos.py --dry-run
    python scripts/archive_todos.py --quiet
    python scripts/archive_todos.py --no-backup

    Task runner shortcuts for this script are defined in ``Taskfile.yml``.

Portability:
    Can be used in any repo — archives TODO items from Markdown notes.
    Requires shared modules: ``_colors.py``, ``_imports.py``,
    ``_ui.py``.
"""

from __future__ import annotations

import argparse
import logging
import re
import shutil
from datetime import datetime
from pathlib import Path

# -- Local script modules (not third-party; live in scripts/) ----------------
from _colors import Colors, unicode_symbols
from _imports import find_repo_root
from _ui import UI

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ROOT = find_repo_root()
SCRIPT_VERSION = "1.4.0"

# Theme color for this script's dashboard output.
THEME = "magenta"

DEFAULT_TODO = ROOT / "docs" / "notes" / "todo.md"
DEFAULT_ARCHIVE = ROOT / "docs" / "notes" / "archive.md"

# TODO (template users): If your project uses a different file for
#   tracking tasks (e.g. TODO.md at root), update DEFAULT_TODO and
#   DEFAULT_ARCHIVE paths above.

log = logging.getLogger(__name__)

# Matches a top-level completed item and any indented continuation lines
# (sub-items, notes) that belong to it.  Blank lines between a parent
# item and its indented children are tolerated — the ``(?:\n\n?(?=  )``
# alternation allows one optional blank line before an indented continuation.
_COMPLETED_BLOCK_RE = re.compile(
    r"^- \[[xX]\] .+(?:\n\n?(?=  ).*)*",
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


def _collect_completed_blocks(text: str) -> list[str]:
    """Return completed item blocks (including indented sub-items).

    Args:
        text: Full contents of the todo file.

    Returns:
        List of matched blocks, each potentially multi-line.
    """
    return _COMPLETED_BLOCK_RE.findall(text)


def _remove_blocks(text: str, blocks: list[str]) -> str:
    """Remove exact block occurrences from *text* and collapse blank lines.

    Uses regex escaping so special characters in items can't cause
    mismatches.

    Args:
        text: Original file content.
        blocks: Blocks to remove (as literal strings).

    Returns:
        Cleaned text with blocks removed and excess blank lines collapsed.
    """
    for block in blocks:
        # Escape the block and remove it along with its trailing newline
        pattern = re.escape(block) + r"\n?"
        text = re.sub(pattern, "", text, count=1)

    # Collapse triple-or-more blank lines down to double
    return re.sub(r"\n{3,}", "\n\n", text)


def _build_archive_content(
    archive_content: str,
    blocks: list[str],
    month_header: str,
) -> str:
    """Insert *blocks* into *archive_content* under *month_header*.

    Creates the month section and ``### Completed`` sub-heading if they
    don't already exist.

    Args:
        archive_content: Current archive file content.
        blocks: Completed item blocks to insert.
        month_header: E.g. ``"## February 2026"``.

    Returns:
        Updated archive content.
    """
    # Ensure trailing newline
    if not archive_content.endswith("\n"):
        archive_content += "\n"

    # Create month section if missing
    if month_header not in archive_content:
        archive_content += f"\n{month_header}\n\n### Completed\n\n"

    # Insert items after "### Completed\n" inside the month section
    month_section_pattern = re.compile(
        rf"({re.escape(month_header)}.*?)(### Completed\n+)", re.DOTALL
    )
    items_text = "\n".join(blocks) + "\n"

    match = month_section_pattern.search(archive_content)
    if match:
        insert_pos = match.end()
        archive_content = (
            archive_content[:insert_pos] + items_text + archive_content[insert_pos:]
        )
    else:
        archive_content += items_text

    return archive_content


def archive_todos(
    *,
    todo_file: Path = DEFAULT_TODO,
    archive_file: Path = DEFAULT_ARCHIVE,
    dry_run: bool = False,
    backup: bool = True,
) -> int:
    """Move completed TODO items from todo.md to archive.md.

    Args:
        todo_file: Path to the source todo file.
        archive_file: Path to the destination archive file.
        dry_run: If True, show what would change without modifying files.
        backup: If True, create ``.bak`` copies before writing.

    Returns:
        Number of items archived, or ``-1`` on error.
    """
    # Validate files exist
    c = Colors()
    if not todo_file.exists():
        log.error("File not found: %s", todo_file)
        return -1

    if not archive_file.exists():
        log.error("File not found: %s", archive_file)
        return -1

    # Read todo.md
    todo_content = todo_file.read_text(encoding="utf-8")

    # Collect completed blocks (items + sub-items)
    completed_blocks = _collect_completed_blocks(todo_content)

    if not completed_blocks:
        log.info("%s", c.green("No completed items found in todo.md"))
        return 0

    # Build updated file contents
    new_todo_content = _remove_blocks(todo_content, completed_blocks)

    archive_content = archive_file.read_text(encoding="utf-8")
    current_month = datetime.now().strftime("%B %Y")  # e.g., "February 2026"
    month_header = f"## {current_month}"
    new_archive_content = _build_archive_content(
        archive_content, completed_blocks, month_header
    )

    if dry_run:
        log.info(
            "%s Would archive %s item(s) to %s:",
            c.yellow("[dry-run]"),
            c.yellow(str(len(completed_blocks))),
            c.cyan(current_month),
        )
        for block in completed_blocks:
            for line in block.splitlines():
                log.info("  %s", c.dim(line))
        return len(completed_blocks)

    # Backup before writing
    if backup:
        shutil.copy2(todo_file, todo_file.with_suffix(".md.bak"))
        shutil.copy2(archive_file, archive_file.with_suffix(".md.bak"))

    # Write updated files
    todo_file.write_text(new_todo_content, encoding="utf-8")
    archive_file.write_text(new_archive_content, encoding="utf-8")

    sym = unicode_symbols()
    log.info(
        "%s Archived %s completed item(s) to %s:",
        c.green(sym["check"]),
        c.green(str(len(completed_blocks))),
        c.cyan(current_month),
    )
    for block in completed_blocks:
        for line in block.splitlines():
            log.info("  %s", c.dim(line))
    if backup:
        log.info(
            "%s Backups: %s, %s",
            c.dim(sym["info"]),
            c.dim(todo_file.with_suffix(".md.bak").name),
            c.dim(archive_file.with_suffix(".md.bak").name),
        )

    return len(completed_blocks)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="archive_todos",
        description="Archive completed TODO items from docs/notes/todo.md.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {SCRIPT_VERSION}",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without modifying files",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress informational output (errors still shown)",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating .bak files before writing",
    )
    parser.add_argument(
        "--todo-file",
        type=Path,
        default=DEFAULT_TODO,
        help="Path to todo file (default: %(default)s)",
    )
    parser.add_argument(
        "--archive-file",
        type=Path,
        default=DEFAULT_ARCHIVE,
        help="Path to archive file (default: %(default)s)",
    )
    args = parser.parse_args()

    # Configure logging: --quiet suppresses INFO, errors always shown
    level = logging.WARNING if args.quiet else logging.INFO
    logging.basicConfig(format="%(message)s", level=level)

    ui = UI(title="Archive TODOs", version=SCRIPT_VERSION, theme=THEME)
    if not args.quiet:
        ui.header()

    result = archive_todos(
        todo_file=args.todo_file,
        archive_file=args.archive_file,
        dry_run=args.dry_run,
        backup=not args.no_backup,
    )

    if not args.quiet:
        if result < 0:
            ui.status_line("cross", "Archive failed", "red")
        elif result == 0:
            ui.status_line("check", "No completed items to archive", "green")
        else:
            ui.status_line("check", f"Archived {result} item(s)", "green")

    return 1 if result < 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
