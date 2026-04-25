#!/usr/bin/env python3
"""Repo doctor — warn-only health checks for repository structure.

Reads rules from ``.repo-doctor.toml`` and reports missing files,
directories, TOML config sections, and content patterns.  Never blocks;
always exits 0.

.. note::
    This tool validates structure based on rules defined in
    ``.repo-doctor.toml`` and profiles under ``repo_doctor.d/``.
    The rules shipped with this template are specific to the
    simple-python-boilerplate project structure, but the engine
    itself is generic — any repository can define its own rules
    in ``.repo-doctor.toml``.  For general repository statistics
    (file counts, line counts, git history), use ``repo_sauron.py``
    instead.

Flags::

    --missing            Scan the working tree for files/dirs that are
                         expected by the rules but don't exist on disk.
                         This is the primary "are my repo files intact?"
                         check.  Useful after branch switches, merges, or
                         partial clones where files may be unexpectedly
                         absent.
    --staged             Inspect the git index (staging area) for files
                         that have been ``git rm``'d but not yet committed.
                         Catches accidental deletions before they land in
                         history.  Complements --missing by focusing on
                         *pending* changes rather than the working tree.
    --diff RANGE         Report deletions in a git diff range
                         (e.g. "origin/main...HEAD")
    --category NAME      Only show rules matching this category
    --min-level LEVEL    Minimum severity to display (default: warn)
    --include-info       Include info-level checks (shorthand for --min-level info)
    --profile NAME       Load additional rules from repo_doctor.d/NAME.toml
                         (repeatable; 'all' loads everything)
    --fix                Show auto-fix commands for rules that define one
    --no-hints           Hide hint lines
    --no-links           Hide link/reference lines
    --no-color           Disable colored output
    --strict             Exit non-zero when warnings are found (CI gating)
    --show-passed        Show checks that passed (in addition to warnings)
    --smoke [NAME]       Inject a synthetic failure for testing the dashboard.
                         Optionally specify a profile name whose first check
                         will be forced to fail; if omitted, a random check
                         from the loaded rules is chosen.
    --version            Print version and exit

Usage::

    python scripts/repo_doctor.py
    python scripts/repo_doctor.py --missing --staged
    python scripts/repo_doctor.py --category ci --min-level info
    python scripts/repo_doctor.py --include-info
    python scripts/repo_doctor.py --profile python --profile docs
    python scripts/repo_doctor.py --fix
    python scripts/repo_doctor.py --smoke
    python scripts/repo_doctor.py --smoke ci

    Task runner shortcuts for this script are defined in ``Taskfile.yml``.

Portability:
    Can be used in any repo with ``repo_doctor.d/`` rule profiles.
    Requires shared modules: ``_colors.py``, ``_imports.py``,
    ``_ui.py``, ``_progress.py``.
"""

from __future__ import annotations

import argparse
import ast
import logging
import os
import random
import re
import shutil
import subprocess  # nosec B404
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# TODO (template users): remove try/except once requires-python >= 3.11 is guaranteed
try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None  # type: ignore[assignment]


# -- Local script modules (not third-party; live in scripts/) ----------------
from _colors import colorize as _colorize
from _colors import supports_color as _supports_color
from _imports import import_sibling
from _ui import UI

Spinner = import_sibling("_progress").Spinner
ProgressBar = import_sibling("_progress").ProgressBar

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OnlyIf:
    """Conditional gate: only evaluate the parent rule when *path* contains *regex*."""

    path: str
    regex: str


@dataclass(frozen=True)
class Rule:
    """A single doctor check loaded from ``.repo-doctor.toml``."""

    type: str  # "exists" | "toml_has_path" | "regex_present"
    path: str
    kind: str = "file"  # for exists: "file" | "dir" | "any"
    level: str = "warn"  # "warn" | "info"
    category: str = ""  # grouping tag (e.g. "ci", "security")
    impact: str = ""
    hint: str = ""
    link: str = ""  # ADR or doc reference
    fix: str = ""  # command to auto-fix
    toml_path: str = ""  # for toml_has_path
    regex: str = ""  # for regex_present
    only_if: OnlyIf | None = field(default=None)


@dataclass
class Warning:
    """A single diagnostic produced during evaluation."""

    rule: Rule
    message: str


@dataclass
class PassedCheck:
    """A rule that was evaluated and passed."""

    rule: Rule
    message: str


@dataclass(frozen=True)
class DoctorConfig:
    """Settings from the ``[doctor]`` section of ``.repo-doctor.toml``."""

    ignore_missing: frozenset[str] = field(default_factory=frozenset)
    profiles: tuple[str, ...] = field(default_factory=tuple)


