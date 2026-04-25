#!/usr/bin/env python3
"""Repository statistics dashboard — the all-seeing eye for any git repo.

Generates a comprehensive Markdown report about the current repository:
file counts by type, lines of code, language breakdown, full directory tree,
file access statistics, per-file git commit history, test coverage analysis,
contributor list, code/script activity tracking, and more.

Works on **any git repository** — file extension detection and language
classification are fully dynamic.  The report adapts to whatever languages
and file types are present in the target repo.

Named after Sauron's all-seeing eye from The Lord of the Rings.

Script compatibility (from this template's ``scripts/`` directory)::

    ✅ Any git repo (language-agnostic):
        repo_sauron.py      — full repo statistics dashboard
        git_doctor.py       — git config, branch ops, integrity
        env_inspect.py      — system environment, PATH, packages
        workflow_versions.py — GitHub Actions SHA-pinned versions
        repo_doctor.py      — repository structure health checks

    🐍 Python projects only:
        check_python_support.py — Python version consistency
        dep_versions.py         — dependency versions / updates
        env_doctor.py           — dev environment diagnostics
        doctor.py               — unified health check (all doctors)
        bootstrap.py            — initial Hatch environment setup

    📦 This template only:
        customize.py — interactive template customisation wizard

Flags::

    --output PATH       Output file path (default: repo-sauron-report.md)
    --json              Output as JSON (for CI integration)
    -q, --quiet         Suppress output; exit code only
    --version           Print version and exit

Usage::

    python scripts/repo_sauron.py
    python scripts/repo_sauron.py --output docs/report.md
    python scripts/repo_sauron.py --json

Output:
    Generates a Markdown file with colored sections, table of contents,
    repo structure tree, file access stats, per-file git history, test
    coverage analysis, and Mermaid charts.

    Task runner shortcuts for this script are defined in ``Taskfile.yml``.

Portability:
    Can be used in any Python repo with a ``pyproject.toml``.
    Requires shared modules: ``_colors.py``, ``_imports.py``,
    ``_progress.py``.
"""

from __future__ import annotations

import argparse
import json
import logging
import os  # TODO (template users): replace os.walk() with Path.walk() when requires-python >= 3.12
import platform
import shutil
import subprocess  # nosec B404
import sys
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

# -- Local script modules (not third-party; live in scripts/) ----------------
from _colors import Colors
from _imports import find_repo_root
from _progress import Spinner

log = logging.getLogger(__name__)

SCRIPT_VERSION = "4.0.0"

ROOT = find_repo_root()

# Directories to skip when scanning (common build/cache artifacts)
SKIP_DIRS = {
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
    "*.egg-info",
    ".cache",
    "htmlcov",
}

_GIT_CMD: str | None = shutil.which("git")

# Map file extensions to language names
_EXT_TO_LANGUAGE: dict[str, str] = {
    ".py": "Python",
    ".pyi": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".jsx": "JavaScript (JSX)",
    ".tsx": "TypeScript (TSX)",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".less": "Less",
    ".java": "Java",
    ".kt": "Kotlin",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".c": "C",
    ".h": "C/C++ Header",
    ".cpp": "C++",
    ".cs": "C#",
    ".swift": "Swift",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".ps1": "PowerShell",
    ".sql": "SQL",
    ".r": "R",
    ".lua": "Lua",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".toml": "TOML",
    ".json": "JSON",
    ".xml": "XML",
    ".md": "Markdown",
    ".rst": "reStructuredText",
    ".txt": "Plain Text",
    ".cfg": "Config",
    ".ini": "Config",
    ".dockerfile": "Dockerfile",
}

# Extensions considered "code" files
_CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".go",
    ".rs",
    ".rb",
    ".java",
    ".c",
    ".cpp",
    ".cs",
    ".sh",
    ".bash",
    ".zsh",
    ".ps1",
}

# Extensions considered "script" files specifically
_SCRIPT_EXTENSIONS = {".py", ".sh", ".bash", ".zsh", ".ps1", ".rb", ".pl"}

# Patterns for test files
_TEST_DIRS = {"tests", "test", "spec"}
_TEST_PREFIXES = ("test_", "conftest")
_TEST_SUFFIXES = tuple(f"_test{ext}" for ext in _CODE_EXTENSIONS)

# Extensions considered "documentation" files
_DOC_EXTENSIONS = {".md", ".rst", ".txt"}

# Extensions considered "configuration" files
_CONFIG_EXTENSIONS = {".toml", ".yml", ".yaml", ".json", ".cfg", ".ini", ".xml"}

# Emoji icons for file extensions
_EXT_TO_ICON: dict[str, str] = {
    ".py": "\U0001f40d",
    ".pyi": "\U0001f40d",
    ".js": "\U0001f7e1",
    ".ts": "\U0001f535",
    ".jsx": "\U0001f7e1",
    ".tsx": "\U0001f535",
    ".html": "\U0001f310",
    ".htm": "\U0001f310",
    ".css": "\U0001f3a8",
    ".scss": "\U0001f3a8",
    ".less": "\U0001f3a8",
    ".java": "\u2615",
    ".kt": "\U0001f7e3",
    ".go": "\U0001f535",
    ".rs": "\U0001f980",
    ".rb": "\U0001f48e",
    ".php": "\U0001f418",
    ".c": "\u2699\ufe0f",
    ".h": "\u2699\ufe0f",
    ".cpp": "\u2699\ufe0f",
    ".cs": "\U0001f7e2",
    ".swift": "\U0001f34e",
    ".sh": "\U0001f41a",
    ".bash": "\U0001f41a",
    ".zsh": "\U0001f41a",
    ".ps1": "\U0001f5a5\ufe0f",
    ".sql": "\U0001f5c4\ufe0f",
    ".r": "\U0001f4ca",
    ".lua": "\U0001f319",
    ".yml": "\u2699\ufe0f",
    ".yaml": "\u2699\ufe0f",
    ".toml": "\U0001f527",
    ".json": "\U0001f4cb",
    ".xml": "\U0001f4f0",
    ".md": "\U0001f4dd",
    ".rst": "\U0001f4dd",
    ".txt": "\U0001f4c4",
    ".cfg": "\U0001f527",
    ".ini": "\U0001f527",
    ".dockerfile": "\U0001f433",
}

# Emoji icons for languages
_LANG_TO_ICON: dict[str, str] = {
    "Python": "\U0001f40d",
    "JavaScript": "\U0001f7e1",
    "TypeScript": "\U0001f535",
    "JavaScript (JSX)": "\U0001f7e1",
    "TypeScript (TSX)": "\U0001f535",
    "HTML": "\U0001f310",
    "CSS": "\U0001f3a8",
    "SCSS": "\U0001f3a8",
    "Less": "\U0001f3a8",
    "Java": "\u2615",
    "Kotlin": "\U0001f7e3",
    "Go": "\U0001f535",
    "Rust": "\U0001f980",
    "Ruby": "\U0001f48e",
    "PHP": "\U0001f418",
    "C": "\u2699\ufe0f",
    "C/C++ Header": "\u2699\ufe0f",
    "C++": "\u2699\ufe0f",
    "C#": "\U0001f7e2",
    "Swift": "\U0001f34e",
    "Shell": "\U0001f41a",
    "PowerShell": "\U0001f5a5\ufe0f",
    "SQL": "\U0001f5c4\ufe0f",
    "R": "\U0001f4ca",
    "Lua": "\U0001f319",
    "YAML": "\u2699\ufe0f",
    "TOML": "\U0001f527",
    "JSON": "\U0001f4cb",
    "XML": "\U0001f4f0",
    "Markdown": "\U0001f4dd",
    "reStructuredText": "\U0001f4dd",
    "Plain Text": "\U0001f4c4",
    "Config": "\U0001f527",
    "Dockerfile": "\U0001f433",
}

# Shields.io badge info for VS Code-style file type badges.
# Maps language name -> (logo_slug | None, hex_color, logo_color).
_LANG_BADGE_INFO: dict[str, tuple[str | None, str, str]] = {
    "Python": ("python", "3776AB", "white"),
    "JavaScript": ("javascript", "F7DF1E", "black"),
    "TypeScript": ("typescript", "3178C6", "white"),
    "JavaScript (JSX)": ("react", "61DAFB", "black"),
    "TypeScript (TSX)": ("react", "61DAFB", "black"),
    "HTML": ("html5", "E34F26", "white"),
    "CSS": ("css3", "1572B6", "white"),
    "SCSS": ("sass", "CC6699", "white"),
    "Less": ("less", "1D365D", "white"),
    "Java": ("openjdk", "437291", "white"),
    "Kotlin": ("kotlin", "7F52FF", "white"),
    "Go": ("go", "00ADD8", "white"),
    "Rust": ("rust", "000000", "white"),
    "Ruby": ("ruby", "CC342D", "white"),
    "PHP": ("php", "777BB4", "white"),
    "C": ("c", "A8B9CC", "black"),
    "C/C++ Header": ("c", "A8B9CC", "black"),
    "C++": ("cplusplus", "00599C", "white"),
    "C#": ("csharp", "512BD4", "white"),
    "Swift": ("swift", "F05138", "white"),
    "Shell": ("gnubash", "4EAA25", "white"),
    "PowerShell": ("powershell", "5391FE", "white"),
    "SQL": (None, "4169E1", "white"),
    "R": ("r", "276DC3", "white"),
    "Lua": ("lua", "2C2D72", "white"),
    "YAML": (None, "CB171E", "white"),
    "TOML": (None, "9C4121", "white"),
    "JSON": (None, "000000", "white"),
    "XML": (None, "005FAD", "white"),
    "Markdown": ("markdown", "000000", "white"),
    "reStructuredText": ("readthedocs", "8CA1AF", "white"),
    "Plain Text": (None, "778899", "white"),
    "Config": (None, "778899", "white"),
    "Dockerfile": ("docker", "2496ED", "white"),
}


