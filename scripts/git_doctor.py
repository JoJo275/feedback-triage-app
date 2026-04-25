#!/usr/bin/env python3
"""Git-focused health check and information dashboard.

Displays a comprehensive overview of the repository's git state:
branches, remotes, current working branch, recent commits,
release automation branches, and git-related health checks.

Flags::

    --help                       Show help message and exit
    --no-color                   Disable colored output
    --json                       Output results as JSON (for CI integration)
    --export-config              Export full git config reference to Markdown file
    --apply-from PATH            Apply desired values from an edited reference file
    --apply-recommended          Apply ALL catalog recommended values and scopes
    --apply-recommended-minimal  Apply core subset of recommended configs (12 keys)
    --dry-run                    Preview changes without applying (with --apply-from/--apply-recommended/--apply-recommended-minimal/--refresh/--cleanup)
    --new-branch                 Interactive branch creation off origin/main
    --watch [N]                  Re-run dashboard every N seconds (default: 10, minimum: 2)
    --refresh                    Interactive refresh: fetch remotes, prune stale refs, sync tags, update remote HEAD
    --cleanup                    Interactive cleanup: delete stale local branches (90+ days), gone upstream branches, run git gc
    --view-commits               Detailed commit report: SHAs, messages, authors, dates, per-file stats, conflicts
    --markdown                   With --view-commits, write a Markdown commit report to commit-report.md
    --version                    Print version and exit

Usage::

    python scripts/git_doctor.py
    python scripts/git_doctor.py --json
    python scripts/git_doctor.py --no-color
    python scripts/git_doctor.py --new-branch
    python scripts/git_doctor.py --watch
    python scripts/git_doctor.py --watch 30
    python scripts/git_doctor.py --export-config
    python scripts/git_doctor.py --apply-from git-config-reference.md
    python scripts/git_doctor.py --apply-from git-config-reference.md --dry-run
    python scripts/git_doctor.py --apply-recommended
    python scripts/git_doctor.py --apply-recommended --dry-run
    python scripts/git_doctor.py --apply-recommended-minimal
    python scripts/git_doctor.py --apply-recommended-minimal --dry-run
    python scripts/git_doctor.py --refresh
    python scripts/git_doctor.py --refresh --dry-run
    python scripts/git_doctor.py --cleanup
    python scripts/git_doctor.py --cleanup --dry-run
    python scripts/git_doctor.py --view-commits
    python scripts/git_doctor.py --view-commits --markdown
    python scripts/git_doctor.py --help

Workflow for editing and applying config::

    1. Export:   python scripts/git_doctor.py --export-config
    2. Edit:     Open git-config-reference.md, change "Desired value" and/or
                 "Desired scope" cells
    3. Preview:  python scripts/git_doctor.py --apply-from git-config-reference.md --dry-run
    4. Apply:    python scripts/git_doctor.py --apply-from git-config-reference.md

    Both "Desired value" AND "Desired scope" must be set for an entry
    to be applied.  If only one is provided, the entry is skipped with
    an error message.  See ``git-config-reference.md`` for full details.

To apply ALL catalog recommended values and scopes (overwriting existing)::

    python scripts/git_doctor.py --apply-recommended --dry-run   # preview
    python scripts/git_doctor.py --apply-recommended              # apply

    .. note:: ``--apply-recommended`` sets **every** key that has a concrete
       recommended value in the catalog, **regardless** of whether it is
       already set.  This is intentional — it resets your config to the
       catalog baseline.  For per-key control, use ``--export-config`` and
       ``--apply-from`` instead.  See ``git-config-reference.md`` for the
       full catalog and recommended values.

To apply only the core minimal set (12 high-impact keys)::

    python scripts/git_doctor.py --apply-recommended-minimal --dry-run   # preview
    python scripts/git_doctor.py --apply-recommended-minimal              # apply

    .. note:: ``--apply-recommended-minimal`` is a safer, lighter-touch
       alternative for first-time setup.  It sets only the keys in
       ``MINIMAL_RECOMMENDED_CONFIGS`` — non-destructive defaults that
       benefit most workflows (e.g. ``pull.rebase``, ``fetch.prune``,
       ``rerere.enabled``).  Use ``--apply-recommended`` for the full
       catalog.

.. note::
   ``--export-config`` writes to ``git-config-reference.md`` by default
   (or a custom path if provided). The file is **replaced entirely** on
   each run — it is a generated artifact, not a hand-edited document.
   The exported reference covers commonly used git configurations (62 keys
   across 17 sections) — not every possible git config key.

Customisation notes:

- **Merge-base freshness threshold**: ``check_merge_base_freshness()``
  warns when the default branch is >10 commits ahead of the merge-base.
  Adjust the threshold (``default_ahead <= 10``) if your workflow merges
  main less frequently.
- **Branch commit counts**: ``get_recent_branches_with_stats()`` shows
  commits *unique* to each branch (since diverging from default), not
  total reachable commits.  ``get_branch_commit_count()`` still returns
  the total if needed.
- **Unmerged branches**: Branches whose remote tracking ref is ``[gone]``
  (deleted on the remote) are excluded by default — they were almost
  certainly merged via PR (rebase-merge or squash-merge).  See the TODO
  in ``get_unmerged_branches()`` if your team's workflow differs.
  The three merge strategies GitHub supports are:

  1. **Rebase-merge** — replays branch commits on top of the target;
     produces a linear history with the original commits preserved.
  2. **Squash-merge** — condenses all branch commits into a single
     commit on the target; original commit SHAs are lost.
  3. **Merge commit** — creates a merge commit; original commits are
     reachable via the merge parent and ``--no-merged`` works correctly.

  Because rebase-merge and squash-merge both create new commit objects,
  ``git branch --no-merged`` can't detect that the branch's *content*
  was already integrated.  Filtering out ``[gone]`` branches handles
  this correctly for normal post-PR-merge cleanup workflows.
- **Branch activity accuracy**: ``get_recent_branches_with_stats()`` uses
  ``origin/<default>`` (not the local ref) as the comparison base so
  that stats remain accurate even when the local default branch is stale.
- **Auto-fetch**: The script runs ``git fetch --all --prune`` at startup
  to ensure remote-tracking refs are current and deleted remote branches
  are cleaned up.

    Task runner shortcuts for this script are defined in ``Taskfile.yml``.

Portability:
    Can be used in any Git repository.  Requires shared modules:
    ``_colors.py``, ``_imports.py``, ``_ui.py``, ``_progress.py``.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import logging
import os
import re
import shutil
import subprocess  # nosec B404
import sys
import time
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path

# -- Local script modules (not third-party; live in scripts/) ----------------
from _colors import Colors
from _colors import status_icon as _icon
from _colors import supports_color as _supports_color
from _colors import supports_unicode as _supports_unicode
from _colors import unicode_symbols as _unicode_symbols
from _doctor_common import extract_repo_slug, read_pyproject
from _imports import find_repo_root
from _progress import ProgressBar, Spinner
from _ui import UI

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCRIPT_VERSION = "3.1.0"

# Theme color for this script's dashboard output.
THEME = "cyan"

# When the GIT_CONFIG_CATALOG entries were last reviewed / updated.
# Printed in git-config-reference.md so readers know the catalog's age.
CATALOG_LAST_UPDATED = "2026-03-16"

# TODO (template users): Tune these thresholds to match your team's workflow.
#   _LARGE_FILE_THRESHOLD_MB: files above this trigger the staged-files check.
#   _MERGE_BASE_THRESHOLD: commits-ahead before merge-base freshness warns.
#   _STALE_BRANCH_DAYS / _AGING_BRANCH_DAYS: branch activity buckets.
#   _LOOSE_OBJECTS_GC_THRESHOLD: count-objects trigger for gc suggestion.
_LARGE_FILE_THRESHOLD_MB: int = 5
_MERGE_BASE_THRESHOLD: int = 10
_STALE_BRANCH_DAYS: int = 30
_AGING_BRANCH_DAYS: int = 7
_LOOSE_OBJECTS_GC_THRESHOLD: int = 50

logger = logging.getLogger(__name__)

ROOT = find_repo_root()

_GIT: str | None = shutil.which("git")

# ---------------------------------------------------------------------------
# Minimal recommended configs for --apply-recommended-minimal
# ---------------------------------------------------------------------------

# Core subset of high-impact, non-destructive defaults that benefit most
# development workflows. Used by --apply-recommended-minimal for a safer,
# lighter-touch alternative to --apply-recommended (which applies all ~62
# catalog entries). Also used by _RECOMMENDED_LOOKUP for terminal display
# hints in the dashboard.
# Keys that depend on personal preference (e.g. core.editor) are omitted.
MINIMAL_RECOMMENDED_CONFIGS: list[tuple[str, str, str]] = [
    # (key, value, scope)
    ("pull.rebase", "true", "global"),
    ("push.default", "current", "global"),
    ("push.autoSetupRemote", "true", "global"),
    ("fetch.prune", "true", "global"),
    ("fetch.prunetags", "true", "global"),
    ("merge.conflictstyle", "zdiff3", "global"),
    ("rebase.autostash", "true", "global"),
    ("rebase.autoSquash", "true", "global"),
    ("rerere.enabled", "true", "global"),
    ("branch.sort", "-committerdate", "global"),
    ("diff.algorithm", "histogram", "global"),
    ("init.defaultBranch", "main", "global"),
]

# Quick lookup: key -> recommended value (for terminal display hints)
_RECOMMENDED_LOOKUP: dict[str, str] = {k: v for k, v, _ in MINIMAL_RECOMMENDED_CONFIGS}

# ---------------------------------------------------------------------------
# Git configuration catalog (used by --export-config)
# ---------------------------------------------------------------------------

# Curated catalog of commonly used git configurations.
# This is NOT exhaustive — git has 500+ keys; this covers the ones
# most relevant to day-to-day development workflows.
# Format: (key, recommended_scope, description, recommendation)
GIT_CONFIG_CATALOG: list[tuple[str, str, str, str]] = [
    # ── Core ──
    (
        "core.autocrlf",
        "global",
        "Line ending conversion: 'true'=CRLF<>LF (Windows), 'input'=LF on commit only, 'false'=off",
        "'input' on macOS/Linux, 'true' on Windows",
    ),
    (
        "core.editor",
        "global",
        "Default text editor for commit messages, interactive rebase, and other editing",
        "e.g. 'code --wait', 'vim', 'nano'",
    ),
    (
        "core.pager",
        "global",
        "Pager program for git output (log, diff). 'delta' gives syntax-highlighted diffs",
        "'delta' for better diffs, or 'less -FRX'",
    ),
    (
        "core.excludesfile",
        "global",
        "Path to a global gitignore file applied to ALL repositories (editor/OS ignores)",
        "'~/.gitignore_global'",
    ),
    (
        "core.filemode",
        "local",
        "Track file permission (executable bit) changes. Windows doesn't support Unix perms",
        "'false' on Windows if you see spurious permission diffs",
    ),
    (
        "core.longpaths",
        "global",
        "Enable paths longer than 260 chars on Windows. Required for deep node_modules",
        "'true' on Windows",
    ),
    (
        "core.quotepath",
        "global",
        "Quote non-ASCII characters in pathnames. Disable to see UTF-8 filenames correctly",
        "'false' to display non-ASCII filenames correctly",
    ),
    (
        "core.hooksPath",
        "local",
        "Custom directory for git hooks. Usually managed by pre-commit",
        "Leave unset when using pre-commit",
    ),
    (
        "core.eol",
        "local",
        "Line ending style in working directory: 'lf', 'crlf', or 'native'",
        "'lf' for cross-platform projects, or use .gitattributes",
    ),
    (
        "core.safecrlf",
        "global",
        "Abort/warn if line ending conversion would lose data",
        "'warn' for safety without blocking",
    ),
    (
        "core.symlinks",
        "local",
        "Whether working tree supports symbolic links (auto-detected on clone)",
        "Auto-detected; 'false' if symlinks cause issues on Windows",
    ),
    (
        "core.whitespace",
        "local",
        "Which whitespace problems git notices (trailing-space, space-before-tab, etc.)",
        "Default is fine for most projects",
    ),
    (
        "core.ignorecase",
        "local",
        "Whether filenames are case-insensitive (auto-detected on clone). Affects 'git mv'",
        "Auto-detected; usually 'true' on Windows/macOS, 'false' on Linux",
    ),
    # ── Fetch ──
    (
        "fetch.prune",
        "global",
        "Auto-remove stale remote-tracking branches on every fetch",
        "'true' -- avoids stale branch accumulation",
    ),
    ("fetch.prunetags", "global", "Auto-remove stale remote tags on fetch", "'true'"),
    (
        "fetch.fsckobjects",
        "global",
        "Verify integrity of objects received during fetch (catches corruption)",
        "'true' for security",
    ),
    # ── Pull ──
    (
        "pull.rebase",
        "global",
        "Rebase local commits on top of upstream when pulling. Gives linear history",
        "'true' for linear history",
    ),
    (
        "pull.ff",
        "global",
        "Fast-forward behavior on pull: 'only' refuses merge commits, 'true' allows any merge",
        "'only' to prevent accidental merge commits",
    ),
    # ── Push ──
    (
        "push.default",
        "global",
        "What to push when no refspec given: 'current'=same-named branch, 'simple'=default",
        "'current' or 'simple'",
    ),
    (
        "push.autoSetupRemote",
        "global",
        "Auto-set upstream tracking on first push (no more --set-upstream). Git 2.37+",
        "'true'",
    ),
    (
        "push.followTags",
        "global",
        "Push annotated tags along with commits automatically",
        "'true' if you use annotated tags for releases",
    ),
    # ── Merge ──
    (
        "merge.ff",
        "local",
        "Fast-forward on merge: 'only'=refuse merge commits, 'false'=always create them",
        "'only' for linear history, 'false' for explicit merge commits",
    ),
    (
        "merge.conflictstyle",
        "global",
        "Conflict marker format: 'diff3'/'zdiff3' shows the common ancestor (3-way diff)",
        "'zdiff3' (git 2.35+) or 'diff3'",
    ),
    (
        "merge.tool",
        "global",
        "Default tool for resolving merge conflicts interactively",
        "e.g. 'vscode', 'meld', 'vimdiff'",
    ),
    (
        "merge.log",
        "global",
        "Include one-line descriptions of merged commits in merge commit message",
        "'true' for informative merge commits",
    ),
    # ── Rebase ──
    (
        "rebase.autostash",
        "global",
        "Auto-stash uncommitted changes before rebase, unstash after",
        "'true' -- prevents 'dirty worktree' errors",
    ),
    (
        "rebase.autoSquash",
        "global",
        "Auto-apply fixup!/squash! prefixes in interactive rebase (with --fixup)",
        "'true'",
    ),
    (
        "rebase.updateRefs",
        "global",
        "Auto-update stacked branch refs during rebase. Git 2.38+",
        "'true' for stacked branch workflows",
    ),
    # ── Rerere ──
    (
        "rerere.enabled",
        "global",
        "REuse REcorded Resolution -- remember and replay merge conflict fixes",
        "'true' -- saves time on repeated rebases",
    ),
    # ── Stash ──
    (
        "stash.showPatch",
        "global",
        "Show the patch (diff) in 'git stash show' instead of just a file stat summary",
        "'true' for detailed stash inspection",
    ),
    # ── Branch & Init ──
    (
        "branch.autosetuprebase",
        "global",
        "Auto-set pull.rebase for new tracking branches: 'always', 'local', 'remote', 'never'",
        "'always' if you prefer rebasing consistently",
    ),
    (
        "branch.sort",
        "global",
        "Default sort for 'git branch': '-committerdate' shows most recent first",
        "'-committerdate'",
    ),
    ("init.defaultBranch", "global", "Default branch name for 'git init'", "'main'"),
    (
        "tag.sort",
        "global",
        "Sort for 'git tag': 'version:refname' gives natural version ordering (v1.9 < v1.10)",
        "'version:refname'",
    ),
    # ── Identity & Signing ──
    (
        "user.name",
        "global",
        "Author name recorded in every commit. Use local scope for work-specific identity",
        "Your full name (required)",
    ),
    (
        "user.email",
        "global",
        "Author email recorded in every commit. Use local scope for per-project email",
        "Your email (required; local for work repos)",
    ),
    (
        "commit.gpgsign",
        "global",
        "Auto-sign every commit with GPG/SSH key. GitHub shows 'Verified' badge",
        "'true' for verified commits",
    ),
    (
        "tag.gpgsign",
        "global",
        "Auto-sign every tag with GPG/SSH key",
        "'true' if signing commits",
    ),
    (
        "gpg.format",
        "global",
        "Signing format: 'openpgp' (GPG) or 'ssh' (SSH keys -- simpler setup)",
        "'ssh' for SSH-based signing",
    ),
    (
        "gpg.ssh.allowedSignersFile",
        "global",
        "Allowed SSH public keys file for signature verification",
        "Set if using SSH signing for local verification",
    ),
    # ── Commit ──
    (
        "commit.template",
        "local",
        "Path to default commit message template shown in editor on 'git commit'",
        "'.gitmessage.txt' for this project",
    ),
    (
        "commit.verbose",
        "global",
        "Show diff of staged changes in commit message editor for review",
        "'true'",
    ),
    # ── Diff ──
    (
        "diff.algorithm",
        "global",
        "Diff algorithm: 'histogram' gives better results than default 'myers'",
        "'histogram'",
    ),
    (
        "diff.colorMoved",
        "global",
        "Highlight moved lines in diffs (not just added/deleted). Makes refactoring clearer",
        "'default' or 'zebra'",
    ),
    (
        "diff.colorMovedWS",
        "global",
        "Whitespace handling for moved-line detection",
        "'allow-indentation-change' with colorMoved",
    ),
    (
        "diff.tool",
        "global",
        "Default tool for side-by-side diff comparison",
        "e.g. 'vscode', 'meld', 'delta'",
    ),
    (
        "diff.renameLimit",
        "global",
        "Max files for rename detection. Increase if git misses renames in large changesets",
        "Increase (e.g. 5000) for large repos",
    ),
    (
        "diff.submodule",
        "global",
        "Submodule diff format: 'log' shows commit summaries, 'short' shows only SHAs",
        "'log' if you use submodules",
    ),
    # ── Log & Display ──
    (
        "log.date",
        "global",
        "Default date format for 'git log': 'relative', 'short', 'iso', 'local'",
        "'relative' or 'short'",
    ),
    (
        "color.ui",
        "global",
        "Enable colored output: 'auto' enables when stdout is a terminal",
        "'auto' (default in modern git)",
    ),
    (
        "column.ui",
        "global",
        "Display branch/tag listings in columns when terminal is wide enough",
        "'auto'",
    ),
    # ── Credential & Transfer ──
    (
        "credential.helper",
        "global",
        "How git stores credentials (passwords/tokens). 'manager' uses OS credential store",
        "'manager' (Windows), 'osxkeychain' (macOS), 'store' (Linux)",
    ),
    (
        "http.sslVerify",
        "global",
        "Verify SSL certs for HTTPS. Disabling is a security risk",
        "Keep 'true' (default); only disable for self-signed certs",
    ),
    (
        "transfer.fsckobjects",
        "global",
        "Verify object integrity during push/pull transfers",
        "'true' for data integrity",
    ),
    # ── Performance ──
    (
        "gc.auto",
        "global",
        "Threshold for auto garbage collection (loose object count)",
        "Default (6700) is fine; increase for busy repos",
    ),
    (
        "feature.manyFiles",
        "local",
        "Enable optimizations for repos with many files (untracked cache, fsmonitor)",
        "'true' for large repos",
    ),
    (
        "index.version",
        "local",
        "Index format version. V4 is more compact and faster",
        "'4' for large repos",
    ),
    # ── Help & UX ──
    (
        "help.autocorrect",
        "global",
        "Auto-correct mistyped commands: 'prompt'=ask, N=wait N deciseconds, '0'=off",
        "'prompt' or '10' (1 second delay)",
    ),
    (
        "status.showUntrackedFiles",
        "global",
        "Untracked file display: 'all'=individual files, 'normal'=group by directory",
        "'all' for complete visibility",
    ),
    # ── Advice ──
    (
        "advice.detachedHead",
        "global",
        "Show the advice message when entering detached HEAD state",
        "'false' to suppress if you frequently check out tags or SHAs",
    ),
    (
        "advice.statusHints",
        "global",
        "Show hints in 'git status' about staging, unstaging, and conflict resolution",
        "'true' (default) for beginners, 'false' for cleaner output",
    ),
    # ── Protocol ──
    (
        "protocol.version",
        "global",
        "Git protocol version: v2 is faster (partial clone, faster negotiation). Git 2.26+",
        "'2' (default in modern git)",
    ),
]

# ---------------------------------------------------------------------------
# Valid values for each config key (used by --export-config)
# ---------------------------------------------------------------------------

# Maps config keys to their accepted values.  Entries with a short fixed set
# list the values explicitly; freeform keys describe the expected format.
# Keys absent from this dict get a generic "(freeform)" note in the export.
#
# TODO (template users): Add valid-values entries when you add new catalog
#   keys so the exported reference stays informative.
CONFIG_VALID_VALUES: dict[str, str] = {
    # ── Core ──
    "core.autocrlf": "`true`, `false`, `input`",
    "core.editor": "Any editor command — e.g. `code --wait`, `vim`, `nano`, `emacs`",
    "core.pager": "Any pager command — e.g. `delta`, `less -FRX`, `cat`, `bat`",
    "core.excludesfile": "Absolute path to a global gitignore file — e.g. `~/.gitignore_global`",
    "core.filemode": "`true`, `false`",
    "core.longpaths": "`true`, `false`",
    "core.quotepath": "`true`, `false`",
    "core.hooksPath": "Path to hooks directory — e.g. `.husky`, `.githooks`, or leave unset",
    "core.eol": "`lf`, `crlf`, `native`",
    "core.safecrlf": "`true` (abort), `warn` (warn only), `false` (off)",
    "core.symlinks": "`true`, `false` (auto-detected on clone)",
    "core.whitespace": "Comma-separated list — e.g. `trailing-space,space-before-tab,indent-with-non-tab`",
    "core.ignorecase": "`true`, `false` (auto-detected on clone)",
    # ── Fetch ──
    "fetch.prune": "`true`, `false`",
    "fetch.prunetags": "`true`, `false`",
    "fetch.fsckobjects": "`true`, `false`",
    # ── Pull ──
    "pull.rebase": "`true`, `false`, `merges`, `interactive`",
    "pull.ff": "`true`, `false`, `only`",
    # ── Push ──
    "push.default": "`current`, `simple`, `upstream`, `matching`, `nothing`",
    "push.autoSetupRemote": "`true`, `false`",
    "push.followTags": "`true`, `false`",
    # ── Merge ──
    "merge.ff": "`true`, `false`, `only`",
    "merge.conflictstyle": "`merge`, `diff3`, `zdiff3` (git 2.35+)",
    "merge.tool": "Any merge tool — e.g. `vscode`, `meld`, `vimdiff`, `kdiff3`, `opendiff`",
    "merge.log": "`true`, `false`, or integer (max entries to include)",
    # ── Rebase ──
    "rebase.autostash": "`true`, `false`",
    "rebase.autoSquash": "`true`, `false`",
    "rebase.updateRefs": "`true`, `false`",
    # ── Rerere ──
    "rerere.enabled": "`true`, `false`",
    # ── Stash ──
    "stash.showPatch": "`true`, `false`",
    # ── Branch & Init ──
    "branch.autosetuprebase": "`always`, `local`, `remote`, `never`",
    "branch.sort": "Sort key — e.g. `-committerdate`, `refname`, `authordate`, `-authordate`",
    "init.defaultBranch": "Branch name — e.g. `main`, `master`, `trunk`, `develop`",
    "tag.sort": "Sort key — e.g. `version:refname`, `refname`, `-creatordate`",
    # ── Identity & Signing ──
    "user.name": "Your full name — e.g. `Jane Doe`",
    "user.email": "Your email address — e.g. `jane@example.com`",
    "commit.gpgsign": "`true`, `false`",
    "tag.gpgsign": "`true`, `false`",
    "gpg.format": "`openpgp`, `ssh`, `x509`",
    "gpg.ssh.allowedSignersFile": "Path to an allowed signers file — e.g. `~/.config/git/allowed_signers`",
    # ── Commit ──
    "commit.template": "Path to template file — e.g. `.gitmessage.txt`, `~/.gitmessage`",
    "commit.verbose": "`true`, `false`",
    # ── Diff ──
    "diff.algorithm": "`myers` (default), `minimal`, `patience`, `histogram`",
    "diff.colorMoved": "`no`, `default`, `plain`, `blocks`, `zebra`, `dimmed-zebra`",
    "diff.colorMovedWS": "`no`, `allow-indentation-change`, `ignore-space-at-eol`, `ignore-space-change`, `ignore-all-space`",
    "diff.tool": "Any diff tool — e.g. `vscode`, `meld`, `delta`, `vimdiff`, `kdiff3`",
    "diff.renameLimit": "Integer — e.g. `0` (disabled), `5000`, `10000`",
    "diff.submodule": "`short`, `log`, `diff`",
    # ── Log & Display ──
    "log.date": "`relative`, `short`, `local`, `iso`, `iso-strict`, `rfc`, `format:...`",
    "color.ui": "`auto`, `always`, `false`",
    "column.ui": "`auto`, `always`, `never`, `column`, `row`, `plain`",
    # ── Credential & Transfer ──
    "credential.helper": "`manager` (Windows/macOS), `osxkeychain` (macOS), `store` (plaintext), `cache` (in-memory)",
    "http.sslVerify": "`true`, `false`",
    "transfer.fsckobjects": "`true`, `false`",
    # ── Performance ──
    "gc.auto": "Integer (loose object count) — e.g. `6700` (default), `0` (disable auto-gc)",
    "feature.manyFiles": "`true`, `false`",
    "index.version": "`2` (legacy), `3`, `4` (compact, recommended for large repos)",
    # ── Help & UX ──
    "help.autocorrect": "`0` (off), `prompt` (ask), or integer (decisecond delay) — e.g. `10` = 1 second",
    "status.showUntrackedFiles": "`all`, `normal`, `no`",
    "advice.detachedHead": "`true`, `false`",
    "advice.statusHints": "`true`, `false`",
    # ── Protocol ──
    "protocol.version": "`0`, `1`, `2`",
}

# ---------------------------------------------------------------------------
# Beginner-friendly notes (used by --export-config)
# ---------------------------------------------------------------------------

# Plain-English explanations aimed at newcomers to git. Rendered as an
# italicised paragraph below the succinct technical description in the
# exported Markdown reference. Keys absent from this dict get no extra note.
CONFIG_BEGINNER_NOTES: dict[str, str] = {
    # ── Core ──
    "core.autocrlf": (
        "Windows and macOS/Linux use different invisible characters at the end "
        "of each line. This setting tells git how to convert between them so "
        "files look correct on every operating system."
    ),
    "core.editor": (
        "When you run `git commit` without the `-m` flag, git opens a text "
        "editor so you can write your commit message. This setting picks which "
        "editor opens. `code --wait` means VS Code."
    ),
    "core.pager": (
        "When git output is longer than your terminal, it scrolls through a "
        '"pager" program (like `less`). `delta` is a popular pager that adds '
        "syntax highlighting and side-by-side diffs."
    ),
    "core.excludesfile": (
        "A personal `.gitignore` that applies to every repo on your machine. "
        "Put OS junk (`.DS_Store`, `Thumbs.db`) and editor files (`.idea/`, "
        "`.vscode/`) here so they never get committed anywhere."
    ),
    "core.filemode": (
        'On Linux/macOS, files can be marked as "executable." Windows doesn\'t '
        "have this concept, so git may think every file's permissions changed. "
        "Setting this to `false` on Windows silences those false diffs."
    ),
    "core.longpaths": (
        "Windows traditionally limits file paths to 260 characters. Some "
        "projects (especially with `node_modules/`) exceed this. Setting this "
        "to `true` removes the limit."
    ),
    "core.quotepath": (
        "By default, git escapes non-English characters in file names, showing "
        "them as `\\nnn` sequences. Set to `false` to see the actual characters."
    ),
    "core.hooksPath": (
        "Git hooks are scripts that run automatically at certain points (e.g. "
        "before a commit). This setting points git to a custom hooks folder. "
        "If you use pre-commit, it manages hooks for you — leave this unset."
    ),
    "core.eol": (
        "Controls which line-ending style git uses in your working files. "
        "`lf` is standard for cross-platform projects. For per-file control, "
        "use a `.gitattributes` file instead."
    ),
    "core.safecrlf": (
        "A safety net: if converting line endings would change a file in a way "
        "that can't be reversed, git warns or blocks the operation."
    ),
    "core.symlinks": (
        "Symbolic links are shortcuts that point to another file. Some "
        "operating systems (especially older Windows) don't support them. "
        "Git auto-detects this on clone."
    ),
    "core.whitespace": (
        "Tells git which whitespace issues to flag — like trailing spaces at "
        "the end of a line, or spaces before tabs. Helpful for keeping code clean."
    ),
    "core.ignorecase": (
        "On Windows and macOS, `File.txt` and `file.txt` are the same file. "
        "On Linux, they're different. Git auto-detects this, but it affects "
        "whether `git mv` can rename a file by just changing its case."
    ),
    # ── Fetch ──
    "fetch.prune": (
        "When a teammate deletes a branch on GitHub, your local git still "
        "remembers it. With `fetch.prune = true`, those stale references are "
        "automatically cleaned up every time you fetch."
    ),
    "fetch.prunetags": (
        "Same idea as `fetch.prune`, but for tags. Removes references to "
        "remote tags that no longer exist."
    ),
    "fetch.fsckobjects": (
        "Runs an integrity check on every object received from a remote. "
        "Catches corrupted data before it enters your repo. Slightly slower "
        "but much safer."
    ),
    # ── Pull ──
    "pull.rebase": (
        'When you `git pull`, your local commits can either be "merged" on '
        'top (creating a merge commit) or "rebased" (replayed one by one on '
        "top of the remote changes). Rebase keeps the history cleaner and "
        "linear — no unnecessary merge commits cluttering your log."
    ),
    "pull.ff": (
        'A "fast-forward" is when git can just move the branch pointer forward '
        "without creating a merge commit. Setting this to `only` means git "
        "refuses to pull if a fast-forward isn't possible, so you never get "
        "surprise merge commits."
    ),
    # ── Push ──
    "push.default": (
        "When you type `git push` without specifying a branch, git needs to "
        "decide what to push. `current` pushes your current branch to a "
        "remote branch with the same name. `simple` does the same but only "
        "if the upstream branch also has the same name."
    ),
    "push.autoSetupRemote": (
        "Normally, the first time you push a new branch, git makes you type "
        "`git push --set-upstream origin my-branch`. With this set to `true`, "
        "a simple `git push` just works — git creates the remote branch and "
        "sets up tracking automatically."
    ),
    "push.followTags": (
        "Tags are named markers on specific commits (like `v1.0.0`). With "
        "this on, `git push` automatically sends any new annotated tags along "
        "with your commits, so you don't have to push tags separately."
    ),
    # ── Merge ──
    "merge.ff": (
        "Controls whether `git merge` creates a merge commit or just moves "
        "the branch pointer forward. `only` means: if the merge can't be a "
        "simple fast-forward, refuse to merge (keeping history linear). "
        "`false` means: always create a merge commit, even when fast-forward "
        "is possible."
    ),
    "merge.conflictstyle": (
        "When two people edit the same lines, git inserts conflict markers in "
        'the file. The default (`merge`) shows only "their version" vs '
        '"your version." With `diff3`/`zdiff3`, you also see the original '
        "code before either person changed it, making it much easier to "
        "understand what each side intended."
    ),
    "merge.tool": (
        "Instead of manually editing conflict markers in a text file, you "
        "can use a visual tool that shows both versions side by side. This "
        "setting picks which tool opens when you run `git mergetool`."
    ),
    "merge.log": (
        "When git creates a merge commit, this setting adds a summary of "
        "all the commits being merged into the merge message — helpful for "
        "understanding what a merge brought in."
    ),
    # ── Rebase ──
    "rebase.autostash": (
        "If you have uncommitted changes and try to rebase, git normally "
        "refuses. With this on, git automatically stashes your changes, "
        "does the rebase, then restores them — no manual stash/unstash needed."
    ),
    "rebase.autoSquash": (
        "When you make a fixup commit (`git commit --fixup <sha>`), this "
        "setting automatically moves and squashes it into the right place "
        "during interactive rebase. Great for polishing a branch before merging."
    ),
    "rebase.updateRefs": (
        "If you have multiple branches stacked on top of each other, rebasing "
        "the base branch normally leaves the others pointing at the old "
        "commits. This setting automatically updates all the stacked branch "
        "pointers."
    ),
    # ── Rerere ──
    "rerere.enabled": (
        '"Rerere" stands for "reuse recorded resolution." If you resolve '
        "a merge conflict, git remembers how you resolved it. The next time "
        "the same conflict appears (e.g. during repeated rebases), git applies "
        "your previous resolution automatically."
    ),
    # ── Stash ──
    "stash.showPatch": (
        "By default, `git stash show` only lists which files changed. With "
        "this on, it shows the actual diff — the line-by-line changes — so "
        "you can see exactly what's in each stash without applying it."
    ),
    # ── Branch & Init ──
    "branch.autosetuprebase": (
        "When you create a new branch that tracks a remote branch, this "
        "setting automatically configures it to rebase on pull instead of "
        "merge. Saves you from setting `pull.rebase` for each branch individually."
    ),
    "branch.sort": (
        "By default, `git branch` lists branches alphabetically. With "
        "`-committerdate`, the most recently worked-on branches appear first "
        "— much more useful when you have many branches."
    ),
    "init.defaultBranch": (
        "When you create a brand-new repo with `git init`, this is the name "
        "of the first branch. Most projects now use `main` instead of the "
        "older default `master`."
    ),
    "tag.sort": (
        "By default, `git tag` sorts alphabetically, which puts `v1.10` "
        "before `v1.9`. Setting this to `version:refname` sorts by version "
        "number correctly."
    ),
    # ── Identity & Signing ──
    "user.name": (
        "Your name appears in every commit you make. Set this once globally "
        "and override locally if you need a different name for work repos."
    ),
    "user.email": (
        "Your email appears in every commit. GitHub uses this to link commits "
        "to your account. Use a `local` override if your work email differs "
        "from your personal one."
    ),
    "commit.gpgsign": (
        "Signing commits proves they really came from you. GitHub shows a "
        '"Verified" badge next to signed commits. Requires a GPG or SSH '
        "key to be set up first."
    ),
    "tag.gpgsign": (
        "Like commit signing, but for tags. Proves a release tag was created "
        "by an authorized person."
    ),
    "gpg.format": (
        "Choose between GPG (traditional, more complex setup) or SSH keys "
        "(simpler — you may already have one for GitHub authentication). "
        'Both produce "Verified" badges on GitHub.'
    ),
    "gpg.ssh.allowedSignersFile": (
        "A file listing trusted SSH public keys. Git checks this file to "
        "verify signatures locally. Without it, `git log --show-signature` "
        "can't confirm who signed a commit."
    ),
    # ── Commit ──
    "commit.template": (
        "A template file whose contents pre-fill the commit message editor "
        "every time you commit. Useful for enforcing a team format (e.g. "
        "type, scope, description)."
    ),
    "commit.verbose": (
        "When writing a commit message, this shows the full diff of your "
        "staged changes right in the editor. Helpful for reviewing exactly "
        "what you're about to commit."
    ),
    # ── Diff ──
    "diff.algorithm": (
        "Git uses an algorithm to figure out what changed between two "
        "versions of a file. `histogram` generally produces more readable "
        "diffs than the default `myers`, especially for moved code blocks."
    ),
    "diff.colorMoved": (
        "When you move code from one place to another, normal diffs show it "
        "as deleted + added. This setting highlights moved lines in a "
        "different color so you can tell they were moved, not rewritten."
    ),
    "diff.colorMovedWS": (
        "Controls whether whitespace changes (like re-indenting) prevent "
        "moved-line detection. `allow-indentation-change` means moving code "
        'into a nested block still counts as "moved."'
    ),
    "diff.tool": (
        "When you run `git difftool`, this picks which visual diff program "
        "opens. VS Code, Meld, and delta are popular choices."
    ),
    "diff.renameLimit": (
        "Git tries to detect when a file was renamed rather than deleted and "
        "re-created. In large changesets, rename detection can be slow or "
        "miss renames. Increasing this limit makes it try harder."
    ),
    "diff.submodule": (
        "Submodules are repos inside repos. This controls how their changes "
        "show in diffs — `log` shows the commit messages, which is more "
        "informative than just SHAs."
    ),
    # ── Log & Display ──
    "log.date": (
        'Controls how dates appear in `git log`. `relative` shows "3 days '
        'ago", `short` shows "2026-03-16", `iso` shows full timestamps.'
    ),
    "color.ui": (
        "Enables colored output in the terminal (green for added lines, red "
        "for removed, etc.). `auto` turns color on when outputting to a "
        "terminal but off when piping to a file."
    ),
    "column.ui": (
        "When listing branches or tags, `auto` arranges them in columns "
        "(like `ls` does for files) to fit more on screen."
    ),
    # ── Credential & Transfer ──
    "credential.helper": (
        "Instead of typing your password or token every time you push/pull, "
        "a credential helper stores it securely. `manager` uses your OS "
        "keychain (Windows Credential Manager or macOS Keychain)."
    ),
    "http.sslVerify": (
        "Git verifies HTTPS certificates to prevent man-in-the-middle "
        "attacks. Disabling this is a security risk — only do it for "
        "self-signed certificates in trusted environments."
    ),
    "transfer.fsckobjects": (
        "Runs integrity checks on data during push and pull. Catches "
        "corruption that could silently break your repository. Worth "
        "enabling for important projects."
    ),
    # ── Performance ──
    "gc.auto": (
        "Git stores objects as loose files. Over time, these accumulate and "
        "slow things down. `gc.auto` triggers automatic cleanup when the "
        "count exceeds the threshold."
    ),
    "feature.manyFiles": (
        "Enables performance optimizations for repos with thousands of files "
        "— things like the untracked file cache and filesystem monitor. "
        "Not needed for small-to-medium repos."
    ),
    "index.version": (
        "The index (staging area) file format. Version 4 is more compact and "
        "faster, especially in repos with many files."
    ),
    # ── Help & UX ──
    "help.autocorrect": (
        "If you mistype a command (e.g. `git statuus` instead of `git status`), "
        "git can auto-correct it. `prompt` asks first; a number auto-runs "
        "after that many tenths of a second."
    ),
    "status.showUntrackedFiles": (
        "`all` shows every untracked file individually. `normal` groups them "
        "by directory. `all` is more verbose but ensures you never miss a "
        "file that should be committed or gitignored."
    ),
    # ── Advice ──
    "advice.detachedHead": (
        '"Detached HEAD" means you\'re not on a branch — you checked out a '
        "specific commit or tag. Git shows a long warning about this. If you "
        "do it often (e.g. reviewing old releases), set to `false` to silence it."
    ),
    "advice.statusHints": (
        '`git status` normally includes hints like "use git add to stage" or '
        '"use git restore to discard changes." Helpful when learning git; '
        "set to `false` once you know the commands."
    ),
    # ── Protocol ──
    "protocol.version": (
        "Git protocol v2 is more efficient — faster clones, smarter "
        "negotiation of what data to transfer. It's the default in modern "
        "git versions."
    ),
}

# ---------------------------------------------------------------------------
# Config section descriptions (used by terminal display and --export-config)
# ---------------------------------------------------------------------------

# One-line description of each logical config section.
# TODO (template users): Add descriptions for any custom sections you define
#   in CONFIG_SECTION_MAP.
SECTION_DESCRIPTIONS: dict[str, str] = {
    "Core": "Fundamental git behavior: line endings, editor, pager, file handling.",
    "Fetch": "How git retrieves objects and refs from remotes.",
    "Pull": "Behavior when pulling changes from a remote branch.",
    "Push": "Defaults for pushing commits to remotes.",
    "Merge": "How git handles merges and conflict markers.",
    "Rebase": "Rebase workflow helpers: auto-stash, fixup squashing, stacked refs.",
    "Rerere": "Reuse recorded resolutions for recurring merge conflicts.",
    "Stash": "Temporary work storage: stash display and behavior.",
    "Branch & Init": "Branch/tag display, sorting, and defaults for new repositories.",
    "Identity & Signing": "Author identity and GPG/SSH commit/tag signing.",
    "Commit": "Commit message templates and editor behavior.",
    "Diff": "Diff algorithm, moved-line detection, and rename handling.",
    "Log & Display": "Date format, color output, and column display for listings.",
    "Credential & Transfer": "Credential storage, SSL, and object integrity verification.",
    "Performance": "Garbage collection, index format, and large-repo optimizations.",
    "Help & UX": "Autocorrect, advice messages, and other UX settings.",
    "Protocol": "Git wire protocol version for network communication.",
}

# Section display names for the exported config reference.  Key-specific
# overrides take priority, then prefix-based defaults.  Keys not listed
# here use the capitalised key prefix (e.g. "core.editor" -> "Core").
CONFIG_SECTION_MAP: dict[str, str] = {
    # Prefix-based
    "branch": "Branch & Init",
    "init": "Branch & Init",
    "user": "Identity & Signing",
    "gpg": "Identity & Signing",
    "log": "Log & Display",
    "color": "Log & Display",
    "column": "Log & Display",
    "credential": "Credential & Transfer",
    "http": "Credential & Transfer",
    "transfer": "Credential & Transfer",
    "gc": "Performance",
    "feature": "Performance",
    "index": "Performance",
    "help": "Help & UX",
    "status": "Help & UX",
    "advice": "Help & UX",
    "stash": "Stash",
    # Key-specific (when prefix alone is ambiguous)
    "commit.gpgsign": "Identity & Signing",
    "tag.gpgsign": "Identity & Signing",
    "tag.sort": "Branch & Init",
}


def _config_section(key: str) -> str:
    """Return the display section name for a git config key."""
    if key in CONFIG_SECTION_MAP:
        return CONFIG_SECTION_MAP[key]
    prefix = key.split(".")[0]
    return CONFIG_SECTION_MAP.get(prefix, prefix.capitalize())


# Keys shown in terminal output (top 18 most useful for daily workflow).
# TODO (template users): Add or remove keys to match your team's workflow.
TERMINAL_CONFIG_KEYS: list[str] = [
    # Core
    "core.autocrlf",
    "core.editor",
    # Fetch / Pull / Push
    "fetch.prune",
    "pull.rebase",
    "pull.ff",
    "push.default",
    "push.autoSetupRemote",
    # Merge / Rebase
    "merge.ff",
    "merge.conflictstyle",
    "rebase.autostash",
    "rebase.autoSquash",
    "rerere.enabled",
    # Branch & Init
    "branch.autosetuprebase",
    "init.defaultBranch",
    # Commit & Signing
    "commit.template",
    "commit.gpgsign",
    "tag.gpgsign",
    # Diff
    "diff.algorithm",
]

# TODO (template users): Update HEALTH_CHECKS at the bottom of this file
#   if you add/remove git-related conventions (e.g. signed commits,
#   different branch naming, or GPG verification).


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------


def _run_git(args: list[str], *, timeout: int = 15) -> tuple[int, str, str]:
    """Run a git command and return (returncode, stdout, stderr)."""
    if _GIT is None:
        return 1, "", "git not found on PATH"
    try:
        result = subprocess.run(  # nosec B603
            [_GIT, *args],
            cwd=str(ROOT),
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return 1, "", "git command timed out"
    except (OSError, UnicodeDecodeError) as exc:
        return 1, "", str(exc)


# ---------------------------------------------------------------------------
# Fetch & prune (keep remote-tracking refs current)
# ---------------------------------------------------------------------------


def _fetch_and_prune(*, timeout: int = 30) -> tuple[bool, str]:
    """Run ``git fetch --all --prune`` to refresh remote-tracking refs.

    This ensures the branch activity section works with accurate data
    and that deleted remote branches are cleaned up before we enumerate
    them.  Errors are non-fatal — the rest of the script still runs.
    """
    # TODO (template users): Increase the timeout if your repository has
    #   many remotes or a slow network connection.  Set to 0 to disable
    #   the auto-fetch entirely (the script will use whatever refs are
    #   already cached locally).
    code, out, err = _run_git(["fetch", "--all", "--prune"], timeout=timeout)
    if code == 0:
        return True, out or "fetched successfully"
    return False, err or "fetch failed"


# ---------------------------------------------------------------------------
# Information collectors
# ---------------------------------------------------------------------------


def get_current_branch() -> str:
    """Return the current branch name, or HEAD state."""
    code, out, _ = _run_git(["branch", "--show-current"])
    if code == 0 and out:
        return out
    # Detached HEAD — get short SHA
    code, out, _ = _run_git(["rev-parse", "--short", "HEAD"])
    return f"(detached HEAD: {out})" if code == 0 else "(unknown)"


def get_default_branch() -> str:
    """Return the default branch from origin/HEAD."""
    code, out, _ = _run_git(["symbolic-ref", "refs/remotes/origin/HEAD"])
    if code == 0 and out:
        # refs/remotes/origin/main -> main
        return out.rsplit("/", 1)[-1]
    return "(unknown)"


def get_remote_url() -> str:
    """Return the origin remote URL."""
    code, out, _ = _run_git(["remote", "get-url", "origin"])
    return out if code == 0 and out else "(no remote)"


def get_all_remotes() -> list[dict[str, str]]:
    """Return list of all configured remotes."""
    code, out, _ = _run_git(["remote", "-v"])
    if code != 0 or not out:
        return []
    remotes: dict[str, dict[str, str]] = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            name = parts[0]
            url = parts[1]
            direction = parts[2].strip("()") if len(parts) > 2 else "fetch"
            if name not in remotes:
                remotes[name] = {"name": name, "url": url, "direction": direction}
    return list(remotes.values())


def get_local_branches() -> list[dict[str, str]]:
    """Return local branches with tracking info."""
    code, out, _ = _run_git(
        [
            "branch",
            "-vv",
            "--format=%(refname:short)\t%(upstream:short)\t%(upstream:track)\t%(objectname:short)\t%(committerdate:relative)",
        ]
    )
    if code != 0 or not out:
        return []
    branches: list[dict[str, str]] = []
    for line in out.splitlines():
        parts = line.split("\t", 4)
        if len(parts) >= 1:
            branch: dict[str, str] = {"name": parts[0]}
            if len(parts) >= 2 and parts[1]:
                branch["tracking"] = parts[1]
            if len(parts) >= 3 and parts[2]:
                branch["status"] = parts[2]
            if len(parts) >= 4:
                branch["sha"] = parts[3]
            if len(parts) >= 5:
                branch["last_commit"] = parts[4]
            branches.append(branch)
    return branches


def get_remote_branches() -> list[str]:
    """Return remote branch names (excluding HEAD)."""
    code, out, _ = _run_git(["branch", "-r", "--format=%(refname:short)"])
    if code != 0 or not out:
        return []
    return [b for b in out.splitlines() if b and "HEAD" not in b]


def get_recent_commits(count: int = 5) -> list[dict[str, str]]:
    """Return recent commits on the current branch."""
    code, out, _ = _run_git(
        ["log", f"--max-count={count}", "--format=%h\t%s\t%an\t%ar"]
    )
    if code != 0 or not out:
        return []
    commits: list[dict[str, str]] = []
    for line in out.splitlines():
        parts = line.split("\t", 3)
        if len(parts) >= 2:
            commit: dict[str, str] = {"sha": parts[0], "message": parts[1]}
            if len(parts) >= 3:
                commit["author"] = parts[2]
            if len(parts) >= 4:
                commit["date"] = parts[3]
            commits.append(commit)
    return commits


def get_stash_count() -> int:
    """Return the number of stash entries."""
    code, out, _ = _run_git(["stash", "list"])
    if code != 0 or not out:
        return 0
    return len(out.splitlines())


def get_tags(count: int = 5) -> list[str]:
    """Return recent tags sorted by creation date."""
    code, out, _ = _run_git(["tag", "--sort=-creatordate", f"--count={count}"])
    if code != 0 or not out:
        return []
    return [t for t in out.splitlines() if t]


def get_commit_count() -> int:
    """Return total commit count on the current branch."""
    code, out, _ = _run_git(["rev-list", "--count", "HEAD"])
    if code != 0 or not out:
        return 0
    try:
        return int(out)
    except ValueError:
        return 0


def get_repo_age() -> str:
    """Return the date of the first commit (repo creation proxy).

    Uses ``git rev-list --max-parents=0`` to find the root commit(s),
    then reads the relative date of the earliest one.  The previous
    approach (``git log --reverse -1``) was buggy because ``-1`` limits
    *before* ``--reverse``, giving the most-recent commit instead.
    """
    # Find root commit(s) — commits with no parents
    code, out, _ = _run_git(["rev-list", "--max-parents=0", "HEAD"])
    if code != 0 or not out:
        return "unknown"
    root_sha = out.splitlines()[0]
    code, date_str, _ = _run_git(["log", "-1", "--format=%ar", root_sha])
    return date_str if code == 0 and date_str else "unknown"


def get_contributors_count() -> int:
    """Return unique author count."""
    code, out, _ = _run_git(["shortlog", "-sn", "--all", "--no-merges"])
    if code != 0 or not out:
        return 0
    return len([line for line in out.splitlines() if line.strip()])


def get_top_contributors(limit: int = 5) -> list[dict[str, object]]:
    """Return the top *limit* contributors by commit count.

    Each entry is ``{"name": str, "commits": int}``.
    """
    code, out, _ = _run_git(["shortlog", "-sn", "--all", "--no-merges"])
    if code != 0 or not out:
        return []
    result: list[dict[str, object]] = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        match = re.match(r"(\d+)\s+(.*)", line)
        if match:
            result.append(
                {"name": match.group(2).strip(), "commits": int(match.group(1))}
            )
        if len(result) >= limit:
            break
    return result


def get_commit_frequency() -> dict[str, int]:
    """Return commit counts per day for the last 14 days."""
    code, out, _ = _run_git(
        ["log", "--format=%cd", "--date=short", "--since=14 days ago"]
    )
    if code != 0 or not out:
        return {}
    freq: dict[str, int] = {}
    for line in out.splitlines():
        date = line.strip()
        if date:
            freq[date] = freq.get(date, 0) + 1
    return freq


def _parse_shortstat(text: str) -> dict[str, int]:
    """Parse git ``--shortstat`` output into file/insertion/deletion counts."""
    counts: dict[str, int] = {"files_changed": 0, "insertions": 0, "deletions": 0}
    for line in text.splitlines():
        if "changed" not in line:
            continue
        for part in line.strip().split(","):
            part = part.strip()
            if "file" in part:
                counts["files_changed"] = int(re.sub(r"\D", "", part) or 0)
            elif "insertion" in part:
                counts["insertions"] = int(re.sub(r"\D", "", part) or 0)
            elif "deletion" in part:
                counts["deletions"] = int(re.sub(r"\D", "", part) or 0)
    return counts


def get_file_change_summary() -> dict[str, int]:
    """Return file change counts from recent commits."""
    code, out, _ = _run_git(["diff", "--stat", "--shortstat", "HEAD~5..HEAD"])
    if code != 0 or not out:
        return {}
    return _parse_shortstat(out)


def get_working_tree_status() -> dict[str, int]:
    """Return counts of working tree changes."""
    code, out, _ = _run_git(["status", "--porcelain"])
    if code != 0:
        return {}
    counts: dict[str, int] = {
        "staged": 0,
        "modified": 0,
        "untracked": 0,
        "conflicted": 0,
    }
    for line in out.splitlines():
        if len(line) < 2:
            continue
        index = line[0]
        worktree = line[1]
        if index == "U" or worktree == "U":
            counts["conflicted"] += 1
        elif index == "?":
            counts["untracked"] += 1
        elif worktree in ("M", "D"):
            counts["modified"] += 1
        elif index in ("A", "M", "D", "R", "C"):
            counts["staged"] += 1
    return counts


def find_release_please_branches() -> list[str]:
    """Check for release-please branches (local and remote)."""
    branches: list[str] = []
    # Check remote
    remote_branches = get_remote_branches()
    for b in remote_branches:
        name = b.split("/", 1)[-1] if "/" in b else b
        if name.startswith("release-please"):
            branches.append(b)
    # Check local
    code, out, _ = _run_git(
        ["branch", "--list", "release-please*", "--format=%(refname:short)"]
    )
    if code == 0 and out:
        for b in out.splitlines():
            if b and b not in branches:
                branches.append(b)
    return branches


# ---------------------------------------------------------------------------
# Auto-release system detection
# ---------------------------------------------------------------------------

# Known auto-release branch patterns and config files
_RELEASE_SYSTEMS: list[dict[str, object]] = [
    {
        "name": "release-please",
        "branch_patterns": ["release-please"],
        "config_files": [
            "release-please-config.json",
            ".release-please-manifest.json",
        ],
        "workflow_patterns": ["release-please", "release_please"],
    },
    {
        "name": "semantic-release",
        "branch_patterns": ["semantic-release"],
        "config_files": [
            ".releaserc",
            ".releaserc.json",
            ".releaserc.yml",
            ".releaserc.yaml",
            "release.config.js",
            "release.config.cjs",
        ],
        "workflow_patterns": ["semantic-release", "semantic_release"],
    },
    {
        "name": "changesets",
        "branch_patterns": ["changeset-release"],
        "config_files": [".changeset/config.json"],
        "workflow_patterns": ["changesets", "changeset"],
    },
    {
        "name": "standard-version",
        "branch_patterns": [],
        "config_files": [".versionrc", ".versionrc.json", ".versionrc.js"],
        "workflow_patterns": ["standard-version"],
    },
    {
        "name": "commitizen",
        "branch_patterns": [],
        "config_files": [".cz.toml", ".cz.json", "cz.json"],
        "workflow_patterns": ["commitizen", "cz"],
    },
]


def detect_release_system() -> dict:
    """Detect which auto-release system is configured in this repo.

    Returns a dict with:
        - name: str | None — detected system name
        - config_found: list[str] — config files found
        - branches: list[str] — release branches found
        - workflow_found: bool — whether a matching workflow was found
    """
    result: dict = {
        "name": None,
        "config_found": [],
        "branches": [],
        "workflow_found": False,
        "workflow_files": [],
    }

    remote_branches = get_remote_branches()
    local_branch_names: list[str] = []
    code, out, _ = _run_git(["branch", "--format=%(refname:short)"])
    if code == 0 and out:
        local_branch_names = out.strip().splitlines()

    all_branch_names = []
    for b in remote_branches:
        name = b.split("/", 1)[-1] if "/" in b else b
        all_branch_names.append((name, b))
    all_branch_names.extend((b, b) for b in local_branch_names)

    # Check workflows directory
    workflows_dir = ROOT / ".github" / "workflows"
    workflow_files: list[str] = []
    if workflows_dir.is_dir():
        workflow_files = [
            f.name.lower() for f in workflows_dir.iterdir() if f.is_file()
        ]

    for system in _RELEASE_SYSTEMS:
        sys_name: str = system["name"]  # type: ignore[assignment]
        branch_patterns: list[str] = system["branch_patterns"]  # type: ignore[assignment]
        config_files: list[str] = system["config_files"]  # type: ignore[assignment]
        wf_patterns: list[str] = system["workflow_patterns"]  # type: ignore[assignment]

        # Check config files
        found_configs = []
        for cf in config_files:
            config_path = ROOT / cf
            if config_path.exists():
                found_configs.append(cf)

        # Check branches
        found_branches = []
        for pattern in branch_patterns:
            for short_name, full_name in all_branch_names:
                if short_name.startswith(pattern) and full_name not in found_branches:
                    found_branches.append(full_name)

        # Check workflow files
        wf_found = False
        matched_workflows: list[str] = []
        for wf_pattern in wf_patterns:
            for wf_file in workflow_files:
                if wf_pattern in wf_file and wf_file not in matched_workflows:
                    matched_workflows.append(wf_file)
                    wf_found = True

        # If we found config or workflow, this is the system
        if found_configs or wf_found:
            result["name"] = sys_name
            result["config_found"] = found_configs
            result["branches"] = found_branches
            result["workflow_found"] = wf_found
            result["workflow_files"] = matched_workflows
            break

        # Also match on branches alone if patterns match
        if found_branches:
            result["name"] = sys_name
            result["branches"] = found_branches
            break

    # If no system detected but there are release-please branches,
    # fall back to release-please detection
    if not result["name"] and not result["branches"]:
        # Check for any release-like branches
        for short_name, full_name in all_branch_names:
            if "release" in short_name.lower():
                result["branches"].append(full_name)

    return result


def get_upstream_status() -> str:
    """Check if current branch is ahead/behind its upstream tracking ref.

    Returns a descriptive string including the tracking ref name.
    """
    # Get tracking ref name
    code_ref, tracking_ref, _ = _run_git(
        ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"]
    )
    tracking_name = tracking_ref if code_ref == 0 and tracking_ref else ""

    code, out, _ = _run_git(
        ["rev-list", "--left-right", "--count", "@{upstream}...HEAD"]
    )
    if code != 0:
        return "no upstream"
    parts = out.split()
    if len(parts) == 2:
        behind, ahead = int(parts[0]), int(parts[1])
        suffix = f" (tracking: {tracking_name})" if tracking_name else ""
        if ahead == 0 and behind == 0:
            return f"up to date{suffix}"
        msgs: list[str] = []
        if ahead > 0:
            msgs.append(f"{ahead} ahead")
        if behind > 0:
            msgs.append(f"{behind} behind")
        return ", ".join(msgs) + suffix
    return "unknown"


def get_branch_characteristics() -> dict[str, str]:
    """Compute helpful characteristics of the current working branch.

    Returns a dict with keys like 'on_default_head', 'stale',
    'behind_default', 'fast_forwardable', 'local_only'.
    """
    chars: dict[str, str] = {}
    current = get_current_branch()
    default = get_default_branch()

    if current.startswith("(") or default == "(unknown)":
        return chars

    # Check if branch is on the default branch HEAD
    code_cur, sha_cur, _ = _run_git(["rev-parse", "HEAD"])
    base = _resolve_comparison_base(default)
    code_def, sha_def, _ = _run_git(["rev-parse", base])
    if code_cur == 0 and code_def == 0:
        if sha_cur == sha_def:
            chars["on_default_head"] = f"at {default} HEAD"
        else:
            # Determine if we're ahead (normal feature branch) or behind+ahead
            # to give a more helpful description than just "diverged"
            code_behind, out_behind, _ = _run_git(
                ["rev-list", "--count", f"HEAD..{base}"]
            )
            behind_count = int(out_behind) if code_behind == 0 and out_behind else -1
            if behind_count == 0:
                # Branch has all of default's commits but also has its own
                chars["on_default_head"] = (
                    f"ahead of {default} (contains all {default} commits)"
                )
            else:
                chars["on_default_head"] = f"diverged from {default}"

    # Behind default branch count
    code, out, _ = _run_git(["rev-list", "--count", f"HEAD..{base}"])
    if code == 0 and out:
        behind_default = int(out)
        if behind_default > 0:
            chars["behind_default"] = f"{behind_default} commit(s) behind {default}"
        else:
            chars["behind_default"] = f"up to date with {default}"

    # Staleness — days since last commit on current branch
    code, out, _ = _run_git(["log", "-1", "--format=%ct", current])
    if code == 0 and out:
        last_commit_ts = int(out)
        days_since = (time.time() - last_commit_ts) / 86400
        if days_since > _STALE_BRANCH_DAYS:
            chars["stale"] = f"stale ({int(days_since)} days since last commit)"
        elif days_since > _AGING_BRANCH_DAYS:
            chars["stale"] = f"aging ({int(days_since)} days since last commit)"
        else:
            chars["stale"] = "active"

    # Fast-forwardable — can branch be fast-forwarded to default?
    code, out, _ = _run_git(["merge-base", "--is-ancestor", "HEAD", base])
    if code == 0:
        chars["fast_forwardable"] = f"already contained in {default}"
    else:
        code, out, _ = _run_git(["merge-base", "--is-ancestor", base, "HEAD"])
        if code == 0:
            chars["fast_forwardable"] = f"fast-forwardable into {default}"
        else:
            chars["fast_forwardable"] = "requires merge/rebase"

    # Local-only — no remote tracking branch
    code_ref, tracking_ref, _ = _run_git(
        ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"]
    )
    if code_ref != 0:
        chars["local_only"] = "local only (no remote tracking)"
    else:
        chars["local_only"] = "remote tracked"

    # Unpushed commits — ahead of tracking branch
    if code_ref == 0 and tracking_ref:
        code, out, _ = _run_git(["rev-list", "--count", f"{tracking_ref}..HEAD"])
        if code == 0 and out:
            unpushed = int(out)
            if unpushed > 0:
                chars["unpushed"] = f"{unpushed} unpushed commit(s)"
            else:
                chars["unpushed"] = "all commits pushed"

    # Branch age — time since first commit unique to this branch
    if base != "(unknown)":
        code, out, _ = _run_git(
            ["log", "--reverse", "--format=%cr", f"{base}..{current}", "--"]
        )
        if code == 0 and out:
            first_line = out.splitlines()[0]
            chars["branch_age"] = f"created {first_line}"

    # Ahead of default — commits unique to this branch
    if base != "(unknown)":
        code, out, _ = _run_git(["rev-list", "--count", f"{base}..{current}"])
        if code == 0 and out:
            ahead_count = int(out)
            chars["ahead_default"] = f"{ahead_count} commit(s) ahead of {default}"

    # Commit density — commits in last 7 days on this branch
    code, out, _ = _run_git(["rev-list", "--count", "--since=7.days", current])
    if code == 0 and out:
        recent = int(out)
        if recent == 0:
            chars["commit_density"] = "no commits in last 7 days"
        elif recent <= 3:
            chars["commit_density"] = f"{recent} commit(s) in last 7 days (light)"
        elif recent <= 10:
            chars["commit_density"] = f"{recent} commit(s) in last 7 days (moderate)"
        else:
            chars["commit_density"] = f"{recent} commit(s) in last 7 days (heavy)"

    # Has merge conflicts in progress
    if get_merge_conflicts():
        chars["conflicts"] = "unresolved merge conflicts"

    return chars


def get_merge_conflicts() -> bool:
    """Check if there are unresolved merge conflicts."""
    code, out, _ = _run_git(["diff", "--check"])
    return code != 0 and "conflict" in out.lower()


def get_git_config_value(key: str) -> str:
    """Get a git config value."""
    code, out, _ = _run_git(["config", "--get", key])
    return out if code == 0 else ""


def get_git_config_scope(key: str) -> str:
    """Return the scope where a git config key is set (local/global/system/unset)."""
    code, out, _ = _run_git(["config", "--show-scope", "--get", key])
    if code != 0 or not out:
        return "unset"
    return out.split()[0]


def get_branch_diff_stats(branch: str, base: str) -> dict[str, int]:
    """Get insertions/deletions/files changed for *branch* vs *base*."""
    code, out, _ = _run_git(["diff", "--shortstat", f"{base}...{branch}"])
    if code != 0 or not out:
        return {"files_changed": 0, "insertions": 0, "deletions": 0}
    return _parse_shortstat(out)


def get_branch_commit_count(ref: str) -> int:
    """Return total commit count reachable from *ref*.

    .. note:: This counts the **entire history** reachable from the ref,
       not just commits unique to a branch.  For branch-specific counts
       use ``get_branch_unique_commit_count()`` instead.
    """
    code, out, _ = _run_git(["rev-list", "--count", ref])
    if code != 0 or not out:
        return 0
    try:
        return int(out)
    except ValueError:
        return 0


def get_branch_unique_commit_count(branch: str, base: str) -> int:
    """Return commits on *branch* not reachable from *base*.

    This gives the number of commits unique to *branch* since it
    diverged from *base* (typically the default branch).
    """
    code, out, _ = _run_git(["rev-list", "--count", f"{base}..{branch}"])
    if code != 0 or not out:
        return 0
    try:
        return int(out)
    except ValueError:
        return 0


def _resolve_comparison_base(default: str) -> str:
    """Return the best ref to compare branches against.

    Prefers ``origin/<default>`` because the local default branch may be
    stale (behind origin).  Using the local ref inflates commit counts
    and diff stats for every remote branch.
    """
    if default == "(unknown)":
        return default
    origin_ref = f"origin/{default}"
    # Verify origin ref exists
    code, _, _ = _run_git(["rev-parse", "--verify", origin_ref])
    if code == 0:
        return origin_ref
    return default


def get_recent_branches_with_stats(
    count: int = 5,
) -> list[dict[str, object]]:
    """Return most recent branches (local + remote) with diff stats vs default.

    Uses ``origin/<default>`` as the comparison base so stats remain
    accurate even when the local default branch is behind the remote.
    Stale remote-tracking refs are avoided by running ``git fetch --prune``
    before this function is called.
    """
    default = get_default_branch()
    base = _resolve_comparison_base(default)

    code, out, _ = _run_git(
        [
            "for-each-ref",
            "--sort=-committerdate",
            "--format=%(refname:short)\t%(committerdate:relative)\t%(objectname:short)\t%(refname)",
            "refs/heads/",
            "refs/remotes/",
        ]
    )
    if code != 0 or not out:
        return []

    seen: set[str] = set()
    branches: list[dict[str, object]] = []

    for line in out.splitlines():
        parts = line.split("\t", 3)
        if len(parts) < 4:
            continue
        name, date, sha, ref = parts[0], parts[1], parts[2], parts[3]
        if "HEAD" in name:
            continue
        # Skip the default branch itself (both local and remote)
        base_name = name.split("/", 1)[-1] if name.startswith("origin/") else name
        if base_name == default:
            continue
        # Deduplicate local/remote pairs
        if base_name in seen:
            continue
        seen.add(base_name)

        # Verify ref is still reachable (deleted remote branches may linger)
        verify_code, _, _ = _run_git(["rev-parse", "--verify", name])
        if verify_code != 0:
            continue

        # Count only commits unique to this branch (not entire repo history)
        if base != "(unknown)":
            unique_commits = get_branch_unique_commit_count(name, base)
        else:
            unique_commits = get_branch_commit_count(name)

        entry: dict[str, object] = {
            "name": name,
            "base_name": base_name,
            "date": date,
            "sha": sha,
            "source": "remote" if ref.startswith("refs/remotes/") else "local",
            "commits": unique_commits,
            "files_changed": 0,
            "insertions": 0,
            "deletions": 0,
        }
        if base != "(unknown)":
            stats = get_branch_diff_stats(name, base)
            entry.update(stats)
        branches.append(entry)
        if len(branches) >= count:
            break

    return branches


def get_working_branch_stats() -> dict[str, dict[str, int]]:
    """Get current branch stats: staged, unstaged, and total diff vs default."""
    empty: dict[str, int] = {"files_changed": 0, "insertions": 0, "deletions": 0}
    result: dict[str, dict[str, int]] = {}

    # Unstaged changes
    code, out, _ = _run_git(["diff", "--shortstat"])
    result["unstaged"] = _parse_shortstat(out) if code == 0 and out else dict(empty)

    # Staged changes
    code, out, _ = _run_git(["diff", "--cached", "--shortstat"])
    result["staged"] = _parse_shortstat(out) if code == 0 and out else dict(empty)

    # Total branch diff vs default
    default = get_default_branch()
    if default != "(unknown)":
        current = get_current_branch()
        result["vs_default"] = get_branch_diff_stats(current, default)
    else:
        result["vs_default"] = dict(empty)

    return result


# ---------------------------------------------------------------------------
# --view-commits: detailed commit info for current branch
# ---------------------------------------------------------------------------


def get_branch_origin_point() -> dict[str, str]:
    """Return info about where the current branch diverges from default."""
    default = get_default_branch()
    current = get_current_branch()
    if default == "(unknown)" or current.startswith("("):
        return {"origin_branch": "(unknown)"}
    base = _resolve_comparison_base(default)
    code, merge_base, _ = _run_git(["merge-base", current, base])
    if code != 0 or not merge_base:
        return {"origin_branch": default}
    code, out, _ = _run_git(["log", "-1", "--format=%h\t%ar", merge_base])
    result: dict[str, str] = {"origin_branch": default, "merge_base": merge_base[:10]}
    if code == 0 and out:
        parts = out.split("\t", 1)
        result["merge_base_short"] = parts[0]
        if len(parts) >= 2:
            result["merge_base_date"] = parts[1]
    return result


def get_detailed_branch_commits(
    *,
    progress_bar: ProgressBar | None = None,
) -> list[dict[str, object]]:
    """Return every commit on the current branch (unique vs default).

    Each entry contains: sha, message, author, date, datetime, and a
    list of files with per-file insertions/deletions.

    Args:
        progress_bar: Optional ProgressBar whose ``total`` will be set
            to the commit count once known, then ``update()`` called
            after each commit's file stats are fetched.
    """
    default = get_default_branch()
    current = get_current_branch()
    if default == "(unknown)" or current.startswith("("):
        # Fallback: last 50 commits on HEAD
        range_spec = "-50"
    else:
        base = _resolve_comparison_base(default)
        range_spec = f"{base}..HEAD"

    # Get commit SHAs first (fast — single git call)
    code, out, _ = _run_git(["log", range_spec, "--format=%H\t%h\t%s\t%an\t%aI\t%ar"])
    if code != 0 or not out:
        return []

    raw_lines = [ln for ln in out.splitlines() if ln.split("\t", 1)[0]]

    # Set progress bar total now that we know the commit count
    if progress_bar is not None:
        progress_bar.total = len(raw_lines)

    commits: list[dict[str, object]] = []
    for line in raw_lines:
        parts = line.split("\t", 5)
        if len(parts) < 2:
            continue
        entry: dict[str, object] = {
            "sha": parts[0],
            "sha_short": parts[1],
            "message": parts[2] if len(parts) >= 3 else "",
            "author": parts[3] if len(parts) >= 4 else "",
            "datetime": parts[4] if len(parts) >= 5 else "",
            "date_relative": parts[5] if len(parts) >= 6 else "",
        }

        # Per-commit file stats
        stat_code, stat_out, _ = _run_git(
            ["diff-tree", "--no-commit-id", "-r", "--numstat", parts[0]]
        )
        files: list[dict[str, str | int]] = []
        commit_ins = 0
        commit_del = 0
        if stat_code == 0 and stat_out:
            for stat_line in stat_out.splitlines():
                stat_parts = stat_line.split("\t", 2)
                if len(stat_parts) >= 3:
                    ins = int(stat_parts[0]) if stat_parts[0] != "-" else 0
                    dels = int(stat_parts[1]) if stat_parts[1] != "-" else 0
                    files.append(
                        {
                            "file": stat_parts[2],
                            "insertions": ins,
                            "deletions": dels,
                        }
                    )
                    commit_ins += ins
                    commit_del += dels

        entry["files"] = files
        entry["total_insertions"] = commit_ins
        entry["total_deletions"] = commit_del
        commits.append(entry)

        if progress_bar is not None:
            progress_bar.update(parts[1])  # short SHA

    return commits


def get_branch_conflict_files() -> list[str]:
    """Check if the current branch has conflicts with the default branch.

    Does a trial merge (without committing) to detect files that would
    conflict. Returns a list of conflicting file paths.
    """
    default = get_default_branch()
    if default == "(unknown)":
        return []
    base = _resolve_comparison_base(default)

    # Check working tree is clean enough for a trial merge
    status = get_working_tree_status()
    if status.get("conflicted", 0) > 0:
        # Already in a conflict state
        code, out, _ = _run_git(["diff", "--name-only", "--diff-filter=U"])
        if code == 0 and out:
            return out.splitlines()
        return []

    # Use merge-tree (git 2.38+) for a safe conflict check without touching worktree
    code, out, _ = _run_git(["merge-tree", "--write-tree", "HEAD", base])
    if code == 0:
        # No conflicts
        return []
    # merge-tree exits non-zero if conflicts; parse the output
    conflicts: list[str] = []
    if out:
        for line in out.splitlines():
            # Lines starting with "CONFLICT" indicate conflict files
            if line.startswith("CONFLICT"):
                # Extract filename from "CONFLICT (content): Merge conflict in <file>"
                match = re.search(r"Merge conflict in (.+)$", line)
                if match:
                    conflicts.append(match.group(1).strip())
    return conflicts


def get_modified_files(limit: int = 15) -> list[dict[str, str]]:
    """Return modified/untracked files in the working directory."""
    code, out, _ = _run_git(["status", "--porcelain"])
    if code != 0 or not out:
        return []
    _status_map = {
        "M": "modified",
        "A": "added",
        "D": "deleted",
        "R": "renamed",
        "C": "copied",
        "?": "untracked",
        "U": "conflicted",
    }
    files: list[dict[str, str]] = []
    for line in out.splitlines():
        if len(line) < 3:
            continue
        idx, wt = line[0], line[1]
        fname = line[3:]
        if idx == "?" or wt == "?":
            label = "untracked"
        elif idx == "U" or wt == "U":
            label = "conflicted"
        elif wt in ("M", "D"):
            label = _status_map.get(wt, wt)
        else:
            label = _status_map.get(idx, idx) + " (staged)"
        files.append({"file": fname, "status": label})
        if len(files) >= limit:
            break
    return files


def get_stale_branches(days: int = 30) -> list[dict[str, str]]:
    """Return local branches with no commits in the last *days* days."""
    code, out, _ = _run_git(
        [
            "for-each-ref",
            "--sort=committerdate",
            "--format=%(refname:short)\t%(committerdate:relative)\t%(committerdate:unix)",
            "refs/heads/",
        ]
    )
    if code != 0 or not out:
        return []
    cutoff = time.time() - (days * 86400)
    stale: list[dict[str, str]] = []
    for line in out.splitlines():
        parts = line.split("\t", 2)
        if len(parts) < 3:
            continue
        try:
            ts = float(parts[2])
        except ValueError:
            continue
        if ts < cutoff:
            stale.append({"name": parts[0], "last_commit": parts[1]})
    return stale


def get_git_config_summary() -> dict[str, str]:
    """Return key git configuration values (top 18 for terminal display).

    Returns the terminal-display subset of config keys with their values.
    Keys not set in any scope get ``"(unset)"``.  The full catalog is
    available via ``--export-config``.
    """
    return {k: get_git_config_value(k) or "(unset)" for k in TERMINAL_CONFIG_KEYS}


def get_unmerged_branches() -> list[dict[str, str]]:
    """Return local branches not yet merged into the default branch.

    Compares against ``origin/<default>`` (not the local ref) so
    branches that were merged via PR and deleted on the remote are
    correctly excluded — even if the local ``<default>`` hasn't been
    pulled recently.

    Branches whose upstream tracking reference is ``[gone]`` (remote
    deleted) are **excluded** by default — they were almost certainly
    merged via PR (rebase-merge or squash-merge) and deleting the
    remote branch is the normal post-merge workflow.  These are not
    "unmerged" in the meaningful sense; ``git branch --no-merged``
    reports them because rebase-merge and squash-merge create new
    commits rather than fast-forwarding.
    """
    # TODO (template users): If your team uses regular merges (not
    #   rebase-merge or squash-merge), you may want to re-include [gone]
    #   branches since they could genuinely be unmerged.  Change
    #   ``if "gone" in track: continue`` to the annotation approach
    #   from the previous version.
    default = get_default_branch()
    if default == "(unknown)":
        return []
    # Prefer origin/<default> for accuracy; fall back to local ref
    target = f"origin/{default}"
    code, out, _ = _run_git(
        ["branch", "--no-merged", target, "--format=%(refname:short)"]
    )
    if code != 0:
        # Fallback: local default branch ref
        code, out, _ = _run_git(
            ["branch", "--no-merged", default, "--format=%(refname:short)"]
        )
    if code != 0 or not out:
        return []

    # Cross-reference with tracking status to detect squash-merged branches
    tracking_info: dict[str, str] = {}
    tc, tout, _ = _run_git(
        ["branch", "-vv", "--format=%(refname:short)\t%(upstream:track)"]
    )
    if tc == 0 and tout:
        for line in tout.splitlines():
            parts = line.split("\t", 1)
            if len(parts) == 2:
                tracking_info[parts[0]] = parts[1]

    branches: list[dict[str, str]] = []
    for b in out.splitlines():
        b = b.strip()
        if not b:
            continue
        track = tracking_info.get(b, "")
        # Skip branches whose remote has been deleted — these are almost
        # certainly merged via squash/PR.  Listing them as "unmerged" is
        # misleading because the remote deletion is the normal post-merge
        # cleanup step.
        if "gone" in track:
            continue
        branches.append({"name": b, "note": ""})
    return branches


def get_last_merge_from_default() -> dict[str, str]:
    """Return info about the last merge from the default branch into current.

    Finds the most recent merge commit where the default branch (e.g. main)
    was merged into the current branch. Useful for knowing how fresh your
    branch is relative to the mainline.
    """
    default = get_default_branch()
    current = get_current_branch()
    if default == "(unknown)" or current == default:
        return {}

    # Find the merge-base (common ancestor)
    code, merge_base, _ = _run_git(["merge-base", current, default])
    if code != 0 or not merge_base:
        return {}

    # Get the date and message of the merge-base commit
    code, out, _ = _run_git(
        ["log", "-1", "--format=%H\t%h\t%s\t%an\t%ar\t%ai", merge_base]
    )
    if code != 0 or not out:
        return {}

    parts = out.split("\t", 5)
    result: dict[str, str] = {"merge_base_sha": parts[0], "sha_short": parts[1]}
    if len(parts) >= 3:
        result["message"] = parts[2]
    if len(parts) >= 4:
        result["author"] = parts[3]
    if len(parts) >= 5:
        result["relative_date"] = parts[4]
    if len(parts) >= 6:
        result["date"] = parts[5]

    # Count how many commits default branch is ahead of the merge-base
    code, out, _ = _run_git(["rev-list", "--count", f"{merge_base}..{default}"])
    if code == 0 and out:
        result["default_ahead"] = out

    # Count how many commits current branch is ahead of the merge-base
    code, out, _ = _run_git(["rev-list", "--count", f"{merge_base}..{current}"])
    if code == 0 and out:
        result["current_ahead"] = out

    return result


def get_first_commit_on_branch() -> dict[str, str]:
    """Return info about when the current branch diverged from default."""
    default = get_default_branch()
    current = get_current_branch()
    if default == "(unknown)" or current == default:
        return {}

    # Find the first commit after diverging from default
    code, merge_base, _ = _run_git(["merge-base", current, default])
    if code != 0 or not merge_base:
        return {}

    code, out, _ = _run_git(
        ["log", "--format=%h\t%s\t%ar", "--reverse", f"{merge_base}..HEAD", "-1"]
    )
    if code != 0 or not out:
        return {}

    parts = out.split("\t", 2)
    result: dict[str, str] = {"sha": parts[0]}
    if len(parts) >= 2:
        result["message"] = parts[1]
    if len(parts) >= 3:
        result["date"] = parts[2]
    return result


# ---------------------------------------------------------------------------
# Health checks
# ---------------------------------------------------------------------------


def check_git_installed() -> tuple[bool, str]:
    """Verify git is available."""
    if _GIT is None:
        return False, "git not found in PATH"
    code, out, _ = _run_git(["--version"])
    return (True, out) if code == 0 else (False, "git found but failed to run")


def check_inside_repo() -> tuple[bool, str]:
    """Verify we're inside a git repo."""
    code, _, _ = _run_git(["rev-parse", "--is-inside-work-tree"])
    if code == 0:
        return True, "Inside a git repository"
    return False, "Not inside a git repository"


