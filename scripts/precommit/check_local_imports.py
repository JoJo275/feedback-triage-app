#!/usr/bin/env python3
"""Pre-commit hook: enforce local-module comment before local imports.

Scripts in ``scripts/`` that import underscore-prefixed siblings
(``_colors``, ``_imports``, ``_ui``, etc.) must include the standard
section comment before the first such import::

    # -- Local script modules (not third-party; live in scripts/) ----------------

This keeps the import convention visible and consistent.

Usage (called by pre-commit, receives filenames as arguments)::

    python scripts/precommit/check_local_imports.py file1 file2 ...

Flags::

    files             Files to check (positional, passed by pre-commit)
    --version         Print version and exit

Exit codes:
    0 — all files comply
    1 — one or more files are missing the comment
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

SCRIPT_VERSION = "1.0.0"

# The comment that must appear before local imports
_MARKER = "# -- Local script modules"

# Pattern matching local module imports (from _foo import ...)
_LOCAL_IMPORT_RE = re.compile(r"^from\s+_\w+\s+import\s|^import\s+_\w+\b")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Enforce local-module section comment in scripts.",
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


def check_file(path: Path) -> bool:
    """Return True if the file is compliant, False otherwise."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return True  # skip unreadable files

    has_local_import = False
    has_marker = False

    for line in text.splitlines():
        if _MARKER in line:
            has_marker = True
        if _LOCAL_IMPORT_RE.match(line):
            has_local_import = True

    # Only enforce the marker when there are local imports
    return not (has_local_import and not has_marker)


def main() -> int:
    """Entry point."""
    parser = _build_parser()
    args = parser.parse_args()

    failures: list[str] = []
    for filepath in args.files:
        p = Path(filepath)
        # Only check Python files under scripts/ (not under precommit/)
        if p.suffix != ".py":
            continue
        if not check_file(p):
            failures.append(str(p))

    if failures:
        print("Missing local-module section comment:")
        print(f"  Expected: {_MARKER}...")
        for f in failures:
            print(f"  {f}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
