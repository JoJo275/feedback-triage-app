#!/usr/bin/env python3
"""Pre-commit hook: warn when a script changed but ``SCRIPT_VERSION`` didn't.

Each CLI script in ``scripts/`` defines a module-level
``SCRIPT_VERSION = "x.y.z"`` constant (see
[`docs/notes/script-conventions.md`](../../docs/notes/script-conventions.md)).
Bumping it on every meaningful change is a manual ritual that's easy to
forget. This hook compares the staged version of each touched script
against ``HEAD``:

- If the file's body changed but ``SCRIPT_VERSION`` is identical, fail.
- If ``SCRIPT_VERSION`` changed (any direction) or the file is new, pass.
- If the file has no ``SCRIPT_VERSION`` constant at all, pass (not all
  files in ``scripts/`` are versioned CLIs — shared helpers, the
  ``precommit/`` hooks, and ``__init__``-style modules don't need it).

The hook only inspects the diff for **non-trivial** changes: pure
whitespace, comment-only, and docstring-only edits don't trigger a
required bump. The heuristic is conservative — when in doubt, the hook
fails closed and asks the author to either bump the version or add
``# bump-script-version: skip`` near the top of the file.

Skipping
========
- Per-file: add a ``# bump-script-version: skip`` comment near the top
  of the file. Use sparingly — usually a sign the file should be moved
  out of the versioned-script set. The hook runs in the ``pre-commit``
  stage (before the commit message exists), so commit-message-based
  skip markers are not supported.

Usage (called by pre-commit, receives staged filenames as arguments)::

    python scripts/precommit/bump_script_version.py file1 file2 ...

Flags::

    files             Files to check (positional, passed by pre-commit)
    --version         Print version and exit
    --smoke           Self-check; exit 0 on success

Exit codes:
    0 — all files are fine (or were skipped/ignored)
    1 — one or more files have body changes but a stale ``SCRIPT_VERSION``
"""

from __future__ import annotations

import argparse
import io
import re
import shutil
import subprocess  # nosec B404 — argv-only invocations below
import sys
import tokenize
from pathlib import Path

SCRIPT_VERSION = "1.1.0"

_GIT_CMD: str | None = shutil.which("git")

# Match `SCRIPT_VERSION = "x.y.z"` (single or double quotes).
_VERSION_RE = re.compile(
    r"""^\s*SCRIPT_VERSION\s*=\s*["']([^"']+)["']\s*$""",
    re.MULTILINE,
)

# Per-file skip marker.
_FILE_SKIP_RE = re.compile(r"#\s*bump-script-version:\s*skip", re.IGNORECASE)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bump_script_version",
        description=("Fail when a script's body changed but SCRIPT_VERSION didn't."),
    )
    parser.add_argument(
        "files", nargs="*", help="Files to check (passed by pre-commit)."
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {SCRIPT_VERSION}"
    )
    parser.add_argument(
        "--smoke", action="store_true", help="Self-check; exit 0 on success."
    )
    return parser


def _git_show_head(path: str) -> str | None:
    """Return file contents at HEAD, or None if the file is new/missing."""
    if _GIT_CMD is None:
        return None
    try:
        result = subprocess.run(  # nosec B603 — argv list, no shell
            [_GIT_CMD, "show", f"HEAD:{path}"],
            capture_output=True,
            timeout=10,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.decode("utf-8", errors="replace")


def _extract_version(text: str) -> str | None:
    match = _VERSION_RE.search(text)
    return match.group(1) if match else None


def _strip_comments_and_docstrings(text: str) -> str:
    """Approximate body comparison, ignoring comments and docstrings.

    Uses :mod:`tokenize` for accuracy: comments (including inline ones)
    and standalone string statements (which covers module/class/function
    docstrings) are dropped. Whitespace-only differences are also
    ignored. Falls back to the raw text if tokenization fails (e.g. a
    syntactically invalid staged file).
    """
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return text

    out: list[str] = []
    prev_meaningful = "NEWLINE"
    for tok in tokens:
        ttype = tok.type
        tstr = tok.string
        if ttype in (
            tokenize.COMMENT,
            tokenize.NL,
            tokenize.NEWLINE,
            tokenize.INDENT,
            tokenize.DEDENT,
            tokenize.ENCODING,
            tokenize.ENDMARKER,
        ):
            continue
        # Drop standalone string statements (docstrings).
        if ttype == tokenize.STRING and prev_meaningful in {"NEWLINE", ":"}:
            prev_meaningful = "STRING_STMT"
            continue
        out.append(tstr)
        prev_meaningful = tstr if tstr in {":", ";"} else "TOKEN"
    return " ".join(out)


def _body_changed(head_text: str, current_text: str) -> bool:
    """Return True if the non-trivial body differs between HEAD and now."""
    return _strip_comments_and_docstrings(head_text) != _strip_comments_and_docstrings(
        current_text
    )


def check_file(path: Path) -> tuple[bool, str]:
    """Return ``(ok, reason)`` for a single file.

    Args:
        path: Repo-relative path to a staged Python file.

    Returns:
        ``(True, "")`` if the file is fine; ``(False, reason)`` if the
        body changed but ``SCRIPT_VERSION`` did not.
    """
    try:
        current = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return True, ""

    # Per-file skip marker.
    if _FILE_SKIP_RE.search(current):
        return True, ""

    current_version = _extract_version(current)
    if current_version is None:
        # Not a versioned CLI script; ignore.
        return True, ""

    head_text = _git_show_head(str(path).replace("\\", "/"))
    if head_text is None:
        # New file (or git unavailable). Nothing to compare against.
        return True, ""

    head_version = _extract_version(head_text)
    if head_version is None:
        # Newly versioned file: counts as a bump.
        return True, ""

    if head_version != current_version:
        return True, ""

    if _body_changed(head_text, current):
        return False, (f"body changed but SCRIPT_VERSION is still {current_version!r}")
    return True, ""


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns the exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.smoke:
        # Self-check core helpers.
        assert _extract_version('SCRIPT_VERSION = "1.2.3"') == "1.2.3"
        assert _extract_version("# nothing here") is None
        assert not _body_changed("a = 1\n", "a = 1  # comment\n")
        assert _body_changed("a = 1\n", "a = 2\n")
        assert _FILE_SKIP_RE.search("# bump-script-version: skip\n")
        print(f"bump_script_version {SCRIPT_VERSION}: smoke ok")
        return 0

    failures: list[tuple[str, str]] = []
    for raw in args.files:
        p = Path(raw)
        if p.suffix != ".py":
            continue
        ok, reason = check_file(p)
        if not ok:
            failures.append((raw, reason))

    if not failures:
        return 0

    print("SCRIPT_VERSION not bumped for changed script(s):")
    for f, reason in failures:
        print(f"  {f}: {reason}")
    print()
    print("Fix it:")
    print("  - Bump SCRIPT_VERSION at the top of the file (semver):")
    print("      * patch (x.y.Z) - bug fix or trivial change")
    print("      * minor (x.Y.0) - new flag, new behaviour, refactor")
    print("      * major (X.0.0) - breaking CLI surface change")
    print("  - Or, if the change is genuinely trivial (formatting, typo,")
    print("    pure comment edit), add this near the top of the file:")
    print("      * '# bump-script-version: skip'")
    print("  - Commit-message tags ('[skip script-version]') are NOT")
    print("    honoured: this hook runs at the pre-commit stage, before")
    print("    the commit message exists. Use the in-file marker.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