def check_clean_workdir() -> tuple[bool, str]:
    """Check for uncommitted changes."""
    status = get_working_tree_status()
    total = sum(status.values())
    if total == 0:
        return True, "Working directory clean"
    parts: list[str] = []
    for key, count in status.items():
        if count > 0:
            parts.append(f"{count} {key}")
    return False, f"Dirty working directory: {', '.join(parts)}"


def check_no_conflicts() -> tuple[bool, str]:
    """Check for merge conflicts."""
    code, out, _ = _run_git(["diff", "--name-only", "--diff-filter=U"])
    if code != 0 or not out:
        return True, "No merge conflicts"
    count = len(out.splitlines())
    return False, f"{count} file(s) with merge conflicts"


def check_upstream_configured() -> tuple[bool, str]:
    """Check if current branch tracks an upstream."""
    branch = get_current_branch()
    code, out, _ = _run_git(["config", f"branch.{branch}.remote"])
    if code == 0 and out:
        return True, f"Upstream configured: {out}/{branch}"
    return False, f"Branch '{branch}' has no upstream tracking"


def check_no_detached_head() -> tuple[bool, str]:
    """Check we're not in detached HEAD state."""
    code, _out, _ = _run_git(["symbolic-ref", "-q", "HEAD"])
    if code == 0:
        return True, "On a named branch"
    return False, "Detached HEAD state"


