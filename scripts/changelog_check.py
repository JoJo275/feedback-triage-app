#!/usr/bin/env python3
"""Verify CHANGELOG.md entries match git tags.

Compares version headings in CHANGELOG.md against git tags to detect
drift between what release-please generates and what's actually tagged.
Also checks for duplicate entries and correct ordering.

Flags::

    -v, --verbose           Show versions that are in sync
    -q, --quiet             Suppress output; exit code only (for CI)
    --changelog-path PATH   Path to CHANGELOG.md (default: CHANGELOG.md)
    --version               Print version and exit

Usage::

    python scripts/changelog_check.py
    python scripts/changelog_check.py --verbose
    python scripts/changelog_check.py --quiet       # Exit code only (for CI)
    python scripts/changelog_check.py --changelog-path docs/CHANGES.md

    Task runner shortcuts for this script are defined in ``Taskfile.yml``.

Portability:
    Can be used in any repo with a Keep a Changelog-style CHANGELOG.md
    and semver git tags.  Requires shared modules: ``_colors.py``,
    ``_imports.py``, ``_ui.py``.
"""

from __future__ import annotations

import argparse
import logging
import re
import subprocess  # nosec B404
from pathlib import Path

# -- Local script modules (not third-party; live in scripts/) ----------------
from _colors import Colors
from _imports import find_repo_root
from _ui import UI

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ROOT = find_repo_root()
CHANGELOG = ROOT / "CHANGELOG.md"
SCRIPT_VERSION = "1.4.0"

# Theme color for this script's dashboard output.
THEME = "magenta"

# TODO (template users): If your project uses a different changelog
#   format (e.g. Keep a Changelog without release-please), update
#   VERSION_HEADING_RE to match your heading style.
# Matches release-please style headings: ## [1.2.3](url) (date) or ## 1.2.3
VERSION_HEADING_RE = re.compile(
    r"^##\s+\[?(\d+\.\d+\.\d+(?:[a-zA-Z0-9.+-]*)?)\]?",
    re.MULTILINE,
)

# Git tag pattern (release-please convention)
TAG_RE = re.compile(r"^v(\d+\.\d+\.\d+(?:[a-zA-Z0-9.+-]*)?)$")