_LEVEL_ORDER: dict[str, int] = {"info": 0, "warn": 1}

SCRIPT_VERSION = "2.0.0"

# Theme color for this script's dashboard output.
THEME = "yellow"

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

_GIT_CMD: str | None = shutil.which("git")


def _run_git(root: Path, args: list[str]) -> tuple[int, str, str]:
    """Run a git command and return *(returncode, stdout, stderr)*."""
    if _GIT_CMD is None:
        return 1, "", "git not found on PATH"
    result = subprocess.run(  # nosec B603
        [_GIT_CMD, *args],
        cwd=root,
        text=True,
        capture_output=True,
        timeout=30,
    )
    return result.returncode, result.stdout, result.stderr


def _repo_root() -> Path:
    """Discover the repository root via ``git rev-parse``."""
    code, out, _ = _run_git(Path.cwd(), ["rev-parse", "--show-toplevel"])
    return Path(out.strip()) if code == 0 else Path.cwd()


def _list_deleted_paths(
    root: Path, *, staged: bool, diff_range: str | None
) -> list[str]:
    """Return repo-relative paths that are deleted in the given scope."""
    if diff_range:
        code, out, _ = _run_git(
            root, ["diff", "--name-status", "--diff-filter=D", diff_range]
        )
        if code != 0:
            return []
    elif staged:
        code, out, _ = _run_git(
            root, ["diff", "--cached", "--name-status", "--diff-filter=D"]
        )
        if code != 0:
            return []
    else:
        return []

    deleted: list[str] = []
    for line in out.splitlines():
        parts = line.split("\t", 1)
        if len(parts) == 2 and parts[0].strip() == "D":
            deleted.append(parts[1].strip())
    return deleted


# ---------------------------------------------------------------------------
# File scanning helpers
# ---------------------------------------------------------------------------


def _exists_kind(root: Path, rel: str, kind: str) -> bool:
    """Check whether *rel* exists under *root* with the expected *kind*."""
    target = root / rel
    if kind == "dir":
        return target.is_dir()
    if kind == "any":
        return target.exists()
    return target.is_file()


def _iter_files_under(root: Path, rel: str) -> list[Path]:
    """List all files at or beneath *rel*."""
    base = root / rel
    if base.is_file():
        return [base]
    if base.is_dir():
        return [p for p in base.rglob("*") if p.is_file()]
    return []


def _file_contains_regex(root: Path, rel: str, pattern: str) -> bool:
    """Return ``True`` if any file at or beneath *rel* matches *pattern*."""
    rx = re.compile(pattern, re.MULTILINE)
    for filepath in _iter_files_under(root, rel):
        try:
            text = filepath.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if rx.search(text):
            return True
    return False


def _toml_has_path(root: Path, rel: str, dotted: str) -> tuple[bool, str]:
    """Check for a dotted key path in a TOML file.

    Supports ``|`` separated alternatives — the check passes if ANY
    alternative path exists (e.g. ``"project.version|project.dynamic"``).

    Returns:
        A tuple of ``(ok, note)`` where *note* is non-empty on parse failure.
    """
    target = root / rel
    if not target.is_file():
        return False, ""
    if tomllib is None:
        return False, "tomllib not available (need Python 3.11+ for TOML checks)."

    try:
        data = tomllib.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return False, f"Could not parse TOML: {exc!s}"

    for alternative in dotted.split("|"):
        cur: Any = data
        for part in alternative.strip().split("."):
            if not isinstance(cur, dict) or part not in cur:
                break
            cur = cur[part]
        else:
            return True, ""
    return False, ""


def _matches_deletion(rule_path: str, rule_kind: str, deleted_path: str) -> bool:
    """Return ``True`` if *deleted_path* falls under *rule_path*."""
    if rule_kind != "dir":
        return deleted_path == rule_path
    prefix = rule_path.rstrip("/") + "/"
    return deleted_path.startswith(prefix) or deleted_path == rule_path.rstrip("/")


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


def _parse_rule_entries(raw_rules: list[dict[str, Any]]) -> list[Rule]:
    """Convert raw TOML dicts into validated :class:`Rule` objects."""
    rules: list[Rule] = []
    for entry in raw_rules:
        only_if = None
        oi = entry.get("only_if")
        if isinstance(oi, dict) and oi.get("path") and oi.get("regex"):
            only_if = OnlyIf(path=str(oi["path"]), regex=str(oi["regex"]))

        rules.append(
            Rule(
                type=str(entry.get("type", "")).strip(),
                path=str(entry.get("path", "")).strip(),
                kind=str(entry.get("kind", "file")).strip(),
                level=str(entry.get("level", "warn")).strip(),
                category=str(entry.get("category", "")).strip(),
                impact=str(entry.get("impact", "")).strip(),
                hint=str(entry.get("hint", "")).strip(),
                link=str(entry.get("link", "")).strip(),
                fix=str(entry.get("fix", "")).strip(),
                toml_path=str(entry.get("toml_path", "")).strip(),
                regex=str(entry.get("regex", "")).strip(),
                only_if=only_if,
            )
        )
    return [r for r in rules if r.type and r.path]