def check_fetch_recent() -> tuple[bool, str]:
    """Check if a fetch has happened recently (last hour)."""
    fetch_head = ROOT / ".git" / "FETCH_HEAD"
    if not fetch_head.exists():
        return False, "Never fetched - run: git fetch"

    age_seconds = time.time() - fetch_head.stat().st_mtime
    age_minutes = age_seconds / 60
    age_hours = age_seconds / 3600
    if age_hours < 1:
        return True, f"Last fetch: {age_minutes:.0f}m ago"
    if age_hours < 24:
        return True, f"Last fetch: {age_hours:.1f}h ago"
    days = age_hours / 24
    return False, f"Last fetch: {days:.0f}d ago - consider running: git fetch"


def check_gitignore_exists() -> tuple[bool, str]:
    """Check .gitignore exists."""
    if (ROOT / ".gitignore").is_file():
        return True, ".gitignore present"
    return False, ".gitignore missing"


def check_no_large_files_staged() -> tuple[bool, str]:
    """Warn about files above *_LARGE_FILE_THRESHOLD_MB* staged for commit."""
    code, out, _ = _run_git(["diff", "--cached", "--name-only"])
    if code != 0 or not out:
        return True, "No large staged files"
    large: list[str] = []
    for fname in out.splitlines():
        fpath = ROOT / fname
        if fpath.is_file():
            size_mb = fpath.stat().st_size / (1024 * 1024)
            if size_mb > _LARGE_FILE_THRESHOLD_MB:
                large.append(f"{fname} ({size_mb:.1f} MB)")
    if large:
        return False, f"Large staged files: {', '.join(large[:3])}"
    return True, "No large staged files"


def check_branch_protection_alignment() -> tuple[bool, str]:
    """Check if default branch in git matches workflow expectations.

    .. note:: This check uses a simple regex to find ``branches:`` keys in
       workflow YAML.  It can false-positive on workflows that intentionally
       omit the default branch (e.g. release-only or tag-triggered workflows)
       or match commented-out lines.
    """
    # TODO (template users): If your workflows intentionally target branches
    #   other than the default, exclude those workflow files here or adjust
    #   the regex to skip commented-out lines.
    code, out, _ = _run_git(["symbolic-ref", "refs/remotes/origin/HEAD"])
    if code != 0:
        return (
            False,
            "Cannot determine default branch - run: git remote set-head origin --auto",
        )
    default_branch = out.rsplit("/", 1)[-1]

    # Check workflows reference the same branch
    workflows_dir = ROOT / ".github" / "workflows"
    mismatches: list[str] = []
    if workflows_dir.is_dir():
        for wf in workflows_dir.glob("*.yml"):
            try:
                content = wf.read_text(encoding="utf-8")
                for match in re.finditer(
                    r"branches:\s*\[([^\]]+)\]|branches:\s*\n\s*-\s*(\S+)",
                    content,
                ):
                    branch_refs = match.group(1) or match.group(2)
                    if branch_refs and default_branch not in branch_refs:
                        mismatches.append(wf.name)
                        break
            except OSError:
                continue

    if mismatches:
        return (
            False,
            f"Default branch '{default_branch}' not referenced in workflows: "
            f"{', '.join(mismatches[:5])}",
        )
    return True, f"Default branch '{default_branch}' aligns with workflows"


def check_git_hooks_integrity() -> tuple[bool, str]:
    """Verify pre-commit hook files are actual pre-commit scripts.

    Goes beyond existence checking — reads content to detect empty
    stubs, corrupted files, sample hooks, or non-pre-commit hooks.
    """
    hooks_dir = ROOT / ".git" / "hooks"
    if not hooks_dir.is_dir():
        return False, "No .git/hooks directory"

    expected = ["pre-commit", "commit-msg", "pre-push"]
    issues: list[str] = []
    ok_count = 0

    for hook_name in expected:
        hook_path = hooks_dir / hook_name
        if not hook_path.is_file():
            issues.append(f"{hook_name}: missing")
            continue

        try:
            content = hook_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            issues.append(f"{hook_name}: unreadable")
            continue

        content_stripped = content.strip()
        if not content_stripped:
            issues.append(f"{hook_name}: empty file")
        elif len(content_stripped) < 10:
            issues.append(
                f"{hook_name}: suspiciously small ({len(content_stripped)} bytes)"
            )
        elif "generated by pre-commit" not in content.lower():
            if ".sample" in hook_path.name or "this sample" in content.lower():
                issues.append(f"{hook_name}: git sample hook (not pre-commit)")
            else:
                issues.append(f"{hook_name}: custom script (not managed by pre-commit)")
        else:
            ok_count += 1

    if not issues:
        return True, f"All {ok_count} hook files are valid pre-commit hooks"
    return False, "; ".join(issues)


def check_git_remote_health() -> tuple[bool, str]:
    """Verify origin remote URL looks correct and matches pyproject.toml."""
    url = get_remote_url()
    if url == "(no remote)":
        return False, "No origin remote configured"

    issues: list[str] = []

    valid_prefixes = ("https://", "git@", "ssh://", "git://")
    if not any(url.startswith(p) for p in valid_prefixes):
        issues.append(f"Unusual URL scheme: {url}")

    pyproject = read_pyproject(ROOT)
    if pyproject is not None:
        project = pyproject.get("project", {})
        if isinstance(project, dict):
            urls = project.get("urls", {})
            if isinstance(urls, dict):
                repo_url = urls.get("Repository", "")
                if isinstance(repo_url, str) and repo_url:
                    remote_slug = extract_repo_slug(url)
                    declared_slug = extract_repo_slug(repo_url)
                    if remote_slug and declared_slug and remote_slug != declared_slug:
                        issues.append(
                            f"Remote ({remote_slug}) doesn't match "
                            f"pyproject.toml Repository URL ({declared_slug})"
                        )

    if issues:
        return False, "; ".join(issues)
    return True, f"Remote origin: {url}"


def check_conventional_commits() -> tuple[bool, str]:
    """Check if recent commits follow Conventional Commits format."""
    code, out, _ = _run_git(["log", "-10", "--format=%s"])
    if code != 0 or not out:
        return True, "No commits to check"
    conventional_re = re.compile(
        r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"
        r"(\([^)]+\))?!?: .+"
    )
    non_conventional: list[str] = []
    subjects = out.splitlines()
    for subject in subjects:
        # Skip merge commits and release-please commits
        if subject.startswith(("Merge ", "chore(main):")):
            continue
        if not conventional_re.match(subject):
            non_conventional.append(subject[:50])
    if non_conventional:
        count = len(non_conventional)
        example = non_conventional[0]
        return (
            False,
            f"{count}/{len(subjects)} recent commits non-conventional "
            f'(e.g. "{example}")',
        )
    return True, "Recent commits follow Conventional Commits"


def check_gitmessage_template() -> tuple[bool, str]:
    """Check if .gitmessage commit template is configured."""
    template_path = ROOT / ".gitmessage.txt"
    if not template_path.is_file():
        return True, "No .gitmessage.txt (optional)"
    configured = get_git_config_value("commit.template")
    if configured:
        return True, f"Commit template configured: {configured}"
    return (
        False,
        "Found .gitmessage.txt but git commit.template not set "
        "- run: git config commit.template .gitmessage.txt",
    )


def check_user_identity() -> tuple[bool, str]:
    """Check that user.name and user.email are configured."""
    name = get_git_config_value("user.name")
    email = get_git_config_value("user.email")
    if name and email:
        return True, f"Identity: {name} <{email}>"
    missing: list[str] = []
    if not name:
        missing.append("user.name")
    if not email:
        missing.append("user.email")
    return False, f"Missing git config: {', '.join(missing)}"


def check_merge_base_freshness() -> tuple[bool, str]:
    """Warn if the current branch hasn't been rebased/merged from default recently.

    Checks how many commits the default branch is ahead of the merge-base.
    A high divergence means the branch may have merge conflicts waiting.
    """
    current = get_current_branch()
    default = get_default_branch()
    if default == "(unknown)" or current == default:
        return True, "On default branch (no merge-base to check)"

    merge_info = get_last_merge_from_default()
    if not merge_info:
        return False, f"Cannot determine merge-base with {default}"

    default_ahead = int(merge_info.get("default_ahead", "0"))
    rel_date = merge_info.get("relative_date", "unknown")

    if default_ahead == 0:
        return True, f"Branch is up to date with {default}"
    if default_ahead <= _MERGE_BASE_THRESHOLD:
        return (
            True,
            f"{default} is {default_ahead} commits ahead (merge-base: {rel_date})",
        )
    return (
        False,
        f"{default} is {default_ahead} commits ahead "
        f"(merge-base: {rel_date}) "
        f"- consider: git fetch origin && git rebase origin/{default}",
    )


# ---------------------------------------------------------------------------
# Helpful git commands reference
# ---------------------------------------------------------------------------

# TODO (template users): Add or remove helpful git commands that match your
#   team's git workflow (e.g. signed commits, rebase preferences).
HELPFUL_COMMANDS: list[dict[str, str]] = [
    {
        "cmd": "git fetch --all --prune",
        "desc": "Fetch all remotes, remove stale tracking branches",
    },
    {"cmd": "git log --oneline -10", "desc": "Show last 10 commits"},
    {"cmd": "git status -sb", "desc": "Short status with branch info"},
    {"cmd": "git stash list", "desc": "List stash entries"},
    {"cmd": "git branch -vv", "desc": "List branches with tracking info"},
    {"cmd": "git remote -v", "desc": "Show all remotes"},
    {"cmd": "git diff --stat", "desc": "Summary of uncommitted changes"},
    {"cmd": "git log --all --graph --oneline -20", "desc": "Visual branch graph"},
    {"cmd": "git reflog -10", "desc": "Recent HEAD movements (undo helper)"},
    {"cmd": "git clean -fdn", "desc": "Preview untracked files that would be removed"},
    {
        "cmd": "git config --global --list",
        "desc": "View all global git configuration settings",
    },
    {
        "cmd": "git config --list --show-origin",
        "desc": "View all git config values with their source file",
    },
    {
        "cmd": "git pull --rebase",
        "desc": "Pull and rebase local commits on top of upstream (linear history)",
    },
    {
        "cmd": "git push --force-with-lease",
        "desc": "Force push safely (fails if remote has unexpected new commits)",
    },
]


