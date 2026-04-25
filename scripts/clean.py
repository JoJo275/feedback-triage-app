#!/usr/bin/env python3
"""Remove build artifacts and caches from the repository.

Cleans: dist/, build/, *.egg-info/, __pycache__/, .pytest_cache/,
.mypy_cache/, .ruff_cache/, .cache/, site/, .coverage, htmlcov/, *.pyc

Flags::

    --dry-run        Show what would be removed without deleting
    --include-venv   Also remove .venv* directories (requires confirmation)
    -y, --yes        Skip confirmation prompt for --include-venv
    -q, --quiet      Suppress informational output (exit code still shown)
    --version        Print version and exit

Usage::

    python scripts/clean.py
    python scripts/clean.py --dry-run
    python scripts/clean.py --quiet
    python scripts/clean.py --include-venv          # Also removes .venv directories
    python scripts/clean.py --include-venv --yes    # Skip confirmation prompt

    Task runner shortcuts for this script are defined in ``Taskfile.yml``.

Portability:
    Can be used in any Python repo — cleans standard build artifacts.
    Requires shared modules: ``_colors.py``, ``_imports.py``,
    ``_ui.py``, ``_progress.py``.
"""

from __future__ import annotations

import argparse
import contextlib
import logging
import shutil
import sys
from pathlib import Path

# -- Local script modules (not third-party; live in scripts/) ----------------
from _colors import Colors, unicode_symbols
from _imports import find_repo_root, import_sibling
from _ui import UI

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ROOT = find_repo_root()
SCRIPT_VERSION = "2.0.0"

# Theme color for this script's dashboard output.
THEME = "cyan"

ProgressBar = import_sibling("_progress").ProgressBar

# Top-level cache directories to remove
# TODO (template users): Add any project-specific cache directories here
#   (e.g. ".tox", ".nox", ".hypothesis") if your toolchain generates them.
CACHE_DIRS = [
    ".cache",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "htmlcov",
    "site",
]

# Top-level cache files to remove
CACHE_FILES = [
    ".coverage",
]

# Directories to remove recursively (anywhere in tree)
RECURSIVE_DIRS = [
    "__pycache__",
    "*.egg-info",
]

# Top-level build directories
BUILD_DIRS = [
    "dist",
    "build",
]

# File patterns to remove (skips files inside already-removed __pycache__ dirs)
FILE_PATTERNS = [
    "*.pyc",
    "*.pyo",
    ".coverage.*",
]

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


def remove_path(path: Path, *, dry_run: bool = False) -> bool | None:
    """Remove a file or directory.

    Args:
        path: Path to remove.
        dry_run: If True, only log what would be removed.

    Returns:
        True if path was (or would be) removed, None on error,
        False if path doesn't exist.
    """
    if not path.exists():
        return False

    kind = "directory" if path.is_dir() else "file"
    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        rel = path

    if dry_run:
        log.info("  Would remove %s: %s", kind, rel)
        return True

    try:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    except (OSError, PermissionError) as exc:
        log.warning("  Failed to remove %s: %s (%s)", kind, rel, exc)
        return None

    log.info("  Removed %s: %s", kind, rel)
    return True