def _load_doctor_config(data: dict[str, Any]) -> DoctorConfig:
    """Parse the ``[doctor]`` section from parsed TOML *data*."""
    doctor = data.get("doctor", {})
    if not isinstance(doctor, dict):
        return DoctorConfig()

    ignore = doctor.get("ignore_missing", [])
    if not isinstance(ignore, list):
        ignore = []

    profiles = doctor.get("profiles", [])
    if not isinstance(profiles, list):
        profiles = []

    return DoctorConfig(
        ignore_missing=frozenset(str(p) for p in ignore),
        profiles=tuple(str(p) for p in profiles),
    )


def _load_rules(root: Path) -> tuple[list[Rule], DoctorConfig]:
    """Parse ``.repo-doctor.toml`` and return rules plus doctor config."""
    cfg = root / ".repo-doctor.toml"
    if not cfg.exists():
        return [], DoctorConfig()
    if tomllib is None:
        return [], DoctorConfig()

    data = tomllib.loads(cfg.read_text(encoding="utf-8"))
    rules = _parse_rule_entries(data.get("rule", []))
    config = _load_doctor_config(data)
    return rules, config


def _load_profile_rules(root: Path, profiles: list[str]) -> list[Rule]:
    """Load additional rules from ``repo_doctor.d/<name>.toml`` files.

    The special profile name ``"all"`` loads every ``.toml`` file in the
    directory.
    """
    profile_dir = root / "repo_doctor.d"
    if not profile_dir.is_dir() or tomllib is None:
        return []

    files_to_load: list[Path] = []
    for name in profiles:
        if name == "all":
            files_to_load = sorted(profile_dir.glob("*.toml"))
            break
        candidate = profile_dir / f"{name}.toml"
        if candidate.is_file():
            files_to_load.append(candidate)

    all_rules: list[Rule] = []
    for fpath in files_to_load:
        try:
            data = tomllib.loads(fpath.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError) as exc:
            logger.warning("Could not load profile %s: %s", fpath.name, exc)
            continue
        all_rules.extend(_parse_rule_entries(data.get("rule", [])))
    return all_rules


# ---------------------------------------------------------------------------
# Rule evaluation
# ---------------------------------------------------------------------------


def _evaluate_rules(
    root: Path,
    rules: list[Rule],
    *,
    check_missing: bool,
    deleted: set[str],
) -> tuple[list[Warning], list[PassedCheck]]:
    """Evaluate all rules and return warnings and passed checks."""
    warnings: list[Warning] = []
    passed: list[PassedCheck] = []

    # Track paths that already have a deletion warning to avoid duplicates
    deleted_rule_paths: set[str] = set()

    # Track which rules already produced a warning (by id) so we can
    # classify the rest as passed.
    warned_rules: set[int] = set()

    # Deletion warnings
    if deleted:
        for rule in rules:
            kind = rule.kind if rule.type == "exists" else "file"
            for deleted_path in deleted:
                if _matches_deletion(rule.path, kind, deleted_path):
                    warnings.append(Warning(rule=rule, message=f"Deleted: {rule.path}"))
                    deleted_rule_paths.add(rule.path)
                    warned_rules.add(id(rule))
                    break

    # Rule checks
    for rule in rules:
        if rule.only_if and not _file_contains_regex(
            root, rule.only_if.path, rule.only_if.regex
        ):
            # Skipped due to only_if gate — not a pass or fail
            continue

        failed = False

        if rule.type == "exists":
            if (
                check_missing
                and not _exists_kind(root, rule.path, rule.kind)
                and rule.path not in deleted_rule_paths
            ):
                warnings.append(Warning(rule=rule, message=f"Missing: {rule.path}"))
                failed = True

        elif rule.type == "regex_present":
            if not _exists_kind(root, rule.path, "any"):
                if check_missing and rule.path not in deleted_rule_paths:
                    warnings.append(Warning(rule=rule, message=f"Missing: {rule.path}"))
                    failed = True
                else:
                    # File missing but not checking missing — skip (not pass/fail)
                    continue
            elif rule.regex and not _file_contains_regex(root, rule.path, rule.regex):
                warnings.append(
                    Warning(
                        rule=rule,
                        message=f"Check failed: expected pattern in {rule.path}",
                    )
                )
                failed = True

        elif rule.type == "toml_has_path":
            if not _exists_kind(root, rule.path, "file"):
                # Target file missing — the anchor "exists" rule covers this.
                continue
            ok, note = _toml_has_path(root, rule.path, rule.toml_path)
            if not ok:
                if note:
                    warnings.append(
                        Warning(
                            rule=rule,
                            message=f"TOML parse issue in {rule.path}: {note}",
                        )
                    )
                warnings.append(
                    Warning(
                        rule=rule,
                        message=(
                            f"Check failed: [{rule.toml_path}] missing in {rule.path}"
                        ),
                    )
                )
                failed = True

        else:
            warnings.append(
                Warning(
                    rule=rule,
                    message=(
                        f"Unknown rule type '{rule.type}' for"
                        f" path '{rule.path}' (ignored)"
                    ),
                )
            )
            failed = True

        if not failed and id(rule) not in warned_rules:
            passed.append(PassedCheck(rule=rule, message=f"OK: {rule.path}"))
        if failed:
            warned_rules.add(id(rule))

    return warnings, passed


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------


