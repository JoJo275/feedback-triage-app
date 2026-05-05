#!/usr/bin/env python3
"""Pre-flight check for ``task branch``.

Refuses to switch to ``main`` when the working tree has changes git
would refuse to abandon, and prints actionable next steps. Without
this, ``task branch`` fails on the first command (``git switch main``)
with a terse git error and no guidance.

Flags::

    --quiet         Suppress informational output on success
    --version       Print version and exit
    --smoke         Self-check (no git calls); exit 0 on success

Usage::

    python scripts/branch_preflight.py
    # invoked automatically by ``task branch``

Exit codes:
    0 = clean working tree, safe to proceed
    1 = dirty working tree (modified/staged/untracked/conflicted)
    2 = git not available or not inside a repo

Portability:
    Repo-agnostic. Requires shared modules ``_colors.py``, ``_imports.py``,
    ``_ui.py``.
"""

from __future__ import annotations

import argparse
import logging
import shutil
import subprocess  # nosec B404 — argv-only invocations below
import sys
from pathlib import Path

# -- Local script modules (not third-party; live in scripts/) ----------------
from _colors import Colors, unicode_symbols
from _imports import find_repo_root
from _ui import UI

logger = logging.getLogger(__name__)

# --- Constants ---
SCRIPT_VERSION = "1.2.0"
THEME = "cyan"


# --- Helpers ---
def _git() -> str | None:
    """Return path to git executable, or None if unavailable."""
    return shutil.which("git")


