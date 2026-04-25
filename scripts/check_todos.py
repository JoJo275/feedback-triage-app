#!/usr/bin/env python3
"""Scan for TODO (template users) comments and report customization status.

After forking this template, many files contain ``TODO (template users):``
comments that need to be addressed. This script finds them all and reports
which ones remain, grouped by file.

Flags::

    --pattern TEXT      Text pattern to search for (default: "TODO (template users)")
    --count             Only print the count of TODOs found
    --json              Output results as JSON (for CI integration)
    --exclude PREFIX    Additional path prefixes to exclude (repeatable)
    --version           Print version and exit

Usage::

    python scripts/check_todos.py
    python scripts/check_todos.py --count
    python scripts/check_todos.py --json
    python scripts/check_todos.py --pattern "TODO"
    python scripts/check_todos.py --exclude docs/notes

    Task runner shortcuts for this script are defined in ``Taskfile.yml``.

Portability:
    Can be used in any repo — scans for a configurable text pattern.
    Requires shared modules: ``_colors.py``, ``_imports.py``,
    ``_ui.py``, ``_progress.py``.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import logging
from pathlib import Path

# -- Local script modules (not third-party; live in scripts/) ----------------
from _colors import Colors, unicode_symbols
from _imports import find_repo_root, import_sibling
from _ui import UI

_progress = import_sibling("_progress")
ProgressBar = _progress.ProgressBar

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ROOT = find_repo_root()
SCRIPT_VERSION = "1.4.0"

# Theme color for this script's dashboard output.
THEME = "yellow"
# TODO (template users): Change DEFAULT_PATTERN if your project uses a
#   different convention for TODO markers (e.g., "FIXME", "HACK", or
#   "TODO (fork users)").
DEFAULT_PATTERN = "TODO (template users)"

# Directory names to skip (exact path-component match).
DEFAULT_EXCLUDE = {
    ".git",
    ".venv",
    ".venv-1",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    "node_modules",
    "site",
}

# Directory name suffixes to skip.  A path component whose name *ends with*
# one of these is excluded (e.g. ".egg-info" matches
# "simple_python_boilerplate.egg-info").
DEFAULT_EXCLUDE_SUFFIXES = {
    ".egg-info",
}

# File extensions to scan (text files only)
SCAN_EXTENSIONS = {
    ".py",
    ".pyi",
    ".toml",
    ".yml",
    ".yaml",
    ".md",
    ".rst",
    ".txt",
    ".cfg",
    ".ini",
    ".json",
    ".sh",
    ".ps1",
    ".bat",
    ".html",
    ".css",
    ".js",
    ".ts",
    ".sql",
    ".env",
    ".containerfile",
    ".dockerfile",
    ".xml",
    ".properties",
    ".gitignore",
    ".gitattributes",
    ".editorconfig",
    ".flake8",
    ".pylintrc",
    ".pre-commit-config",
    ".dockerignore",
    ".j2",
    ".jinja2",
    ".tf",
    ".hcl",
    ".lock",
    ".csv",
    ".r",
    ".rb",
    ".go",
    ".java",
    ".c",
    ".h",
    ".cpp",
    ".rs",
    ".lua",
    ".tex",
    ".bib",
    ".graphql",
    ".proto",
    ".conf",
}

# Extensionless filenames that should always be scanned
SCAN_FILENAMES = {
    "Containerfile",
    "Dockerfile",
    "Makefile",
    "Taskfile",
    "Procfile",
    "Vagrantfile",
    "Rakefile",
    "Gemfile",
    "LICENSE",
    "CODEOWNERS",
    "FUNDING",
}

# Binary extensions to always skip (never try to read these)
BINARY_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".bmp",
    ".webp",
    ".svg",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".otf",
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
    ".7z",
    ".rar",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".bin",
    ".obj",
    ".o",
    ".pyc",
    ".pyo",
    ".class",
    ".jar",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".sqlite3",
    ".db",
    ".sqlite",
    ".whl",
    ".egg",
    ".mp3",
    ".mp4",
    ".avi",
    ".mov",
    ".wav",
    ".pgp",
    ".asc",
    ".sig",
    ".gpg",
}

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


def _is_excluded(
    path: Path,
    exclude_dirs: set[str],
    exclude_suffixes: set[str],
) -> bool:
    """Check whether *path* falls under an excluded directory.

    Supports two matching modes:

    * **Exact match** — the directory name equals an entry in *exclude_dirs*
      (e.g. ``".git"``, ``"__pycache__"``).
    * **Suffix match** — the directory name *ends with* an entry in
      *exclude_suffixes* (e.g. ``".egg-info"`` matches
      ``"simple_python_boilerplate.egg-info"``).

    Args:
        path: File path to test.
        exclude_dirs: Set of directory names to exclude (exact match).
        exclude_suffixes: Set of suffixes to exclude (endswith match).

    Returns:
        True if the path should be skipped.
    """
    for part in path.parts:
        if part in exclude_dirs:
            return True
        if any(part.endswith(sfx) for sfx in exclude_suffixes):
            return True
    return False


def find_todos(
    root: Path,
    pattern: str,
    exclude_dirs: set[str],
    extra_excludes: list[str] | None = None,
    exclude_suffixes: set[str] | None = None,
    *,
    show_progress: bool = False,
) -> tuple[dict[Path, list[tuple[int, str]]], int]:
    """Find all lines matching the pattern, grouped by file.

    Args:
        root: Project root directory.
        pattern: Text pattern to search for (case-insensitive).
        exclude_dirs: Directory names to skip entirely.
        extra_excludes: Additional path prefixes to exclude.
        exclude_suffixes: Directory name suffixes to skip.
        show_progress: Show a progress bar while scanning.

    Returns:
        Tuple of (results dict mapping file paths to matches, files_scanned count).
    """
    results: dict[Path, list[tuple[int, str]]] = {}
    pattern_lower = pattern.lower()
    extra = [Path(root / e) for e in (extra_excludes or [])]
    suffixes = exclude_suffixes or set()
    files_scanned = 0

    # Collect candidate files first so we can show a progress bar
    candidates: list[tuple[Path, bool]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() in BINARY_EXTENSIONS:
            continue
        is_known_text = (
            path.suffix.lower() in SCAN_EXTENSIONS or path.name in SCAN_FILENAMES
        )
        if _is_excluded(path, exclude_dirs, suffixes):
            continue
        if any(path.is_relative_to(e) for e in extra):
            continue
        candidates.append((path, is_known_text))

    bar: ProgressBar | contextlib.nullcontext[None] = (
        ProgressBar(
            total=len(candidates), label="Scanning files", color="cyan", pulse=True
        )
        if show_progress
        else contextlib.nullcontext()
    )

    with bar as active_bar:
        for path, is_known_text in candidates:
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except (OSError, PermissionError):
                if active_bar:
                    active_bar.update()
                continue
            # Skip files that look binary (contain null bytes in first 8KB)
            if not is_known_text and "\x00" in text[:8192]:
                if active_bar:
                    active_bar.update()
                continue

            files_scanned += 1
            if active_bar:
                active_bar.update(str(path.relative_to(root)))
            matches = []
            for i, line in enumerate(text.splitlines(), start=1):
                if pattern_lower in line.lower():
                    matches.append((i, line.rstrip()))

            if matches:
                results[path] = matches
    log.debug("Scanned %d file(s)", files_scanned)
    return results, files_scanned


def format_report(
    results: dict[Path, list[tuple[int, str]]],
    root: Path,
    *,
    count_only: bool = False,
    as_json: bool = False,
    colors: Colors | None = None,
    files_scanned: int = 0,
    skip_header: bool = False,
) -> str:
    """Build a report string for the found TODOs.

    Args:
        results: Output from find_todos().
        root: Project root (for relative path display).
        count_only: If True, only return summary counts.
        as_json: If True, return a JSON-encoded report.
        colors: Colors instance for styled output.
        files_scanned: Total number of files scanned.
        skip_header: If True, omit the title header (caller already printed it).

    Returns:
        Formatted report string.
    """
    total = sum(len(matches) for matches in results.values())
    c = colors or Colors(enabled=False)

    if as_json:
        data = {
            "total": total,
            "file_count": len(results),
            "files_scanned": files_scanned,
            "files": {
                path.relative_to(root).as_posix(): [
                    {"line": num, "text": text.strip()} for num, text in matches
                ]
                for path, matches in results.items()
            },
        }
        return json.dumps(data, indent=2)

    if count_only:
        count_str = c.yellow(str(total)) if total else c.green(str(total))
        return f"{count_str} TODO(s) across {len(results)} file(s)"

    if not results:
        sym = unicode_symbols()
        return c.green(
            f"{sym['check']} No TODOs found {sym['dash']} template has been fully customized!"
        )

    sym = unicode_symbols()
    ui = UI(title="TODO Scanner", version=SCRIPT_VERSION, theme=THEME)
    lines: list[str] = []

    # Header (double-border box)
    if not skip_header:
        lines.append("")
        lines.append(c.bold(ui._themed(f"  {ui.tl_d}{ui.h_double * 60}{ui.tr_d}")))
        lines.append(
            f"  {c.bold(ui._themed(ui.vl_d))} "
            f"{c.bold(ui._themed('TODO Scanner'))}  "
            f"{c.dim(f'v{SCRIPT_VERSION}')}"
        )
        lines.append(c.bold(ui._themed(f"  {ui.bl_d}{ui.h_double * 60}{ui.br_d}")))

    # Section: results
    lines.append("")
    lines.append(ui._themed(f"  {ui.tl}{ui.h_line * 60}{ui.tr}"))
    lines.append(
        f"  {ui._themed(ui.vl)} {c.bold(f'Found {c.yellow(str(total))} TODO(s) across {c.yellow(str(len(results)))} file(s)')}"
    )
    lines.append(ui._themed(f"  {ui.bl}{ui.h_line * 60}{ui.br}"))
    lines.append("")

    for path, matches in results.items():
        rel = path.relative_to(root)
        match_count = len(matches)
        suffix = "es" if match_count != 1 else ""
        lines.append(
            f"    {c.yellow(str(rel))}  {c.dim(f'({match_count} match{suffix})')}"
        )
        lines.append("")
        for line_num, line_text in matches:
            display = line_text.strip()
            if len(display) > 100:
                display = display[:97] + "..."
            lines.append(f"      {c.dim('L' + str(line_num) + ':')} {display}")
        lines.append("")

    # Footer
    lines.append(f"  {c.dim(ui.h_double * 60)}")
    lines.append("")
    scanned_info = f" (scanned {files_scanned} files)" if files_scanned else ""
    lines.append(
        f"  {c.yellow(sym['flag'])} {total} TODO(s) remaining{scanned_info} "
        f"{sym['dash']} run with --json for CI integration"
    )
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

_EPILOG = """\
exit codes:
  0  No TODOs found (template fully customized)
  1  TODOs remain (useful as a CI gate)