def _format_warning(
    warning: Warning,
    *,
    show_hints: bool,
    show_links: bool,
    show_fix: bool,
    use_color: bool = False,
) -> str:
    """Format a single warning as a human-readable string."""
    rule = warning.rule
    level_colors = {"warn": "33", "info": "36"}  # nosec
    color_code = level_colors.get(rule.level, "0")
    tag = _colorize(
        f"[{rule.level}]" if rule.level else "[warn]",
        color_code,
        use_color=use_color,
    )
    cat = f" ({rule.category})" if rule.category else ""

    lines: list[str] = []
    if not use_color:
        lines.append(f"  {'─' * 56}")
    lines.append(f"{tag}{cat} {warning.message}")
    if rule.impact:
        lines.append(f"  Impact: {rule.impact}")
    if show_hints and rule.hint:
        lines.append(f"  Hint:   {rule.hint}")
    if show_links and rule.link:
        lines.append(f"  See:    {rule.link}")
    if show_fix and rule.fix:
        lines.append(f"  Fix:    {rule.fix}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Shared module dependency checks
# ---------------------------------------------------------------------------

# Maps shared internal modules (underscore-prefixed) to the scripts that
# import from them.  If a shared module is deleted or missing, every script
# listed here will fail on import.
#
# TODO (template users): Update this map when you add new shared modules
#   or new scripts that depend on them.
_SHARED_MODULE_DEPENDENTS: dict[str, list[str]] = {
    "_colors.py": [
        "doctor.py",
        "env_doctor.py",
        "git_doctor.py",
        "repo_doctor.py",
        "apply_labels.py",
        "bootstrap.py",
        "customize.py",
        "dep_versions.py",
        "workflow_versions.py",
        "check_todos.py",
        "archive_todos.py",
        "changelog_check.py",
        "check_known_issues.py",
        "clean.py",
    ],
    "_doctor_common.py": [
        "doctor.py",
        "env_doctor.py",
        "git_doctor.py",
    ],
    "_imports.py": [
        "doctor.py",
        "env_doctor.py",
        "git_doctor.py",
        "repo_doctor.py",
        "bootstrap.py",
        "dep_versions.py",
        "workflow_versions.py",
    ],
    "_progress.py": [
        "apply_labels.py",
        "git_doctor.py",
        "repo_doctor.py",
        "dep_versions.py",
        "workflow_versions.py",
    ],
    "_container_common.py": [
        "test_containerfile.py",
        "test_docker_compose.py",
    ],
    "_ui.py": [
        "check_python_support.py",
        "check_todos.py",
        "check_known_issues.py",
        "clean.py",
        "changelog_check.py",
        "archive_todos.py",
        "env_doctor.py",
        "doctor.py",
        "repo_doctor.py",
        "bootstrap.py",
        "dep_versions.py",
        "workflow_versions.py",
        "apply_labels.py",
        "customize.py",
        "test_containerfile.py",
        "test_docker_compose.py",
        "generate_command_reference.py",
    ],
}


def _check_shared_modules(
    root: Path,
    *,
    deleted: set[str],
    use_color: bool,
) -> list[Warning]:
    """Warn if shared internal modules are missing or staged for deletion.

    Scripts that import from ``_colors.py``, ``_doctor_common.py``,
    ``_imports.py``, or ``_progress.py`` will crash at startup if any
    of those modules are removed.
    """
    extra_warnings: list[Warning] = []
    scripts_dir = root / "scripts"

    for module, dependents in _SHARED_MODULE_DEPENDENTS.items():
        module_path = scripts_dir / module
        rel_path = f"scripts/{module}"
        missing = not module_path.is_file() or rel_path in deleted

        if missing:
            dep_list = ", ".join(dependents[:5])
            suffix = f" (+{len(dependents) - 5} more)" if len(dependents) > 5 else ""
            rule = Rule(
                type="exists",
                path=rel_path,
                kind="file",
                level="warn",
                category="scripts",
                impact=(
                    f"Removing {module} will break {len(dependents)} script(s) "
                    f"that import from it: {dep_list}{suffix}"
                ),
                hint=(
                    f"Restore {module} or update dependent scripts to "
                    f"remove the import."
                ),
                link="docs/adr/031-script-conventions.md",
            )
            extra_warnings.append(
                Warning(rule=rule, message=f"Shared module missing: {rel_path}")
            )

    return extra_warnings


# ---------------------------------------------------------------------------
# Built-in programmatic checks (beyond TOML rules)
# ---------------------------------------------------------------------------

_SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    "node_modules",
    ".venv",
    "venv",
    ".tox",
    ".nox",
    "site",
    "dist",
    "build",
    ".eggs",
    ".cache",
    "htmlcov",
}