def _porcelain_status(git_bin: str, root: Path) -> tuple[int, str]:
    """Run ``git status --porcelain`` and return (returncode, stdout)."""
    proc = subprocess.run(  # nosec B603 — argv list, no shell
        [git_bin, "status", "--porcelain"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout


def _classify(porcelain: str) -> dict[str, list[str]]:
    """Split porcelain output into modified/staged/untracked/conflicted lists."""
    buckets: dict[str, list[str]] = {
        "staged": [],
        "modified": [],
        "untracked": [],
        "conflicted": [],
    }
    for line in porcelain.splitlines():
        if len(line) < 3:
            continue
        index, worktree, path = line[0], line[1], line[3:]
        if index == "U" or worktree == "U" or (index == "A" and worktree == "A"):
            buckets["conflicted"].append(path)
        elif index == "?":
            buckets["untracked"].append(path)
        elif worktree in {"M", "D"}:
            buckets["modified"].append(path)
        elif index in {"A", "M", "D", "R", "C"}:
            buckets["staged"].append(path)
    return buckets


def _print_dirty_report(buckets: dict[str, list[str]], ui: UI) -> None:
    """Print a per-bucket summary plus an actionable fix list."""
    c = Colors()
    sym = unicode_symbols()

    ui.section("Working tree is not clean")
    print(
        f"  {c.red(sym['cross'])} "
        f"{c.bold('task branch')} cannot switch to "
        f"{c.cyan('main')} while there are local changes git would "
        f"refuse to abandon."
    )
    print()

    label_color = {
        "staged": c.green,
        "modified": c.yellow,
        "untracked": c.dim,
        "conflicted": c.red,
    }
    for bucket in ("conflicted", "staged", "modified", "untracked"):
        files = buckets[bucket]
        if not files:
            continue
        head = f"  {label_color[bucket](bucket)}: {len(files)} file(s)"
        print(head)
        for path in files[:10]:
            print(f"      {c.dim('-')} {path}")
        if len(files) > 10:
            print(f"      {c.dim(f'... and {len(files) - 10} more')}")
        print()

    ui.section("Fix it")
    fixes: list[tuple[str, str]] = []
    if buckets["conflicted"]:
        fixes.append(
            (
                "Resolve merge conflicts first",
                "git status   # see conflicted files\n"
                "    # edit the files, then:\n"
                "    git add <file> && git commit",
            ),
        )
    if buckets["staged"] or buckets["modified"]:
        fixes.extend(
            [
                (
                    "Commit the work-in-progress",
                    "git add -A && git commit -m 'wip: <message>'",
                ),
                (
                    "Or stash it (recoverable, not lost)",
                    "git stash push -u -m 'pre-branch-switch'\n"
                    "    # later: git stash pop",
                ),
                (
                    "Or discard it (destructive \u2014 only if you mean it)",
                    "git restore --staged --worktree .",
                ),
            ]
        )
    if buckets["untracked"] and not (buckets["staged"] or buckets["modified"]):
        fixes.append(
            (
                "Untracked files alone don't block a switch, but "
                "double-check none are work-in-progress",
                "git status --short\n"
                "    # add to .gitignore, commit, or remove as needed",
            ),
        )
    if not fixes:
        fixes.append(
            (
                "Inspect the state and decide",
                "git status",
            ),
        )

    for n, (label, cmd) in enumerate(fixes, 1):
        print(f"  {c.cyan(f'{n}.')} {label}")
        for ln in cmd.splitlines():
            print(f"     {c.dim(ln) if ln.startswith('    ') else ln}")
        print()

    print(f"  {c.dim('After the tree is clean, re-run:')} {c.cyan('task branch')}")


# --- CLI ---
def _build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        prog="branch_preflight",
        description=(
            "Verify the working tree is clean before `task branch` "
            "switches to main. Prints actionable fixes on failure."
        ),
        epilog=(
            "Examples:\n"
            "  python scripts/branch_preflight.py\n"
            "  python scripts/branch_preflight.py --quiet\n"
            "  python scripts/branch_preflight.py --smoke\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns the exit code."""
    parser = _build_parser()
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {SCRIPT_VERSION}"
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress success output"
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Self-check (no git calls); exit 0 on success",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(format="%(message)s", level=logging.INFO)

    if args.smoke:
        # Validate constants and that helpers are wired correctly.
        assert SCRIPT_VERSION
        assert THEME
        # Exercise classifier on a representative sample.
        # Porcelain XY columns: X=index, Y=worktree.
        sample = " M src/foo.py\n?? notes.txt\nA  staged.txt\nUU conflict.txt\n"
        buckets = _classify(sample)
        assert buckets["modified"] == ["src/foo.py"]
        assert buckets["untracked"] == ["notes.txt"]
        assert buckets["staged"] == ["staged.txt"]
        assert buckets["conflicted"] == ["conflict.txt"]
        print(f"branch_preflight {SCRIPT_VERSION}: smoke ok")
        return 0

    git_bin = _git()
    if git_bin is None:
        logger.error("git not found in PATH")
        return 2

    try:
        root = find_repo_root()
    except FileNotFoundError:
        logger.error(
            "Not inside a git repository. Run this command from inside the "
            "feedback-triage-app working tree."
        )
        return 2

    code, out = _porcelain_status(git_bin, root)
    if code != 0:
        logger.error("git status failed (rc=%d). Are you inside a repo?", code)
        return 2

    buckets = _classify(out)
    total = sum(len(v) for v in buckets.values())

    ui = UI(title="Branch Pre-flight", version=SCRIPT_VERSION, theme=THEME)

    # Untracked files alone do NOT block `git switch main`; only
    # modified/staged/conflicted do.
    blocking = (
        len(buckets["modified"]) + len(buckets["staged"]) + len(buckets["conflicted"])
    )

    if blocking == 0:
        if not args.quiet:
            ui.header()
            c = Colors()
            sym = unicode_symbols()
            print()
            print(
                f"  {c.green(sym['check'])} "
                f"{c.green('Working tree is clean')} "
                f"({total} untracked file(s) ignored \u2014 they don't block "
                f"a branch switch)."
                if buckets["untracked"]
                else f"  {c.green(sym['check'])} "
                f"{c.green('Working tree is clean. Safe to switch.')}"
            )
            print()
        return 0

    ui.header()
    _print_dirty_report(buckets, ui)
    return 1


if __name__ == "__main__":
    sys.exit(main())