def clean(
    *, dry_run: bool = False, include_venv: bool = False, quiet: bool = False
) -> tuple[int, int]:
    """Remove all build artifacts and caches.

    Args:
        dry_run: If True, only log what would be removed.
        include_venv: If True, also remove .venv* directories.
        quiet: If True, suppress headers and progress bars.

    Returns:
        Tuple of (items_removed, errors).
    """
    removed = 0
    errors = 0
    c = Colors()
    # Per-section counters for the summary
    section_counts: dict[str, int] = {}
    # Track bytes reclaimed
    bytes_reclaimed = 0

    # Track directories removed in previous phases so we don't double-count
    # files inside them (e.g. .pyc files inside already-removed __pycache__).
    removed_dirs: set[Path] = set()

    def _dir_size(path: Path) -> int:
        """Calculate total size of a directory tree."""
        total = 0
        try:
            for f in path.rglob("*"):
                if f.is_file():
                    total += f.stat().st_size
        except (OSError, PermissionError):
            pass
        return total

    def _track(result: bool | None, path: Path | None = None) -> None:
        """Update counters and track removed directories."""
        nonlocal removed, errors, bytes_reclaimed
        if result is True:
            removed += 1
            if path and path.is_dir():
                removed_dirs.add(path)
        elif result is None:
            errors += 1

    action = "Scanning" if dry_run else "Removing"
    sym = unicode_symbols()
    ui = UI(title="Clean", version=SCRIPT_VERSION, theme=THEME)
    if not quiet:
        ui.header()

    # ── Collect all targets first ────────────────────────────
    # Build a flat list of (section_label, path) so we can drive a single bar.
    all_targets: list[tuple[str, Path]] = []

    # Cache directories
    all_targets.extend(("cache items", ROOT / name) for name in CACHE_DIRS)
    all_targets.extend(("cache items", ROOT / name) for name in CACHE_FILES)

    # Build directories
    all_targets.extend(("build directories", ROOT / name) for name in BUILD_DIRS)

    # Recursive directories
    for pattern in RECURSIVE_DIRS:
        for path in sorted(ROOT.rglob(pattern)):
            if ".venv" in path.parts and not include_venv:
                continue
            all_targets.append(("recursive directories", path))

    # Stale file patterns
    for pattern in FILE_PATTERNS:
        for path in sorted(ROOT.rglob(pattern)):
            if ".venv" in path.parts and not include_venv:
                continue
            all_targets.append(("stale files", path))

    # Virtual environments (optional)
    if include_venv:
        all_targets.extend(
            ("virtual environments", venv_dir)
            for venv_dir in sorted(ROOT.glob(".venv*"))
            if venv_dir.is_dir()
        )

    # ── Single progress bar across all targets ───────────────
    bar = None
    if all_targets and not quiet:
        bar = ProgressBar(
            total=len(all_targets),
            label=action,
            color="cyan",
        )

    current_section = ""
    for section_label, path in all_targets:
        # Print section header when entering a new section
        if section_label != current_section:
            if current_section:
                # Spacing between sections
                log.info("")
            current_section = section_label
            section_counts.setdefault(section_label, 0)
            if not quiet:
                ui.section(f"{action} {section_label}")

        # Skip files inside already-removed directories
        if section_label == "stale files" and any(
            path.is_relative_to(d) for d in removed_dirs
        ):
            if bar:
                bar.update(path.name)
            continue

        # Measure size before removal
        if path.exists():
            if path.is_dir():
                bytes_reclaimed += _dir_size(path)
            elif path.is_file():
                with contextlib.suppress(OSError):
                    bytes_reclaimed += path.stat().st_size

        result = remove_path(path, dry_run=dry_run)
        _track(result, path if path.is_dir() else None)
        if result is True:
            section_counts[section_label] = section_counts.get(section_label, 0) + 1
        if bar:
            bar.update(path.name)

    if bar:
        bar.finish()

    # ── Summary ──────────────────────────────────────────────
    ok = sym["check"]
    fail = sym["cross"]
    verb = "Would remove" if dry_run else "Cleaned"

    log.info("")
    if not quiet:
        ui.section("Summary")

    for label, count in section_counts.items():
        if count > 0:
            log.info("  %s %s %d %s", c.green(ok), verb, count, label)

    if removed == 0:
        log.info("  %s", c.green(ok + " Nothing to clean — already tidy!"))
    else:
        log.info("")
        if not quiet:
            ui.separator()
        size_str = _format_size(bytes_reclaimed)
        log.info(
            "  Total: %s %d item(s)  %s %s",
            verb.lower(),
            removed,
            c.dim(sym["dash"]),
            c.cyan(f"{size_str} {'would be ' if dry_run else ''}reclaimed"),
        )

    if errors:
        log.info("")
        log.warning("  %s %d item(s) failed to remove", c.red(fail), errors)

    log.info("")
    return removed, errors


def _format_size(size_bytes: int) -> str:
    """Format bytes into a human-readable size string."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}" if unit != "B" else f"{size_bytes} {unit}"
        size_bytes /= 1024  # type: ignore[assignment]
    return f"{size_bytes:.1f} TB"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

_EPILOG = """\
exit codes:
  0  Clean completed successfully (or aborted by user)
  1  Error during cleanup
"""


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="clean",
        description="Remove build artifacts and caches from the repository.",
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {SCRIPT_VERSION}",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without deleting",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress informational output (exit code still shown)",
    )
    parser.add_argument(
        "--include-venv",
        action="store_true",
        help="Also remove .venv* directories (requires confirmation)",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompt for --include-venv",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Quick import and arg-parse health check; exit 0 immediately",
    )
    args = parser.parse_args()

    if args.smoke:
        print(f"clean {SCRIPT_VERSION}: smoke ok")
        return 0

    # Configure logging
    level = logging.WARNING if args.quiet else logging.INFO
    logging.basicConfig(format="%(message)s", level=level)

    if args.include_venv and not args.dry_run and not args.yes:
        # Guard against non-TTY stdin (e.g. piped input in CI)
        if not sys.stdin.isatty():
            log.error(
                "Cannot confirm interactively (stdin is not a TTY). "
                "Use --yes to skip the prompt."
            )
            return 1
        try:
            confirm = input("This will delete .venv* directories. Continue? [y/N] ")
        except (EOFError, KeyboardInterrupt):
            log.info("\nAborted.")
            return 0
        if confirm.lower() != "y":
            log.info("Aborted.")
            return 0

    _removed, err = clean(
        dry_run=args.dry_run, include_venv=args.include_venv, quiet=args.quiet
    )
    exit_code = 1 if err else 0

    # Always show exit code, even in quiet mode
    if args.quiet:
        print(f"exit {exit_code}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
