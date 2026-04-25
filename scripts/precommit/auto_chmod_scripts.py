#!/usr/bin/env python3
"""Pre-commit hook: auto-add executable bit to new scripts with shebangs.

When a new script is staged for commit and contains a shebang line
(``#!/usr/bin/env python3``, ``#!/bin/bash``, etc.) but is not marked
executable, this hook automatically runs ``git add --chmod=+x`` on it.

This eliminates the common mistake of forgetting to set the executable
bit when adding new scripts — one of the most frequent friction points
in the development workflow.

Usage (called by pre-commit, receives filenames as arguments)::

    python scripts/precommit/auto_chmod_scripts.py file1 file2 ...

Flags::

    files             Files to check (positional, passed by pre-commit)
    --version         Print version and exit

Exit codes:
    0 — all files are fine (or were auto-fixed)
    1 — git chmod failed on one or more files
"""

from __future__ import annotations

import argparse
import shutil
import subprocess  # nosec B404
from pathlib import Path

SCRIPT_VERSION = "1.0.0"

_GIT_CMD: str | None = shutil.which("git")

# Common shebang prefixes that indicate an executable script
_SHEBANG_PREFIX = b"#!"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Auto-add executable bit to scripts with shebangs.",
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Files to check (passed by pre-commit).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {SCRIPT_VERSION}",
    )
    return parser


def _has_shebang(path: Path) -> bool:
    """Return True if the file starts with a shebang line."""
    try:
        with path.open("rb") as f:
            first_line = f.readline(256)
        return first_line.startswith(_SHEBANG_PREFIX)
    except OSError:
        return False


def _is_executable_in_git(path: str) -> bool:
    """Check if git already tracks the file as executable."""
    if _GIT_CMD is None:
        return True  # can't check, assume ok
    try:
        result = subprocess.run(  # nosec B603
            [_GIT_CMD, "ls-files", "--stage", "--", path],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return True  # not tracked or error, skip
        # Output format: "100755 <hash> <stage>\t<path>" or "100644 ..."
        mode = result.stdout.strip().split()[0]
        return mode == "100755"
    except (subprocess.TimeoutExpired, OSError):
        return True  # can't check, assume ok


def _git_chmod_add(path: str) -> bool:
    """Run ``git add --chmod=+x`` on the file. Return True on success."""
    if _GIT_CMD is None:
        return False
    try:
        result = subprocess.run(  # nosec B603
            [_GIT_CMD, "add", "--chmod=+x", "--", path],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def main() -> int:
    """Entry point."""
    parser = _build_parser()
    args = parser.parse_args()

    fixed: list[str] = []
    failures: list[str] = []

    for filepath in args.files:
        p = Path(filepath)
        if not p.is_file():
            continue

        if not _has_shebang(p):
            continue

        if _is_executable_in_git(filepath):
            continue

        # File has a shebang but is not executable — fix it
        if _git_chmod_add(filepath):
            fixed.append(filepath)
        else:
            failures.append(filepath)

    if fixed:
        print(f"Auto-fixed executable bit on {len(fixed)} file(s):")
        for f in fixed:
            print(f"  +x {f}")

    if failures:
        print(f"Failed to set executable bit on {len(failures)} file(s):")
        for f in failures:
            print(f"  FAIL {f}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