# release-please generates headings like: ## [1.2.3](url) (date)
# Manually written entries look like:     ## 0.1.0 (date)
_RP_HEADING_RE = re.compile(
    r"^##\s+\[(\d+\.\d+\.\d+(?:[a-zA-Z0-9.+-]*)?)\]\(",
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


def get_changelog_versions(changelog_path: Path) -> list[str]:
    """Extract version numbers from CHANGELOG.md headings.

    Args:
        changelog_path: Path to the CHANGELOG.md file.

    Returns:
        List of version strings found in headings, in file order.
    """
    if not changelog_path.exists():
        return []
    text = changelog_path.read_text(encoding="utf-8")
    return VERSION_HEADING_RE.findall(text)


def get_git_tag_versions() -> list[str]:
    """Extract version numbers from git tags matching ``v*.*.*``.

    Returns:
        Sorted list of version strings (without the ``v`` prefix).
    """
    try:
        result = subprocess.run(  # nosec B603 B607 — git only, no shell, no user input
            ["git", "tag", "--list", "v*"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=ROOT,
        )
        if result.returncode != 0:
            return []
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return []

    versions = []
    for line in result.stdout.strip().splitlines():
        match = TAG_RE.match(line.strip())
        if match:
            versions.append(match.group(1))

    return sorted(versions, key=_version_key)


def _version_key(version: str) -> tuple[tuple[int, int | str], ...]:
    """Convert a version string to a sortable tuple.

    Handles semver with optional pre-release suffixes (e.g., ``1.2.3-rc.1``).
    Each segment becomes ``(0, int_value)`` for numeric parts or
    ``(1, str_value)`` for non-numeric parts, ensuring ints and strings
    never compare directly (which raises ``TypeError`` in Python 3).

    Args:
        version: Semver-like version string (e.g., "1.2.3", "1.2.3-rc.1").

    Returns:
        Tuple for sorting.
    """
    parts: list[tuple[int, int | str]] = []
    for segment in re.split(r"[.-]", version):
        if segment.isdigit():
            parts.append((0, int(segment)))
        else:
            parts.append((1, segment))
    return tuple(parts)


def check_duplicates(
    versions: list[str],
) -> list[str]:
    """Find duplicate version entries.

    Args:
        versions: List of version strings (in file order).

    Returns:
        List of duplicated version strings.
    """
    seen: set[str] = set()
    duplicates: list[str] = []
    for v in versions:
        if v in seen and v not in duplicates:
            duplicates.append(v)
        seen.add(v)

    if duplicates:
        log.info("\n  Duplicate CHANGELOG entries (%d):", len(duplicates))
        for v in duplicates:
            log.info("    - %s", v)

    return duplicates


def check_ordering(
    versions: list[str],
) -> bool:
    """Verify versions in CHANGELOG are in descending order (newest first).

    Args:
        versions: Version strings in file order.

    Returns:
        True if ordering is correct.
    """
    if len(versions) <= 1:
        return True

    # Deduplicate while preserving order for comparison
    seen: set[str] = set()
    unique: list[str] = []
    for v in versions:
        if v not in seen:
            unique.append(v)
            seen.add(v)

    misordered = [
        (unique[i], unique[i + 1])
        for i in range(len(unique) - 1)
        if _version_key(unique[i]) < _version_key(unique[i + 1])
    ]

    if misordered:
        log.info("\n  Misordered versions (%d):", len(misordered))
        for before, after in misordered:
            log.info("    - %s appears before %s (should be after)", before, after)

    return len(misordered) == 0


def _has_release_please() -> bool:
    """Check whether the project uses release-please.

    Looks for ``release-please-config.json`` in the repo root or a
    release-please workflow in ``.github/workflows/``.
    """
    if (ROOT / "release-please-config.json").is_file():
        return True
    wf_dir = ROOT / ".github" / "workflows"
    if wf_dir.is_dir():
        for wf in wf_dir.iterdir():
            if wf.is_file() and "release-please" in wf.name:
                return True
    return False


def _detect_pre_release_please(
    untagged_versions: list[str],
    changelog_path: Path,
) -> set[str]:
    """Identify changelog entries that predate release-please adoption.

    release-please generates headings with a link: ``## [1.2.3](url)``.
    Manually written entries lack the link: ``## 0.1.0 (date)``.
    If an untagged version's heading is *not* in the release-please link
    format, it was likely written before release-please was adopted and
    no tag was ever intended.

    When the project does **not** use release-please at all, every
    manually written entry is treated as intentional (no tag expected)
    so it is not flagged as drift.

    Args:
        untagged_versions: Versions in CHANGELOG but not in git tags.
        changelog_path: Path to the CHANGELOG.md file.

    Returns:
        Set of version strings identified as manually written.
    """
    if not untagged_versions or not changelog_path.exists():
        return set()

    text = changelog_path.read_text(encoding="utf-8")
    rp_versions = set(_RP_HEADING_RE.findall(text))

    # If release-please is not configured, ALL manually written entries
    # (those not in release-please link format) are intentional.
    if not _has_release_please():
        return {v for v in untagged_versions if v not in rp_versions}

    return {v for v in untagged_versions if v not in rp_versions}


def compare_versions(
    changelog_versions: list[str],
    tag_versions: list[str],
    *,
    verbose: bool = False,
    changelog_path: Path = CHANGELOG,
) -> int:
    """Compare changelog versions against git tags and report differences.

    Also checks for duplicate entries and correct ordering in the changelog.

    Args:
        changelog_versions: Versions found in CHANGELOG.md.
        tag_versions: Versions found in git tags.
        verbose: Log detailed output (in-sync versions).
        changelog_path: Path to the CHANGELOG.md file.

    Returns:
        Exit code: 0 if in sync, 1 if drift detected.
    """
    c = Colors()
    ui = UI(title="Changelog Check", version=SCRIPT_VERSION, theme=THEME)
    changelog_set = set(changelog_versions)
    tag_set = set(tag_versions)

    in_changelog_not_tagged = sorted(changelog_set - tag_set, key=_version_key)
    tagged_not_in_changelog = sorted(tag_set - changelog_set, key=_version_key)
    in_sync = sorted(changelog_set & tag_set, key=_version_key)

    # Header first, before sub-checks that may also log
    ui.header()
    ui.section("CHANGELOG vs Git Tags")
    ui.kv("CHANGELOG versions", c.magenta(str(len(changelog_versions))))
    ui.kv("Git tag versions", c.magenta(str(len(tag_versions))))
    ui.kv("In sync", c.green(str(len(in_sync))))

    # Additional checks (logged under the header)
    duplicates = check_duplicates(changelog_versions)
    ordering_ok = check_ordering(changelog_versions)

    # Detect pre-release-please entries (manually written, no tag expected).
    # These are typically the first entry in the CHANGELOG that predates
    # release-please adoption — no corresponding git tag was ever created.
    pre_rp_versions = _detect_pre_release_please(
        in_changelog_not_tagged, changelog_path
    )
    # Only count genuinely unexpected drift (exclude pre-release-please entries)
    real_drift = [v for v in in_changelog_not_tagged if v not in pre_rp_versions]

    has_drift = bool(
        real_drift or tagged_not_in_changelog or duplicates or not ordering_ok
    )

    if pre_rp_versions:
        uses_rp = _has_release_please()
        if uses_rp:
            section_label = (
                f"Pre-release-please entries ({len(pre_rp_versions)}) "
                f"— no tag expected:"
            )
            entry_hint = "(manually written before release-please adoption)"
        else:
            section_label = (
                f"Manually written entries ({len(pre_rp_versions)}) — no tag expected:"
            )
            entry_hint = "(manually written changelog entry, no git tag)"
        log.info(
            "\n  %s",
            c.cyan(section_label),
        )
        for v in pre_rp_versions:
            log.info(
                "    - %s  %s",
                c.cyan(v),
                c.dim(entry_hint),
            )

    if real_drift:
        log.info(
            "\n  %s",
            c.yellow(f"In CHANGELOG but not tagged ({len(real_drift)}):"),
        )
        for v in real_drift:
            log.info("    - %s", c.yellow(v))

    if tagged_not_in_changelog:
        log.info(
            "\n  %s",
            c.yellow(f"Tagged but not in CHANGELOG ({len(tagged_not_in_changelog)}):"),
        )
        for v in tagged_not_in_changelog:
            log.info("    - %s", c.yellow(v))

    if verbose and in_sync:
        log.info("\n  %s", c.dim(f"In sync ({len(in_sync)}):"))
        for v in in_sync:
            log.info("    - %s", c.dim(v))

    ui.blank()
    if not has_drift:
        ui.status_line("check", "All versions are in sync.", "green")
    else:
        ui.status_line(
            "cross",
            "Drift detected between CHANGELOG.md and git tags.",
            "red",
        )

    ui.footer(
        passed=len(in_sync) + len(pre_rp_versions),
        failed=len(real_drift) + len(tagged_not_in_changelog) + len(duplicates),
    )

    return 1 if has_drift else 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    """Entry point for changelog_check.

    Returns:
        Exit code from compare_versions().
    """
    parser = argparse.ArgumentParser(
        description="Verify CHANGELOG.md entries match git tags.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {SCRIPT_VERSION}",
    )
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show versions that are in sync",
    )
    verbosity.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress output; exit code only (for CI)",
    )
    parser.add_argument(
        "--changelog-path",
        type=Path,
        default=CHANGELOG,
        help="Path to CHANGELOG.md (default: %(default)s)",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Quick import and arg-parse health check; exit 0 immediately",
    )
    args = parser.parse_args()

    if args.smoke:
        print(f"changelog_check {SCRIPT_VERSION}: smoke ok")
        return 0

    level = logging.WARNING if args.quiet else logging.INFO
    logging.basicConfig(format="%(message)s", level=level)

    changelog_path: Path = args.changelog_path
    if not changelog_path.exists():
        log.error("CHANGELOG.md not found at %s", changelog_path)
        return 1

    changelog_versions = get_changelog_versions(changelog_path)
    tag_versions = get_git_tag_versions()

    return compare_versions(
        changelog_versions,
        tag_versions,
        verbose=args.verbose,
        changelog_path=changelog_path,
    )


if __name__ == "__main__":
    raise SystemExit(main())