# ---------------------------------------------------------------------------
# Check runner
# ---------------------------------------------------------------------------

CheckFn = Callable[[], tuple[bool, str]]

# TODO (template users): Add or remove health checks to match your
#   project's git conventions (e.g. require signed commits, enforce
#   branch naming patterns, check for .gitmessage).
HEALTH_CHECKS: list[tuple[str, CheckFn]] = [
    ("Git installed", check_git_installed),
    ("Inside git repo", check_inside_repo),
    ("Not detached HEAD", check_no_detached_head),
    ("Working directory", check_clean_workdir),
    ("Merge conflicts", check_no_conflicts),
    ("Upstream tracking", check_upstream_configured),
    ("Recent fetch", check_fetch_recent),
    (".gitignore", check_gitignore_exists),
    ("Large staged files", check_no_large_files_staged),
    ("Default branch", check_branch_protection_alignment),
    ("Hook integrity", check_git_hooks_integrity),
    ("Remote health", check_git_remote_health),
    ("Conventional commits", check_conventional_commits),
    ("Commit template", check_gitmessage_template),
    ("User identity", check_user_identity),
    ("Merge-base freshness", check_merge_base_freshness),
]


def _collect_info(
    *,
    spinner_color: str | None = "cyan",
) -> dict[
    str,
    str | int | list[str] | list[dict[str, str]] | dict[str, int],
]:
    """Collect all git information into a dict."""
    collectors: list[tuple[str, Callable[[], object]]] = [
        ("current_branch", get_current_branch),
        ("default_branch", get_default_branch),
        ("remote_url", get_remote_url),
        ("remotes", get_all_remotes),
        ("upstream_status", get_upstream_status),
        ("local_branches", get_local_branches),
        ("remote_branches", get_remote_branches),
        ("recent_commits", lambda: get_recent_commits(5)),
        ("tags", lambda: get_tags(5)),
        ("stash_count", get_stash_count),
        ("commit_count", get_commit_count),
        ("repo_age", get_repo_age),
        ("contributors", get_contributors_count),
        ("top_contributors", get_top_contributors),
        ("working_tree", get_working_tree_status),
        ("release_please_branches", find_release_please_branches),
        ("release_system", detect_release_system),
        ("user_name", lambda: get_git_config_value("user.name")),
        ("user_email", lambda: get_git_config_value("user.email")),
        ("branch_activity", lambda: get_recent_branches_with_stats(5)),
        ("working_branch_stats", get_working_branch_stats),
        ("modified_files", get_modified_files),
        ("stale_branches", get_stale_branches),
        ("git_config", get_git_config_summary),
        (
            "git_config_scopes",
            lambda: {k: get_git_config_scope(k) for k in TERMINAL_CONFIG_KEYS},
        ),
        ("unmerged_branches", get_unmerged_branches),
        ("last_merge_from_default", get_last_merge_from_default),
        ("branch_divergence", get_first_commit_on_branch),
        ("commit_frequency", get_commit_frequency),
        ("file_change_summary", get_file_change_summary),
        ("branch_characteristics", get_branch_characteristics),
    ]
    info: dict[str, object] = {}
    with Spinner("Collecting git info", log_interval=5, color=spinner_color) as spin:
        for key, fn in collectors:
            spin.update(key)
            info[key] = fn()
    return info  # type: ignore[return-value]


def _collect_health(
    *,
    spinner_color: str | None = "cyan",
) -> tuple[list[dict[str, str]], int]:
    """Run all health checks and return (results, failure_count)."""
    results: list[dict[str, str]] = []
    failures = 0
    with Spinner("Running health checks", log_interval=5, color=spinner_color) as spin:
        for name, check_fn in HEALTH_CHECKS:
            spin.update(name)
            passed, msg = check_fn()
            status = "PASS" if passed else "FAIL"
            if not passed:
                failures += 1
            results.append({"name": name, "status": status, "message": msg})
    return results, failures


def run(
    *,
    color: bool | None = None,
    output_json: bool = False,
) -> int:
    """Run git doctor and print results.

    Args:
        color: Force color on/off. None = auto-detect.
        output_json: Output as JSON.

    Returns:
        Exit code: 0 = healthy, 1 = issues found.
    """
    elapsed_start = time.monotonic()

    # Resolve spinner color: --no-color (color=False) disables it.
    spinner_color: str | None = None if color is False else "cyan"

    # Fetch and prune stale remote-tracking refs before collecting data.
    # This ensures branch activity stats are accurate and deleted remote
    # branches don't pollute the output.
    with Spinner("Fetching remotes", log_interval=5, color=spinner_color):
        fetch_ok, fetch_msg = _fetch_and_prune()
        if not fetch_ok:
            logger.warning(
                "git fetch failed: %s (continuing with stale data)", fetch_msg
            )

    # Run additional diagnostic commands at startup
    _status_code, _status_out, _ = _run_git(["status", "--porcelain"])
    status_cmd_ok = _status_code == 0
    _revparse_code, _, _ = _run_git(["rev-parse", "--git-dir"])
    revparse_cmd_ok = _revparse_code == 0

    # Collect info once and reuse for both display and JSON
    info = _collect_info(spinner_color=spinner_color)
    current_branch: str = info["current_branch"]  # type: ignore[assignment]
    default_branch: str = info["default_branch"]  # type: ignore[assignment]
    remote_url: str = info["remote_url"]  # type: ignore[assignment]
    upstream_status: str = info["upstream_status"]  # type: ignore[assignment]
    local_branches: list[dict[str, str]] = info["local_branches"]  # type: ignore[assignment]
    recent_commits: list[dict[str, str]] = info["recent_commits"]  # type: ignore[assignment]
    tags: list[str] = info["tags"]  # type: ignore[assignment]
    stash_count: int = info["stash_count"]  # type: ignore[assignment]
    commit_count: int = info["commit_count"]  # type: ignore[assignment]
    repo_age: str = info["repo_age"]  # type: ignore[assignment]
    contributors: int = info["contributors"]  # type: ignore[assignment]
    top_contributors: list[dict[str, object]] = info["top_contributors"]  # type: ignore[assignment]
    working_tree: dict[str, int] = info["working_tree"]  # type: ignore[assignment]
    rp_branches: list[str] = info["release_please_branches"]  # type: ignore[assignment]
    release_system: dict = info.get("release_system", {})  # type: ignore[assignment]
    user_name: str = info["user_name"]  # type: ignore[assignment]
    user_email: str = info["user_email"]  # type: ignore[assignment]
    branch_activity: list[dict[str, object]] = info["branch_activity"]  # type: ignore[assignment]
    wb_stats: dict[str, dict[str, int]] = info["working_branch_stats"]  # type: ignore[assignment]
    modified_files: list[dict[str, str]] = info["modified_files"]  # type: ignore[assignment]
    stale_branches: list[dict[str, str]] = info["stale_branches"]  # type: ignore[assignment]
    git_config: dict[str, str] = info["git_config"]  # type: ignore[assignment]
    git_config_scopes: dict[str, str] = info["git_config_scopes"]  # type: ignore[assignment]
    unmerged_branches: list[dict[str, str]] = info["unmerged_branches"]  # type: ignore[assignment]
    last_merge: dict[str, str] = info["last_merge_from_default"]  # type: ignore[assignment]
    branch_divergence: dict[str, str] = info["branch_divergence"]  # type: ignore[assignment]
    commit_freq: dict[str, int] = info["commit_frequency"]  # type: ignore[assignment]
    file_changes: dict[str, int] = info["file_change_summary"]  # type: ignore[assignment]
    branch_chars: dict[str, str] = info["branch_characteristics"]  # type: ignore[assignment]

    health_results, failures = _collect_health(spinner_color=spinner_color)

    if output_json:
        payload: dict[str, object] = {
            "version": SCRIPT_VERSION,
            "info": info,
            "startup_commands": {
                "git_status_porcelain": status_cmd_ok,
                "git_rev_parse_git_dir": revparse_cmd_ok,
            },
            "health": health_results,
            "failures": failures,
            "helpful_git_commands": HELPFUL_COMMANDS,
        }
        print(json.dumps(payload, indent=2, default=str))
        return 1 if failures else 0

    use_color = color if color is not None else _supports_color(sys.stdout)
    use_unicode = _supports_unicode(sys.stdout)
    sym = _unicode_symbols(sys.stdout)
    bar_char = "\u2588" if use_unicode else "#"
    bar_left = "\u258c" if use_unicode else "["
    bar_right = "\u2590" if use_unicode else "]"
    dash = sym["dash"]
    c = Colors(enabled=use_color)

    # Box-drawing characters for section headers
    # TODO: Extract box-drawing char initialization, _section(), _kv(), and
    #   _merge_row() into a shared _UIContext dataclass.  Duplicated in 8
    #   functions: run(), apply_from_reference(), apply_recommended_config(),
    #   apply_recommended_minimal_config(), refresh_repo(), cleanup_repo(),
    #   create_new_branch(), _show_commits_terminal().  ~200 lines of
    #   boilerplate could collapse to a single factory call per function.
    #   Tracked in known-issues.md.
    h_line = "\u2500" if use_unicode else "-"  # ─
    h_double = "\u2550" if use_unicode else "="  # ═
    tl = "\u250c" if use_unicode else "+"  # ┌
    tr = "\u2510" if use_unicode else "+"  # ┐
    bl = "\u2514" if use_unicode else "+"  # └
    br = "\u2518" if use_unicode else "+"  # ┘
    tl_d = "\u2554" if use_unicode else "+"  # ╔
    tr_d = "\u2557" if use_unicode else "+"  # ╗
    bl_d = "\u255a" if use_unicode else "+"  # ╚
    br_d = "\u255d" if use_unicode else "+"  # ╝
    vl = "\u2502" if use_unicode else "|"  # │
    vl_d = "\u2551" if use_unicode else "|"  # ║
    dot = "\u2022" if use_unicode else "*"  # •

    def _section(title: str) -> None:
        """Print a section header with colored box-drawing border."""
        border = h_line * 60
        print()
        print(c.cyan(f"  {tl}{border}{tr}"))
        print(f"  {c.cyan(vl)} {c.bold(title)}")
        print(c.cyan(f"  {bl}{border}{br}"))
        print()

    def _kv(label: str, value: str, width: int = 18, hint: str = "") -> None:
        """Print a key-value pair with consistent alignment.

        When *hint* is provided it is rendered on a separate indented
        line below the value in dim text, keeping the main line clean.
        """
        print(f"    {label + ':':{width}s} {value}")
        if hint:
            # Indent hint below, aligned past the label column
            print(f"    {'':{width}s} {c.dim(hint)}")

    # ── Header ──
    header_border = h_double * 60
    check = sym.get("check", "+")
    cross = sym.get("cross", "x")
    warn_sym = sym.get("warn", "!")
    print()
    print(c.bold(c.cyan(f"  {tl_d}{header_border}{tr_d}")))
    print(
        f"  {c.bold(c.cyan(vl_d))} "
        f"{c.bold(c.cyan('Git Doctor'))}  {c.dim(f'v{SCRIPT_VERSION}')}"
    )
    print(c.bold(c.cyan(f"  {bl_d}{header_border}{br_d}")))

    # Quick status bar — three indicators with explicit labels
    clean = not any(working_tree.values())
    sync_ok = "behind" not in upstream_status.lower()
    passed_count = len(health_results) - failures

    wt_icon = c.green(check) if clean else c.yellow(warn_sym)
    wt_label = c.green("clean") if clean else c.yellow("dirty")
    sync_icon = c.green(check) if sync_ok else c.yellow(warn_sym)
    sync_label = c.green("synced") if sync_ok else c.yellow("behind")
    hc_icon = c.green(check) if not failures else c.red(cross)
    hc_label = (
        c.green(f"{passed_count}/{len(health_results)} passed")
        if not failures
        else c.red(f"{failures} failed, {passed_count} passed")
    )

    # Extract branch age and unpushed count for the status bar
    _age_str = branch_chars.get("branch_age", "")
    _unpushed_str = branch_chars.get("unpushed", "")
    _unpushed_count = ""
    if _unpushed_str and "unpushed" in _unpushed_str:
        _unpushed_count = _unpushed_str.split()[0]  # e.g. "4"

    print()
    _status_w = 22  # pad labels to align values vertically
    print(f"  {wt_icon} {c.dim('Working tree:'.ljust(_status_w))} {wt_label}")
    print(
        f"  {sync_icon} {c.dim('Remote sync (origin):'.ljust(_status_w))} {sync_label}"
    )
    print(f"  {hc_icon} {c.dim('Health:'.ljust(_status_w))} {hc_label}")
    if _age_str:
        print(
            f"  {c.dim(dot)} {c.dim('Branch age:'.ljust(_status_w))} {c.dim(_age_str)}"
        )
    if _unpushed_count:
        print(
            f"  {c.yellow(warn_sym)} {c.dim('Unpushed commits:'.ljust(_status_w))} "
            f"{c.yellow(_unpushed_count)}"
        )

    # ── Startup Commands ──
    _section("Startup Commands")
    print(f"    {c.dim('Commands executed automatically to ensure fresh data.')}")
    print()
    print(
        f"    {c.green(check)} = {c.green('passed')}  "
        f"{c.red(cross)} = {c.red('failed')}"
    )
    print()
    cmd_w = 30
    desc_w = 48
    # Table header
    print(
        f"    {c.dim('Command'.ljust(cmd_w))} "
        f"{c.dim('Description'.ljust(desc_w))} "
        f"{c.dim('Status')}"
    )
    print(
        f"    {c.cyan(h_line * cmd_w)} {c.cyan(h_line * desc_w)} {c.cyan(h_line * 6)}"
    )
    # Table rows
    print(
        f"    {c.cyan('git fetch --all --prune'.ljust(cmd_w))} "
        f"{c.dim('sync remote-tracking refs, remove stale branches'.ljust(desc_w))} "
        f"{c.green(check) if fetch_ok else c.red(cross)}"
    )
    print(
        f"    {c.cyan('git status --porcelain'.ljust(cmd_w))} "
        f"{c.dim('check working tree state'.ljust(desc_w))} "
        f"{c.green(check) if status_cmd_ok else c.red(cross)}"
    )
    print(
        f"    {c.cyan('git rev-parse --git-dir'.ljust(cmd_w))} "
        f"{c.dim('verify git repository'.ljust(desc_w))} "
        f"{c.green(check) if revparse_cmd_ok else c.red(cross)}"
    )

    # ── Repository Info ──
    _section("Repository")
    _kv("Remote URL", remote_url, hint="origin remote (fetch/push URL)")
    _kv("Current branch", c.green(current_branch), hint="your active branch (HEAD)")
    _kv(
        "Default branch",
        default_branch,
        hint=f"base branch for PRs (origin/{default_branch})",
    )
    _kv("Upstream", upstream_status, hint="remote tracking status (origin)")
    _kv("User", f"{user_name} <{user_email}>", hint="from git config")
    _kv("Commits", str(commit_count), hint="total repo history")
    _kv("Contributors", str(contributors), hint="unique commit authors")
    _kv("Repo age", repo_age, hint="first commit to now")

    # ── Git Configuration (top 18 — use --export-config for full reference) ──
    if git_config:
        set_count = sum(1 for v in git_config.values() if v != "(unset)")
        unset_count = len(git_config) - set_count
        _section(
            f"Git Configuration  {c.dim(f'({set_count} set, {unset_count} unset)')}"
        )
        print(
            f"    {c.dim('Showing commonly used keys — not every git config.')}"
            f"  {c.dim('Run')} {c.cyan('--export-config')} {c.dim('for full reference.')}"
        )
        print()
        # Column layout — widened to accommodate longer config key names
        key_w = 30
        scope_w = 12
        val_w = 20
        total_w = key_w + scope_w + val_w + 2  # +2 for spaces between columns
        # Column headers
        hdr_key = c.dim("Key".ljust(key_w))
        hdr_scope = c.dim("Scope".ljust(scope_w))
        hdr_val = c.dim("Value")
        print(f"    {hdr_key} {hdr_scope} {hdr_val}")
        print(
            f"    {c.cyan(h_line * key_w)} {c.cyan(h_line * scope_w)} {c.cyan(h_line * val_w)}"
        )
        # Group keys by their logical section for visual separation
        current_group = ""
        for key, val in git_config.items():
            group = _config_section(key)
            if group != current_group:
                if current_group:
                    print()  # blank line between groups
                current_group = group
                # Prominent section header with colored borders
                pad_len = max(total_w - len(group) - 3, 4)
                group_line = f"{h_line * 2} {group} {h_line * pad_len}"
                print(f"    {c.bold(c.cyan(group_line))}")
            scope = git_config_scopes.get(key, "unset")
            scope_str = f"[{scope}]".ljust(scope_w)
            key_padded = key.ljust(key_w)
            # Check if this key has a recommended value and it differs
            rec_value = _RECOMMENDED_LOOKUP.get(key)
            if val == "(unset)":
                hint_str = ""
                if rec_value:
                    hint_str = f"  {c.dim(f'(recommended: {rec_value})')}"
                print(
                    f"    {c.dim(key_padded)} {c.dim(scope_str)} {c.dim(val)}{hint_str}"
                )
            elif rec_value and val != rec_value:
                print(
                    f"    {key_padded} {c.dim(scope_str)} {c.yellow(val)}"
                    f"  {c.dim(f'(recommended: {rec_value})')}"
                )
            else:
                print(f"    {key_padded} {c.dim(scope_str)} {c.cyan(val)}")
        print()
        print(
            f"    {c.dim('Run with')} {c.cyan('--export-config')} {c.dim('for full reference,')}"
            f" {c.cyan('--apply-recommended')} {c.dim('to apply all,')}"
            f" {c.cyan('--apply-recommended-minimal')} {c.dim('for core subset')}"
        )

    # ── Commit Activity — current branch (last 14 days) ──
    if commit_freq:
        _section(f"Commit Activity {dash} {c.green(current_branch)} (last 14 days)")
        print(f"    {c.dim('Daily commit frequency on this branch')}")
        print()
        max_count = max(commit_freq.values()) if commit_freq else 1
        sorted_dates = sorted(commit_freq)
        bar_data: list[tuple[str, int, int]] = []
        for date in sorted_dates:
            count = commit_freq[date]
            bar_len = int((count / max_count) * 30) if max_count > 0 else 0
            bar_data.append((date, count, bar_len))
        for idx, (date, count, bar_len) in enumerate(bar_data):
            inner = bar_char * bar_len if bar_len > 0 else ""
            bar = (
                c.green(f"{bar_left}{inner}{bar_right}")
                if bar_len > 0
                else c.dim(bar_left + bar_right)
            )
            print(f"    {date}  {bar} {count}")
            # Blank line between bars for visual separation (skip after last)
            if idx < len(bar_data) - 1:
                print()
        total_recent = sum(commit_freq.values())
        avg = total_recent / len(commit_freq) if commit_freq else 0
        print()
        print(f"    {c.dim(f'Total: {total_recent} commits, avg {avg:.1f}/day')}")

    # ── Top 5 Contributors ──
    if top_contributors:
        _section("Top Contributors (by commit count)")
        print(f"    {c.dim('All-time commit counts excluding merge commits')}")
        print()
        max_contrib = max(int(e["commits"]) for e in top_contributors)
        # Determine name column width from longest contributor name
        name_w = max(len(str(e["name"])) for e in top_contributors)
        name_w = min(max(name_w, 10), 30)
        for idx, entry in enumerate(top_contributors):
            name = str(entry["name"])
            commits = int(entry["commits"])  # type: ignore[arg-type]
            bar_len = int((commits / max_contrib) * 30) if max_contrib > 0 else 0
            inner = bar_char * bar_len if bar_len > 0 else ""
            bar = (
                c.green(f"{bar_left}{inner}{bar_right}")
                if bar_len > 0
                else c.dim(bar_left + bar_right)
            )
            display_name = (
                name[: name_w - 1] + sym["ellip"] if len(name) > name_w else name
            )
            print(f"    {display_name:{name_w}s}  {bar} {commits}")
            # Blank line between bars for visual separation (skip after last)
            if idx < len(top_contributors) - 1:
                print()
        total_all = sum(int(e["commits"]) for e in top_contributors)  # type: ignore[arg-type]
        print()
        print(
            f"    {c.dim(f'Total from top {len(top_contributors)}: {total_all} commits')}"
        )

    # ── File Change Summary — current branch (last 5 commits) ──
    if file_changes and any(file_changes.values()):
        _section(
            f"Recent File Changes {dash} {c.green(current_branch)} (last 5 commits)"
        )
        print(
            f"    {c.dim('Diff of HEAD~5..HEAD — only the last 5 commits on this branch')}"
        )
        print()
        fc = file_changes
        ins = fc.get("insertions", 0)
        dels = fc.get("deletions", 0)
        files = fc.get("files_changed", 0)
        _kv("Files changed", str(files), hint="unique files touched")
        _kv("Insertions", c.green(f"+{ins}"), hint="lines added")
        _kv("Deletions", c.red(f"-{dels}"), hint="lines removed")

    # ── Repo Branch Activity (top 5 most recent) ──
    if branch_activity:
        _section("Repo Branch Activity (top 5 most recent)")
        print(
            f"    {c.dim('Total diff of each branch vs merge-base with default branch')}"
        )
        print()
        # Dynamic column width based on longest branch name (cap at 50)
        max_name = max((len(str(e["base_name"])) for e in branch_activity), default=20)
        name_w = min(max(max_name, 10), 50)
        # Header
        hdr_b = c.dim("Branch".ljust(name_w))
        hdr_s = c.dim("Source".ljust(8))
        hdr_d = c.dim("Last Commit".ljust(16))
        hdr_c = c.dim("Commits".rjust(8))
        hdr_f = c.dim("Files".rjust(6))
        hdr_i = c.dim("+Ins".rjust(7))
        hdr_dl = c.dim("-Del".rjust(7))
        print(f"    {hdr_b} {hdr_s} {hdr_d} {hdr_c} {hdr_f} {hdr_i} {hdr_dl}")
        for entry in branch_activity:
            bname = str(entry["base_name"])
            src = str(entry["source"])
            bdate = str(entry["date"])
            bcommits = int(entry.get("commits", 0))  # type: ignore[arg-type]
            bf = int(entry.get("files_changed", 0))  # type: ignore[arg-type]
            bi = int(entry.get("insertions", 0))  # type: ignore[arg-type]
            bd = int(entry.get("deletions", 0))  # type: ignore[arg-type]
            # Truncate long names with ellipsis
            display_name = (
                bname[: name_w - 1] + sym["ellip"] if len(bname) > name_w else bname
            )
            name_padded = display_name.ljust(name_w)
            name_display = (
                c.green(name_padded) if bname == current_branch else name_padded
            )
            ins_s = c.green(f"+{bi}".rjust(7)) if bi else str(bi).rjust(7)
            del_s = c.red(f"-{bd}".rjust(7)) if bd else str(bd).rjust(7)
            print(
                f"    {name_display} {src:8s} {bdate:16s}"
                f" {bcommits:>8d} {bf:>6d} {ins_s} {del_s}"
            )

    # ── Current Working Branch ──
    _section(f"Current Working Branch: {c.green(current_branch)}")
    # Show branch-specific commit count when on a feature branch
    if current_branch != default_branch and default_branch != "(unknown)":
        branch_commits = get_branch_unique_commit_count(current_branch, default_branch)
        _kv(
            "Branch commits",
            f"{branch_commits}  {c.dim(f'(repo total: {commit_count})')}",
            hint="commits unique to this branch",
        )
    else:
        _kv("Total commits", str(commit_count))
    vd = wb_stats.get("vs_default", {})
    st = wb_stats.get("staged", {})
    us = wb_stats.get("unstaged", {})
    vd_f, vd_i, vd_d = (
        vd.get("files_changed", 0),
        vd.get("insertions", 0),
        vd.get("deletions", 0),
    )
    st_f, st_i, st_d = (
        st.get("files_changed", 0),
        st.get("insertions", 0),
        st.get("deletions", 0),
    )
    us_f, us_i, us_d = (
        us.get("files_changed", 0),
        us.get("insertions", 0),
        us.get("deletions", 0),
    )
    if vd_f or vd_i or vd_d:
        _kv(
            f"vs {default_branch}",
            f"{vd_f} files changed, "
            f"{c.green(f'+{vd_i}')} insertions, {c.red(f'-{vd_d}')} deletions",
            hint="total diff from default branch",
        )
    else:
        _kv(
            f"vs {default_branch}",
            c.yellow("no divergence"),
            hint="total diff from default branch",
        )
    if st_f or st_i or st_d:
        _kv(
            "Staged",
            f"{st_f} files changed, "
            f"{c.green(f'+{st_i}')} insertions, {c.red(f'-{st_d}')} deletions",
            hint="changes in index (git add)",
        )
    else:
        _kv("Staged", c.yellow("nothing staged"), hint="changes in index (git add)")
    if us_f or us_i or us_d:
        _kv(
            "Unstaged",
            f"{us_f} files changed, "
            f"{c.green(f'+{us_i}')} insertions, {c.red(f'-{us_d}')} deletions",
            hint="modified but not yet staged",
        )
    else:
        _kv("Unstaged", c.yellow("clean"), hint="modified but not yet staged")

    # ── Branch Characteristics ──
    if branch_chars:
        _section(f"Branch Characteristics: {c.green(current_branch)}")
        # Ordered characteristics with semantic coloring and descriptor hints
        char_keys: list[tuple[str, str, str]] = [
            (
                "Default branch",
                "behind_default",
                "commits on default not on this branch",
            ),
            ("Ahead of default", "ahead_default", "commits unique to this branch"),
            (
                "Head position",
                "on_default_head",
                "branch tip vs default tip (can be ahead and up-to-date)",
            ),
            ("Activity", "stale", "time since last commit on this branch"),
            ("Commit density", "commit_density", "recent commit frequency"),
            ("Branch age", "branch_age", "when branch first diverged from default"),
            ("Merge status", "fast_forwardable", "can branch merge without conflicts"),
            ("Remote", "local_only", "whether branch is pushed to remote (origin)"),
            ("Unpushed", "unpushed", "local commits not yet on remote (origin)"),
        ]
        # Keywords that indicate good/warning/info states
        _good = (
            "up to date",
            "active",
            "tracked",
            "fast-forwardable",
            "all commits pushed",
            "contained",
            "ahead of",
        )
        _warn = (
            "stale",
            "behind",
            "requires",
            "aging",
            "unpushed",
            "no commits",
            "local only",
        )
        for label, key, hint_text in char_keys:
            val = branch_chars.get(key, "")
            if not val:
                continue
            if any(w in val for w in _warn):
                _kv(label, c.yellow(val), hint=hint_text)
            elif any(w in val for w in _good):
                _kv(label, c.green(val), hint=hint_text)
            else:
                _kv(label, c.cyan(val), hint=hint_text)
        if "conflicts" in branch_chars:
            _kv(
                "Conflicts",
                c.red(branch_chars["conflicts"]),
                hint="unresolved merge conflicts",
            )

    # ── Last Merge from Default Branch (table format) ──
    if last_merge and current_branch != default_branch:
        _section(f"Last Merge from {default_branch}")
        sha_short = last_merge.get("sha_short", "?")
        msg = last_merge.get("message", "")
        rel_date = last_merge.get("relative_date", "")
        author = last_merge.get("author", "")
        default_ahead = last_merge.get("default_ahead", "0")
        current_ahead = last_merge.get("current_ahead", "0")

        # Build table rows: (Label, Value, Time/Detail)
        lbl_w = 18
        val_w = 52
        time_w = 18
        hdr_lbl = c.dim("Property".ljust(lbl_w))
        hdr_val = c.dim("Value".ljust(val_w))
        hdr_time = c.dim("When")
        print(f"    {hdr_lbl} {hdr_val} {hdr_time}")
        print(
            f"    {c.dim(h_line * lbl_w)} {c.dim(h_line * val_w)}"
            f" {c.dim(h_line * time_w)}"
        )

        def _merge_row(
            label: str,
            val_plain: str,
            color_fn: Callable[[str], str],
            when: str = "",
        ) -> None:
            """Print a merge-table row with ANSI-safe column alignment."""
            # Truncate value to fit column, then pad plain text before coloring
            if len(val_plain) > val_w:
                val_plain = val_plain[: val_w - 1] + "\u2026"
            padded = val_plain.ljust(val_w)
            colored = color_fn(padded)
            when_str = f" {c.dim(when)}" if when else ""
            print(f"    {label.ljust(lbl_w)} {colored}{when_str}")

        # Merge base row — truncate long commit messages to fit
        merge_plain = f"{sha_short} {msg}"
        _merge_row("Merge base", merge_plain, c.yellow, rel_date)
        print(f"    {'':{lbl_w}s} {c.dim('last common ancestor with default')}")
        if author:
            print()
            print(f"    {'Author'.ljust(lbl_w)} {author}")
            print(f"    {'':{lbl_w}s} {c.dim('commit author of merge base')}")
        if default_ahead != "0":
            print()
            ahead_plain = f"{default_ahead} commit(s) ahead of merge base"
            _merge_row(default_branch + " ahead", ahead_plain, c.yellow)
            print(
                f"    {'':{lbl_w}s} {c.dim('new work on default since you branched')}"
            )
        if current_ahead != "0":
            print()
            br_plain = f"{current_ahead} commit(s) ahead of merge base"
            _merge_row("Branch ahead", br_plain, c.cyan)
            print(f"    {'':{lbl_w}s} {c.dim('your unique work since branching')}")
        if branch_divergence:
            print()
            div_sha = branch_divergence.get("sha", "")
            div_msg = branch_divergence.get("message", "")
            div_date = branch_divergence.get("date", "")
            div_plain = f"{div_sha} {div_msg}"
            _merge_row("Branch started", div_plain, c.yellow, div_date)
            print(f"    {'':{lbl_w}s} {c.dim('first commit on this branch')}")

    # ── Working Tree ──
    if any(working_tree.values()) or modified_files:
        _section("Working Tree")
        for key, count in working_tree.items():
            if count > 0:
                color_fn = c.yellow if key != "conflicted" else c.red
                _kv(key.capitalize(), color_fn(str(count)), width=14)
        if modified_files:
            print()
            status_colors = {
                "modified": c.yellow,
                "added": c.green,
                "added (staged)": c.green,
                "modified (staged)": c.green,
                "deleted": c.red,
                "deleted (staged)": c.red,
                "untracked": c.cyan,
                "conflicted": c.red,
                "renamed": c.cyan,
                "renamed (staged)": c.cyan,
            }
            for mf in modified_files:
                color_fn = status_colors.get(mf["status"], c.cyan)
                print(f"    {color_fn(mf['status'].ljust(18))} {mf['file']}")
            total_mf = len(modified_files)
            code_mf, out_mf, _ = _run_git(["status", "--porcelain"])
            real_total = (
                len(out_mf.splitlines()) if code_mf == 0 and out_mf else total_mf
            )
            if real_total > total_mf:
                print(f"    {c.dim(f'... and {real_total - total_mf} more')}")
    else:
        print(f"\n    {c.green('Working directory is clean')}")

    # ── Local Branches ──
    if local_branches:
        _section("Local Branches")
        # Compute column widths from data
        name_w = max(len(b["name"]) for b in local_branches)
        name_w = max(name_w, 6) + 2  # min "Branch" + padding
        track_w = max((len(b.get("tracking", "")) for b in local_branches), default=8)
        track_w = max(track_w, 8) + 2  # min "Tracking" + padding
        status_w = max((len(b.get("status", "")) for b in local_branches), default=6)
        status_w = max(status_w, 6) + 2  # min "Status" + padding
        last_w = 16  # "Last Commit" column

        # Column headers
        hdr_branch = c.dim("Branch".ljust(name_w))
        hdr_track = c.dim("Tracking".ljust(track_w))
        hdr_status = c.dim("Status".ljust(status_w))
        hdr_last = c.dim("Last Commit")
        print(f"    {hdr_branch} {hdr_track} {hdr_status} {hdr_last}")
        print(
            f"    {c.dim(h_line * name_w)} {c.dim(h_line * track_w)} "
            f"{c.dim(h_line * status_w)} {c.dim(h_line * last_w)}"
        )

        for b in local_branches:
            is_current = b["name"] == current_branch
            marker = "* " if is_current else "  "
            bname = b["name"]
            name_str = c.green(bname) if is_current else bname
            tracking = b.get("tracking", "")
            bstatus = b.get("status", "")
            last = b.get("last_commit", "")

            # Pad name with raw text width (before color codes)
            name_pad = " " * max(0, name_w - len(bname))
            track_str = (
                tracking.ljust(track_w) if tracking else c.dim("(none)".ljust(track_w))
            )
            status_str = (
                bstatus.ljust(status_w) if bstatus else c.dim(dash.ljust(status_w))
            )
            # Color-code age: green (<7d), yellow (7-30d), red (>30d)
            if last:
                last_lower = last.lower()
                if any(x in last_lower for x in ("month", "year", "weeks")):
                    last_str = c.red(last)
                elif "week" in last_lower or (
                    "day" in last_lower
                    and not any(last_lower.startswith(f"{n} day") for n in range(1, 8))
                ):
                    last_str = c.yellow(last)
                else:
                    last_str = c.green(last)
            else:
                last_str = ""

            print(f"  {marker}{name_str}{name_pad} {track_str} {status_str} {last_str}")

    # ── Stale Branches ──
    if stale_branches:
        _section("Stale Branches (no activity > 30 days)")
        sb_name_w = max(len(sb["name"]) for sb in stale_branches)
        sb_name_w = max(sb_name_w, 6) + 2
        print(f"    {c.dim('Branch'.ljust(sb_name_w))} {c.dim('Last Activity')}")
        print(f"    {c.dim(h_line * sb_name_w)} {c.dim(h_line * 20)}")
        for sb in stale_branches:
            print(
                f"    {c.yellow(sb['name'].ljust(sb_name_w))} "
                f"{c.red(sb['last_commit'])}"
            )

    # ── Unmerged Branches ──
    if unmerged_branches:
        _section(f"Unmerged Branches (not in {default_branch})")
        ub_name_w = max(len(ub["name"]) for ub in unmerged_branches)
        ub_name_w = max(ub_name_w, 6) + 2
        print(f"    {c.dim('Branch'.ljust(ub_name_w))} {c.dim('Note')}")
        print(f"    {c.dim(h_line * ub_name_w)} {c.dim(h_line * 20)}")
        for ub in unmerged_branches:
            name = ub["name"]
            note = ub.get("note", "")
            note_str = c.dim(note) if note else c.dim(dash)
            print(f"    {name.ljust(ub_name_w)} {note_str}")

    # ── Recent Tags ──
    if tags:
        _section("Recent Tags")
        for tag in tags:
            print(f"    {tag}")

    # ── Recent Commits ──
    if recent_commits:
        _section(f"Recent Commits {dash} {c.green(current_branch)}")
        sha_w = 8
        msg_w = max(
            (len(cm["message"]) for cm in recent_commits),
            default=40,
        )
        msg_w = min(msg_w, 50) + 2  # cap at 50 chars
        author_w = max(
            (len(cm.get("author", "")) for cm in recent_commits),
            default=10,
        )
        author_w = min(author_w, 20) + 2
        print(
            f"    {c.dim('SHA'.ljust(sha_w))} "
            f"{c.dim('Message'.ljust(msg_w))} "
            f"{c.dim('Author'.ljust(author_w))} "
            f"{c.dim('When')}"
        )
        print(
            f"    {c.dim(h_line * sha_w)} "
            f"{c.dim(h_line * msg_w)} "
            f"{c.dim(h_line * author_w)} "
            f"{c.dim(h_line * 16)}"
        )
        for commit in recent_commits:
            sha = c.yellow(commit["sha"])
            msg = commit["message"]
            if len(msg) > 50:
                msg = msg[:47] + "..."
            author = commit.get("author", "")
            if len(author) > 20:
                author = author[:17] + "..."
            cdate = commit.get("date", "")
            # Pad raw text before color codes
            msg_pad = msg.ljust(msg_w)
            author_pad = author.ljust(author_w)
            print(f"    {sha} {msg_pad} {c.dim(author_pad)} {c.dim(cdate)}")

    # ── Stashes ──
    _stash_count_colored = (
        c.yellow(str(stash_count)) if stash_count > 0 else c.green(str(stash_count))
    )
    _section(f"Stashes  ({_stash_count_colored})")
    if stash_count > 0:
        print(
            f"    {c.yellow(str(stash_count))} stash(es) saved  {c.dim('shelved changes via')} {c.cyan('git stash')}"
        )
    else:
        print(f"    {c.green('0')} stashes  {c.dim('no shelved changes')}")
    print()
    print(
        f"    {c.dim('A stash is a snapshot of uncommitted changes saved locally via')}"
    )
    print(
        f"    {c.cyan('git stash')}{c.dim('. Forgotten stashes may contain important work-in-progress.')}"
    )
    print(
        f"    {c.dim('Run')} {c.cyan('git stash list')} {c.dim('to review,')} {c.cyan('git stash pop')} {c.dim('to restore.')}"
    )

    # ── Release Branch ──
    _section("Release Branch")
    print(
        f"    {c.dim('Automated release branches managed by the configured release system.')}"
    )

    print(f"    {c.cyan(h_line * 56)}")

    # Show detected release system status
    detected_name = release_system.get("name") if release_system else None
    if detected_name:
        print(
            f"    {c.bold(c.cyan('Status:'))}   {c.green(f'{detected_name} detected')}"
        )
        print()
        config_found = release_system.get("config_found", [])
        if config_found:
            print(f"    {c.bold(c.cyan('Config:'))}   {', '.join(config_found)}")
            print()
        wf_files = release_system.get("workflow_files", [])
        if release_system.get("workflow_found"):
            if wf_files:
                print(
                    f"    {c.bold(c.cyan('Workflow:'))} {', '.join(c.cyan(f) for f in wf_files)}"
                )
            else:
                print(f"    {c.bold(c.cyan('Workflow:'))} matching workflow file found")
            print()
    else:
        print(
            f"    {c.bold(c.cyan('Status:'))}   {c.yellow('No release automation detected')}"
        )
        print()
        print(
            f"    {c.dim('No known release system config found')}"
            f" {c.dim('(release-please, semantic-release, changesets, standard-version, commitizen)')}"
        )
        print()

    # Show release branches (from the release system or fallback to rp_branches)
    display_branches = release_system.get("branches", []) if release_system else []
    if not display_branches:
        display_branches = rp_branches
    if display_branches:
        print(f"    {c.bold(c.cyan('Branches:'))}")
        for branch in display_branches:
            print(f"      {c.cyan(dot)} {c.cyan(branch)}")
    elif detected_name:
        print(f"    {c.yellow('No active release branches (normal between releases)')}")

    # ── Health Checks ──
    _section("Health Checks")
    check_sym = sym.get("check", "")
    cross_sym = sym.get("cross", "")
    hc_name_w = (
        max((len(r["name"]) for r in health_results), default=0) + 1
    )  # +1 for colon
    for r in health_results:
        if r["status"] == "PASS":
            icon = (
                c.green(check_sym)
                if use_unicode
                else _icon(r["status"], use_color=use_color)
            )
        else:
            icon = (
                c.red(cross_sym)
                if use_unicode
                else _icon(r["status"], use_color=use_color)
            )
        label = (r["name"] + ":").ljust(hc_name_w)
        print(f"    {icon} {c.dim(label)} {r['message']}")

    # ── Helpful Git Commands ──
    _section("Helpful Git Commands")
    for cmd_info in HELPFUL_COMMANDS:
        print(f"    {c.cyan(cmd_info['cmd'])}")
        print(f"      {c.dim(cmd_info['desc'])}")

    # ── Recommended Scripts ──
    _ui = UI(
        title="Git Doctor", version=SCRIPT_VERSION, theme=THEME, no_color=not use_color
    )
    _ui.recommended_scripts(
        [
            "repo_sauron",
            "env_inspect",
            "check_python_support",
            "repo_doctor",
            "dep_versions",
            "env_doctor",
            "doctor",
            "workflow_versions",
        ],
        preamble="Scripts that expand on repository health and diagnostics.",
    )

    # ── Summary ──
    elapsed = time.monotonic() - elapsed_start
    total = len(health_results)
    passed = total - failures
    print()
    print(c.cyan(f"  {h_double * 60}"))
    if failures == 0:
        sym_str = c.green(check_sym) if use_unicode else c.green("OK")
        print(f"  {sym_str} {c.green(f'All {total} health checks passed')}")
    else:
        sym_str = c.red(cross_sym) if use_unicode else c.red("!!")
        print(
            f"  {sym_str} {c.red(f'{failures} issue(s) found')}  "
            f"{c.dim(f'({passed}/{total} passed)')}"
        )
    print(
        f"  {c.dim(f'Completed in {elapsed:.1f}s  {dot}  git-doctor v{SCRIPT_VERSION}')}"
    )
    print(c.cyan(f"  {h_double * 60}"))
    print()

    return 1 if failures else 0


