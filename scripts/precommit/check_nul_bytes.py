#!/usr/bin/env python3
"""Pre-commit hook: fail if any staged file contains NUL (0x00) bytes.

NUL bytes in source/config files are almost always accidental (binary
corruption, bad copy-paste) and silently break many tools.

Usage (called by pre-commit, receives filenames as arguments):
    python scripts/precommit/check_nul_bytes.py file1 file2 ...

Flags::

    files             Files to check (positional, passed by pre-commit)
    --version         Print version and exit

Exit codes:
    0 — no NUL bytes found
    1 — one or more files contain NUL bytes
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_VERSION = "1.1.0"
CHUNK_SIZE = 1024 * 1024  # 1 MiB


def _build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the NUL-byte checker."""
    parser = argparse.ArgumentParser(
        description="Fail if any file contains NUL (0x00) bytes.",
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


def check_file(path: str) -> bool:
    """Return True if *path* contains at least one NUL byte."""
    try:
        with Path(path).open("rb") as f:
            for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
                if b"\x00" in chunk:
                    return True
        return False
    except OSError as e:
        print(f"ERROR: could not read {path}: {e}", file=sys.stderr)
        return True  # treat unreadable as failure


def main(argv: list[str] | None = None) -> int:
    """Check all files passed as arguments for NUL bytes."""
    args = _build_parser().parse_args(argv)
    found = False
    for path in args.files:
        if check_file(path):
            print(f"ERROR: NUL byte detected in {path}", file=sys.stderr)
            found = True
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