_CONFLICT_RE = re.compile(r"^(<{7}|={7}|>{7})\s", re.MULTILINE)


def _iter_py_files(root: Path) -> list[Path]:
    """Yield all ``.py`` files under *root*, skipping common artifact dirs."""
    results: list[Path] = []
    for dirpath_str, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        dirpath = Path(dirpath_str)
        results.extend(dirpath / f for f in filenames if f.endswith(".py"))
    return results


def _check_python_syntax(root: Path) -> list[Warning]:
    """Check all ``.py`` files for syntax errors using :func:`ast.parse`."""
    warnings: list[Warning] = []
    for py_file in _iter_py_files(root):
        try:
            source = py_file.read_text(encoding="utf-8", errors="ignore")
            ast.parse(source, filename=str(py_file))
        except SyntaxError as exc:
            rel = py_file.relative_to(root).as_posix()
            line_info = f" (line {exc.lineno})" if exc.lineno else ""
            warnings.append(
                Warning(
                    rule=Rule(
                        type="syntax",
                        path=rel,
                        level="warn",
                        category="python",
                        impact=f"Python syntax error{line_info}: {exc.msg}",
                        hint="Fix the syntax error before committing.",
                    ),
                    message=f"Syntax error: {rel}{line_info}",
                )
            )
    return warnings


def _check_merge_conflict_markers(root: Path) -> list[Warning]:
    """Scan tracked text files for leftover merge conflict markers."""
    warnings: list[Warning] = []
    # Use git to list tracked files to avoid scanning generated/ignored dirs
    if _GIT_CMD is None:
        return warnings
    code, out, _ = _run_git(root, ["ls-files", "-z"])
    if code != 0:
        return warnings
    for entry in out.split("\0"):
        entry = entry.strip()
        if not entry:
            continue
        fpath = root / entry
        if not fpath.is_file():
            continue
        # Only check text-like files by trying to read as utf-8
        try:
            text = fpath.read_text(encoding="utf-8", errors="strict")
        except (OSError, UnicodeDecodeError):
            continue
        if _CONFLICT_RE.search(text):
            warnings.append(
                Warning(
                    rule=Rule(
                        type="conflict_markers",
                        path=entry,
                        level="warn",
                        category="git",
                        impact="Leftover merge conflict markers will break code or produce invalid output.",
                        hint="Resolve the merge conflict and remove the markers.",
                    ),
                    message=f"Merge conflict markers found: {entry}",
                )
            )
    return warnings