# ---------------------------------------------------------------------------
# Config export
# ---------------------------------------------------------------------------


def _aligned_md_table(
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    col_aligns: str = "",
) -> list[str]:
    """Return aligned Markdown table lines.

    Each column is padded to the width of the widest cell in that column.
    ``col_aligns`` is one char per column: ``'l'`` left (default), ``'r'``
    right.  Missing positions default to ``'l'``.
    """
    ncols = len(headers)
    w = [len(h) for h in headers]
    for row in rows:
        for i in range(ncols):
            w[i] = max(w[i], len(row[i]))

    def _fmt(cells: Sequence[str]) -> str:
        parts: list[str] = []
        for i in range(ncols):
            a = col_aligns[i] if i < len(col_aligns) else "l"
            cell = cells[i] if i < len(cells) else ""
            if a == "r":
                parts.append(f"{cell:>{w[i]}}")
            else:
                parts.append(f"{cell:<{w[i]}}")
        return "| " + " | ".join(parts) + " |"

    seps: list[str] = []
    for i in range(ncols):
        a = col_aligns[i] if i < len(col_aligns) else "l"
        dashes = "-" * (w[i] - 1) if w[i] > 1 else "-"
        if a == "r":
            seps.append(dashes + ":")
        else:
            seps.append(":" + dashes)
    sep_line = "| " + " | ".join(seps) + " |"

    out = [_fmt(headers), sep_line]
    out.extend(_fmt(row) for row in rows)
    return out


def export_git_config_reference(filepath: str) -> str:
    """Write a comprehensive git configuration reference to a Markdown file.

    Args:
        filepath: Output file path.

    Returns:
        The absolute path of the written file.
    """
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Build table of contents from catalog sections
    seen_sections: list[str] = []
    for key, _, _, _ in GIT_CONFIG_CATALOG:
        section = _config_section(key)
        if section not in seen_sections:
            seen_sections.append(section)

    # Count config keys per section for the summary table
    section_counts: dict[str, int] = {}
    for key, _, _, _ in GIT_CONFIG_CATALOG:
        section = _config_section(key)
        section_counts[section] = section_counts.get(section, 0) + 1

    toc_rows: list[list[str]] = []
    for s in seen_sections:
        anchor = s.lower().replace(" & ", "--").replace(" ", "-")
        count = section_counts.get(s, 0)
        desc = SECTION_DESCRIPTIONS.get(s, "")
        toc_rows.append([f"[{s}](#{anchor})", str(count), desc])
    toc_rows.extend(
        [
            [
                "[Glossary](#glossary)",
                "\u2014",
                "Definitions of common git config terminology.",
            ],
            [
                "[Customizing This Reference](#customizing-this-reference)",
                "\u2014",
                "How to add or remove config entries.",
            ],
            [
                "[.gitattributes Reference](#gitattributes-reference)",
                "\u2014",
                "Per-path repo settings (line endings, binary, diff drivers).",
            ],
        ]
    )

    total_keys = len(GIT_CONFIG_CATALOG)

    lines: list[str] = [
        "# Git Configuration Reference",
        "",
        "<!-- Auto-generated by git_doctor.py — do not edit by hand. -->",
        "",
        *_aligned_md_table(
            ["**Generated by**", f"`git_doctor.py` v{SCRIPT_VERSION}"],
            [
                ["**Timestamp**", timestamp],
                [
                    "**Catalog updated**",
                    f"{CATALOG_LAST_UPDATED} (when config entries were last reviewed)",
                ],
                ["**Command**", "`python scripts/git_doctor.py --export-config`"],
                [
                    "**Regenerate**",
                    "Run the command above to refresh with current settings",
                ],
                [
                    "**Total keys**",
                    f"{total_keys} commonly used keys across {len(seen_sections)} sections",
                ],
            ],
        ),
        "",
        "## How This File Works",
        "",
        "This file is a generated reference of commonly used git config keys.",
        "Each entry has a table with **Current value**, **Desired value**,",
        "**Current scope**, **Desired scope**, **Valid values**, and **Valid scopes**",
        "columns. To change a setting:",
        "",
        "1. Set **both** `Desired value` **and** `Desired scope` in the entry's table.",
        "2. Use `--dry-run` to preview what would change:",
        "   `python scripts/git_doctor.py --apply-from git-config-reference.md --dry-run`",
        "3. Apply your changes:",
        "   `python scripts/git_doctor.py --apply-from git-config-reference.md`",
        "",
        "> **Important:** Both columns must be set for an entry to be applied.",
        "> If only one is filled in, the entry is skipped with an error.",
        "> Complete entries in other sections are still applied.",
        "",
        "### Applying All Recommended Values at Once",
        "",
        "If you want to set every config key to the catalog's recommended",
        "value and scope (overwriting any existing values):",
        "",
        "```bash",
        "python scripts/git_doctor.py --apply-recommended --dry-run   # preview",
        "python scripts/git_doctor.py --apply-recommended              # apply",
        "```",
        "",
        "> **Warning:** `--apply-recommended` overwrites existing values.",
        "> It resets your config to the catalog baseline. For per-key",
        "> control, edit this file and use `--apply-from` instead.",
        "",
        "### Applying Only the Core Minimal Set",
        "",
        f"If you want a safer, lighter-touch setup with just {len(MINIMAL_RECOMMENDED_CONFIGS)} high-impact",
        "keys (e.g. `pull.rebase`, `fetch.prune`, `rerere.enabled`):",
        "",
        "```bash",
        "python scripts/git_doctor.py --apply-recommended-minimal --dry-run   # preview",
        "python scripts/git_doctor.py --apply-recommended-minimal              # apply",
        "```",
        "",
        "> **Tip:** `--apply-recommended-minimal` is ideal for first-time setup.",
        "> Use `--apply-recommended` later to adopt the full catalog baseline.",
        "",
        "---",
        "",
        "> **Note:** This reference covers commonly used git configuration",
        "> options — it is not an exhaustive list. Git has 500+ configuration",
        "> keys; this file curates the ones most relevant to day-to-day",
        "> development workflows. See the [Glossary](#glossary) at the end",
        "> for definitions of common git config terminology, and",
        "> [Customizing This Reference](#customizing-this-reference) for how",
        "> to add or remove config entries.",
        "",
        "---",
        "",
        "## Contents",
        "",
        *_aligned_md_table(
            ["Section", "Keys", "Description"],
            toc_rows,
            col_aligns="lrl",
        ),
        "",
        "---",
        "",
        "## Scope Guide",
        "",
        *_aligned_md_table(
            ["Scope", "File Location", "Applies To"],
            [
                [
                    "**local**",
                    "`.git/config` in the repository",
                    "This repository only",
                ],
                [
                    "**global**",
                    "`~/.gitconfig` or `~/.config/git/config`",
                    "All your repositories",
                ],
                [
                    "**system**",
                    "`/etc/gitconfig` (Linux/macOS) or `C:\\Program Files\\Git\\etc\\gitconfig` (Windows)",
                    "All users on machine",
                ],
            ],
        ),
        "",
        "**Precedence:** local > global > system.",
        "",
        "Set most configs at **global** scope so they apply everywhere,",
        "then override at **local** scope for project-specific needs",
        "(e.g. different email for work repos, project-specific commit template).",
        "",
        "> **How `--apply-from` works:** When you edit this file and run",
        "> `--apply-from`, **both** the Desired value and Desired scope columns",
        "> must be set for an entry to apply. If only one is filled in, the",
        "> entry is skipped with an error message. Complete entries in other",
        "> sections are still applied normally.",
        "",
        "### Updating Config Values",
        "",
        "```bash",
        "# Read a value (shows effective value from highest-priority scope)",
        "git config <key>",
        "",
        "# Read with origin (shows which file defines the value)",
        "git config --show-origin <key>",
        "",
        "# Set at different scopes",
        "git config --global <key> <value>    # ~/.gitconfig",
        "git config --local <key> <value>     # .git/config (this repo only)",
        "git config --system <key> <value>    # system-wide (requires admin)",
        "",
        "# Remove a value",
        "git config --global --unset <key>",
        "",
        "# List all settings with their scopes",
        "git config --list --show-origin",
        "```",
        "",
        "### Further Reading",
        "",
        *_aligned_md_table(
            ["Resource", "Link"],
            [
                [
                    "**Official git-config docs**",
                    "<https://git-scm.com/docs/git-config>",
                ],
                [
                    "**All git config variables**",
                    "<https://git-scm.com/docs/git-config#_variables>",
                ],
                [
                    "**Pro Git book (customization)**",
                    "<https://git-scm.com/book/en/v2/Customizing-Git-Git-Configuration>",
                ],
                ["**Git attributes**", "<https://git-scm.com/docs/gitattributes>"],
                [
                    "**Conditional includes**",
                    "<https://git-scm.com/docs/git-config#_conditional_includes>",
                ],
            ],
        ),
        "",
    ]

    current_section = ""
    for key, rec_scope, description, recommendation in GIT_CONFIG_CATALOG:
        section = _config_section(key)
        if section != current_section:
            if current_section:
                lines.append("---")
                lines.append("")
            current_section = section
            lines.append(f"## {section}")
            lines.append("")
            sect_desc = SECTION_DESCRIPTIONS.get(section, "")
            if sect_desc:
                lines.append(f"*{sect_desc}*")
                lines.append("")

        value = get_git_config_value(key) or "(unset)"
        scope = get_git_config_scope(key)

        lines.append(f"### `{key}`")
        lines.append("")
        lines.append(f"{description}")
        lines.append("")
        beginner_note = CONFIG_BEGINNER_NOTES.get(key)
        if beginner_note:
            lines.append(f"> **What this does:** {beginner_note}")
            lines.append("")
        valid_vals = CONFIG_VALID_VALUES.get(key, "_(freeform)_")

        lines.extend(
            _aligned_md_table(
                ["Property", "Value"],
                [
                    ["**Current value**", f"`{value}`"],
                    ["**Current scope**", scope],
                    ["**Valid values**", valid_vals],
                    ["**Valid scopes**", "`local`, `global`, `system`"],
                    ["**Recommended value**", recommendation],
                    ["**Recommended scope**", rec_scope],
                    ["**Desired value**", "_(no change)_"],
                    ["**Desired scope**", "_(no change)_"],
                ],
            )
        )
        lines.append("")

    # ── Glossary ──
    glossary_rows = [
        [
            "**scope**",
            "Where a config value is stored: `local` (this repo), `global` (all your repos), or `system` (all users). Local overrides global, global overrides system.",
        ],
        [
            "**local**",
            "Config stored in `.git/config` — applies to this repository only. Best for project-specific settings (e.g. commit template, email for work repos).",
        ],
        [
            "**global**",
            "Config stored in `~/.gitconfig` — applies to all your repositories. Best for personal preferences (e.g. editor, signing, aliases).",
        ],
        [
            "**system**",
            "Config stored in `/etc/gitconfig` (Linux/macOS) or `C:\\\\Program Files\\\\Git\\\\etc\\\\gitconfig` (Windows). Requires admin access. Rarely needed.",
        ],
        [
            "**unset**",
            "The key has no value at any scope. Git uses its built-in default.",
        ],
        [
            "**override**",
            "When the same key is set at multiple scopes, the most specific scope wins: local > global > system.",
        ],
        [
            "**(no change)**",
            'Placeholder in the Desired columns meaning "leave as-is." Replace with a value to apply a change.',
        ],
        [
            "**recommended**",
            "The opinionated default suggested by this catalog. Not mandatory — adjust to your workflow.",
        ],
        [
            "**LF / CRLF**",
            "Line ending styles: LF (`\\\\n`, Linux/macOS) vs CRLF (`\\\\r\\\\n`, Windows). See `core.autocrlf` and `core.eol`.",
        ],
        [
            "**fast-forward**",
            "A merge where the branch pointer simply moves forward (no merge commit). Controlled by `pull.ff` and `merge.ff`.",
        ],
        [
            "**rebase**",
            "Replaying commits on top of another branch instead of merging. See `pull.rebase`, `rebase.autostash`.",
        ],
        [
            "**rerere**",
            "REuse REcorded Resolution — git remembers how you resolved a conflict and auto-applies it next time. See `rerere.enabled`.",
        ],
        [
            "**GPG / SSH signing**",
            'Cryptographic signatures on commits/tags. GitHub shows a "Verified" badge. See `commit.gpgsign`, `gpg.format`.',
        ],
        [
            "**delta**",
            "A popular terminal diff viewer with syntax highlighting. Used as `core.pager` or `diff.tool`. See <https://github.com/dandavison/delta>.",
        ],
        [
            "**fsck**",
            "File System Check — integrity verification of git objects. See `fetch.fsckobjects`, `transfer.fsckobjects`.",
        ],
        [
            "**refspec**",
            "A mapping between remote and local refs (e.g. `+refs/heads/*:refs/remotes/origin/*`). Controls what `fetch` and `push` transfer.",
        ],
    ]
    lines.extend(
        [
            "---",
            "",
            "## Glossary",
            "",
            "Quick reference for git configuration terminology used in this file.",
            "",
            *_aligned_md_table(["Term", "Meaning"], glossary_rows),
            "",
            "---",
            "",
            "## Customizing This Reference",
            "",
            "This reference is generated from the `GIT_CONFIG_CATALOG` list in",
            "`scripts/git_doctor.py`. To add or remove config entries:",
            "",
            "### Adding a New Config Entry",
            "",
            "1. Add a tuple to `GIT_CONFIG_CATALOG` in the appropriate section:",
            "",
            "   ```python",
            '   ("section.key", "recommended_scope", "Description of what it does", "recommended value"),',
            "   ```",
            "",
            "2. Add a valid-values entry to `CONFIG_VALID_VALUES`:",
            "",
            "   ```python",
            '   "section.key": "`value1`, `value2`, `value3`",',
            "   ```",
            "",
            "3. If the key belongs to a new section, add it to `CONFIG_SECTION_MAP`",
            "   and `SECTION_DESCRIPTIONS`.",
            "",
            "4. Regenerate this file:",
            "",
            "   ```bash",
            "   python scripts/git_doctor.py --export-config",
            "   ```",
            "",
            "### Removing a Config Entry",
            "",
            "1. Delete the tuple from `GIT_CONFIG_CATALOG`.",
            "2. Delete the key from `CONFIG_VALID_VALUES` (if present).",
            "3. Regenerate this file.",
            "",
            "### Notes",
            "",
            "- The `--apply-recommended` flag iterates `GIT_CONFIG_CATALOG`.",
            "  Adding or removing entries there changes what gets applied.",
            "- Entries with recommendation text that starts with common skip",
            '  patterns (e.g. "e.g.", "Leave unset", "Your", "Set if",',
            '  "Auto-detected", "Default is", "Keep", "Increase") are skipped',
            "  by `--apply-recommended` because they lack a concrete default.",
            "- Git occasionally adds or deprecates config keys across versions.",
            "  Run `git config --list --show-origin` to see what your version supports.",
            "",
            "### Implementation Note",
            "",
            "`GIT_CONFIG_CATALOG` is a list of 4-tuples and `CONFIG_VALID_VALUES`",
            "is a separate dict. If a key is in the catalog but not in the dict,",
            "the export shows _(freeform)_. Currently all 62 keys are covered —",
            "keep them in sync when adding new ones.",
            "",
            "If you add new tables to the export in the future, use",
            "`_aligned_md_table()` to keep the alignment consistent.",
            "",
        ]
    )

    # ── .gitattributes Reference ──
    lines.extend(
        [
            "---",
            "",
            "## .gitattributes Reference",
            "",
            "`.gitattributes` controls per-path settings in your repository.",
            "Unlike `.gitconfig`, these settings are **committed and shared**",
            "with all collaborators. Place this file in the repository root.",
            "",
            "### Key Terms",
            "",
            *_aligned_md_table(
                ["Term", "Meaning"],
                [
                    [
                        "**eol**",
                        "End Of Line — the character(s) that mark the end of a line in a text file. Controlled per-path in `.gitattributes` via `eol=lf` or `eol=crlf`.",
                    ],
                    [
                        "**LF**",
                        "Line Feed (`\\n`, hex `0x0A`). The standard line ending on Linux and macOS. One byte per line break. Used as the canonical format inside git's object store.",
                    ],
                    [
                        "**CRLF**",
                        "Carriage Return + Line Feed (`\\r\\n`, hex `0x0D 0x0A`). The standard line ending on Windows. Two bytes per line break. Git can auto-convert CRLF↔LF via `core.autocrlf` or `.gitattributes` rules.",
                    ],
                    [
                        "**diff drivers**",
                        "Built-in or custom programs that control how `git diff` displays changes for specific file types. For example, `diff=python` tells git to use Python-aware function boundary detection, so diff headers show `def func_name()` instead of generic context. Common built-in drivers: `python`, `markdown`, `html`, `css`, `java`.",
                    ],
                ],
            ),
            "",
            "### Sample .gitattributes",
            "",
            "```text",
            "# ── Line Endings ─────────────────────────────────────────",
            "# Force LF in the repo, let git handle working-tree conversion",
            "* text=auto eol=lf",
            "",
            "# Explicitly mark text files (override auto-detection)",
            "*.py    text eol=lf",
            "*.md    text eol=lf",
            "*.yml   text eol=lf",
            "*.yaml  text eol=lf",
            "*.toml  text eol=lf",
            "*.json  text eol=lf",
            "*.html  text eol=lf",
            "*.css   text eol=lf",
            "*.js    text eol=lf",
            "*.sh    text eol=lf",
            "",
            "# Windows-specific files that need CRLF",
            "*.bat   text eol=crlf",
            "*.cmd   text eol=crlf",
            "*.ps1   text eol=crlf",
            "",
            "# ── Binary Files ─────────────────────────────────────────",
            "# Mark binary files so git doesn't try to diff/merge them",
            "*.png    binary",
            "*.jpg    binary",
            "*.jpeg   binary",
            "*.gif    binary",
            "*.ico    binary",
            "*.woff   binary",
            "*.woff2  binary",
            "*.ttf    binary",
            "*.zip    binary",
            "*.tar.gz binary",
            "*.sqlite3 binary",
            "*.db     binary",
            "*.pdf    binary",
            "",
            "# ── Diff Drivers ─────────────────────────────────────────",
            "# Tell git to use language-aware diff heuristics for these file types.",
            "# This improves diff output by showing function/section names in headers.",
            "*.md diff=markdown",
            "*.py diff=python",
            "",
            "# ── Export Ignore ────────────────────────────────────────",
            "# Files excluded from 'git archive' exports",
            ".gitattributes   export-ignore",
            ".gitignore       export-ignore",
            ".github/         export-ignore",
            "tests/           export-ignore",
            "docs/            export-ignore",
            "Taskfile.yml     export-ignore",
            "*.code-workspace export-ignore",
            "",
            "# ── Linguist (GitHub) ────────────────────────────────────",
            "# Override GitHub's language statistics",
            "docs/*    linguist-documentation",
            "scripts/* linguist-vendored=false",
            "```",
            "",
            "### Pattern Syntax",
            "",
            *_aligned_md_table(
                ["Pattern", "Meaning"],
                [
                    ["`*`", "Match all files"],
                    ["`*.py`", "Match files ending in .py"],
                    ["`text`", "Treat as text (enable line-ending conversion)"],
                    [
                        "`text=auto`",
                        "Let git auto-detect text vs binary; convert line endings for detected text files",
                    ],
                    [
                        "`binary`",
                        "Treat as binary — skip newline conversion and textual diff entirely",
                    ],
                    [
                        "`eol=lf`",
                        "Normalize line endings to LF (`\\n`) when checking in and checking out",
                    ],
                    [
                        "`eol=crlf`",
                        "Convert to CRLF (`\\r\\n`) in the working tree while storing as LF in the repo",
                    ],
                    [
                        "`diff=python`",
                        "Use Python-aware diff heuristics (function names in diff headers)",
                    ],
                    [
                        "`diff=markdown`",
                        "Use Markdown-aware diff (section headings in diff headers)",
                    ],
                    [
                        "`export-ignore`",
                        "Exclude from `git archive` exports (tarballs, zips)",
                    ],
                    [
                        "`linguist-documentation`",
                        "Tell GitHub to classify these files as documentation (not source code) in language stats",
                    ],
                ],
            ),
            "",
            "---",
            "",
            "## Applying Changes from This File",
            "",
            "Edit **both** the **Desired value** and **Desired scope** columns",
            "for any config entry above, then apply all changes at once:",
            "",
            "```bash",
            "python scripts/git_doctor.py --apply-from git-config-reference.md",
            "```",
            "",
            "**How it works:**",
            "",
            "- Only entries where **both** `Desired value` **and** `Desired scope`",
            "  are changed from `_(no change)_` are applied.",
            "- If you set a **Desired value** but leave **Desired scope** unchanged",
            "  (or vice versa), the entry is **skipped with an error**.",
            "- Complete entries in other sections are still applied normally.",
            "",
            "To apply the catalog's **recommended** values for **all** keys",
            "(overwriting existing values):",
            "",
            "```bash",
            "python scripts/git_doctor.py --apply-recommended              # apply all",
            "python scripts/git_doctor.py --apply-recommended --dry-run   # preview first",
            "```",
            "",
            "> **Warning:** `--apply-recommended` overwrites existing values",
            "> to match the catalog baseline. For per-key control, edit this",
            "> file and use `--apply-from` instead.",
            "",
            f"To apply only the **core minimal set** ({len(MINIMAL_RECOMMENDED_CONFIGS)} high-impact keys):",
            "",
            "```bash",
            "python scripts/git_doctor.py --apply-recommended-minimal              # apply core set",
            "python scripts/git_doctor.py --apply-recommended-minimal --dry-run   # preview first",
            "```",
            "",
            "To preview what would change without applying:",
            "",
            "```bash",
            "python scripts/git_doctor.py --apply-from git-config-reference.md --dry-run",
            "```",
            "",
        ]
    )

    out_path = Path(filepath).resolve()
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return str(out_path)