"""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Scan for TODO (template users) comments in the repository.",
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {SCRIPT_VERSION}",
    )
    parser.add_argument(
        "--pattern",
        default=DEFAULT_PATTERN,
        help=f'Text pattern to search for (default: "{DEFAULT_PATTERN}")',
    )
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "--count",
        action="store_true",
        help="Only print the count of TODOs found",
    )
    output_group.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results as JSON (for CI integration)",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Additional path prefixes to exclude (relative to project root)",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Quick import and arg-parse health check; exit 0 immediately",
    )
    return parser.parse_args(argv)


def main() -> int:
    """Entry point for the check_todos script.

    Returns:
        Exit code: 0 if no TODOs found, 1 if TODOs remain.
    """
    args = parse_args()

    if args.smoke:
        print(f"check_todos {SCRIPT_VERSION}: smoke ok")
        return 0

    # Configure logging
    logging.basicConfig(format="%(message)s", level=logging.INFO)

    c = Colors()
    show_progress = not args.json_output and not args.count

    results, files_scanned = find_todos(
        root=ROOT,
        pattern=args.pattern,
        exclude_dirs=DEFAULT_EXCLUDE,
        extra_excludes=args.exclude,
        exclude_suffixes=DEFAULT_EXCLUDE_SUFFIXES,
        show_progress=show_progress,
    )

    if show_progress:
        ui = UI(title="TODO Scanner", version=SCRIPT_VERSION, theme=THEME)
        ui.header()

    report = format_report(
        results,
        ROOT,
        count_only=args.count,
        as_json=args.json_output,
        colors=c,
        files_scanned=files_scanned,
        skip_header=show_progress,
    )
    # All human-readable output goes to stdout so that callers
    # (e.g. Taskfile, PowerShell) don't treat it as an error.
    print(report)

    # Non-zero exit if TODOs remain (useful in CI)
    return 1 if results else 0


if __name__ == "__main__":
    raise SystemExit(main())