def _check_future_annotations(root: Path) -> list[Warning]:
    """Flag ``.py`` files under ``src/`` missing ``from __future__ import annotations``.

    Also warns when the import appears *after* the first local/relative
    import, since it must be active before any annotation is evaluated.
    """
    warnings: list[Warning] = []
    src_dir = root / "src"
    if not src_dir.is_dir():
        return warnings
    marker = "from __future__ import annotations"
    # Matches ``from .foo`` or ``from _bar`` — typical local/private imports.
    _local_import_re = re.compile(r"^\s*from\s+[._]")
    for py_file in _iter_py_files(src_dir):
        try:
            text = py_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # Skip empty or near-empty files (e.g. __init__.py stubs, one-liners)
        if len(text.strip()) < 50:
            continue
        rel = py_file.relative_to(root).as_posix()
        lines = text.splitlines()
        marker_line: int | None = None
        first_local_line: int | None = None
        for idx, line in enumerate(lines):
            if marker in line and marker_line is None:
                marker_line = idx
            if (
                _local_import_re.match(line)
                and marker not in line
                and first_local_line is None
            ):
                first_local_line = idx
        if marker_line is None:
            warnings.append(
                Warning(
                    rule=Rule(
                        type="future_annotations",
                        path=rel,
                        level="info",
                        category="python",
                        impact="Missing 'from __future__ import annotations' — PEP 604 union syntax (X | Y) won't work at runtime on older Python.",
                        hint="Add 'from __future__ import annotations' at the top of the file.",
                    ),
                    message=f"Missing future annotations: {rel}",
                )
            )
        elif first_local_line is not None and marker_line > first_local_line:
            warnings.append(
                Warning(
                    rule=Rule(
                        type="future_annotations",
                        path=rel,
                        level="warning",
                        category="python",
                        impact="'from __future__ import annotations' appears after a local import — annotations evaluated before the future import won't use PEP 604 syntax.",
                        hint="Move 'from __future__ import annotations' above all local imports.",
                    ),
                    message=f"Future annotations import too late: {rel}",
                )
            )
    return warnings


def _check_large_tracked_files(root: Path, threshold_kb: int = 512) -> list[Warning]:
    """Warn about tracked files larger than *threshold_kb* kilobytes."""
    warnings: list[Warning] = []
    if _GIT_CMD is None:
        return warnings
    code, out, _ = _run_git(root, ["ls-files", "-z"])
    if code != 0:
        return warnings
    for entry in out.split("\0"):
        entry = entry.strip()
        if not entry:
            continue
        fpath = root / entry
        if not fpath.is_file():
            continue
        try:
            size = fpath.stat().st_size
        except OSError:
            continue
        if size > threshold_kb * 1024:
            size_kb = size / 1024
            size_str = (
                f"{size_kb:.0f} KB" if size_kb < 1024 else f"{size_kb / 1024:.1f} MB"
            )
            warnings.append(
                Warning(
                    rule=Rule(
                        type="large_file",
                        path=entry,
                        level="info",
                        category="git",
                        impact=f"Large tracked file ({size_str}) increases clone size and slows git operations.",
                        hint="Consider using .gitignore, git-lfs, or removing from tracking.",
                    ),
                    message=f"Large tracked file ({size_str}): {entry}",
                )
            )
    return warnings


def _run_programmatic_checks(
    root: Path, *, min_level: str = "warn"
) -> tuple[list[Warning], list[PassedCheck]]:
    """Run all built-in programmatic checks and return warnings + passed."""
    all_warnings: list[Warning] = []
    all_passed: list[PassedCheck] = []
    min_order = _LEVEL_ORDER.get(min_level, 0)

    checks: list[tuple[str, list[Warning]]] = [
        ("Python syntax", _check_python_syntax(root)),
        ("Merge conflict markers", _check_merge_conflict_markers(root)),
        ("Future annotations", _check_future_annotations(root)),
        ("Large tracked files", _check_large_tracked_files(root)),
    ]

    for name, ws in checks:
        # Filter by severity level
        ws = [w for w in ws if _LEVEL_ORDER.get(w.rule.level, 0) >= min_order]
        if ws:
            all_warnings.extend(ws)
        else:
            all_passed.append(
                PassedCheck(
                    rule=Rule(type="programmatic", path="", category="builtin"),
                    message=f"OK: {name}",
                )
            )

    return all_warnings, all_passed


# Succinct one-line descriptions for each repo_doctor.d profile.
_PROFILE_DESCRIPTORS: dict[str, str] = {
    "ci.toml": "CI/CD workflow hardening & pinning",
    "python.toml": "Packaging, typing, linting & coverage",
    "docs.toml": "MkDocs structure & documentation hygiene",
    "db.toml": "Schema, migrations & seed consistency",
    "container.toml": "Containerfile hygiene & build context",
    "security.toml": "Security policy, scanning & secret guards",
}


# ---------------------------------------------------------------------------
# Profile summary helpers
# ---------------------------------------------------------------------------