# ---------------------------------------------------------------------------
# Apply config from reference file
# ---------------------------------------------------------------------------


def apply_from_reference(filepath: str, *, dry_run: bool = False) -> int:
    """Apply git config changes from an edited git-config-reference.md file.

    Parses the Markdown file for entries where **both** the ``Desired value``
    and ``Desired scope`` columns have been changed from ``_(no change)_``.
    If only one of the two is set, the entry is flagged as an error and
    skipped.  Complete entries in other sections are still applied.

    Args:
        filepath: Path to the edited reference Markdown file.
        dry_run: If True, print what would be changed without applying.

    Returns:
        Number of settings applied (or that would be applied in dry-run).
    """
    use_color = _supports_color(sys.stdout)
    use_unicode = _supports_unicode(sys.stdout)
    c = Colors(enabled=use_color)

    h_double = "\u2550" if use_unicode else "="
    h_line = "\u2500" if use_unicode else "-"
    tl_d = "\u2554" if use_unicode else "+"
    tr_d = "\u2557" if use_unicode else "+"
    bl_d = "\u255a" if use_unicode else "+"
    br_d = "\u255d" if use_unicode else "+"
    vl_d = "\u2551" if use_unicode else "|"
    tl = "\u250c" if use_unicode else "+"
    tr = "\u2510" if use_unicode else "+"
    bl = "\u2514" if use_unicode else "+"
    br = "\u2518" if use_unicode else "+"
    vl = "\u2502" if use_unicode else "|"
    dot = "\u2022" if use_unicode else "*"
    sym = _unicode_symbols(sys.stdout)
    check_sym = sym.get("check", "+")
    cross_sym = sym.get("cross", "x")
    warn_sym = sym.get("warn", "!")

    ref_path = Path(filepath)
    if not ref_path.is_file():
        print(c.red(f"File not found: {filepath}"))
        return 0

    content = ref_path.read_text(encoding="utf-8")

    # Build a catalog lookup for recommendations
    catalog_lookup: dict[str, tuple[str, str, str]] = {}
    for cat_key, cat_scope, cat_desc, cat_rec in GIT_CONFIG_CATALOG:
        catalog_lookup[cat_key] = (cat_scope, cat_desc, cat_rec)

    VALID_SCOPES = {"local", "global", "system"}
    UNCHANGED = {"_(no change)_", "", "-"}

    key_pattern = re.compile(r"^### `(.+?)`$", re.MULTILINE)

    # ── Styled header ──
    header_border = h_double * 60
    mode_label = " (dry run)" if dry_run else ""
    print()
    print(c.bold(c.cyan(f"  {tl_d}{header_border}{tr_d}")))
    print(
        f"  {c.bold(c.cyan(vl_d))} "
        f"{c.bold(c.cyan('Apply Config from Reference'))}{c.dim(mode_label)}"
        f"  {c.dim(f'v{SCRIPT_VERSION}')}"
    )
    print(c.bold(c.cyan(f"  {bl_d}{header_border}{br_d}")))
    print()
    print(f"  {c.dim(dot)} Source: {c.cyan(filepath)}")
    print(f"  {c.dim(dot)} Both 'Desired value' AND 'Desired scope' must be set")

    # ── First pass: parse all entries and group by section ──
    #   entry = (key, desired_value|None, desired_scope|None, section)
    ParsedEntry = tuple[str, str | None, str | None, str]
    parsed: list[ParsedEntry] = []

    matches = list(key_pattern.finditer(content))
    for i, match in enumerate(matches):
        key = match.group(1)
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        block = content[start:end]
        section = _config_section(key)

        # Desired value
        desired_match = re.search(
            r"\|\s*\*\*Desired value\*\*\s*\|\s*(.+?)\s*\|", block
        )
        desired_raw = desired_match.group(1).strip() if desired_match else ""
        has_value = desired_raw not in UNCHANGED
        desired = desired_raw.strip("`'\"") if has_value else None

        # Desired scope
        scope_match = re.search(r"\|\s*\*\*Desired scope\*\*\s*\|\s*(.+?)\s*\|", block)
        scope_raw = scope_match.group(1).strip() if scope_match else ""
        has_scope = scope_raw not in UNCHANGED
        scope = scope_raw.strip("`'\"").lower() if has_scope else None

        # Only include entries where at least one field was changed
        if has_value or has_scope:
            parsed.append((key, desired, scope, section))

    if not parsed:
        print()
        print(
            c.dim(
                "  No changes found. Edit both 'Desired value' and 'Desired scope'\n"
                "  columns in the reference file, then re-run."
            )
        )
        print()
        return 0

    # ── Categorise: complete (both set) vs. incomplete (only one set) ──
    complete: list[tuple[str, str, str, str]] = []  # key, value, scope, section
    incomplete: list[tuple[str, str | None, str | None, str]] = []

    for key, desired, scope, section in parsed:
        if desired and scope:
            complete.append((key, desired, scope, section))
        else:
            incomplete.append((key, desired, scope, section))

    # Column widths
    col_key = 30
    col_status = 13
    col_scope = 8
    col_value = 26

    def _row(
        key_s: str,
        status_s: str,
        scope_s: str,
        val_s: str,
        *,
        key_fmt: Callable[[str], str] = lambda x: x,
        status_fmt: Callable[[str], str] = lambda x: x,
        scope_fmt: Callable[[str], str] = lambda x: x,
        val_fmt: Callable[[str], str] = lambda x: x,
    ) -> None:
        """Print a table row with correct alignment despite ANSI codes."""
        print(
            f"    {key_fmt(key_s.ljust(col_key))}"
            f"  {status_fmt(status_s.ljust(col_status))}"
            f"  {scope_fmt(scope_s.ljust(col_scope))}"
            f"  {val_fmt(val_s)}"
        )

    applied = 0
    errors = 0

    # ── Apply complete entries, grouped by section ──
    if complete:
        sections_order: list[str] = []
        by_section: dict[str, list[tuple[str, str, str]]] = {}
        for key, val, scp, sec in complete:
            if sec not in by_section:
                sections_order.append(sec)
                by_section[sec] = []
            by_section[sec].append((key, val, scp))

        for sec_name in sections_order:
            sec_border = h_line * 60
            print()
            print(c.cyan(f"  {tl}{sec_border}{tr}"))
            print(f"  {c.cyan(vl)} {c.bold(sec_name)}")
            print(c.cyan(f"  {bl}{sec_border}{br}"))
            print()
            _row(
                "Key",
                "Status",
                "Scope",
                "Value",
                key_fmt=c.bold,
                status_fmt=c.bold,
                scope_fmt=c.bold,
                val_fmt=c.bold,
            )
            print(
                f"    {h_line * col_key}"
                f"  {h_line * col_status}"
                f"  {h_line * col_scope}"
                f"  {h_line * col_value}"
            )

            for key, desired, scope in by_section[sec_name]:
                cat_info = catalog_lookup.get(key)
                cat_rec_scope = cat_info[0] if cat_info else "global"
                cat_rec_value = cat_info[2] if cat_info else ""

                # Validate scope
                if scope not in VALID_SCOPES:
                    errors += 1
                    _row(
                        key,
                        "invalid scope",
                        scope,
                        desired,
                        status_fmt=c.red,
                        scope_fmt=c.red,
                        val_fmt=c.red,
                    )
                    print(
                        f"    {''.ljust(col_key)}  "
                        f"{c.dim('valid: ' + ', '.join(sorted(VALID_SCOPES)))}  "
                        f"{c.dim(f'rec: {cat_rec_scope} / {cat_rec_value}')}"
                    )
                    continue

                if dry_run:
                    _row(
                        key,
                        "would set",
                        scope,
                        desired,
                        status_fmt=c.cyan,
                        scope_fmt=c.dim,
                    )
                else:
                    git_code, _, err = _run_git(["config", f"--{scope}", key, desired])
                    if git_code == 0:
                        _row(
                            key,
                            "applied",
                            scope,
                            desired,
                            status_fmt=c.green,
                            scope_fmt=c.dim,
                        )
                    else:
                        errors += 1
                        _row(
                            key,
                            "failed",
                            scope,
                            err,
                            status_fmt=c.red,
                            scope_fmt=c.dim,
                            val_fmt=c.red,
                        )
                        continue
                applied += 1

    # ── Report incomplete entries ──
    if incomplete:
        sec_border = h_line * 60
        print()
        print(c.yellow(f"  {tl}{sec_border}{tr}"))
        print(f"  {c.yellow(vl)} {c.bold(c.yellow('Incomplete Entries (skipped)'))}")
        print(c.yellow(f"  {bl}{sec_border}{br}"))
        print()
        print(
            f"  {c.yellow(warn_sym)} Both 'Desired value' AND 'Desired scope' "
            f"must be set."
        )
        print("    Entries with only one field filled are skipped.")
        print()
        _row(
            "Key",
            "Has Value",
            "Has Scope",
            "Missing",
            key_fmt=c.bold,
            status_fmt=c.bold,
            scope_fmt=c.bold,
            val_fmt=c.bold,
        )
        print(
            f"    {h_line * col_key}"
            f"  {h_line * col_status}"
            f"  {h_line * col_scope}"
            f"  {h_line * col_value}"
        )
        for key, desired, scope, _section in incomplete:
            has_v = "yes" if desired else "no"
            has_s = "yes" if scope else "no"
            missing = "scope" if desired and not scope else "value"
            _row(
                key,
                has_v,
                has_s,
                f"missing {missing}",
                status_fmt=c.green if desired else c.red,
                scope_fmt=c.green if scope else c.red,
                val_fmt=c.yellow,
            )
            errors += 1

    # ── Summary footer ──
    print()
    print(c.cyan(f"  {h_double * 60}"))
    if errors == 0:
        sym_str = c.green(check_sym) if use_unicode else c.green("OK")
        if dry_run:
            print(f"  {sym_str} {c.cyan(f'{applied} setting(s) would be applied')}")
        else:
            print(f"  {sym_str} {c.green(f'{applied} setting(s) applied')}")
    else:
        sym_str = c.red(cross_sym) if use_unicode else c.red("!!")
        if applied:
            print(
                f"  {sym_str} {c.green(f'{applied} applied')}"
                f"  {c.red(f'{errors} error(s) — see above')}"
            )
        else:
            print(f"  {sym_str} {c.red(f'{errors} error(s) — nothing applied')}")
    print(c.cyan(f"  {h_double * 60}"))
    print()
    return applied


# ---------------------------------------------------------------------------
# Apply recommended config (catalog defaults for unset keys)
# ---------------------------------------------------------------------------


def apply_recommended_config(*, dry_run: bool = False) -> int:
    """Apply ALL catalog recommended values and scopes.

    Sets **every** key in ``GIT_CONFIG_CATALOG`` that has a concrete
    recommended value, **regardless** of whether it is already set.
    This resets config to the catalog baseline.  For per-key control,
    use ``--export-config`` + ``--apply-from`` instead.

    See ``git-config-reference.md`` for the full catalog and values.

    Args:
        dry_run: If True, print what would be changed without applying.

    Returns:
        Number of settings applied (or that would be applied in dry-run).
    """
    elapsed_start = time.monotonic()
    use_color = _supports_color(sys.stdout)
    use_unicode = _supports_unicode(sys.stdout)
    c = Colors(enabled=use_color)

    # Box-drawing chars matching the main dashboard style
    h_double = "\u2550" if use_unicode else "="
    tl_d = "\u2554" if use_unicode else "+"
    tr_d = "\u2557" if use_unicode else "+"
    bl_d = "\u255a" if use_unicode else "+"
    br_d = "\u255d" if use_unicode else "+"
    vl_d = "\u2551" if use_unicode else "|"
    h_line = "\u2500" if use_unicode else "-"
    tl = "\u250c" if use_unicode else "+"
    tr = "\u2510" if use_unicode else "+"
    bl = "\u2514" if use_unicode else "+"
    br = "\u2518" if use_unicode else "+"
    vl = "\u2502" if use_unicode else "|"
    dot = "\u2022" if use_unicode else "*"
    sym = _unicode_symbols(sys.stdout)
    check_sym = sym.get("check", "+")
    cross_sym = sym.get("cross", "x")

    applied = 0
    failed = 0
    no_rec = 0

    # ── Styled header ──
    header_border = h_double * 60
    mode_label = " (dry run)" if dry_run else ""
    print()
    print(c.bold(c.cyan(f"  {tl_d}{header_border}{tr_d}")))
    print(
        f"  {c.bold(c.cyan(vl_d))} "
        f"{c.bold(c.cyan('Apply Recommended Config'))}{c.dim(mode_label)}"
        f"  {c.dim(f'v{SCRIPT_VERSION}')}"
    )
    print(c.bold(c.cyan(f"  {bl_d}{header_border}{br_d}")))
    print()
    print(f"  {c.dim(dot)} Sets ALL catalog recommended values and scopes")
    print(f"  {c.dim(dot)} Overwrites existing values to match the catalog baseline")
    print(f"  {c.dim(dot)} Keys without a concrete recommendation are skipped")
    print(f"  {c.dim(dot)} For per-key control: --export-config + --apply-from")

    # Column widths for aligned table output
    col_key = 30
    col_status = 13
    col_scope = 8
    col_value = 26

    def _row(
        key_s: str,
        status_s: str,
        scope_s: str,
        val_s: str,
        *,
        key_fmt: Callable[[str], str] = lambda x: x,
        status_fmt: Callable[[str], str] = lambda x: x,
        scope_fmt: Callable[[str], str] = lambda x: x,
        val_fmt: Callable[[str], str] = lambda x: x,
    ) -> None:
        """Print a table row with correct alignment despite ANSI codes."""
        print(
            f"    {key_fmt(key_s.ljust(col_key))}"
            f"  {status_fmt(status_s.ljust(col_status))}"
            f"  {scope_fmt(scope_s.ljust(col_scope))}"
            f"  {val_fmt(val_s)}"
        )

    # Collect entries grouped by section
    sections: dict[str, list[tuple[str, str, str, str]]] = {}
    for key, rec_scope, _desc, recommendation in GIT_CONFIG_CATALOG:
        section = _config_section(key)
        if section not in sections:
            sections[section] = []
        sections[section].append((key, rec_scope, _desc, recommendation))

    skip_patterns = (
        "e.g.",
        "your ",
        "set if",
        "leave unset",
        "auto-detected",
        "default is",
        "default (",
        "increase (",
        "keep ",
    )

    for section_name, entries in sections.items():
        # Section header
        sec_border = h_line * 60
        print()
        print(c.cyan(f"  {tl}{sec_border}{tr}"))
        print(f"  {c.cyan(vl)} {c.bold(section_name)}")
        print(c.cyan(f"  {bl}{sec_border}{br}"))
        print()
        # Table heading
        _row(
            "Key",
            "Status",
            "Scope",
            "Value",
            key_fmt=c.bold,
            status_fmt=c.bold,
            scope_fmt=c.bold,
            val_fmt=c.bold,
        )
        print(
            f"    {h_line * col_key}"
            f"  {h_line * col_status}"
            f"  {h_line * col_scope}"
            f"  {h_line * col_value}"
        )

        for key, rec_scope, _desc, recommendation in entries:
            rec_lower = recommendation.lower()
            if any(rec_lower.startswith(p) or p in rec_lower for p in skip_patterns):
                _row(
                    key,
                    "skip",
                    h_line * 3,
                    recommendation,
                    key_fmt=c.dim,
                    status_fmt=c.dim,
                    scope_fmt=c.dim,
                    val_fmt=c.dim,
                )
                no_rec += 1
                continue

            # Extract concrete value
            quoted = re.search(r"'([^']+)'", recommendation)
            value = quoted.group(1) if quoted else recommendation.strip("'\"` ")

            current = get_git_config_value(key)

            if dry_run:
                if current and current == value:
                    _row(
                        key,
                        "already rec",
                        rec_scope,
                        value,
                        status_fmt=c.green,
                        scope_fmt=c.dim,
                    )
                elif current:
                    _row(
                        key,
                        "would reset",
                        rec_scope,
                        value,
                        status_fmt=c.cyan,
                        scope_fmt=c.dim,
                    )
                else:
                    _row(
                        key,
                        "would set",
                        rec_scope,
                        value,
                        status_fmt=c.cyan,
                        scope_fmt=c.dim,
                    )
            else:
                git_code, _, err = _run_git(["config", f"--{rec_scope}", key, value])
                if git_code == 0:
                    if current and current == value:
                        _row(
                            key,
                            "already rec",
                            rec_scope,
                            value,
                            status_fmt=c.green,
                            scope_fmt=c.dim,
                        )
                    elif current:
                        _row(
                            key,
                            "reset",
                            rec_scope,
                            value,
                            status_fmt=c.green,
                            scope_fmt=c.dim,
                        )
                    else:
                        _row(
                            key,
                            "applied",
                            rec_scope,
                            value,
                            status_fmt=c.green,
                            scope_fmt=c.dim,
                        )
                else:
                    _row(
                        key,
                        "failed",
                        rec_scope,
                        err,
                        status_fmt=c.red,
                        scope_fmt=c.dim,
                        val_fmt=c.red,
                    )
                    failed += 1
                    continue
            applied += 1

    # ── Summary footer ──
    elapsed = time.monotonic() - elapsed_start
    print()
    print(c.cyan(f"  {h_double * 60}"))
    if failed == 0:
        sym_str = c.green(check_sym) if use_unicode else c.green("OK")
        if dry_run:
            print(
                f"  {sym_str} {c.cyan(f'{applied} setting(s) would be applied')}"
                f"  {c.dim(f'{no_rec} skipped (no concrete default)')}"
            )
        else:
            print(
                f"  {sym_str} {c.green(f'{applied} setting(s) applied')}"
                f"  {c.dim(f'{no_rec} skipped (no concrete default)')}"
            )
    else:
        sym_str = c.red(cross_sym) if use_unicode else c.red("!!")
        print(
            f"  {sym_str} {c.red(f'{failed} failed')}"
            f"  {c.dim(f'{applied} applied, {no_rec} skipped')}"
        )
    print(
        f"  {c.dim(f'Completed in {elapsed:.1f}s  {dot}  git-doctor v{SCRIPT_VERSION}')}"
    )
    print(c.cyan(f"  {h_double * 60}"))
    print()
    return applied


# ---------------------------------------------------------------------------
# Apply recommended minimal config (core subset)
# ---------------------------------------------------------------------------


def apply_recommended_minimal_config(*, dry_run: bool = False) -> int:
    """Apply only the core minimal recommended configs.

    Uses ``MINIMAL_RECOMMENDED_CONFIGS`` (12 high-impact keys) instead of
    the full 62-key catalog.  Safer for first-time setup — only sets
    non-destructive, broadly useful defaults.

    Args:
        dry_run: If True, print what would be changed without applying.

    Returns:
        Number of settings applied (or that would be applied in dry-run).
    """
    elapsed_start = time.monotonic()
    use_color = _supports_color(sys.stdout)
    use_unicode = _supports_unicode(sys.stdout)
    c = Colors(enabled=use_color)

    h_double = "\u2550" if use_unicode else "="
    tl_d = "\u2554" if use_unicode else "+"
    tr_d = "\u2557" if use_unicode else "+"
    bl_d = "\u255a" if use_unicode else "+"
    br_d = "\u255d" if use_unicode else "+"
    vl_d = "\u2551" if use_unicode else "|"
    h_line = "\u2500" if use_unicode else "-"
    dot = "\u2022" if use_unicode else "*"
    sym = _unicode_symbols(sys.stdout)
    check_sym = sym.get("check", "+")
    cross_sym = sym.get("cross", "x")

    applied = 0
    failed = 0

    # ── Styled header ──
    header_border = h_double * 60
    mode_label = " (dry run)" if dry_run else ""
    print()
    print(c.bold(c.cyan(f"  {tl_d}{header_border}{tr_d}")))
    print(
        f"  {c.bold(c.cyan(vl_d))} "
        f"{c.bold(c.cyan('Apply Recommended Minimal Config'))}{c.dim(mode_label)}"
        f"  {c.dim(f'v{SCRIPT_VERSION}')}"
    )
    print(c.bold(c.cyan(f"  {bl_d}{header_border}{br_d}")))
    print()
    print(
        f"  {c.dim(dot)} Sets {len(MINIMAL_RECOMMENDED_CONFIGS)} core high-impact configs"
    )
    print(
        f"  {c.dim(dot)} Safer alternative to --apply-recommended (which sets all ~62 keys)"
    )
    print(f"  {c.dim(dot)} For full catalog: --apply-recommended")
    print(f"  {c.dim(dot)} For per-key control: --export-config + --apply-from")

    col_key = 30
    col_status = 13
    col_scope = 8
    col_value = 26

    def _row(
        key_s: str,
        status_s: str,
        scope_s: str,
        val_s: str,
        *,
        key_fmt: Callable[[str], str] = lambda x: x,
        status_fmt: Callable[[str], str] = lambda x: x,
        scope_fmt: Callable[[str], str] = lambda x: x,
        val_fmt: Callable[[str], str] = lambda x: x,
    ) -> None:
        print(
            f"    {key_fmt(key_s.ljust(col_key))}"
            f"  {status_fmt(status_s.ljust(col_status))}"
            f"  {scope_fmt(scope_s.ljust(col_scope))}"
            f"  {val_fmt(val_s)}"
        )

    # Table heading
    print()
    _row(
        "Key",
        "Status",
        "Scope",
        "Value",
        key_fmt=c.bold,
        status_fmt=c.bold,
        scope_fmt=c.bold,
        val_fmt=c.bold,
    )
    print(
        f"    {h_line * col_key}"
        f"  {h_line * col_status}"
        f"  {h_line * col_scope}"
        f"  {h_line * col_value}"
    )

    for key, value, scope in MINIMAL_RECOMMENDED_CONFIGS:
        current = get_git_config_value(key)

        if dry_run:
            if current and current == value:
                _row(
                    key,
                    "already set",
                    scope,
                    value,
                    status_fmt=c.green,
                    scope_fmt=c.dim,
                )
            elif current:
                _row(
                    key, "would reset", scope, value, status_fmt=c.cyan, scope_fmt=c.dim
                )
            else:
                _row(key, "would set", scope, value, status_fmt=c.cyan, scope_fmt=c.dim)
        else:
            git_code, _, err = _run_git(["config", f"--{scope}", key, value])
            if git_code == 0:
                if current and current == value:
                    _row(
                        key,
                        "already set",
                        scope,
                        value,
                        status_fmt=c.green,
                        scope_fmt=c.dim,
                    )
                elif current:
                    _row(
                        key, "reset", scope, value, status_fmt=c.green, scope_fmt=c.dim
                    )
                else:
                    _row(
                        key,
                        "applied",
                        scope,
                        value,
                        status_fmt=c.green,
                        scope_fmt=c.dim,
                    )
            else:
                _row(
                    key,
                    "failed",
                    scope,
                    err,
                    status_fmt=c.red,
                    scope_fmt=c.dim,
                    val_fmt=c.red,
                )
                failed += 1
                continue
        applied += 1

    # ── Summary footer ──
    elapsed = time.monotonic() - elapsed_start
    print()
    print(c.cyan(f"  {h_double * 60}"))
    if failed == 0:
        sym_str = c.green(check_sym) if use_unicode else c.green("OK")
        if dry_run:
            print(f"  {sym_str} {c.cyan(f'{applied} setting(s) would be applied')}")
        else:
            print(f"  {sym_str} {c.green(f'{applied} setting(s) applied')}")
    else:
        sym_str = c.red(cross_sym) if use_unicode else c.red("!!")
        print(f"  {sym_str} {c.red(f'{failed} failed')}  {c.dim(f'{applied} applied')}")
    print(
        f"  {c.dim(f'Completed in {elapsed:.1f}s  {dot}  git-doctor v{SCRIPT_VERSION}')}"
    )
    print(c.cyan(f"  {h_double * 60}"))
    print()
    return applied


# ---------------------------------------------------------------------------
# Branch creation workflow (--new-branch)
# ---------------------------------------------------------------------------

# Well-known branch prefixes for the interactive picker.
# TODO (template users): Add, remove, or reorder prefixes to match your
#   team's branch naming conventions. The first entry is the default when
#   the user presses Enter without choosing.
_BRANCH_PREFIXES: list[tuple[str, str]] = [
    ("feature/", "New functionality"),
    ("fix/", "Bug fixes"),
    ("chore/", "Maintenance, deps"),
    ("docs/", "Documentation"),
    ("spike/", "Experimental / exploratory"),
    ("wip/", "Work in progress / scratch"),
    ("hotfix/", "Urgent production fix"),
    ("refactor/", "Code refactor"),
    ("test/", "Test additions / changes"),
    ("ci/", "CI/CD changes"),
]