def _ext_badge(ext: str) -> str:
    """Return a shields.io badge markdown image for a file extension."""
    lang = _EXT_TO_LANGUAGE.get(ext, "")
    info = _LANG_BADGE_INFO.get(lang) if lang else None
    if info:
        logo, color, lc = info
        safe = ext.replace("-", "--")
        url = f"https://img.shields.io/badge/{safe}-{color}?style=flat-square"
        if logo:
            url += f"&logo={logo}&logoColor={lc}"
        return f"![{ext}]({url})"
    return _EXT_TO_ICON.get(ext, "\U0001f4c4")


def _lang_badge(lang: str) -> str:
    """Return a shields.io badge markdown image for a language name."""
    info = _LANG_BADGE_INFO.get(lang)
    if info:
        logo, color, lc = info
        safe = (
            lang.replace("-", "--")
            .replace(" ", "%20")
            .replace("+", "%2B")
            .replace("#", "%23")
            .replace("/", "%2F")
        )
        url = f"https://img.shields.io/badge/{safe}-{color}?style=flat-square"
        if logo:
            url += f"&logo={logo}&logoColor={lc}"
        return f"![{lang}]({url})"
    return _LANG_TO_ICON.get(lang, "\U0001f4c4")


# ---------------------------------------------------------------------------
# Markdown table helper
# ---------------------------------------------------------------------------


def _aligned_table(
    headers: list[str],
    rows: list[list[str]],
    aligns: str = "",
) -> list[str]:
    """Build a Markdown table with padded columns for clean raw formatting.

    Args:
        headers: Column header strings.
        rows: List of rows, each a list of cell strings.
        aligns: One char per column — ``'l'`` left, ``'r'`` right.
                Missing positions default to ``'l'``.

    Returns:
        List of Markdown lines (header, separator, data rows).
    """
    ncols = len(headers)
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row[:ncols]):
            widths[i] = max(widths[i], len(cell))

    def _align(col: int) -> str:
        a = aligns[col] if col < len(aligns) else "l"
        return a

    # Header
    hdr = "| " + " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)) + " |"
    # Separator
    seps: list[str] = []
    for i in range(ncols):
        if _align(i) == "r":
            seps.append("-" * (widths[i] - 1) + ":")
        else:
            seps.append("-" * widths[i])
    sep = "| " + " | ".join(seps) + " |"
    # Rows
    lines = [hdr, sep]
    for row in rows:
        cells: list[str] = []
        for i in range(ncols):
            val = row[i] if i < len(row) else ""
            if _align(i) == "r":
                cells.append(val.rjust(widths[i]))
            else:
                cells.append(val.ljust(widths[i]))
        lines.append("| " + " | ".join(cells) + " |")
    return lines


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------