def _count_profile_rules(root: Path) -> list[tuple[str, int]]:
    """Return a list of ``(filename, rule_count)`` for each profile in ``repo_doctor.d/``."""
    profile_dir = root / "repo_doctor.d"
    results: list[tuple[str, int]] = []
    if not profile_dir.is_dir() or tomllib is None:
        return results
    for fpath in sorted(profile_dir.glob("*.toml")):
        try:
            data = tomllib.loads(fpath.read_text(encoding="utf-8"))
            count = len(data.get("rule", []))
            results.append((fpath.name, count))
        except (OSError, ValueError, TypeError):
            results.append((fpath.name, 0))
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        description="Warn-only repo doctor checks "
        "(missing files, deletions, config presence).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {SCRIPT_VERSION}",
    )
    parser.add_argument(
        "--missing",
        action="store_true",
        help="Report missing files/dirs in working tree.",
    )
    parser.add_argument(
        "--staged",
        action="store_true",
        help="Report staged deletions (index).",
    )
    parser.add_argument(
        "--diff",
        default=None,
        metavar="RANGE",
        help='Report deletions in a git diff range, e.g. "origin/main...HEAD".',
    )
    parser.add_argument(
        "--category",
        default=None,
        metavar="CAT",
        help="Only show rules matching this category (e.g. ci, hooks, security).",
    )
    parser.add_argument(
        "--min-level",
        default="warn",
        choices=["info", "warn"],
        help="Minimum severity to display (default: warn). Use 'info' to include everything.",
    )
    parser.add_argument(
        "--include-info",
        action="store_true",
        help="Include info-level checks (shorthand for --min-level info).",
    )
    parser.add_argument(
        "--profile",
        action="append",
        default=None,
        metavar="NAME",
        help=(
            "Load additional rules from repo_doctor.d/NAME.toml "
            "(repeatable; 'all' loads everything)."
        ),
    )
    parser.add_argument(
        "--no-hints",
        action="store_true",
        help="Hide hint lines.",
    )
    parser.add_argument(
        "--no-links",
        action="store_true",
        help="Hide link/reference lines.",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Show auto-fix commands for rules that define one.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output.",
    )
    parser.add_argument(
        "--show-passed",
        action="store_true",
        help="Show checks that passed (in addition to warnings).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when warnings are found (for CI gating).",
    )
    parser.add_argument(
        "--smoke",
        nargs="?",
        const="",
        default=None,
        metavar="NAME",
        help=(
            "Inject a synthetic failure to test dashboard appearance. "
            "Optionally specify a profile name (e.g. 'ci') to fail its "
            "first check; if omitted, a random loaded rule is chosen."
        ),
    )
    return parser