def _prompt(prompt_text: str, *, default: str = "") -> str:
    """Read a line from stdin with an optional default value."""
    suffix = f" [{default}]" if default else ""
    try:
        value = input(f"  {prompt_text}{suffix}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(130)
    return value or default


def _confirm(prompt_text: str, *, default_yes: bool = False) -> bool:
    """Ask a yes/no question and return True if the user confirms."""
    hint = "Y/n" if default_yes else "y/N"
    try:
        answer = input(f"  {prompt_text} [{hint}]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(130)
    if not answer:
        return default_yes
    return answer in ("y", "yes")


# ---------------------------------------------------------------------------
# Refresh: update refs, tags, and remote metadata
# ---------------------------------------------------------------------------


def refresh_repo(
    *,
    dry_run: bool = False,
    color: bool | None = None,
) -> int:
    """Interactive refresh of remote refs, tags, and remote-tracking data.

    Fetches all remotes, prunes stale remote-tracking refs, syncs tags,
    and updates the default branch ref.  Reports what was updated in
    dashboard style.

    Args:
        dry_run: If True, show what would be done without executing.
        color: Force color on/off, or None for auto-detect.

    Returns:
        0 on success, 1 if any operation failed.
    """
    elapsed_start = time.monotonic()
    use_color = color if color is not None else _supports_color(sys.stdout)
    use_unicode = _supports_unicode(sys.stdout)
    c = Colors(enabled=use_color)

    # Box-drawing chars
    h_double = "\u2550" if use_unicode else "="
    tl_d = "\u2554" if use_unicode else "+"
    tr_d = "\u2557" if use_unicode else "+"
    bl_d = "\u255a" if use_unicode else "+"
    br_d = "\u255d" if use_unicode else "+"
    vl_d = "\u2551" if use_unicode else "|"
    h_line = "\u2500" if use_unicode else "-"
    tl = "\u250c" if use_unicode else "+"
    tr = "\u2510" if use_unicode else "+"
    bl = "\u2514" if use_unicode else "+"
    br = "\u2518" if use_unicode else "+"
    vl = "\u2502" if use_unicode else "|"
    dot = "\u2022" if use_unicode else "*"
    sym = _unicode_symbols(sys.stdout)
    check_sym = sym.get("check", "+")
    cross_sym = sym.get("cross", "x")
    warn_sym = sym.get("warn", "!")

    # ── Header ──
    mode_label = " (dry run)" if dry_run else ""
    header_border = h_double * 60
    print()
    print(c.bold(c.cyan(f"  {tl_d}{header_border}{tr_d}")))
    print(
        f"  {c.bold(c.cyan(vl_d))} "
        f"{c.bold(c.cyan('Refresh'))}{c.dim(mode_label)}"
        f"  {c.dim(f'v{SCRIPT_VERSION}')}"
    )
    print(c.bold(c.cyan(f"  {bl_d}{header_border}{br_d}")))

    # ── Collect what will be refreshed ──
    operations: list[tuple[str, str, list[str]]] = []

    # 1. Fetch all remotes + prune stale remote-tracking refs
    remotes_raw = get_all_remotes()
    remote_names = sorted({r["name"] for r in remotes_raw if r.get("name")})
    if remote_names:
        operations.append(
            (
                "Fetch all remotes & prune stale refs",
                f"git fetch --all --prune ({', '.join(remote_names)})",
                ["fetch", "--all", "--prune"],
            )
        )
    else:
        operations.append(
            (
                "Fetch all remotes & prune stale refs",
                "git fetch --all --prune",
                ["fetch", "--all", "--prune"],
            )
        )

    # 2. Sync tags from remote
    operations.append(
        (
            "Sync tags from remote",
            "git fetch --tags --force",
            ["fetch", "--tags", "--force"],
        )
    )

    # 3. Update default branch ref (origin/HEAD)
    operations.append(
        (
            "Update remote HEAD reference",
            "git remote set-head origin --auto",
            ["remote", "set-head", "origin", "--auto"],
        )
    )

    # ── Preview section ──
    sec_border = h_line * 60
    print()
    print(c.cyan(f"  {tl}{sec_border}{tr}"))
    print(f"  {c.cyan(vl)} {c.bold('Operations')}")
    print(c.cyan(f"  {bl}{sec_border}{br}"))
    print()
    for desc, cmd_str, _args in operations:
        print(f"    {c.cyan(dot)} {desc}")
        print(f"      {c.dim(cmd_str)}")

    if dry_run:
        # Show what would happen and exit
        elapsed = time.monotonic() - elapsed_start
        print()
        print(c.cyan(f"  {h_double * 60}"))
        print(
            f"  {c.cyan(check_sym)} "
            f"{c.cyan(f'{len(operations)} operation(s) would run')}"
        )
        print(
            f"  {c.dim(f'Completed in {elapsed:.1f}s  {dot}  git-doctor v{SCRIPT_VERSION}')}"
        )
        print(c.cyan(f"  {h_double * 60}"))
        print()
        return 0

    # ── Confirm ──
    print()
    if not _confirm("Proceed with refresh?", default_yes=True):
        print()
        print(f"  {c.yellow(warn_sym)} {c.yellow('Cancelled')}")
        print()
        return 0

    # ── Execute ──
    print()
    print(c.cyan(f"  {tl}{sec_border}{tr}"))
    print(f"  {c.cyan(vl)} {c.bold('Results')}")
    print(c.cyan(f"  {bl}{sec_border}{br}"))
    print()

    succeeded = 0
    failed = 0
    for desc, _cmd_str, git_args in operations:
        code, out, err = _run_git(git_args, timeout=30)
        if code == 0:
            print(f"    {c.green(check_sym)} {desc}")
            if out:
                for line in out.splitlines()[:3]:
                    print(f"      {c.dim(line)}")
            succeeded += 1
        else:
            print(f"    {c.red(cross_sym)} {desc}")
            if err:
                for line in err.splitlines()[:2]:
                    print(f"      {c.red(line)}")
            failed += 1

    # ── Summary ──
    elapsed = time.monotonic() - elapsed_start
    print()
    print(c.cyan(f"  {h_double * 60}"))
    if failed == 0:
        print(
            f"  {c.green(check_sym)} "
            f"{c.green(f'{succeeded} operation(s) completed successfully')}"
        )
    else:
        print(
            f"  {c.red(cross_sym)} "
            f"{c.red(f'{failed} failed')}"
            f"  {c.dim(f'{succeeded} succeeded')}"
        )
    print(
        f"  {c.dim(f'Completed in {elapsed:.1f}s  {dot}  git-doctor v{SCRIPT_VERSION}')}"
    )
    print(c.cyan(f"  {h_double * 60}"))

    # ── Recommendation ──
    print()
    print(
        f"  {c.dim(dot)} {c.dim('Tip: Run')} {c.cyan('--export-config')} "
        f"{c.dim('to review git settings, or')}"
    )
    print(
        f"  {c.dim('  ')} {c.cyan('--apply-recommended-minimal')} "
        f"{c.dim('to apply core recommended configs')}"
    )
    print()
    print(
        f"  {c.dim(dot)} {c.dim('To automate what --refresh does, set these git configs:')}"
    )
    print(
        f"    {c.dim('git config --global fetch.prune true')}"
        f"       {c.dim('# auto-prune stale refs on every fetch')}"
    )
    print(
        f"    {c.dim('git config --global fetch.prunetags true')}"
        f"   {c.dim('# auto-prune stale tags on every fetch')}"
    )
    print(
        f"  {c.dim(dot)} {c.dim('Run')} {c.cyan('--export-config')} "
        f"{c.dim('to see all configs, or')} {c.cyan('--apply-recommended-minimal')} "
        f"{c.dim('to apply them')}"
    )
    print()

    return 1 if failed > 0 else 0


# ---------------------------------------------------------------------------
# Cleanup: delete stale branches, old tags, and other cruft
# ---------------------------------------------------------------------------


def cleanup_repo(
    *,
    dry_run: bool = False,
    color: bool | None = None,
    stale_days: int = 90,
) -> int:
    """Interactive cleanup of stale branches, gone tracking refs, and cruft.

    Identifies local branches with no commits in *stale_days* days,
    branches whose upstream tracking reference is ``[gone]`` (deleted
    on the remote), and other housekeeping items.  Shows everything
    that would be deleted and asks for confirmation.

    Args:
        dry_run: If True, show what would be deleted without executing.
        color: Force color on/off, or None for auto-detect.
        stale_days: Consider branches stale after this many days of
            inactivity (default: 90).

    Returns:
        0 on success, 1 if any operation failed.
    """
    elapsed_start = time.monotonic()
    use_color = color if color is not None else _supports_color(sys.stdout)
    use_unicode = _supports_unicode(sys.stdout)
    c = Colors(enabled=use_color)

    # Box-drawing chars
    h_double = "\u2550" if use_unicode else "="
    tl_d = "\u2554" if use_unicode else "+"
    tr_d = "\u2557" if use_unicode else "+"
    bl_d = "\u255a" if use_unicode else "+"
    br_d = "\u255d" if use_unicode else "+"
    vl_d = "\u2551" if use_unicode else "|"
    h_line = "\u2500" if use_unicode else "-"
    tl = "\u250c" if use_unicode else "+"
    tr = "\u2510" if use_unicode else "+"
    bl = "\u2514" if use_unicode else "+"
    br = "\u2518" if use_unicode else "+"
    vl = "\u2502" if use_unicode else "|"
    dot = "\u2022" if use_unicode else "*"
    sym = _unicode_symbols(sys.stdout)
    check_sym = sym.get("check", "+")
    cross_sym = sym.get("cross", "x")
    warn_sym = sym.get("warn", "!")
    arrow_sym = sym.get("arrow", "->")

    current_branch = get_current_branch()
    default_branch = get_default_branch()

    # ── Header ──
    mode_label = " (dry run)" if dry_run else ""
    header_border = h_double * 60
    print()
    print(c.bold(c.cyan(f"  {tl_d}{header_border}{tr_d}")))
    print(
        f"  {c.bold(c.cyan(vl_d))} "
        f"{c.bold(c.cyan('Cleanup'))}{c.dim(mode_label)}"
        f"  {c.dim(f'v{SCRIPT_VERSION}')}"
    )
    print(c.bold(c.cyan(f"  {bl_d}{header_border}{br_d}")))

    # ── Collect candidates ──

    # 1. Stale branches (no commits in stale_days days)
    stale = get_stale_branches(days=stale_days)
    # Never delete the current branch or the default branch
    protected = {current_branch, default_branch, "main", "master", "develop"}
    stale_branches = [b for b in stale if b["name"] not in protected]

    # 2. Branches with [gone] upstream (remote deleted, likely merged via PR)
    gone_branches: list[str] = []
    code, out, _ = _run_git(
        ["branch", "-vv", "--format=%(refname:short)\t%(upstream:track)"]
    )
    if code == 0 and out:
        for line in out.splitlines():
            parts = line.split("\t", 1)
            if len(parts) == 2 and "[gone]" in parts[1]:
                name = parts[0].strip()
                if name not in protected:
                    gone_branches.append(name)

    # 3. Expired reflog entries
    has_reflog_cruft = True  # gc always helps

    # 4. Loose objects (git gc)
    code_gc, gc_out, _ = _run_git(["count-objects", "-v"])
    loose_count = 0
    if code_gc == 0 and gc_out:
        for line in gc_out.splitlines():
            if line.startswith("count:"):
                with contextlib.suppress(ValueError):
                    loose_count = int(line.split(":")[1].strip())

    # Determine if there's anything to do
    total_items = len(stale_branches) + len(gone_branches)
    has_gc_work = loose_count > _LOOSE_OBJECTS_GC_THRESHOLD or has_reflog_cruft

    if total_items == 0 and not has_gc_work:
        print()
        print(f"  {c.green(check_sym)} {c.green('Nothing to clean up — repo is tidy')}")
        elapsed = time.monotonic() - elapsed_start
        print()
        print(c.cyan(f"  {h_double * 60}"))
        print(
            f"  {c.dim(f'Completed in {elapsed:.1f}s  {dot}  git-doctor v{SCRIPT_VERSION}')}"
        )
        print(c.cyan(f"  {h_double * 60}"))
        print()
        return 0

    # ── Preview: stale branches ──
    if stale_branches:
        sec_border = h_line * 60
        print()
        print(c.cyan(f"  {tl}{sec_border}{tr}"))
        print(
            f"  {c.cyan(vl)} {c.bold(f'Stale Branches ({len(stale_branches)})')}"
            f"  {c.dim(f'no commits in {stale_days}+ days')}"
        )
        print(c.cyan(f"  {bl}{sec_border}{br}"))
        print()
        for b in stale_branches:
            last = b["last_commit"]
            print(
                f"    {c.yellow(warn_sym)} {b['name']}  {c.dim(f'last commit: {last}')}"
            )

    # ── Preview: gone branches ──
    if gone_branches:
        sec_border = h_line * 60
        print()
        print(c.cyan(f"  {tl}{sec_border}{tr}"))
        print(
            f"  {c.cyan(vl)} {c.bold(f'Gone Branches ({len(gone_branches)})')}"
            f"  {c.dim('remote tracking ref deleted')}"
        )
        print(c.cyan(f"  {bl}{sec_border}{br}"))
        print()
        for name in gone_branches:
            print(
                f"    {c.yellow(warn_sym)} {name}"
                f"  {c.dim(f'{arrow_sym} upstream deleted (likely merged via PR)')}"
            )

    # ── Preview: git gc ──
    if has_gc_work:
        sec_border = h_line * 60
        print()
        print(c.cyan(f"  {tl}{sec_border}{tr}"))
        print(f"  {c.cyan(vl)} {c.bold('Housekeeping')}")
        print(c.cyan(f"  {bl}{sec_border}{br}"))
        print()
        print(f"    {c.cyan(dot)} Run git gc (expire reflogs, pack loose objects)")
        if loose_count > 0:
            print(f"      {c.dim(f'{loose_count} loose objects')}")

    if dry_run:
        # Show summary and exit
        elapsed = time.monotonic() - elapsed_start
        print()
        print(c.cyan(f"  {h_double * 60}"))
        items = []
        if stale_branches:
            items.append(f"{len(stale_branches)} stale branch(es)")
        if gone_branches:
            items.append(f"{len(gone_branches)} gone branch(es)")
        if has_gc_work:
            items.append("git gc")
        print(f"  {c.cyan(check_sym)} {c.cyan('Would clean: ' + ', '.join(items))}")
        print(
            f"  {c.dim(f'Completed in {elapsed:.1f}s  {dot}  git-doctor v{SCRIPT_VERSION}')}"
        )
        print(c.cyan(f"  {h_double * 60}"))
        print()
        return 0

    # ── Confirm ──
    print()
    branch_count = len(stale_branches) + len(gone_branches)
    confirm_msg = f"Delete {branch_count} branch(es)" if branch_count else "Run"
    if has_gc_work and branch_count:
        confirm_msg += " and run git gc"
    elif has_gc_work:
        confirm_msg = "Run git gc"
    confirm_msg += "?"

    if not _confirm(confirm_msg):
        print()
        print(f"  {c.yellow(warn_sym)} {c.yellow('Cancelled')}")
        print()
        return 0

    # ── Execute ──
    sec_border = h_line * 60
    print()
    print(c.cyan(f"  {tl}{sec_border}{tr}"))
    print(f"  {c.cyan(vl)} {c.bold('Results')}")
    print(c.cyan(f"  {bl}{sec_border}{br}"))

    deleted = 0
    failed = 0

    # Delete stale branches
    if stale_branches:
        print()
        print(f"    {c.bold('Stale branches:')}")
        for b in stale_branches:
            name = b["name"]
            code, _, err = _run_git(["branch", "-d", name])
            if code == 0:
                print(f"      {c.green(check_sym)} {name}")
                deleted += 1
            else:
                # Try force-delete if branch wasn't merged
                code2, _, err2 = _run_git(["branch", "-D", name])
                if code2 == 0:
                    print(
                        f"      {c.green(check_sym)} {name}"
                        f"  {c.dim('(force — not fully merged)')}"
                    )
                    deleted += 1
                else:
                    print(f"      {c.red(cross_sym)} {name}  {c.red(err2 or err)}")
                    failed += 1

    # Delete gone branches
    if gone_branches:
        print()
        print(f"    {c.bold('Gone branches:')}")
        for name in gone_branches:
            code, _, err = _run_git(["branch", "-d", name])
            if code == 0:
                print(f"      {c.green(check_sym)} {name}")
                deleted += 1
            else:
                code2, _, err2 = _run_git(["branch", "-D", name])
                if code2 == 0:
                    print(
                        f"      {c.green(check_sym)} {name}"
                        f"  {c.dim('(force — not fully merged)')}"
                    )
                    deleted += 1
                else:
                    print(f"      {c.red(cross_sym)} {name}  {c.red(err2 or err)}")
                    failed += 1

    # Run git gc
    gc_success = False
    if has_gc_work:
        print()
        print(f"    {c.bold('Housekeeping:')}")
        code, out, err = _run_git(["gc", "--auto", "--prune=now"], timeout=60)
        if code == 0:
            print(f"      {c.green(check_sym)} git gc completed")
            gc_success = True
        else:
            print(f"      {c.red(cross_sym)} git gc failed: {c.red(err)}")
            failed += 1

    # ── Summary ──
    elapsed = time.monotonic() - elapsed_start
    print()
    print(c.cyan(f"  {h_double * 60}"))
    print()

    parts: list[str] = []
    if deleted > 0:
        parts.append(f"{deleted} branch(es) deleted")
    if gc_success:
        parts.append("gc completed")

    if failed == 0:
        summary = ", ".join(parts) if parts else "cleanup completed"
        print(f"  {c.green(check_sym)} {c.green(summary)}")
    else:
        summary = ", ".join(parts) if parts else ""
        print(f"  {c.red(cross_sym)} {c.red(f'{failed} failed')}  {c.dim(summary)}")
    print()
    print(
        f"  {c.dim(f'Completed in {elapsed:.1f}s  {dot}  git-doctor v{SCRIPT_VERSION}')}"
    )
    print()
    print(c.cyan(f"  {h_double * 60}"))

    # ── Recommendations ──
    print()
    print(
        f"  {c.dim(dot)} {c.dim('Tip: Run')} {c.cyan('--refresh')} "
        f"{c.dim('to update remote refs and tags')}"
    )
    print(
        f"  {c.dim('  ')} {c.cyan('--apply-recommended-minimal')} "
        f"{c.dim('to apply core recommended git configs')}"
    )
    print()
    print(
        f"  {c.dim(dot)} {c.dim('To automate what --cleanup reduces, set these git configs:')}"
    )
    print(
        f"    {c.dim('git config --global fetch.prune true')}"
        f"       {c.dim('# auto-prune stale remote refs')}"
    )
    print(
        f"    {c.dim('git config --global fetch.prunetags true')}"
        f"   {c.dim('# auto-prune stale remote tags')}"
    )
    print(
        f"    {c.dim('git config --global gc.auto 6700')}"
        f"        {c.dim('# auto garbage-collect (default threshold)')}"
    )
    print(
        f"  {c.dim(dot)} {c.dim('Run')} {c.cyan('--export-config')} "
        f"{c.dim('to see all configs, or')} {c.cyan('--apply-recommended-minimal')} "
        f"{c.dim('to apply them')}"
    )
    print()

    return 1 if failed > 0 else 0


def create_new_branch(*, color: bool | None = None, dry_run: bool = False) -> int:
    """Interactive branch creation workflow.

    Walks the user through creating a branch off ``origin/main``,
    pushing it with upstream tracking, and printing a summary of
    every command that ran.

    Args:
        color: Force color on/off, or None for auto-detect.
        dry_run: If True, show what commands would run without executing.

    Returns:
        Exit code: 0 on success, 1 on failure.
    """
    use_color = color if color is not None else _supports_color(sys.stdout)
    use_unicode = _supports_unicode(sys.stdout)
    sym = _unicode_symbols(sys.stdout)
    c = Colors(enabled=use_color)
    check = sym.get("check", "+")
    cross = sym.get("cross", "x")
    h_line = "\u2500" if use_unicode else "-"
    h_double = "\u2550" if use_unicode else "="
    tl_d = "\u2554" if use_unicode else "+"
    tr_d = "\u2557" if use_unicode else "+"
    bl_d = "\u255a" if use_unicode else "+"
    br_d = "\u255d" if use_unicode else "+"
    vl_d = "\u2551" if use_unicode else "|"
    tl = "\u250c" if use_unicode else "+"
    tr = "\u2510" if use_unicode else "+"
    bl = "\u2514" if use_unicode else "+"
    br = "\u2518" if use_unicode else "+"
    vl = "\u2502" if use_unicode else "|"
    dot = "\u2022" if use_unicode else "*"

    # ── Title ──
    mode_label = " (dry run)" if dry_run else ""
    border = h_double * 60
    print()
    print(c.bold(c.cyan(f"  {tl_d}{border}{tr_d}")))
    print(
        f"  {c.bold(c.cyan(vl_d))} {c.bold(c.cyan('New Branch Creation'))}"
        f"{c.dim(mode_label)}"
    )
    print(c.bold(c.cyan(f"  {bl_d}{border}{br_d}")))
    print()

    # ── Prefix selection ──
    print(f"  {c.bold('Select a branch prefix:')}")
    print()
    for i, (prefix, desc) in enumerate(_BRANCH_PREFIXES, 1):
        print(f"    {c.cyan(str(i).rjust(2))}. {prefix:{14}s} {c.dim(desc)}")
    print()
    choice = _prompt("Choose a prefix (number or type your own)", default="1")

    # Resolve prefix
    if choice.isdigit() and 1 <= int(choice) <= len(_BRANCH_PREFIXES):
        prefix = _BRANCH_PREFIXES[int(choice) - 1][0]
    else:
        # User typed a custom prefix — ensure it ends with /
        prefix = choice if choice.endswith("/") else f"{choice}/"

    # ── Branch name ──
    print()
    slug = _prompt(f"Branch name (after {c.cyan(prefix)})")
    if not slug:
        print(f"\n  {c.red(cross)} Branch name cannot be empty.")
        return 1

    # Sanitise: lowercase, replace spaces/underscores with hyphens
    # TODO (template users): Adjust sanitisation rules if your team uses
    #   uppercase, underscores, or other characters in branch names.
    slug = re.sub(r"[\s_]+", "-", slug.strip().lower())
    slug = re.sub(r"[^a-z0-9\-/.]", "", slug)
    branch_name = f"{prefix}{slug}"

    # Confirm
    print()
    print(f"  Branch to create: {c.bold(c.green(branch_name))}")
    print()
    confirm = _prompt("Proceed? (Y/n)", default="Y")
    if confirm.lower() not in ("y", "yes", ""):
        print(f"\n  {c.dim('Cancelled.')}")
        return 0

    # ── Execute commands ──
    steps: list[tuple[str, list[str], str]] = [
        (
            "Switch to main branch",
            ["switch", "main"],
            "git switch main",
        ),
        (
            "Update main (fast-forward only)",
            ["pull", "--ff-only"],
            "git pull --ff-only",
        ),
        (
            "Fetch latest commits from remote",
            ["fetch", "origin"],
            "git fetch origin",
        ),
        (
            f"Create and switch to {branch_name}",
            ["switch", "-c", branch_name, "origin/main"],
            f"git switch -c {branch_name} origin/main",
        ),
        (
            "Push branch and set upstream tracking",
            ["push", "-u", "origin", "HEAD"],
            "git push -u origin HEAD",
        ),
    ]

    results: list[tuple[str, str, bool, str, str]] = []
    print()
    section_border = h_line * 60
    print(c.cyan(f"  {tl}{section_border}{tr}"))
    header_label = "Would run" if dry_run else "Running commands"
    print(f"  {c.cyan(vl)} {c.bold(header_label)}")
    print(c.cyan(f"  {bl}{section_border}{br}"))
    print()

    if dry_run:
        for description, _git_args, display_cmd in steps:
            print(f"    {c.cyan(dot)} {c.cyan(display_cmd)}")
            print(f"      {c.dim(description)}")
        print()
        print(f"  {c.dim('No changes made (dry run).')}")
        print()

        # ── Command / Status Table (dry run) ──
        dry_results = [(desc, cmd, True, "", "") for desc, _args, cmd in steps]
        cmd_col_w = max(len(cmd) for _, cmd, *_ in dry_results) + 2
        hdr_cmd = "Command"
        hdr_sts = "Status"
        cmd_col_w = max(cmd_col_w, len(hdr_cmd) + 2)
        sts_col_w = 10
        tbl_border = f"    +{h_line * (cmd_col_w + 2)}+{h_line * (sts_col_w + 2)}+"
        print(c.cyan(f"  {tl}{section_border}{tr}"))
        print(f"  {c.cyan(vl)} {c.bold('Command Results (dry run)')}")
        print(c.cyan(f"  {bl}{section_border}{br}"))
        print()
        print(tbl_border)
        hdr_cmd_padded = hdr_cmd + " " * (cmd_col_w - len(hdr_cmd))
        hdr_sts_padded = hdr_sts + " " * (sts_col_w - len(hdr_sts))
        print(f"    {vl} {c.bold(hdr_cmd_padded)} {vl} {c.bold(hdr_sts_padded)} {vl}")
        print(tbl_border)
        for _desc, cmd, *_ in dry_results:
            styled_cmd = c.cyan(cmd)
            cmd_pad = " " * (cmd_col_w - len(cmd))
            sts_text = "pending"
            styled_sts = c.dim(sts_text)
            sts_pad = " " * (sts_col_w - len(sts_text))
            print(f"    {vl} {styled_cmd}{cmd_pad} {vl} {styled_sts}{sts_pad} {vl}")
        print(tbl_border)
        print()

        # ── Glaring ready banner (dry run) ──
        banner_text = " READY FOR COMMITS ON NEW BRANCH "
        banner_pad = (58 - len(banner_text)) // 2
        banner_fill = h_double * banner_pad
        print()
        print(c.bold(c.green(f"  {tl_d}{h_double * 60}{tr_d}")))
        print(
            c.bold(
                c.green(
                    f"  {vl_d}{banner_fill}{banner_text}{banner_fill}"
                    f"{h_double * (60 - 2 * banner_pad - len(banner_text))}{vl_d}"
                )
            )
        )
        print(c.bold(c.green(f"  {bl_d}{h_double * 60}{br_d}")))
        print()
        print(f"    {c.dim('(banner shown on successful run)')}")
        print()

        # ── Next steps ──
        print(f"    {c.bold('Next steps:')}")
        print(
            f"      {dot} Run {c.cyan('python scripts/git_doctor.py --new-branch')} "
            f"(without --dry-run) to execute"
        )
        print(
            f"      {dot} Start making {c.cyan('conventional commits')} "
            f"(e.g. feat:, fix:, docs:)"
        )
        print(
            f"      {dot} When ready, open a {c.cyan('Pull Request')} "
            f"targeting {c.cyan('main')}"
        )
        print()

        # ── Recommended Scripts (dry run) ──
        _nb_ui = UI(
            title="New Branch",
            version=SCRIPT_VERSION,
            theme=THEME,
            no_color=not use_color,
        )
        _nb_ui.recommended_scripts(
            [
                "git_doctor",
                "repo_doctor",
                "env_doctor",
                "doctor",
                "env_inspect",
                "check_python_support",
            ],
            preamble="Scripts that complement branch workflows.",
        )
        print()

        return 0

    failed = False
    for description, git_args, display_cmd in steps:
        if failed:
            results.append((description, display_cmd, False, "", "skipped"))
            print(f"    {c.dim('--')} {c.dim(display_cmd):40s} {c.dim('skipped')}")
            continue

        code, out, err = _run_git(git_args)
        ok = code == 0
        if not ok:
            failed = True
        icon = c.green(check) if ok else c.red(cross)
        status_text = c.green("ok") if ok else c.red("failed")
        results.append((description, display_cmd, ok, out, err))
        print(f"    {icon} {display_cmd:40s} {status_text}")
        if not ok and err:
            print(f"      {c.red(err)}")

    # ── Verify final branch ──
    print()
    code, final_branch, _ = _run_git(["branch", "--show-current"])
    _code2, status_out, _ = _run_git(["status", "-sb"])

    # ── Command / Status Table ──
    print(c.cyan(f"  {tl}{section_border}{tr}"))
    print(f"  {c.cyan(vl)} {c.bold('Command Results')}")
    print(c.cyan(f"  {bl}{section_border}{br}"))
    print()

    # Calculate column widths for aligned table
    cmd_col_w = max(len(cmd) for _, cmd, *_ in results) + 2
    hdr_cmd = "Command"
    hdr_sts = "Status"
    cmd_col_w = max(cmd_col_w, len(hdr_cmd) + 2)
    sts_col_w = 10
    tbl_border = f"    +{h_line * (cmd_col_w + 2)}+{h_line * (sts_col_w + 2)}+"
    print(tbl_border)
    hdr_cmd_padded = hdr_cmd + " " * (cmd_col_w - len(hdr_cmd))
    hdr_sts_padded = hdr_sts + " " * (sts_col_w - len(hdr_sts))
    print(f"    {vl} {c.bold(hdr_cmd_padded)} {vl} {c.bold(hdr_sts_padded)} {vl}")
    print(tbl_border)
    for _desc, cmd, ok, _out, err_msg in results:
        if err_msg == "skipped":
            sts_text = "skipped"
            styled_sts = c.dim(sts_text)
        elif ok:
            sts_text = "success"
            styled_sts = c.green(sts_text)
        else:
            sts_text = "failed"
            styled_sts = c.red(sts_text)
        styled_cmd = c.cyan(cmd)
        cmd_pad = " " * (cmd_col_w - len(cmd))
        sts_pad = " " * (sts_col_w - len(sts_text))
        print(f"    {vl} {styled_cmd}{cmd_pad} {vl} {styled_sts}{sts_pad} {vl}")
    print(tbl_border)
    print()

    # ── Summary ──
    print(c.cyan(f"  {tl}{section_border}{tr}"))
    print(f"  {c.cyan(vl)} {c.bold('Summary')}")
    print(c.cyan(f"  {bl}{section_border}{br}"))
    print()

    if not failed:
        print(f"    {c.green(check)} {c.bold('New branch created successfully')}")
    else:
        print(f"    {c.red(cross)} {c.bold('Branch creation failed')}")

    print(f"    {dot} Branch:  {c.bold(c.green(final_branch or branch_name))}")
    if status_out:
        print(f"    {dot} Status:  {c.dim(status_out.splitlines()[0])}")
    print()

    # ── Glaring ready-for-commits banner ──
    if not failed:
        banner_text = " READY FOR COMMITS ON NEW BRANCH "
        banner_pad = (58 - len(banner_text)) // 2
        banner_fill = h_double * banner_pad
        print()
        print(c.bold(c.green(f"  {tl_d}{h_double * 60}{tr_d}")))
        print(
            c.bold(
                c.green(
                    f"  {vl_d}{banner_fill}{banner_text}{banner_fill}"
                    f"{h_double * (60 - 2 * banner_pad - len(banner_text))}{vl_d}"
                )
            )
        )
        print(c.bold(c.green(f"  {bl_d}{h_double * 60}{br_d}")))
        print()

    # ── Recommendations ──
    print(f"    {c.bold('Next steps:')}")
    print(
        f"      {dot} Run {c.cyan('python scripts/git_doctor.py')} or "
        f"{c.cyan('task doctor:git')} to see full branch diagnostics"
    )
    print(
        f"      {dot} Start making {c.cyan('conventional commits')} "
        f"(e.g. feat:, fix:, docs:)"
    )
    print(
        f"      {dot} When ready, open a {c.cyan('Pull Request')} "
        f"targeting {c.cyan('main')}"
    )
    print()

    # ── Recommended Scripts ──
    _nb_ui = UI(
        title="New Branch",
        version=SCRIPT_VERSION,
        theme=THEME,
        no_color=not use_color,
    )
    _nb_ui.recommended_scripts(
        [
            "git_doctor",
            "repo_doctor",
            "env_doctor",
            "doctor",
            "env_inspect",
            "check_python_support",
        ],
        preamble="Scripts that complement branch workflows.",
    )
    print()

    return 1 if failed else 0


# ---------------------------------------------------------------------------
# --view-commits: detailed commit report for current working branch
# ---------------------------------------------------------------------------


def show_commits(
    *,
    color: bool | None = None,
    markdown: bool = False,
) -> int:
    """Display detailed commit information for the current working branch.

    Shows branch origin, all commits with SHAs, messages, authors, dates,
    per-file stats, total insertions/deletions, and potential conflicts
    with the default branch.  Output follows the same dashboard style as
    the default ``git_doctor`` output.

    When *markdown* is True, writes a Markdown file (``commit-report.md``)
    with a table of contents linking to each commit section via anchor links.

    Args:
        color: Force color on/off, or None for auto-detect.
        markdown: If True, write a Markdown file instead of terminal output.

    Returns:
        Exit code: 0 always (informational output).
    """
    if markdown:
        return _show_commits_markdown()
    return _show_commits_terminal(color=color)


def _show_commits_markdown() -> int:
    """Write a Markdown commit report file with a clickable table of contents."""
    generated_at = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    current_branch = get_current_branch()
    default_branch = get_default_branch()
    origin_info = get_branch_origin_point()

    bar = ProgressBar(total=1, label="Collecting commit data", color="cyan")
    commits = get_detailed_branch_commits(progress_bar=bar)
    bar.finish()

    with Spinner("Checking for conflicts", log_interval=5):
        conflict_files = get_branch_conflict_files()

    total_ins = sum(int(cm.get("total_insertions", 0)) for cm in commits)
    total_del = sum(int(cm.get("total_deletions", 0)) for cm in commits)

    # Build GitHub commit URL base from remote
    remote_url = get_remote_url()
    commit_url_base = ""
    slug = extract_repo_slug(remote_url)
    if slug:
        commit_url_base = f"https://github.com/{slug}/commit/"

    # Count unique authors and files touched
    authors = {str(cm.get("author", "")) for cm in commits if cm.get("author")}
    author_label = "Author" if len(authors) == 1 else "Authors"
    all_files: set[str] = set()
    for cm in commits:
        files = cm.get("files", [])
        if isinstance(files, list):
            for f in files:
                fname = str(f.get("file", ""))
                if fname:
                    all_files.add(fname)

    def _pad_table(
        rows: list[list[str]], alignments: list[str] | None = None
    ) -> list[str]:
        """Pad a table's columns so the raw Markdown source is neatly aligned.

        *rows* is a list of rows; the first row is the header.
        *alignments* is a list of 'l' or 'r' per column (default: all left).
        Returns a list of formatted Markdown lines (header + separator + data).
        """
        if not rows:
            return []
        col_count = len(rows[0])
        if alignments is None:
            alignments = ["l"] * col_count
        # Compute max width per column
        widths = [0] * col_count
        for row in rows:
            for j, cell in enumerate(row):
                widths[j] = max(widths[j], len(cell))
        # Build lines
        out: list[str] = []
        for idx, row in enumerate(rows):
            cells: list[str] = []
            for j, cell in enumerate(row):
                if alignments[j] == "r":
                    cells.append(cell.rjust(widths[j]))
                else:
                    cells.append(cell.ljust(widths[j]))
            out.append("| " + " | ".join(cells) + " |")
            if idx == 0:
                # Separator row
                sep_cells: list[str] = []
                for j in range(col_count):
                    if alignments[j] == "r":
                        sep_cells.append("-" * (widths[j] - 1) + ":")
                    else:
                        sep_cells.append(":" + "-" * (widths[j] - 1))
                out.append("| " + " | ".join(sep_cells) + " |")
        return out

    lines: list[str] = []
    a = lines.append

    a(f"# Commit Report -- {current_branch}")
    a("")
    a(f"> Generated by `git_doctor.py --view-commits --markdown` v{SCRIPT_VERSION}")
    a(f"> {generated_at}")
    a("")

    # ── Quick Stats ──
    a("## Quick Stats")
    a("")
    stat_rows: list[list[str]] = [
        ["Metric", "Value"],
        ["Commits", str(len(commits))],
        ["Insertions", f"+{total_ins}"],
        ["Deletions", f"-{total_del}"],
        ["Files touched", str(len(all_files))],
        [author_label, str(len(authors))],
    ]
    if conflict_files:
        stat_rows.append(["**Conflicts**", f"**{len(conflict_files)}**"])
    else:
        stat_rows.append(["Conflicts", "0"])
    for ln in _pad_table(stat_rows, ["l", "r"]):
        a(ln)
    a("")

    # ── Branch Overview ──
    a("## Branch Overview")
    a("")
    overview_rows: list[list[str]] = [
        ["Field", "Value"],
        ["**Current working branch**", f"`{current_branch}`"],
        ["**Origin branch**", f"`{origin_info.get('origin_branch', '(unknown)')}`"],
    ]
    merge_base_short = origin_info.get("merge_base_short", "")
    merge_base_date = origin_info.get("merge_base_date", "")
    if merge_base_short:
        overview_rows.append(
            [
                "**Merge base**",
                f"`{merge_base_short}` ({merge_base_date}) -- last common ancestor with `{default_branch}`",
            ]
        )
    overview_rows.append(["**Total commits**", str(len(commits))])
    overview_rows.append(["**Insertions / Deletions**", f"+{total_ins} / -{total_del}"])
    for ln in _pad_table(overview_rows, ["l", "l"]):
        a(ln)
    a("")

    # ── Table of Contents ──
    if commits:
        a("## Table of Contents")
        a("")
        toc_rows: list[list[str]] = [["#", "SHA", "Message"]]
        for i, cm in enumerate(commits, 1):
            sha_short = str(cm["sha_short"])
            msg = str(cm["message"])
            toc_rows.append(
                [
                    str(i),
                    f"[`{sha_short}`](#commit-{i})",
                    msg,
                ]
            )
        for ln in _pad_table(toc_rows, ["r", "l", "l"]):
            a(ln)
        a("")

    # ── Detailed Commits ──
    if commits:
        a("## Commits")
        a("")
        for i, cm in enumerate(commits, 1):
            sha_short = str(cm["sha_short"])
            sha_full = str(cm["sha"])
            msg = str(cm["message"])
            author = str(cm.get("author", ""))
            dt = str(cm.get("datetime", ""))
            date_rel = str(cm.get("date_relative", ""))
            cm_ins = int(cm.get("total_insertions", 0))
            cm_del = int(cm.get("total_deletions", 0))
            files = cm.get("files", [])
            if not isinstance(files, list):
                files = []

            sha_link = (
                f"[`{sha_full}`]({commit_url_base}{sha_full})"
                if commit_url_base
                else f"`{sha_full}`"
            )

            # HTML anchor for TOC linking
            a(f'<a id="commit-{i}"></a>')
            a("")
            a(f"### [{i}/{len(commits)}] `{sha_short}` -- {msg}")
            a("")
            detail_rows: list[list[str]] = [
                ["Field", "Value"],
                ["**SHA**", sha_link],
                ["**Author**", author],
                ["**Date**", f"{dt} ({date_rel})"],
                [
                    "**Insertions / Deletions**",
                    f"+{cm_ins} / -{cm_del} in {len(files)} file(s)",
                ],
            ]
            for ln in _pad_table(detail_rows, ["l", "l"]):
                a(ln)
            a("")

            if files:
                file_rows: list[list[str]] = [["File Name", "Insertions", "Deletions"]]
                for f in files:
                    fname = str(f.get("file", ""))
                    fins = int(f.get("insertions", 0))
                    fdel = int(f.get("deletions", 0))
                    file_rows.append([f"`{fname}`", f"+{fins}", f"-{fdel}"])
                for ln in _pad_table(file_rows, ["l", "r", "r"]):
                    a(ln)
                a("")

            # Visual separator between commits (except after the last one)
            if i < len(commits):
                a("---")
                a("")

    # Separator before conflicts section
    a("---")
    a("")

    # ── Conflicts ──
    a(f"## Conflicts with `{default_branch}`")
    a("")
    if conflict_files:
        a(
            f"**{len(conflict_files)} file(s)** would conflict when merging `{default_branch}`:"
        )
        a("")
        for cf in conflict_files:
            a(f"- `{cf}`")
        a("")
        _append_conflict_guidance(lines, default_branch, conflict_files)
    else:
        a(f"No conflicts detected with `{default_branch}`.")
    a("")

    # ── Summary Footer ──
    a("---")
    a("")
    a("## Summary")
    a("")
    summary_rows: list[list[str]] = [
        ["Metric", "Value"],
        ["Total commits", str(len(commits))],
        ["Total insertions", f"+{total_ins}"],
        ["Total deletions", f"-{total_del}"],
        [
            "Net change",
            f"+{total_ins - total_del}"
            if total_ins >= total_del
            else str(total_ins - total_del),
        ],
        ["Files touched", str(len(all_files))],
        [author_label, ", ".join(sorted(authors)) if authors else "(none)"],
        ["Conflicts", str(len(conflict_files))],
    ]
    for ln in _pad_table(summary_rows, ["l", "r"]):
        a(ln)
    a("")
    a(
        f"*Generated by `git_doctor.py --view-commits --markdown` "
        f"v{SCRIPT_VERSION} at {generated_at}*"
    )

    # Write to file
    out_path = ROOT / "commit-report.md"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Commit report written to: {out_path}")
    return 0


def _append_conflict_guidance(
    lines: list[str],
    default_branch: str,
    conflict_files: list[str],
) -> None:
    """Append conflict resolution guidance to a Markdown line list."""
    a = lines.append
    a("### How to Resolve")
    a("")
    a("**Option 1 — Rebase onto the latest default branch (preferred):**")
    a("")
    a("```bash")
    a(f"git fetch origin {default_branch}")
    a(f"git rebase origin/{default_branch}")
    a("# Resolve conflicts in each file, then:")
    a("git add <resolved-file>")
    a("git rebase --continue")
    a("```")
    a("")
    a("**Option 2 — Merge the default branch into your branch:**")
    a("")
    a("```bash")
    a(f"git fetch origin {default_branch}")
    a(f"git merge origin/{default_branch}")
    a("# Resolve conflicts in each file, then:")
    a("git add <resolved-file>")
    a("git commit")
    a("```")
    a("")
    a("**Tips:**")
    a("")
    a(
        f"- Run `git diff origin/{default_branch} -- <file>` to preview what changed on `{default_branch}`"
    )
    a("- Use `git mergetool` to open a visual merge tool")
    a("- If midway through a bad rebase, abort with `git rebase --abort`")
    a(
        f"- The {len(conflict_files)} conflicting file(s) listed above are the only ones that need manual resolution"
    )
    a("")


def _show_commits_terminal(*, color: bool | None = None) -> int:
    """Display detailed commit report with terminal formatting."""
    elapsed_start = time.monotonic()
    use_color = color if color is not None else _supports_color(sys.stdout)
    use_unicode = _supports_unicode(sys.stdout)
    sym = _unicode_symbols(sys.stdout)
    c = Colors(enabled=use_color)

    # Box-drawing characters
    h_line = "\u2500" if use_unicode else "-"
    h_double = "\u2550" if use_unicode else "="
    tl = "\u250c" if use_unicode else "+"
    tr = "\u2510" if use_unicode else "+"
    bl = "\u2514" if use_unicode else "+"
    br = "\u2518" if use_unicode else "+"
    vl = "\u2502" if use_unicode else "|"
    tl_d = "\u2554" if use_unicode else "+"
    tr_d = "\u2557" if use_unicode else "+"
    bl_d = "\u255a" if use_unicode else "+"
    br_d = "\u255d" if use_unicode else "+"
    vl_d = "\u2551" if use_unicode else "|"
    dot = "\u2022" if use_unicode else "*"
    dash = sym["dash"]
    check_sym = sym.get("check", "+")
    cross_sym = sym.get("cross", "x")
    warn_sym = sym.get("warn", "!")
    arrow = sym.get("arrow", "->")

    # OSC 8 hyperlink helpers (clickable links in modern terminals)
    remote_url = get_remote_url()
    commit_url_base = ""
    slug = extract_repo_slug(remote_url)
    if slug:
        commit_url_base = f"https://github.com/{slug}/commit/"

    def _osc_link(url: str, text: str) -> str:
        """Wrap *text* in an OSC 8 hyperlink when color is enabled."""
        if not use_color or not url:
            return text
        return f"\033]8;;{url}\033\\{text}\033]8;;\033\\"

    def _section(title: str) -> None:
        border = h_line * 60
        print()
        print(c.cyan(f"  {tl}{border}{tr}"))
        print(f"  {c.cyan(vl)} {c.bold(title)}")
        print(c.cyan(f"  {bl}{border}{br}"))
        print()

    def _kv(label: str, value: str, width: int = 26, indent: int = 4) -> None:
        pad = " " * indent
        print(f"{pad}{label + ':':{width}s} {value}")

    def _kv_hint(hint: str, width: int = 26, indent: int = 4) -> None:
        pad = " " * indent
        print(f"{pad}{'':{width}s} {c.dim(hint)}")

    # Collect data
    current_branch = get_current_branch()
    default_branch = get_default_branch()
    origin_info = get_branch_origin_point()

    # Fetch commit details with a visible progress bar (the per-commit
    # diff-tree calls are the slow part — one git invocation per SHA).
    bar = ProgressBar(total=1, label="Collecting commit data", color="cyan")
    commits = get_detailed_branch_commits(progress_bar=bar)
    bar.finish()

    with Spinner("Checking for conflicts", log_interval=5):
        conflict_files = get_branch_conflict_files()

    # Compute totals
    total_ins = sum(int(cm.get("total_insertions", 0)) for cm in commits)
    total_del = sum(int(cm.get("total_deletions", 0)) for cm in commits)

    # Count unique authors and files touched
    authors = {str(cm.get("author", "")) for cm in commits if cm.get("author")}
    all_files: set[str] = set()
    for cm in commits:
        files = cm.get("files", [])
        if isinstance(files, list):
            for f in files:
                fname = str(f.get("file", ""))
                if fname:
                    all_files.add(fname)

    # ── Header ──
    header_border = h_double * 60
    print()
    print(c.bold(c.cyan(f"  {tl_d}{header_border}{tr_d}")))
    print(
        f"  {c.bold(c.cyan(vl_d))} "
        f"{c.bold(c.cyan('Commit Report'))} {dash} "
        f"{c.green(current_branch)}  {c.dim(f'v{SCRIPT_VERSION}')}"
    )
    print(c.bold(c.cyan(f"  {bl_d}{header_border}{br_d}")))

    # ── Quick Stats (below header, above branch overview) ──
    author_label = "author" if len(authors) == 1 else "authors"
    print()
    print(
        f"    {c.bold(str(len(commits)))} commits"
        f"  {c.dim(dot)}  "
        f"{c.green(f'+{total_ins}')} / {c.red(f'-{total_del}')}"
        f"  {c.dim(dot)}  "
        f"{c.bold(str(len(all_files)))} files touched"
        f"  {c.dim(dot)}  "
        f"{c.bold(str(len(authors)))} {author_label}"
    )
    if conflict_files:
        print(
            f"    {c.red(f'{warn_sym} {len(conflict_files)} conflict(s) with {default_branch}')}"
        )

    # Thin decorative separator between facets
    _thin_dot = "\u00b7" if use_unicode else "."

    def _facet_sep(indent: int = 4) -> None:
        pad = " " * indent
        print(f"{pad}{c.green(f'{_thin_dot} ' * 20)}")

    # ── Branch Overview ──
    _section(f"Branch Overview: {c.green(current_branch)}")
    _kv("Current working branch", c.green(current_branch))
    _facet_sep()
    _kv(
        "Origin branch",
        f"{origin_info.get('origin_branch', '(unknown)')}  {c.dim('(created from)')}",
    )
    _facet_sep()
    merge_base_short = origin_info.get("merge_base_short", "")
    merge_base_date = origin_info.get("merge_base_date", "")
    if merge_base_short:
        _kv(
            "Merge base",
            f"{c.yellow(merge_base_short)}  {c.dim(merge_base_date)}"
            f"  {c.dim(f'{arrow} divergence point from {default_branch}')}",
        )
        _facet_sep()
    _kv("Total commits on branch", str(len(commits)))
    _facet_sep()
    _kv(
        "Insertions / Deletions",
        f"{c.green(f'+{total_ins}')} / {c.red(f'-{total_del}')}"
        f"  {c.dim('across all commits')}",
    )

    # ── All Commit SHAs ──
    if commits:
        _section("Commit SHAs (quick reference)")
        # Note about GitHub links
        if commit_url_base:
            print(
                f"    {c.yellow(f'{warn_sym} GitHub links open the commit on github.com')}"
            )
            print(
                f"    {c.yellow(f'{warn_sym} Commits not yet pushed will return a 404')}"
            )
            print()
        # Table header — pad plain text first, then colorize
        print(
            f"    {c.bold('#'.rjust(4))}  "
            f"{c.bold('SHA'.ljust(10))}  "
            f"{c.bold('Message'.ljust(50))}  "
            f"{c.bold('GitHub')}"
        )
        print(f"    {h_line * 4}  {h_line * 10}  {h_line * 50}  {h_line * 6}")
        for i, cm in enumerate(commits, 1):
            sha_short = str(cm["sha_short"])
            sha_full = str(cm["sha"])
            msg = str(cm["message"])
            if len(msg) > 50:
                msg = msg[:47] + "..."
            num = c.cyan(c.bold(str(i).rjust(4)))
            sha_url = f"{commit_url_base}{sha_full}" if commit_url_base else ""
            sha_display = c.yellow(sha_short.ljust(10))
            gh_link = _osc_link(sha_url, c.magenta("view")) if sha_url else c.dim("n/a")
            print(f"    {num}  {sha_display}  {msg:<50s}  {gh_link}")
        print()

    # ── Detailed Commits ──
    if commits:
        _section(f"Detailed Commits ({len(commits)} total)")
        for i, cm in enumerate(commits, 1):
            sha_short = str(cm["sha_short"])
            sha_full = str(cm["sha"])
            msg = str(cm["message"])
            author = str(cm.get("author", ""))
            dt = str(cm.get("datetime", ""))
            date_rel = str(cm.get("date_relative", ""))
            cm_ins = int(cm.get("total_insertions", 0))
            cm_del = int(cm.get("total_deletions", 0))
            files = cm.get("files", [])
            if not isinstance(files, list):
                files = []

            # Commit header with number merged into title
            commit_border = h_line * 56
            print(f"    {c.cyan(commit_border)}")
            sha_url = f"{commit_url_base}{sha_full}" if commit_url_base else ""
            sha_display = _osc_link(sha_url, c.bold(c.yellow(sha_short)))
            idx_label = c.dim(f"[{c.cyan(c.bold(str(i)))}/{len(commits)}]")
            print(f"    {idx_label} {sha_display}  {c.bold(msg)}")
            print(f"    {c.cyan(commit_border)}")
            print()
            print(f"      {'SHA:':<24s} {c.dim(sha_full)}")
            _facet_sep(6)
            print(f"      {'Author:':<24s} {author}")
            _facet_sep(6)
            print(f"      {'Date:':<24s} {dt}  {c.dim(f'({date_rel})')}")
            _facet_sep(6)
            print(
                f"      {'Insertions / Deletions:':<24s} "
                f"{c.green(f'+{cm_ins}')} / {c.red(f'-{cm_del}')}"
                f"  {c.dim(f'in {len(files)} file(s)')}"
            )

            # Per-file stats as a table
            if files:
                print()
                file_w = max(len(str(f.get("file", ""))) for f in files)
                file_w = min(max(file_w, 10), 50)
                hdr_name = "File Name"
                hdr_ins = "Insertions"
                hdr_del = "Deletions"
                print(
                    f"      {c.bold(f'{hdr_name:<{file_w}s}')}  "
                    f"{c.bold(f'{hdr_ins:>10s}')}  "
                    f"{c.bold(f'{hdr_del:>10s}')}"
                )
                print(f"      {h_line * file_w}  {h_line * 10}  {h_line * 10}")
                for f in files:
                    fname = str(f.get("file", ""))
                    fins = int(f.get("insertions", 0))
                    fdel = int(f.get("deletions", 0))
                    display_name = (
                        fname[: file_w - 1] + "\u2026" if len(fname) > file_w else fname
                    )
                    ins_s = c.green(f"+{fins}".rjust(10)) if fins else "+0".rjust(10)
                    del_s = c.red(f"-{fdel}".rjust(10)) if fdel else "-0".rjust(10)
                    print(f"      {display_name:<{file_w}s}  {ins_s}  {del_s}")

            print()
            print()

    # ── Conflicts ──
    _section(f"Conflicts with {default_branch}")
    if conflict_files:
        print(
            f"    {c.red(cross_sym)} "
            f"{c.red(f'{len(conflict_files)} file(s) would conflict when merging {default_branch}')}"
        )
        print()
        for cf in conflict_files:
            print(f"      {c.red(warn_sym)} {cf}")
        print()
        # Conflict resolution guidance
        print(f"    {c.bold('How to resolve:')}")
        print()
        print(
            f"    {c.cyan(f'{dot} Option 1 — Rebase (preferred for linear history):')}"
        )
        print(f"        git fetch origin {default_branch}")
        print(f"        git rebase origin/{default_branch}")
        print(
            f"        {c.dim('# resolve conflicts, then: git add <file> && git rebase --continue')}"
        )
        print()
        print(f"    {c.cyan(f'{dot} Option 2 — Merge:')}")
        print(f"        git fetch origin {default_branch}")
        print(f"        git merge origin/{default_branch}")
        print(
            f"        {c.dim('# resolve conflicts, then: git add <file> && git commit')}"
        )
        print()
        print(
            f"    {c.dim(f'{dot} Tip: use git mergetool for visual conflict resolution')}"
        )
        print(
            f"    {c.dim(f'{dot} Tip: git rebase --abort to bail out of a bad rebase')}"
        )
        print(
            f"    {c.dim(f'{dot} Tip: git diff origin/{default_branch} -- <file> to preview upstream changes')}"
        )
    else:
        print(
            f"    {c.green(check_sym)} "
            f"{c.green(f'No conflicts detected with {default_branch}')}"
        )

    # ── Recommended Scripts ──
    _vc_ui = UI(
        title="Git Doctor", version=SCRIPT_VERSION, theme=THEME, no_color=not use_color
    )
    _vc_ui.recommended_scripts(
        [
            "repo_sauron",
            "env_inspect",
            "check_python_support",
            "repo_doctor",
            "dep_versions",
            "env_doctor",
            "doctor",
        ],
        preamble="Scripts that expand on repository health and diagnostics.",
    )

    # ── Summary ──
    elapsed = time.monotonic() - elapsed_start
    print()
    print(c.cyan(f"  {h_double * 60}"))
    print(
        f"  {c.bold(str(len(commits)))} commit(s)"
        f"  {c.cyan(dot)}"
        f"  {c.green(f'+{total_ins}')} / {c.red(f'-{total_del}')}"
        f"  {c.cyan(dot)}"
        f"  {c.dim(f'Completed in {elapsed:.1f}s')}"
        f"  {c.cyan(dot)}"
        f"  {c.dim(f'git-doctor v{SCRIPT_VERSION}')}"
    )
    print(c.cyan(f"  {h_double * 60}"))
    print()

    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    """Entry point for git_doctor.

    Returns:
        Exit code from run().
    """
    parser = argparse.ArgumentParser(
        description="Git-focused health check and information dashboard.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {SCRIPT_VERSION}",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON (for CI integration)",
    )
    parser.add_argument(
        "--export-config",
        nargs="?",
        const="git-config-reference.md",
        default=None,
        metavar="PATH",
        help="Export comprehensive git config reference to a Markdown file "
        "(default: git-config-reference.md). NOTE: overwrites the file on each run.",
    )
    parser.add_argument(
        "--apply-from",
        default=None,
        metavar="PATH",
        help="Apply desired values from an edited config reference file "
        "(exported with --export-config). Both 'Desired value' and "
        "'Desired scope' columns must be set for an entry to apply.",
    )
    parser.add_argument(
        "--apply-recommended",
        action="store_true",
        help="Apply ALL catalog recommended values and scopes, overwriting "
        "existing values. Resets config to the catalog baseline. "
        "Use --dry-run to preview. See git-config-reference.md for details.",
    )
    parser.add_argument(
        "--apply-recommended-minimal",
        action="store_true",
        help="Apply only the core minimal set of recommended configs "
        f"({len(MINIMAL_RECOMMENDED_CONFIGS)} high-impact keys). "
        "Safer alternative to --apply-recommended for first-time setup. "
        "Use --dry-run to preview.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="With --apply-from, --apply-recommended, "
        "--apply-recommended-minimal, --refresh, --cleanup, or "
        "--new-branch: show what would be changed without applying",
    )
    parser.add_argument(
        "--new-branch",
        action="store_true",
        help="Interactive branch creation: prompts for a name, creates the "
        "branch off origin/main, pushes with upstream tracking, and "
        "prints a summary of all commands executed",
    )
    parser.add_argument(
        "--watch",
        nargs="?",
        const=10,
        default=None,
        type=int,
        metavar="SECONDS",
        help="Re-run the dashboard every N seconds (default: 10). "
        "Press Ctrl+C to stop.",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Interactive refresh: fetch all remotes, prune stale "
        "remote-tracking refs, sync tags, and update remote HEAD. "
        "Shows a preview and asks for confirmation before running. "
        "Use --dry-run to preview without executing.",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Interactive cleanup: delete stale local branches (90+ days "
        "inactive), branches with deleted upstreams, and run git gc. "
        "Shows everything that would be deleted and asks for "
        "confirmation. Use --dry-run to preview only.",
    )
    parser.add_argument(
        "--view-commits",
        action="store_true",
        help="Show detailed commit report for the current working branch: "
        "branch origin, all SHAs, messages, authors, dates, per-file "
        "insertions/deletions, and conflict detection with the default branch. "
        "Use --markdown to write a Markdown report file instead.",
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="With --view-commits, write a Markdown commit report to "
        "commit-report.md (in the repo root) instead of terminal output. "
        "Includes quick stats, a clickable table of contents, and GitHub links.",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Quick import and arg-parse health check; exit 0 immediately",
    )
    args = parser.parse_args()

    if args.smoke:
        print(f"git_doctor {SCRIPT_VERSION}: smoke ok")
        return 0

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    # --new-branch mode: interactive branch creation and exit
    if args.new_branch:
        nb_color = False if args.no_color else None
        return create_new_branch(color=nb_color, dry_run=args.dry_run)

    # --apply-from mode: apply desired values from edited reference file
    if args.apply_from:
        apply_from_reference(args.apply_from, dry_run=args.dry_run)
        return 0

    # --apply-recommended mode: apply ALL catalog recommended values
    if args.apply_recommended:
        apply_recommended_config(dry_run=args.dry_run)
        return 0

    # --apply-recommended-minimal mode: apply core subset only
    if args.apply_recommended_minimal:
        apply_recommended_minimal_config(dry_run=args.dry_run)
        return 0

    # --view-commits mode: detailed commit report for current branch
    if args.view_commits:
        cm_color = False if args.no_color else None
        return show_commits(color=cm_color, markdown=args.markdown)

    # --refresh mode: interactive update of refs, tags, remote metadata
    if args.refresh:
        ref_color = False if args.no_color else None
        return refresh_repo(dry_run=args.dry_run, color=ref_color)

    # --cleanup mode: interactive deletion of stale branches and cruft
    if args.cleanup:
        cl_color = False if args.no_color else None
        return cleanup_repo(dry_run=args.dry_run, color=cl_color)

    color = False if args.no_color else None

    # --watch mode: re-run dashboard on an interval until Ctrl+C
    if args.watch is not None:
        interval = max(args.watch, 2)  # minimum 2 seconds
        use_color = not args.no_color and _supports_color(sys.stdout)
        use_unicode = _supports_unicode(sys.stdout)
        _c = Colors(enabled=use_color)
        _h_double = "\u2550" if use_unicode else "="
        _dot = "\u2022" if use_unicode else "*"
        _sym = _unicode_symbols(sys.stdout)
        _check_sym = _sym.get("check", "+")
        try:
            while True:
                # Clear terminal (cross-platform)
                subprocess.run(  # nosec B603
                    ["cmd", "/c", "cls"] if os.name == "nt" else ["clear"],
                    check=False,
                )
                run(color=color, output_json=args.json)
                _watch_border = _h_double * 60
                print()
                print(_c.bold(_c.cyan(f"  {_watch_border}")))
                print(
                    f"  {_c.cyan(_dot)} {_c.bold(_c.cyan(f'Watching every {interval}s'))}"
                    f"  {_c.dim('Press Ctrl+C to stop')}"
                )
                print(_c.bold(_c.cyan(f"  {_watch_border}")))
                time.sleep(interval)
        except KeyboardInterrupt:
            _stop_border = _h_double * 60
            print()
            print(_c.bold(_c.yellow(f"  {_stop_border}")))
            print(
                f"  {_c.yellow(_check_sym)} {_c.bold(_c.yellow('Watch stopped'))}"
                f"  {_c.dim('Dashboard refresh ended')}"
            )
            print(_c.bold(_c.yellow(f"  {_stop_border}")))
            print()
        return 0

    exit_code = run(color=color, output_json=args.json)

    if args.export_config:
        out_path = export_git_config_reference(args.export_config)
        use_color_ec = not args.no_color and _supports_color(sys.stdout)
        use_unicode_ec = _supports_unicode(sys.stdout)
        _ec = Colors(enabled=use_color_ec)
        _ec_h = "\u2550" if use_unicode_ec else "="
        _ec_dot = "\u2022" if use_unicode_ec else "*"
        _ec_sym = _unicode_symbols(sys.stdout)
        _ec_check = _ec_sym.get("check", "+")
        _tl = "\u2554" if use_unicode_ec else "+"
        _tr = "\u2557" if use_unicode_ec else "+"
        _bl = "\u255a" if use_unicode_ec else "+"
        _br = "\u255d" if use_unicode_ec else "+"
        _vl = "\u2551" if use_unicode_ec else "|"
        _bw = 58
        print()
        print(_ec.bold(_ec.cyan(f"  {_tl}{_ec_h * _bw}{_tr}")))
        print(
            f"  {_ec.bold(_ec.cyan(_vl))} "
            f"{_ec.green(_ec_check)} {_ec.bold(_ec.green('Git config reference exported'))}"
        )
        print(
            f"  {_ec.bold(_ec.cyan(_vl))} "
            f"{_ec_dot} {_ec.dim('File:')}  {_ec.cyan(out_path)}"
        )
        print(
            f"  {_ec.bold(_ec.cyan(_vl))} "
            f"{_ec_dot} {_ec.dim('Next:')}  Edit 'Desired value' / 'Desired scope'"
            f" columns, then run --apply-from"
        )
        print(_ec.bold(_ec.cyan(f"  {_bl}{_ec_h * _bw}{_br}")))
        print()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