def _run_git(args: list[str], *, timeout: int = 30) -> tuple[int, str]:
    """Run a git command and return (returncode, stdout)."""
    if _GIT_CMD is None:
        return 1, ""
    try:
        result = subprocess.run(  # nosec B603
            [_GIT_CMD, *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        return 1, ""


# ---------------------------------------------------------------------------
# Stats collectors
# ---------------------------------------------------------------------------


def _collect_file_stats() -> dict:
    """Walk the repo and collect file statistics."""
    total_files = 0
    total_dirs = 0
    total_size = 0
    extension_counts: Counter[str] = Counter()
    extension_lines: Counter[str] = Counter()
    language_lines: Counter[str] = Counter()
    language_files: Counter[str] = Counter()
    largest_files: list[tuple[str, int]] = []
    code_file_count = 0
    script_file_count = 0
    test_file_count = 0
    doc_file_count = 0
    config_file_count = 0
    empty_file_count = 0
    binary_file_count = 0
    found_code_extensions: set[str] = set()
    found_script_extensions: set[str] = set()
    found_test_extensions: set[str] = set()
    all_file_paths: set[str] = set()

    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [
            d for d in dirnames if d not in SKIP_DIRS and not d.endswith(".egg-info")
        ]
        total_dirs += 1

        for fname in filenames:
            filepath = Path(dirpath) / fname
            try:
                size = filepath.stat().st_size
            except OSError:
                continue

            total_files += 1
            total_size += size
            ext = filepath.suffix.lower() or "(no ext)"
            extension_counts[ext] += 1

            lang = _EXT_TO_LANGUAGE.get(ext)
            if lang is None and fname.lower() in ("containerfile", "dockerfile"):
                lang = "Dockerfile"
            if lang:
                language_files[lang] += 1

            if ext in _CODE_EXTENSIONS:
                code_file_count += 1
                found_code_extensions.add(ext)
            if ext in _SCRIPT_EXTENSIONS:
                script_file_count += 1
                found_script_extensions.add(ext)
            if ext in _DOC_EXTENSIONS:
                doc_file_count += 1
            if ext in _CONFIG_EXTENSIONS:
                config_file_count += 1
            if size == 0:
                empty_file_count += 1

            # Test file detection: in test dirs or matching test patterns
            rel_parts = filepath.relative_to(ROOT).parts
            fname_lower = fname.lower()
            is_test = any(part in _TEST_DIRS for part in rel_parts)
            is_test = is_test or any(fname_lower.startswith(p) for p in _TEST_PREFIXES)
            is_test = is_test or any(
                fname_lower.endswith(f"_test{ext}") for ext in _CODE_EXTENSIONS
            )
            if is_test and ext in _CODE_EXTENSIONS:
                test_file_count += 1
                found_test_extensions.add(ext)

            # Simple binary detection: non-text extensions
            text_exts = {
                *_CODE_EXTENSIONS,
                *_DOC_EXTENSIONS,
                *_CONFIG_EXTENSIONS,
                ".sql",
                ".html",
                ".htm",
                ".css",
                ".scss",
                ".less",
                ".xml",
                ".csv",
                ".dockerfile",
            }
            if ext and ext not in text_exts:
                binary_file_count += 1

            if ext in (
                ".py",
                ".yml",
                ".yaml",
                ".md",
                ".toml",
                ".json",
                ".txt",
                ".sh",
                ".sql",
                ".html",
                ".css",
                ".js",
                ".ts",
            ):
                try:
                    line_count = len(filepath.read_bytes().split(b"\n"))
                    extension_lines[ext] += line_count
                    if lang:
                        language_lines[lang] += line_count
                except OSError:
                    pass

            rel = str(filepath.relative_to(ROOT))
            all_file_paths.add(rel)
            largest_files.append((rel, size))

    largest_files.sort(key=lambda x: x[1], reverse=True)

    total_lang_files = sum(language_files.values())
    languages: list[dict] = []
    for lang, count in language_files.most_common(20):
        pct = (count / total_lang_files * 100) if total_lang_files else 0
        languages.append(
            {
                "language": lang,
                "files": count,
                "lines": language_lines.get(lang, 0),
                "percentage": round(pct, 1),
            }
        )

    return {
        "total_files": total_files,
        "total_dirs": total_dirs,
        "total_size_bytes": total_size,
        "avg_file_size_bytes": total_size // total_files if total_files else 0,
        "extension_counts": dict(extension_counts.most_common(20)),
        "extension_lines": dict(extension_lines.most_common(20)),
        "languages": languages,
        "largest_files": [(f, s) for f, s in largest_files[:15]],
        "code_file_count": code_file_count,
        "script_file_count": script_file_count,
        "test_file_count": test_file_count,
        "doc_file_count": doc_file_count,
        "config_file_count": config_file_count,
        "empty_file_count": empty_file_count,
        "binary_file_count": binary_file_count,
        "found_code_extensions": sorted(found_code_extensions),
        "found_script_extensions": sorted(found_script_extensions),
        "found_test_extensions": sorted(found_test_extensions),
        "all_file_paths": all_file_paths,
    }


def _collect_git_stats() -> dict:
    """Collect git repository statistics."""
    stats: dict = {"available": False}

    code, out = _run_git(["rev-parse", "--is-inside-work-tree"])
    if code != 0 or out != "true":
        return stats

    stats["available"] = True

    code, out = _run_git(["rev-list", "--count", "HEAD"])
    stats["total_commits"] = int(out) if code == 0 and out.isdigit() else 0

    code, out = _run_git(["shortlog", "-sn", "--no-merges", "HEAD"])
    if code == 0 and out:
        authors = []
        for line in out.splitlines():
            parts = line.strip().split("\t", 1)
            if len(parts) == 2:
                authors.append(
                    {
                        "commits": int(parts[0].strip()),
                        "name": parts[1].strip(),
                    }
                )
        stats["authors"] = authors[:10]
        stats["author_count"] = len(authors)
    else:
        stats["authors"] = []
        stats["author_count"] = 0

    code, out = _run_git(["branch", "--list"])
    if code == 0:
        branches = [b.strip().lstrip("* ") for b in out.splitlines() if b.strip()]
        stats["branch_count"] = len(branches)
    else:
        stats["branch_count"] = 0

    code, out = _run_git(["tag", "--list"])
    if code == 0:
        tags = [t.strip() for t in out.splitlines() if t.strip()]
        stats["tag_count"] = len(tags)
        stats["latest_tag"] = tags[-1] if tags else None
    else:
        stats["tag_count"] = 0
        stats["latest_tag"] = None

    code, out = _run_git(["branch", "--show-current"])
    stats["current_branch"] = out if code == 0 else None

    code, out = _run_git(["log", "--reverse", "--format=%aI", "-1"])
    stats["first_commit_date"] = out if code == 0 and out else None

    code, out = _run_git(["log", "--format=%aI", "-1"])
    stats["last_commit_date"] = out if code == 0 and out else None

    code, out = _run_git(["remote", "get-url", "origin"])
    stats["remote_url"] = out if code == 0 and out else None

    return stats


def _collect_file_git_stats() -> dict[str, dict]:
    """Collect per-file git commit counts and last commit dates.

    Uses a single ``git log`` pass with ``--name-only`` to extract
    commit counts and last-commit dates for all tracked files,
    instead of spawning two subprocess calls per file.
    """
    file_stats: dict[str, dict] = {}

    if _GIT_CMD is None:
        return file_stats

    # Single pass: get every commit's date and the files it touched.
    # Format: date on one line, then file names, separated by blank lines.
    code, out = _run_git(
        ["log", "--format=%aI", "--name-only", "HEAD"],
        timeout=120,
    )
    if code != 0 or not out:
        return file_stats

    current_date: str | None = None
    for line in out.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # ISO dates start with a digit; filenames don't start with a 4-digit year
        # pattern reliably, but ISO 8601 always matches YYYY-MM-DD
        if len(stripped) >= 10 and stripped[4] == "-" and stripped[7] == "-":
            current_date = stripped
        elif current_date:
            # It's a filename
            if stripped not in file_stats:
                file_stats[stripped] = {
                    "commits": 1,
                    "last_commit": current_date,
                }
            else:
                file_stats[stripped]["commits"] += 1

    return file_stats


def _collect_file_access_stats() -> dict[str, dict]:
    """Collect file access timestamps from the filesystem."""
    access_stats: dict[str, dict] = {}

    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [
            d for d in dirnames if d not in SKIP_DIRS and not d.endswith(".egg-info")
        ]

        for fname in filenames:
            filepath = Path(dirpath) / fname
            try:
                stat = filepath.stat()
                rel = str(filepath.relative_to(ROOT))
                atime = datetime.fromtimestamp(stat.st_atime, tz=UTC)
                mtime = datetime.fromtimestamp(stat.st_mtime, tz=UTC)
                access_stats[rel] = {
                    "last_accessed": atime.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "last_accessed_iso": atime.isoformat(),
                    "last_modified": mtime.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "last_modified_iso": mtime.isoformat(),
                }
            except OSError:
                continue

    return access_stats


def _detect_atime_policy() -> str:
    """Detect the filesystem access time (atime) policy for the repo's filesystem."""
    system = platform.system()

    if system == "Linux":
        try:
            mounts_text = Path("/proc/mounts").read_text(encoding="utf-8")
            best_mount = ""
            best_opts = ""
            repo_str = str(ROOT)
            for line in mounts_text.splitlines():
                parts = line.split()
                if len(parts) >= 4:
                    mount_point = parts[1]
                    options = parts[3]
                    if repo_str.startswith(mount_point) and len(mount_point) > len(
                        best_mount
                    ):
                        best_mount = mount_point
                        best_opts = options
            if best_opts:
                if "noatime" in best_opts:
                    return "noatime \u2014 access times are NOT updated on file reads"
                if "relatime" in best_opts:
                    return (
                        "relatime \u2014 access times updated ~once per day "
                        "or on modification"
                    )
                if "strictatime" in best_opts:
                    return "strictatime \u2014 access times updated on every file read"
                return f"mount options: {best_opts}"
        except OSError:
            pass
        return "unknown (could not read /proc/mounts)"

    if system == "Windows":
        return (
            "NTFS \u2014 last access updates are typically disabled by default "
            "since Windows Vista/Server 2008. "
            "Check with: `fsutil behavior query disablelastaccess`"
        )

    if system == "Darwin":
        return "APFS/HFS+ \u2014 access times are generally tracked by the filesystem"

    return "unknown"


def _collect_health_checks() -> list[tuple[str, bool, str]]:
    """Check for standard repository health indicators.

    Returns a list of (check_name, passed, description) tuples.
    """
    checks: list[tuple[str, bool, str]] = []

    checks.append(
        (
            "README",
            (ROOT / "README.md").exists() or (ROOT / "README.rst").exists(),
            "Has a README file",
        )
    )
    checks.append(
        (
            "LICENSE",
            (ROOT / "LICENSE").exists() or (ROOT / "LICENSE.md").exists(),
            "Has a LICENSE file",
        )
    )
    checks.append(
        (
            "Tests",
            (ROOT / "tests").is_dir() or (ROOT / "test").is_dir(),
            "Has a test directory",
        )
    )
    checks.append(
        (
            ".gitignore",
            (ROOT / ".gitignore").exists(),
            "Has a .gitignore file",
        )
    )
    checks.append(
        (
            "CI config",
            (ROOT / ".github" / "workflows").is_dir()
            or (ROOT / ".gitlab-ci.yml").exists()
            or (ROOT / ".circleci").is_dir(),
            "Has CI/CD configuration",
        )
    )
    checks.append(
        (
            "pyproject.toml",
            (ROOT / "pyproject.toml").exists()
            or (ROOT / "setup.py").exists()
            or (ROOT / "setup.cfg").exists()
            or (ROOT / "package.json").exists(),
            "Has a project configuration file",
        )
    )
    checks.append(
        (
            "CONTRIBUTING",
            (ROOT / "CONTRIBUTING.md").exists(),
            "Has contributing guidelines",
        )
    )
    checks.append(
        (
            "SECURITY",
            (ROOT / "SECURITY.md").exists(),
            "Has a security policy",
        )
    )
    checks.append(
        (
            "CHANGELOG",
            (ROOT / "CHANGELOG.md").exists() or (ROOT / "CHANGES.md").exists(),
            "Has a changelog",
        )
    )
    checks.append(
        (
            "Docs",
            (ROOT / "docs").is_dir(),
            "Has a documentation directory",
        )
    )

    return checks


def _collect_directory_sizes() -> list[tuple[str, int, int]]:
    """Get all directory sizes including all subdirectory contents, sorted largest-first.

    Each directory's reported size and file count includes files in all
    nested subdirectories, not just immediate children.
    """
    # Collect immediate file sizes per directory
    immediate: dict[str, tuple[int, int]] = {}

    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [
            d
            for d in dirnames
            if d not in SKIP_DIRS
            and not d.startswith(".")
            and not d.endswith(".egg-info")
        ]

        rel_path = Path(dirpath).relative_to(ROOT)
        if str(rel_path) == ".":
            continue

        total_size = 0
        file_count = 0
        for fname in filenames:
            try:
                total_size += (Path(dirpath) / fname).stat().st_size
            except OSError:
                continue
            file_count += 1

        immediate[str(rel_path)] = (total_size, file_count)

    # Aggregate: each directory includes its own files plus all descendant files
    aggregated: dict[str, list[int]] = {}
    for dir_path, (size, count) in immediate.items():
        current = Path(dir_path)
        while str(current) != ".":
            key = str(current)
            if key not in aggregated:
                aggregated[key] = [0, 0]
            aggregated[key][0] += size
            aggregated[key][1] += count
            current = current.parent

    result = [(name, vals[0], vals[1]) for name, vals in aggregated.items()]
    result.sort(key=lambda x: x[1], reverse=True)
    return result


def _build_repo_tree() -> str:
    """Build a full directory/file tree of the repository."""
    lines: list[str] = []
    repo_name = ROOT.name

    def _walk(directory: Path, prefix: str = "") -> None:
        entries = sorted(
            directory.iterdir(),
            key=lambda e: (not e.is_dir(), e.name.lower()),
        )
        entries = [
            e
            for e in entries
            if not (
                e.is_dir()
                and (
                    e.name in SKIP_DIRS
                    or e.name.startswith(".")
                    or e.name.endswith(".egg-info")
                )
            )
        ]

        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            connector = "\u2514\u2500\u2500 " if is_last else "\u251c\u2500\u2500 "
            extension = "    " if is_last else "\u2502   "

            if entry.is_dir():
                lines.append(f"{prefix}{connector}{entry.name}/")
                _walk(entry, prefix + extension)
            else:
                lines.append(f"{prefix}{connector}{entry.name}")

    lines.append(f"{repo_name}/")
    _walk(ROOT)
    return "\n".join(lines)


def _collect_code_execution_stats(
    file_git_stats: dict[str, dict],
) -> dict:
    """Estimate code/script activity from git commit frequency.

    Uses per-file commit counts as a proxy for how actively code and
    script files are used/developed.
    """
    code_runs: list[tuple[str, int, str | None]] = []
    script_runs: list[tuple[str, int, str | None]] = []

    for filepath, stats in file_git_stats.items():
        ext = Path(filepath).suffix.lower()
        entry = (filepath, stats["commits"], stats.get("last_commit"))

        if ext in _CODE_EXTENSIONS:
            code_runs.append(entry)
        if ext in _SCRIPT_EXTENSIONS:
            script_runs.append(entry)

    code_runs.sort(key=lambda x: x[1], reverse=True)
    script_runs.sort(key=lambda x: x[1], reverse=True)

    return {
        "code_files": code_runs[:30],
        "script_files": script_runs[:30],
    }


def _collect_test_coverage() -> dict:
    """Analyse which source code files have corresponding test files.

    Heuristic: for each code file ``foo.ext`` outside test directories,
    look for ``test_foo.ext`` or ``foo_test.ext`` anywhere under the
    test directories.
    """
    test_dir_files: dict[str, set[str]] = {}  # basename -> set of full paths
    source_files: list[str] = []

    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [
            d for d in dirnames if d not in SKIP_DIRS and not d.endswith(".egg-info")
        ]
        rel_parts = Path(dirpath).relative_to(ROOT).parts
        in_test_dir = any(part in _TEST_DIRS for part in rel_parts)

        for fname in filenames:
            ext = Path(fname).suffix.lower()
            if ext not in _CODE_EXTENSIONS:
                continue
            rel = str(Path(dirpath, fname).relative_to(ROOT))
            fname_lower = fname.lower()

            if (
                in_test_dir
                or any(fname_lower.startswith(p) for p in _TEST_PREFIXES)
                or any(fname_lower.endswith(s) for s in _TEST_SUFFIXES)
            ):
                stem = Path(fname).stem.lower()
                test_dir_files.setdefault(stem, set()).add(rel)
            else:
                source_files.append(rel)

    tested: list[str] = []
    untested: list[str] = []
    for src_path in sorted(source_files):
        stem = Path(src_path).stem.lower()
        # Check if any test file matches test_<stem> or <stem>_test
        has_test = f"test_{stem}" in test_dir_files or f"{stem}_test" in test_dir_files
        if has_test:
            tested.append(src_path)
        else:
            untested.append(src_path)

    return {
        "tested": tested,
        "untested": untested,
        "tested_count": len(tested),
        "untested_count": len(untested),
        "total_source": len(source_files),
    }


def _try_generate_coverage() -> bool:
    """Attempt to generate coverage.json by running ``coverage json``.

    If ``coverage.json`` and ``coverage.xml`` don't exist but the
    ``coverage`` tool is available and has data (from a prior test run),
    this asks it to export JSON.  Returns True if a file was created.
    """
    cov_cmd = shutil.which("coverage")
    if cov_cmd is None:
        return False
    # Check if .coverage database exists (created by pytest --cov or coverage run)
    cov_db = ROOT / ".coverage"
    if not cov_db.is_file():
        return False
    try:
        result = subprocess.run(  # nosec B603
            [cov_cmd, "json", "-o", str(ROOT / "coverage.json")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0 and (ROOT / "coverage.json").is_file()
    except (subprocess.TimeoutExpired, OSError):
        return False


def _parse_coverage_data() -> dict | None:
    """Parse pytest/coverage.py data from ``coverage.json`` or ``coverage.xml``.

    If neither file exists but a ``.coverage`` database is present (from a
    prior test run), attempts to auto-generate ``coverage.json`` via
    ``coverage json`` so users don't need an extra manual step.

    Returns a dict with overall and per-file line/branch coverage, or
    *None* if no coverage data file is found.
    """
    # --- Try coverage.json first (simplest, most data) ---
    cov_json = ROOT / "coverage.json"
    if cov_json.is_file():
        try:
            data = json.loads(cov_json.read_text(encoding="utf-8"))
            totals = data.get("totals", {})
            meta = data.get("meta", {})
            files_data = data.get("files", {})

            result: dict = {
                "source": "coverage.json",
                "line_pct": totals.get("percent_covered", 0.0),
                "covered_lines": totals.get("covered_lines", 0),
                "num_statements": totals.get("num_statements", 0),
                "missing_lines": totals.get("missing_lines", 0),
                "has_branch": bool(meta.get("branch_coverage")),
                "per_file": {},
            }
            if result["has_branch"]:
                nb = totals.get("num_branches", 0)
                cb = totals.get("covered_branches", 0)
                result["covered_branches"] = cb
                result["num_branches"] = nb
                result["branch_pct"] = (cb / nb * 100) if nb > 0 else 0.0

            for fpath, fdata in files_data.items():
                summary = fdata.get("summary", {})
                result["per_file"][fpath] = {
                    "line_pct": summary.get("percent_covered", 0.0),
                    "covered": summary.get("covered_lines", 0),
                    "statements": summary.get("num_statements", 0),
                }
            return result
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            log.debug("Failed to parse coverage.json", exc_info=True)

    # --- Try coverage.xml (Cobertura format) ---
    cov_xml = ROOT / "coverage.xml"
    if cov_xml.is_file():
        try:
            import xml.etree.ElementTree as ET  # nosec B405

            tree = ET.parse(cov_xml)  # nosec B314
            root_el = tree.getroot()

            line_rate = float(root_el.get("line-rate", "0"))
            branch_rate_str = root_el.get("branch-rate")
            lines_valid = int(root_el.get("lines-valid", "0"))
            lines_covered = int(root_el.get("lines-covered", "0"))

            result = {
                "source": "coverage.xml",
                "line_pct": line_rate * 100,
                "covered_lines": lines_covered,
                "num_statements": lines_valid,
                "missing_lines": lines_valid - lines_covered,
                "has_branch": branch_rate_str is not None,
                "per_file": {},
            }
            if result["has_branch"] and branch_rate_str:
                bv = int(root_el.get("branches-valid", "0"))
                bc = int(root_el.get("branches-covered", "0"))
                result["branch_pct"] = float(branch_rate_str) * 100
                result["covered_branches"] = bc
                result["num_branches"] = bv

            for cls in root_el.iter("class"):
                fname = cls.get("filename", "")
                lr = float(cls.get("line-rate", "0"))
                if fname:
                    result["per_file"][fname] = {"line_pct": lr * 100}
            return result
        except (ValueError, KeyError, TypeError):
            log.debug("Failed to parse coverage.xml", exc_info=True)

    # Neither file exists — try auto-generating from .coverage database
    if _try_generate_coverage():
        cov_json = ROOT / "coverage.json"
        if cov_json.is_file():
            try:
                data = json.loads(cov_json.read_text(encoding="utf-8"))
                totals = data.get("totals", {})
                meta = data.get("meta", {})
                files_data = data.get("files", {})
                result = {
                    "source": "coverage.json (auto-generated from .coverage)",
                    "line_pct": totals.get("percent_covered", 0.0),
                    "covered_lines": totals.get("covered_lines", 0),
                    "num_statements": totals.get("num_statements", 0),
                    "missing_lines": totals.get("missing_lines", 0),
                    "has_branch": bool(meta.get("branch_coverage")),
                    "per_file": {},
                }
                if result["has_branch"]:
                    nb = totals.get("num_branches", 0)
                    cb = totals.get("covered_branches", 0)
                    result["covered_branches"] = cb
                    result["num_branches"] = nb
                    result["branch_pct"] = (cb / nb * 100) if nb > 0 else 0.0
                for fpath, fdata in files_data.items():
                    summary = fdata.get("summary", {})
                    result["per_file"][fpath] = {
                        "line_pct": summary.get("percent_covered", 0.0),
                        "covered": summary.get("covered_lines", 0),
                        "statements": summary.get("num_statements", 0),
                    }
                return result
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                log.debug("Failed to parse auto-generated coverage.json", exc_info=True)

    return None


def _format_size(size_bytes: int) -> str:
    """Format byte size to human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


# ---------------------------------------------------------------------------
# Markdown helpers
# ---------------------------------------------------------------------------


_BADGE_COLORS: dict[str, str] = {
    "blue": "#007ec6",
    "brightgreen": "#4c1",
    "green": "#3c1",
    "yellow": "#dfb317",
    "orange": "#fe7d37",
    "red": "#e05d44",
    "purple": "#9f52e0",
    "lightgrey": "#9f9f9f",
}


def _md_badge(label: str, value: str, color: str = "blue") -> str:
    """Generate a shields.io Markdown image badge.

    Encodes the label and value for shields.io's URL format:
    dashes → ``--``, underscores → ``__``, spaces → ``_``.
    """

    def _encode(text: str) -> str:
        return text.replace("-", "--").replace("_", "__").replace(" ", "_")

    encoded_label = _encode(label)
    encoded_value = _encode(value)
    url = f"https://img.shields.io/badge/{encoded_label}-{encoded_value}-{color}"
    return f"![{label} {value}]({url})"


# ---------------------------------------------------------------------------
# Markdown report generator
# ---------------------------------------------------------------------------


def gather_stats(*, spinner: Spinner | None = None) -> dict:
    """Gather all repository statistics."""
    if spinner:
        spinner.update("Collecting file stats")
    file_stats = _collect_file_stats()

    if spinner:
        spinner.update("Collecting git stats")
    git_stats = _collect_git_stats()

    if spinner:
        spinner.update("Collecting directory sizes")
    directories = [
        {"name": n, "size_bytes": s, "file_count": c}
        for n, s, c in _collect_directory_sizes()
    ]

    if spinner:
        spinner.update("Collecting per-file git history")
    file_git_stats = _collect_file_git_stats()

    if spinner:
        spinner.update("Collecting file access stats")
    file_access_stats = _collect_file_access_stats()

    if spinner:
        spinner.update("Building repository tree")
    repo_tree = _build_repo_tree()

    if spinner:
        spinner.update("Analyzing code activity patterns")
    execution_stats = _collect_code_execution_stats(file_git_stats)

    if spinner:
        spinner.update("Checking repository health")
    health_checks = _collect_health_checks()

    if spinner:
        spinner.update("Detecting filesystem atime policy")
    atime_policy = _detect_atime_policy()

    if spinner:
        spinner.update("Analyzing test coverage")
    test_coverage = _collect_test_coverage()

    if spinner:
        spinner.update("Checking for pytest coverage data")
    pytest_coverage = _parse_coverage_data()

    return {
        "files": file_stats,
        "git": git_stats,
        "directories": directories,
        "file_git_stats": file_git_stats,
        "file_access_stats": file_access_stats,
        "repo_tree": repo_tree,
        "execution_stats": execution_stats,
        "health_checks": health_checks,
        "atime_policy": atime_policy,
        "test_coverage": test_coverage,
        "pytest_coverage": pytest_coverage,
    }


def generate_markdown(stats: dict) -> str:
    """Generate the full Markdown report from gathered statistics."""
    lines: list[str] = []
    now = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    file_stats = stats["files"]
    git_stats = stats["git"]
    file_git = stats.get("file_git_stats", {})
    file_access = stats.get("file_access_stats", {})
    execution = stats.get("execution_stats", {})
    health_checks = stats.get("health_checks", [])
    atime_policy = stats.get("atime_policy", "unknown")
    test_coverage = stats.get("test_coverage", {})
    pytest_cov = stats.get("pytest_coverage")
    repo_name = ROOT.name
    current_files = file_stats.get("all_file_paths", set())

    # ── Title ──
    lines.append(f"# \U0001f534 Repository Sauron Report \u2014 {repo_name}")
    lines.append("")
    lines.append("> *The all-seeing eye peers into every corner of your repository.*")
    lines.append("")
    lines.append(f"\U0001f552 **Generated:** {now}  ")
    lines.append(f"\U0001f4e6 **Version:** {SCRIPT_VERSION}  ")
    if git_stats.get("current_branch"):
        lines.append(f"\U0001f33f **Branch:** `{git_stats['current_branch']}`")
    lines.append("")

    # ── Badges ──
    badges: list[str] = []
    badges.append(_md_badge("total files", str(file_stats["total_files"]), "blue"))
    badges.append(
        _md_badge("size", _format_size(file_stats["total_size_bytes"]), "green")
    )
    if git_stats.get("available"):
        badges.append(
            _md_badge(
                "total repo commits", str(git_stats.get("total_commits", 0)), "orange"
            )
        )
        badges.append(
            _md_badge("contributors", str(git_stats.get("author_count", 0)), "purple")
        )
    badges.append(
        _md_badge(
            "code files", str(file_stats.get("code_file_count", 0)), "brightgreen"
        )
    )
    badges.append(
        _md_badge("script files", str(file_stats.get("script_file_count", 0)), "yellow")
    )
    badges.append(
        _md_badge("test files", str(file_stats.get("test_file_count", 0)), "red")
    )
    # Badges on one line separated by spaces (shields.io images render inline)
    lines.append(" ".join(badges))
    lines.append("")

    # ── Table of Contents ──
    lines.append("---")
    lines.append("")
    lines.append("## \U0001f4d1 Table of Contents")
    lines.append("")
    lines.append("- [Overview](#-overview)")
    lines.append("- [Repository Health](#-repository-health)")
    lines.append("- [Repository Structure](#-repository-structure)")
    lines.append("- [File Types](#-file-types)")
    lines.append("- [Languages](#-languages)")
    lines.append("- [Code & Script Activity](#-code--script-activity)")
    lines.append("- [Directory Sizes](#-directory-sizes)")
    lines.append("- [Largest Files](#-largest-files)")
    lines.append("- [Test Coverage](#-test-coverage)")
    lines.append("- [File Access Statistics](#-file-access-statistics)")
    lines.append("- [Git History](#-git-history)")
    lines.append("- [Recently Modified Files](#-recently-modified-files)")
    lines.append("- [Per-File Git Statistics](#-per-file-git-statistics)")
    lines.append("- [Contributors](#-contributors)")
    lines.append("- [Recommended Scripts](#-recommended-scripts)")
    lines.append("- [Recommended VS Code Extensions](#-recommended-vs-code-extensions)")
    lines.append("")

    # ── Overview ──
    lines.append("---")
    lines.append("")
    lines.append("## \U0001f4ca Overview")
    lines.append("")
    lines.append("> **\u2139\ufe0f Note:** High-level repository metrics at a glance.")
    lines.append("")
    lines.append(
        "> **Code files** count extensions: "
        + ", ".join(
            f"`{e}`"
            for e in file_stats.get("found_code_extensions", sorted(_CODE_EXTENSIONS))
        )
        + ".  "
    )
    lines.append(
        "> **Script files** count extensions: "
        + ", ".join(
            f"`{e}`"
            for e in file_stats.get(
                "found_script_extensions", sorted(_SCRIPT_EXTENSIONS)
            )
        )
        + ".  "
    )
    found_test_exts = file_stats.get("found_test_extensions", [".py"])
    test_ext_list = (
        ", ".join(f"`{e}`" for e in found_test_exts) if found_test_exts else "`.py`"
    )
    lines.append(
        f"> **Test files** are {test_ext_list} files inside `tests/`/`test/` dirs, "
        "or matching `test_*`/`*_test` patterns."
    )
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| \U0001f4c4 **Total files** | {file_stats['total_files']} |")
    lines.append(f"| \U0001f4c2 **Total directories** | {file_stats['total_dirs']} |")
    lines.append(
        f"| \U0001f4be **Total size** | {_format_size(file_stats['total_size_bytes'])} |"
    )
    avg_file = file_stats.get("avg_file_size_bytes", 0)
    if avg_file:
        lines.append(f"| \U0001f4cf **Avg file size** | {_format_size(avg_file)} |")
    lines.append(
        f"| \U0001f4bb **Code files** | {file_stats.get('code_file_count', 0)} |"
    )
    lines.append(
        f"| \U0001f4dc **Script files** | {file_stats.get('script_file_count', 0)} |"
    )
    lines.append(
        f"| \U0001f9ea **Test files** | {file_stats.get('test_file_count', 0)} |"
    )
    lines.append(
        f"| \U0001f4dd **Documentation files** | {file_stats.get('doc_file_count', 0)} |"
    )
    lines.append(
        f"| \u2699\ufe0f **Configuration files** | {file_stats.get('config_file_count', 0)} |"
    )
    lines.append(
        f"| \U0001f4e6 **Estimated binary files** | {file_stats.get('binary_file_count', 0)} |"
    )
    empty = file_stats.get("empty_file_count", 0)
    if empty:
        lines.append(f"| \u26a0\ufe0f **Empty files (0 bytes)** | {empty} |")

    dir_stats = stats["directories"]
    if dir_stats:
        total_dir_size = sum(d["size_bytes"] for d in dir_stats)
        dir_count = len(dir_stats)
        avg_dir = total_dir_size // dir_count if dir_count else 0
        lines.append(
            f"| **Avg directory size** | {_format_size(avg_dir)} ({dir_count} dirs) |"
        )

    total_lines = sum(file_stats["extension_lines"].values())
    if total_lines:
        lines.append(
            f"| \U0001f4d6 **Total lines (code + text + blanks)** | {total_lines:,} |"
        )

    if git_stats.get("available"):
        lines.append(
            f"| \U0001f4e6 **Total git commits** | {git_stats.get('total_commits', 0)} |"
        )
    lines.append("")

    # ── Repository Health ──
    if health_checks:
        lines.append("---")
        lines.append("")
        lines.append("## \U0001fa7a Repository Health")
        lines.append("")
        lines.append(
            "> **\u2139\ufe0f Note:** Quick pass/fail checks for standard "
            "repository health indicators."
        )
        lines.append("")
        hc_rows: list[list[str]] = []
        for name, passed, description in health_checks:
            status = "\u2705" if passed else "\u274c"
            hc_rows.append([f"{status} **{name}**", description])
        lines.extend(_aligned_table(["Check", "Description"], hc_rows, "ll"))
        lines.append("")

    # ── Repository Structure ──
    lines.append("---")
    lines.append("")
    lines.append("## \U0001f333 Repository Structure")
    lines.append("")
    lines.append(
        "> **\U0001f4a1 Tip:** This tree is **dynamically generated** by scanning "
        "the repository at runtime. It reflects the actual state of whichever "
        "git repository this script is run in \u2014 not a hard-coded snapshot."
    )
    lines.append(">")
    lines.append(
        "> Build artifacts and caches "
        f"({', '.join(f'`{d}`' for d in sorted(list(SKIP_DIRS)[:8]))}, \u2026) "
        "are excluded."
    )
    lines.append("")
    lines.append("<details>")
    lines.append(
        "<summary><strong>Click to expand full repository tree</strong></summary>"
    )
    lines.append("")
    lines.append("```")
    lines.append(stats.get("repo_tree", "(tree unavailable)"))
    lines.append("```")
    lines.append("")
    lines.append("</details>")
    lines.append("")

    # ── File Types ──
    lines.append("---")
    lines.append("")
    lines.append("## \U0001f4c1 File Types")
    lines.append("")
    lines.append("> **\U0001f4a1 Tip:** Most common file extensions in the repository.")
    lines.append(">")
    lines.append(
        "> **Lines** = raw newline-separated line count including code, "
        "comments, blank lines, and whitespace-only lines. "
        "Counted for text-based file types only."
    )
    lines.append("")
    ext_counts = file_stats["extension_counts"]
    if ext_counts:
        lines_by_ext = file_stats["extension_lines"]
        ft_rows: list[list[str]] = []
        for ext, count in list(ext_counts.items())[:15]:
            line_count = lines_by_ext.get(ext)
            line_str = f"{line_count:,}" if line_count else "\u2014"
            badge = _ext_badge(ext)
            ft_rows.append([badge, str(count), line_str])
        lines.extend(_aligned_table(["Extension", "Files", "Lines"], ft_rows, "lrr"))
        lines.append("")

    # ── Languages ──
    languages = file_stats.get("languages", [])
    if languages:
        lines.append("---")
        lines.append("")
        lines.append("## \U0001f5e3\ufe0f Languages")
        lines.append("")
        lines.append(
            "> **\u2139\ufe0f Note:** Language breakdown by file count "
            "(percentage of recognized files)."
        )
        lines.append(">")
        lines.append(
            "> **Lines** = total newline-separated lines (code + comments + blanks). "
            "Languages are identified by file extension."
        )
        lines.append("")
        lang_rows: list[list[str]] = []
        for lang in languages:
            pct_str = f"{lang['percentage']:.1f}%"
            lang_lines = f"{lang['lines']:,}" if lang["lines"] else "\u2014"
            badge = _lang_badge(lang["language"])
            lang_rows.append(
                [
                    badge,
                    str(lang["files"]),
                    lang_lines,
                    pct_str,
                ]
            )
        lines.extend(
            _aligned_table(["Language", "Files", "Lines", "%"], lang_rows, "lrrr")
        )
        lines.append("")

        # Language bar chart using diff code block for color
        lines.append("```diff")
        for lang in languages[:10]:
            bar_len = max(1, int(lang["percentage"] / 2))
            bar = "\u2588" * bar_len
            lines.append(f"+ {lang['language']:<20s} {bar} {lang['percentage']:.1f}%")
        lines.append("```")
        lines.append("")

    # ── Code & Script Activity ──
    lines.append("---")
    lines.append("")
    lines.append("## \u26a1 Code & Script Activity")
    lines.append("")
    lines.append(
        "> **\u2139\ufe0f Note:** Commit frequency per file as a proxy for how actively code "
    )
    lines.append("> and scripts are used/developed.")
    lines.append(
        "> Files with more commits are being changed (and likely run) more frequently."
    )
    lines.append("")

    code_files = execution.get("code_files", [])
    script_files = execution.get("script_files", [])

    if code_files:
        lines.append("### Code Files (by commit activity)")
        lines.append("")
        cf_rows: list[list[str]] = []
        for filepath, commits, last_commit in code_files[:20]:
            last_date = last_commit[:10] if last_commit else "\u2014"
            cf_rows.append([f"`{filepath}`", str(commits), last_date])
        lines.extend(_aligned_table(["File", "Commits", "Last Commit"], cf_rows, "lrl"))
        lines.append("")

    if script_files:
        lines.append("### Script Files (by commit activity)")
        lines.append("")
        sf_rows: list[list[str]] = []
        for filepath, commits, last_commit in script_files[:20]:
            last_date = last_commit[:10] if last_commit else "\u2014"
            sf_rows.append([f"`{filepath}`", str(commits), last_date])
        lines.extend(
            _aligned_table(["Script", "Commits", "Last Commit"], sf_rows, "lrl")
        )
        lines.append("")

    # ── Directory Sizes ──
    if dir_stats:
        lines.append("---")
        lines.append("")
        lines.append("## \U0001f4e6 Directory Sizes")
        lines.append("")
        lines.append(
            f"> **\u2139\ufe0f Note:** All {len(dir_stats)} directories sorted by "
            "size (largest first). Each directory's size includes all files in "
            "all nested subdirectories, not just immediate children."
        )
        lines.append("")
        lines.append("<details>")
        lines.append(
            "<summary><strong>Click to expand directory sizes</strong></summary>"
        )
        lines.append("")
        ds_rows: list[list[str]] = [
            [f"`{d['name']}/`", _format_size(d["size_bytes"]), str(d["file_count"])]
            for d in dir_stats
        ]
        lines.extend(_aligned_table(["Directory", "Size", "Files"], ds_rows, "lrr"))
        lines.append("")
        lines.append("</details>")
        lines.append("")

    # ── Largest Files ──
    largest = file_stats["largest_files"]
    if largest:
        lines.append("---")
        lines.append("")
        lines.append("## \U0001f418 Largest Files")
        lines.append("")
        lines.append(
            "> **\u2757 Important:** Individual files sorted by size (top 15)."
        )
        lines.append("")
        lf_rows: list[list[str]] = []
        for path, size in largest:
            lf_rows.append([f"`{path}`", _format_size(size)])
        lines.extend(_aligned_table(["File", "Size"], lf_rows, "lr"))
        lines.append("")

    # ── Test Coverage ──
    if test_coverage and test_coverage.get("total_source", 0) > 0:
        tc = test_coverage
        tested = tc["tested_count"]
        untested = tc["untested_count"]
        total_src = tc["total_source"]
        pct = round(tested / total_src * 100, 1) if total_src else 0

        lines.append("---")
        lines.append("")
        lines.append("## \U0001f9ea Test Coverage")
        lines.append("")
        lines.append(
            "> **\u2139\ufe0f Note:** Heuristic coverage analysis \u2014 each source code "
            "file is checked for a corresponding `test_<name>` or "
            "`<name>_test` file in the test directories.  "
        )
        if pytest_cov:
            lines.append("> Line/branch coverage from `pytest --cov` is shown below.")
        else:
            lines.append(
                "> This does **not** measure line/branch coverage. "
                "Run `pytest --cov --cov-report=json` to generate "
                "`coverage.json`, then re-run this script."
            )
        lines.append("")

        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| \U0001f4c1 **Source code files** | {total_src} |")
        lines.append(f"| \u2705 **Files with tests** | {tested} |")
        lines.append(f"| \u274c **Files without tests** | {untested} |")
        lines.append(f"| \U0001f4ca **Coverage (by file)** | {pct}% |")
        lines.append("")

        # Mermaid pie chart
        lines.append("```mermaid")
        lines.append("pie title Test Coverage (by file)")
        if tested:
            lines.append(f'    "Tested" : {tested}')
        if untested:
            lines.append(f'    "Untested" : {untested}')
        lines.append("```")
        lines.append("")

        if tc.get("untested"):
            lines.append("<details>")
            lines.append(
                "<summary><strong>Click to expand untested source files "
                f"({untested} files)</strong></summary>"
            )
            lines.append("")
            lines.extend(f"- `{f}`" for f in tc["untested"])
            lines.append("")
            lines.append("</details>")
            lines.append("")

    # ── Pytest / coverage.py data (line & branch coverage) ──
    if pytest_cov:
        lines.append("### \U0001f4ca Line & Branch Coverage (pytest --cov)")
        lines.append("")
        lines.append(
            f"> **Source:** `{pytest_cov['source']}` found in repository root."
        )
        lines.append("")

        line_pct = pytest_cov.get("line_pct", 0.0)
        covered = pytest_cov.get("covered_lines", 0)
        statements = pytest_cov.get("num_statements", 0)
        missing = pytest_cov.get("missing_lines", 0)

        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| \U0001f4cf **Statements** | {statements:,} |")
        lines.append(f"| \u2705 **Covered lines** | {covered:,} |")
        lines.append(f"| \u274c **Missing lines** | {missing:,} |")
        lines.append(f"| \U0001f4ca **Line coverage** | {line_pct:.1f}% |")

        if pytest_cov.get("has_branch"):
            nb = pytest_cov.get("num_branches", 0)
            cb = pytest_cov.get("covered_branches", 0)
            bp = pytest_cov.get("branch_pct", 0.0)
            lines.append(f"| \U0001f500 **Branches** | {nb:,} |")
            lines.append(f"| \u2705 **Covered branches** | {cb:,} |")
            lines.append(f"| \U0001f500 **Branch coverage** | {bp:.1f}% |")
        lines.append("")

        # Mermaid pie chart for line coverage
        lines.append("```mermaid")
        lines.append("pie title Line Coverage (pytest --cov)")
        if covered:
            lines.append(f'    "Covered" : {covered}')
        if missing:
            lines.append(f'    "Missing" : {missing}')
        lines.append("```")
        lines.append("")

        # Per-file table: show lowest-covered files
        per_file = pytest_cov.get("per_file", {})
        if per_file:
            sorted_files = sorted(
                per_file.items(), key=lambda x: x[1].get("line_pct", 0)
            )
            low_cov = [
                (fp, fd) for fp, fd in sorted_files if fd.get("line_pct", 0) < 100
            ]
            if low_cov:
                show = low_cov[:20]
                lines.append("<details>")
                lines.append(
                    "<summary><strong>Click to expand files below 100% coverage "
                    f"(showing {len(show)} of {len(low_cov)})</strong></summary>"
                )
                lines.append("")
                lines.append("| File | Coverage | Lines |")
                lines.append("|------|----------|-------|")
                for fp, fd in show:
                    pct = fd.get("line_pct", 0.0)
                    stmts = fd.get("statements", "")
                    cov = fd.get("covered", "")
                    detail = f"{cov}/{stmts}" if stmts else ""
                    lines.append(f"| `{fp}` | {pct:.1f}% | {detail} |")
                lines.append("")
                lines.append("</details>")
                lines.append("")

    # ── File Access Statistics ──
    lines.append("---")
    lines.append("")
    lines.append("## \U0001f550 File Access Statistics")
    lines.append("")
    lines.append(
        "> **\u26a0\ufe0f Warning:** File access times (`atime`) depend on "
        "OS/filesystem configuration."
    )
    lines.append(">")
    lines.append(
        "> **`relatime`** \u2014 access times updated approximately once per day "
        "or when file is modified (common Linux default).  "
    )
    lines.append(
        "> **`noatime`** \u2014 access times are never updated on read "
        "(performance optimization, timestamps may be stale).  "
    )
    lines.append(
        "> **`strictatime`** \u2014 access times updated on every read "
        "(most accurate but slowest).  "
    )
    lines.append(">")
    lines.append(f"> **Detected policy:** {atime_policy}")
    lines.append(">")
    lines.append(
        "> **Detection method:** `atime`/`mtime` gathered via Python "
        "`pathlib.Path.stat()` (OS-level `stat(2)` syscall).  "
    )
    _sys_name = platform.system()
    if _sys_name == "Linux":
        _atime_how = (
            "atime policy auto-detected by parsing `/proc/mounts` for the "
            "mount point containing this repository (dynamic, Linux-specific)."
        )
    elif _sys_name == "Windows":
        _atime_how = (
            "atime policy based on known NTFS defaults "
            "(typically disabled since Vista/Server 2008; "
            "verify with `fsutil behavior query disablelastaccess`)."
        )
    elif _sys_name == "Darwin":
        _atime_how = "atime policy based on known APFS/HFS+ behaviour (macOS)."
    else:
        _atime_how = "atime policy could not be auto-detected on this OS."
    lines.append(f"> **Policy detection:** {_atime_how}")
    lines.append("")

    if file_access:
        sorted_access = sorted(
            file_access.items(),
            key=lambda x: x[1]["last_accessed_iso"],
            reverse=True,
        )

        lines.append("<details>")
        lines.append(
            "<summary><strong>Click to expand file access stats "
            f"({len(sorted_access)} files)</strong></summary>"
        )
        lines.append("")
        fa_rows: list[list[str]] = []
        for filepath, access_info in sorted_access:
            fa_rows.append(
                [
                    f"`{filepath}`",
                    access_info["last_accessed"],
                    access_info.get("last_modified", "\u2014"),
                ]
            )
        lines.extend(
            _aligned_table(
                ["File", "Last Accessed (atime)", "Last Modified (mtime)"],
                fa_rows,
                "lll",
            )
        )
        lines.append("")
        lines.append("</details>")
        lines.append("")

    # ── Git History ──
    if git_stats.get("available"):
        lines.append("---")
        lines.append("")
        lines.append("## \U0001f4dc Git History")
        lines.append("")
        lines.append("> **\u2139\ufe0f Note:** Repository version control summary.")
        lines.append("")
        gh_rows: list[list[str]] = [
            [
                "\U0001f4e6 **Total git commits**",
                str(git_stats.get("total_commits", 0)),
            ],
            ["\U0001f465 **Contributors**", str(git_stats.get("author_count", 0))],
            ["\U0001f33f **Branches**", str(git_stats.get("branch_count", 0))],
            ["\U0001f3f7\ufe0f **Tags**", str(git_stats.get("tag_count", 0))],
        ]
        if git_stats.get("current_branch"):
            gh_rows.append(["**Current branch**", f"`{git_stats['current_branch']}`"])
        if git_stats.get("latest_tag"):
            gh_rows.append(["**Latest tag**", f"`{git_stats['latest_tag']}`"])
        if git_stats.get("first_commit_date"):
            gh_rows.append(["**First commit**", git_stats["first_commit_date"][:10]])
        if git_stats.get("last_commit_date"):
            gh_rows.append(["**Last commit**", git_stats["last_commit_date"][:10]])
        if git_stats.get("remote_url"):
            gh_rows.append(["**Remote**", f"`{git_stats['remote_url']}`"])
        lines.extend(_aligned_table(["Metric", "Value"], gh_rows, "ll"))
        lines.append("")

    # ── Recently Modified Files ──
    if file_git:
        lines.append("---")
        lines.append("")
        lines.append("## \U0001f525 Recently Modified Files")
        lines.append("")
        lines.append(
            "> **\u2139\ufe0f Note:** Files with the most recent git commit dates, "
            "showing what parts of the codebase are actively being worked on."
        )
        lines.append("")
        recent_files = sorted(
            (
                (fp, fs)
                for fp, fs in file_git.items()
                if not current_files or fp in current_files
            ),
            key=lambda x: x[1].get("last_commit", ""),
            reverse=True,
        )
        rf_rows: list[list[str]] = []
        for filepath, fstats in recent_files[:20]:
            last_date = (
                fstats["last_commit"][:10] if fstats.get("last_commit") else "\u2014"
            )
            rf_rows.append([f"`{filepath}`", last_date, str(fstats["commits"])])
        lines.extend(
            _aligned_table(
                ["File", "Last Commit Date", "Total Commits"],
                rf_rows,
                "llr",
            )
        )
        lines.append("")

    # ── Per-File Git Statistics ──
    if file_git:
        lines.append("---")
        lines.append("")
        lines.append("## \U0001f4dd Per-File Git Statistics")
        lines.append("")
        lines.append(
            "> **\U0001f4a1 Tip:** Every tracked file with its total git commit count "
            "(number of commits that touched this file) and last known commit date "
            "(date of the most recent commit that modified this file)."
        )
        lines.append(">")
        lines.append(
            "> **Detection method:** `git log --name-only HEAD` "
            "(single-pass extraction of commit counts and dates)."
        )
        lines.append("")

        # Filter to only currently existing files so count matches badge
        filtered_git = {
            fp: fs
            for fp, fs in file_git.items()
            if not current_files or fp in current_files
        }
        historical_count = len(file_git) - len(filtered_git)

        sorted_files = sorted(
            filtered_git.items(),
            key=lambda x: x[1]["commits"],
            reverse=True,
        )

        summary = f"({len(sorted_files)} files)"
        if historical_count > 0:
            summary = (
                f"({len(sorted_files)} current files; "
                f"{historical_count} deleted/renamed files omitted)"
            )

        lines.append("<details>")
        lines.append(
            f"<summary><strong>Click to expand per-file git stats "
            f"{summary}</strong></summary>"
        )
        lines.append("")
        pfg_rows: list[list[str]] = []
        for filepath, fstats in sorted_files:
            last_date = (
                fstats["last_commit"][:10] if fstats.get("last_commit") else "\u2014"
            )
            pfg_rows.append([f"`{filepath}`", str(fstats["commits"]), last_date])
        lines.extend(
            _aligned_table(
                ["File", "Total Git Commits", "Last Known Commit Date"],
                pfg_rows,
                "lrl",
            )
        )
        lines.append("")
        lines.append("</details>")
        lines.append("")

    # ── Contributors ──
    authors = git_stats.get("authors", []) if git_stats.get("available") else []
    if authors:
        total_count = git_stats.get("author_count", len(authors))
        shown = min(len(authors), 10)
        lines.append("---")
        lines.append("")
        lines.append("## \U0001f465 Contributors")
        lines.append("")
        lines.append(f"> Top {shown} of {total_count} contributors, ranked by commits.")
        lines.append("")
        ct_rows: list[list[str]] = [
            [f"**{a['name']}**", str(a["commits"])] for a in authors[:10]
        ]
        if total_count > 10:
            ct_rows.append([f"*... and {total_count - 10} more*", ""])
        lines.extend(_aligned_table(["Contributor", "Commits"], ct_rows, "lr"))
        lines.append("")

    # ── Recommended Scripts ──
    lines.append("---")
    lines.append("")
    lines.append("## \U0001f9f0 Recommended Scripts")
    lines.append("")
    lines.append("> Scripts that expand on repository information and health checks.")
    lines.append(">")
    remote_url = git_stats.get("remote_url", "") if git_stats.get("available") else ""
    if remote_url:
        lines.append(f"> **Source:** `{remote_url}`")
    else:
        lines.append(
            "> **Source:** "
            "[simple-python-boilerplate]"
            "(https://github.com/JoJo275/simple-python-boilerplate) "
            "by [JoJo275](https://github.com/JoJo275) on GitHub"
        )
    lines.append(">")
    lines.append("> Scripts are located in the `scripts/` directory.")
    lines.append("")
    # Use a spaced list instead of a dense table for readability
    _scripts = [
        (
            "\u2705",
            "python scripts/git_doctor.py",
            "Git health dashboard \u2014 config, branch ops, integrity",
            "Any git repo",
        ),
        (
            "\u2705",
            "python scripts/repo_sauron.py",
            "Full repository statistics dashboard (this script)",
            "Any git repo",
        ),
        (
            "\u2705",
            "python scripts/env_inspect.py",
            "Environment, packages, PATH inspection",
            "Any project",
        ),
        (
            "\u2705",
            "python scripts/workflow_versions.py",
            "GitHub Actions SHA-pinned version status",
            "Any GitHub repo",
        ),
        (
            "\u2705",
            "python scripts/repo_doctor.py",
            "Repository structure health checks",
            "Any git repo",
        ),
        (
            "\U0001f40d",
            "python scripts/check_python_support.py",
            "Python version consistency across configs",
            "Python only",
        ),
        (
            "\U0001f40d",
            "python scripts/dep_versions.py show",
            "Dependency versions and update status",
            "Python only",
        ),
        (
            "\U0001f40d",
            "python scripts/env_doctor.py",
            "Development environment diagnostics",
            "Python only",
        ),
        (
            "\U0001f40d",
            "python scripts/doctor.py",
            "Unified health check (runs all doctors)",
            "Python only",
        ),
    ]
    for icon, cmd, desc, compat in _scripts:
        lines.append(f"- {icon} **`{cmd}`**")
        lines.append(
            f"  {desc} \u00a0 "
            f"![{compat}](https://img.shields.io/badge/{compat.replace(' ', '%20')}-0969DA?style=flat-square)"
        )
        lines.append("")

    # ── Recommended VS Code Extensions ──
    lines.append("---")
    lines.append("")
    lines.append("## \U0001f4e6 Recommended VS Code Extensions")
    lines.append("")
    lines.append(
        "> Install these extensions for the best experience when "
        "viewing this report in VS Code."
    )
    lines.append("")
    _extensions = [
        (
            "bierner.markdown-mermaid",
            "Markdown Preview Mermaid Support",
            "Renders Mermaid charts (pie, flowchart) in markdown preview",
        ),
        (
            "shd101wyy.markdown-preview-enhanced",
            "Markdown Preview Enhanced",
            "Rich preview with colour blocks, badges, code charts, and more",
        ),
        (
            "kamikillerto.vscode-colorize",
            "Colorize",
            "Visualises colour codes (hex, rgb) inline in any file",
        ),
        (
            "yzhang.markdown-all-in-one",
            "Markdown All in One",
            "TOC generation, auto-formatting, list editing, math",
        ),
        (
            "bierner.markdown-checkbox",
            "Markdown Checkboxes",
            "Clickable task list checkboxes in preview",
        ),
        (
            "bierner.github-markdown-preview",
            "GitHub Markdown Preview",
            "GitHub-flavored markdown rendering including alerts and badges",
        ),
    ]
    for ext_id, name, desc in _extensions:
        lines.append(f"- **{name}** (`{ext_id}`)")
        lines.append(f"  {desc}")
        lines.append("")

    # ── Repository Velocity ──
    if git_stats.get("available"):
        first_date = git_stats.get("first_commit_date", "")[:10]
        last_date = git_stats.get("last_commit_date", "")[:10]
        total_commits = git_stats.get("total_commits", 0)
        if first_date and last_date and total_commits > 1:
            try:
                d1 = datetime.fromisoformat(first_date + "T00:00:00+00:00").date()
                d2 = datetime.fromisoformat(last_date + "T00:00:00+00:00").date()
                days = max((d2 - d1).days, 1)
                weeks = max(days / 7, 1)
                commits_per_week = round(total_commits / weeks, 1)

                lines.append("---")
                lines.append("")
                lines.append("## \U0001f680 Repository Velocity")
                lines.append("")
                lines.append(
                    "> **\u2139\ufe0f Note:** Commit activity over the "
                    "lifetime of the repository."
                )
                lines.append("")
                lines.append("| Metric | Value |")
                lines.append("|--------|-------|")
                lines.append(f"| \U0001f4c5 **First commit** | {first_date} |")
                lines.append(f"| \U0001f4c5 **Latest commit** | {last_date} |")
                lines.append(f"| \U0001f4c6 **Repository age** | {days} days |")
                lines.append(f"| \u26a1 **Commits per week** | {commits_per_week} |")
                lines.append(f"| \U0001f4e6 **Total commits** | {total_commits} |")
                lines.append("")
            except (ValueError, TypeError):
                pass

    # ── Footer ──
    lines.append("---")
    lines.append("")
    lines.append(
        f"<sub>Generated by <strong>repo_sauron.py</strong> "
        f"v{SCRIPT_VERSION} \u2014 the all-seeing eye \u2022 {now}</sub>"
    )
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="repo-sauron",
        description=(
            "Repository statistics dashboard \u2014 generates a Markdown report."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {SCRIPT_VERSION}",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="repo-sauron-report.md",
        help="Output file path (default: repo-sauron-report.md)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output as JSON instead of Markdown",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress output; exit code only",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Quick import and arg-parse health check; exit 0 immediately",
    )
    args = parser.parse_args()

    if args.smoke:
        print(f"repo_sauron {SCRIPT_VERSION}: smoke ok")
        return 0

    level = logging.WARNING if args.quiet else logging.INFO
    logging.basicConfig(format="%(message)s", level=level)

    c = Colors()
    start = time.monotonic()

    with Spinner("Scanning repository", color="magenta") as spin:
        stats = gather_stats(spinner=spin)

    elapsed = time.monotonic() - start

    if args.json_output:
        json_stats = {k: v for k, v in stats.items() if k != "repo_tree"}
        json_stats["repo_tree_lines"] = stats.get("repo_tree", "").count("\n") + 1
        print(json.dumps(json_stats, indent=2))
        if not args.quiet:
            print(
                f"\n{c.dim(f'Completed in {elapsed:.1f}s')}",
                file=sys.stderr,
            )
    else:
        markdown = generate_markdown(stats)
        output_path = Path(args.output)
        output_path.write_text(markdown, encoding="utf-8")

        if not args.quiet:
            print()
            checkmark = "\u2713"
            print(f"  {c.green(checkmark)} {c.bold('Report generated successfully')}")
            print(f"  {c.dim('File:')} {c.cyan(str(output_path.resolve()))}")
            elapsed_str = f"Completed in {elapsed:.1f}s"
            print(f"  {c.dim(elapsed_str)}")
            print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