def main() -> int:
    """Entry point.

    Returns 0 by default (warn-only). With ``--strict``, returns 1
    when any warnings are found.
    """
    elapsed_start = time.monotonic()
    parser = _build_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    use_color = False if args.no_color else _supports_color(sys.stdout)

    # Default: check missing + staged
    if not (args.missing or args.staged or args.diff):
        args.missing = True
        args.staged = True

    root = _repo_root()
    rules, config = _load_rules(root)

    # Merge profile rules (config defaults + CLI overrides)
    profile_names: list[str] = list(config.profiles)
    if args.profile:
        profile_names.extend(args.profile)
    if profile_names:
        rules.extend(_load_profile_rules(root, profile_names))

    if not rules:
        logger.info(
            "No rules found (missing .repo-doctor.toml or TOML parser unavailable)."
        )
        return 0

    # Filter by minimum severity level
    min_level = "info" if args.include_info else args.min_level
    min_order = _LEVEL_ORDER.get(min_level, 0)
    rules = [r for r in rules if _LEVEL_ORDER.get(r.level, 0) >= min_order]

    # Filter by category if requested
    if args.category:
        rules = [r for r in rules if r.category == args.category]

    # Remove explicitly ignored paths
    if config.ignore_missing:
        rules = [r for r in rules if r.path not in config.ignore_missing]

    deleted = set(_list_deleted_paths(root, staged=args.staged, diff_range=args.diff))

    # Count total work items for progress: TOML rules + 4 programmatic checks
    total_steps = len(rules) + 4
    with ProgressBar(
        total=total_steps,
        label="Evaluating rules",
        color="yellow",
        log_interval=10,
        pulse=True,
    ) as bar:
        bar.update("TOML rules")
        warnings, passed = _evaluate_rules(
            root, rules, check_missing=args.missing, deleted=deleted
        )
        # Tick for each TOML rule evaluated
        for _ in range(len(rules) - 1):
            bar.update()

        bar.update("shared modules")
        shared_warnings = _check_shared_modules(
            root, deleted=deleted, use_color=use_color
        )
        warnings.extend(shared_warnings)

        bar.update("programmatic checks")
        prog_warnings, prog_passed = _run_programmatic_checks(root, min_level=min_level)
        warnings.extend(prog_warnings)
        passed.extend(prog_passed)
        # Tick remaining programmatic check slots
        bar.update()
        bar.update()

    # --smoke: inject a synthetic failure for testing dashboard appearance
    if args.smoke is not None:
        smoke_target = args.smoke.strip() if args.smoke else ""
        smoke_rule: Rule | None = None
        if smoke_target:
            # Find first rule from the named profile category
            for r in rules:
                if r.category == smoke_target:
                    smoke_rule = r
                    break
            if smoke_rule is None:
                # Try matching profile file name
                profile_rules = _load_profile_rules(root, [smoke_target])
                if profile_rules:
                    smoke_rule = profile_rules[0]
        if smoke_rule is None and rules:
            smoke_rule = random.choice(rules)  # nosec B311
        if smoke_rule is not None:
            warnings.append(
                Warning(
                    rule=Rule(
                        type=smoke_rule.type,
                        path=smoke_rule.path,
                        level="warn",
                        category=smoke_rule.category or "smoke-test",
                        impact="[SMOKE TEST] This is a synthetic failure injected by --smoke to preview dashboard failure output.",
                        hint="This warning is fake. Remove --smoke to see real results.",
                    ),
                    message=f"[SMOKE TEST] Simulated failure: {smoke_rule.path}",
                )
            )

    ui = UI(
        title="Repo Doctor",
        version=SCRIPT_VERSION,
        theme=THEME,
        no_color=not use_color,
    )
    ui.header()

    # ── Rules Upheld bar ──
    total_evaluated = len(passed) + len(warnings)
    ui.blank()
    ui.rules_summary(len(passed), total_evaluated)

    # ── Rule Sources (repo_doctor.d profile breakdown) ──
    profile_counts = _count_profile_rules(root)
    base_rule_count = len(_load_rules(root)[0])
    if profile_counts or base_rule_count:
        ui.section("Rule Sources")
        if base_rule_count:
            ui.kv(".repo-doctor.toml", f"{base_rule_count} rules")
        if profile_counts:
            print()
            ui.info_line("repo_doctor.d/ profiles:")
            print()
            for fname, count in profile_counts:
                name_label = fname.removesuffix(".toml")
                desc = _PROFILE_DESCRIPTORS.get(fname, "")
                colored_name = ui._themed(ui.c.bold(name_label))
                print(f"      {colored_name}  {ui.c.dim(f'{count} rules')}")
                if desc:
                    print(f"      {ui.c.dim(desc)}")
                print(f"      {ui.c.dim(ui.h_line * 40)}")
        print()

    # ── Passed Checks ──
    if args.show_passed and passed:
        ui.section("Passed Checks")
        for p in passed:
            cat = f" ({p.rule.category})" if p.rule.category else ""
            ui.status_line("check", f"{cat} {p.message}", "green")
        print()

    # ── Warnings ──
    if warnings:
        ui.section("Warnings (non-blocking)")
        print()
        for w in warnings:
            print(
                _format_warning(
                    w,
                    show_hints=not args.no_hints,
                    show_links=not args.no_links,
                    show_fix=args.fix,
                    use_color=use_color,
                )
            )
            print()
    else:
        # Enhanced "all passed" output instead of a single line
        ui.section("Results")
        total = len(passed)
        check_sym = ui.sym.get("check", "+")
        ui.status_line("check", f"All {total} checks passed", "green")
        # Group by category for a quick breakdown
        cat_counts: dict[str, int] = {}
        for p in passed:
            cat = p.rule.category or "general"
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
        if cat_counts:
            max_cat_width = max(len(cat) for cat in cat_counts)
            max_cnt_width = max(len(str(cnt)) for cnt in cat_counts.values())
            for cat, cnt in sorted(cat_counts.items()):
                cat_str = cat.ljust(max_cat_width)
                cnt_str = str(cnt).rjust(max_cnt_width)
                ui.info_line(f"  {ui.c.green(check_sym)} {cat_str}  {cnt_str} passed")

    # ── Recommended Scripts ──
    ui.recommended_scripts(
        [
            "repo_sauron",
            "git_doctor",
            "env_doctor",
            "dep_versions",
            "doctor",
        ],
        preamble="Scripts that expand on repository health and diagnostics.",
    )

    # Summary
    elapsed = time.monotonic() - elapsed_start
    ui.footer(
        passed=len(passed),
        failed=0,
        warned=len(warnings),
        elapsed=elapsed,
    )

    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    # Reconfigure stdout for UTF-8 on Windows to handle box-drawing
    # characters and other non-ASCII content in the UI output.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
