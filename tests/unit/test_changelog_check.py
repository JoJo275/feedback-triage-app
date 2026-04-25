"""Unit tests for scripts/changelog_check.py."""

from __future__ import annotations

import sys
from pathlib import Path

# scripts/ is not an installed package — add it to sys.path so we can import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from changelog_check import (
    SCRIPT_VERSION,
    _version_key,
    check_duplicates,
    check_ordering,
    get_changelog_versions,
)

# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


class TestMetadata:
    """Verify module-level metadata."""

    def test_version_is_string(self) -> None:
        assert isinstance(SCRIPT_VERSION, str)

    def test_version_format(self) -> None:
        parts = SCRIPT_VERSION.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)


# ---------------------------------------------------------------------------
# get_changelog_versions
# ---------------------------------------------------------------------------


class TestGetChangelogVersions:
    """Tests for get_changelog_versions()."""

    def test_extracts_versions_from_headings(self, tmp_path: Path) -> None:
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text(
            "# Changelog\n\n"
            "## [1.2.0](https://example.com) (2026-01-01)\n\n"
            "- feat: something\n\n"
            "## [1.1.0](https://example.com) (2025-12-01)\n\n"
            "- fix: something\n\n"
            "## [1.0.0](https://example.com) (2025-11-01)\n"
        )
        versions = get_changelog_versions(changelog)
        assert versions == ["1.2.0", "1.1.0", "1.0.0"]

    def test_extracts_plain_headings(self, tmp_path: Path) -> None:
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text("## 0.1.0\n\n- Initial release\n")
        versions = get_changelog_versions(changelog)
        assert versions == ["0.1.0"]

    def test_returns_empty_for_missing_file(self, tmp_path: Path) -> None:
        assert get_changelog_versions(tmp_path / "missing.md") == []

    def test_returns_empty_for_no_versions(self, tmp_path: Path) -> None:
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text("# Changelog\n\nNo releases yet.\n")
        assert get_changelog_versions(changelog) == []


# ---------------------------------------------------------------------------
# _version_key
# ---------------------------------------------------------------------------


class TestVersionKey:
    """Tests for _version_key()."""

    def test_simple_version(self) -> None:
        key = _version_key("1.2.3")
        assert key == ((0, 1), (0, 2), (0, 3))

    def test_prerelease_version(self) -> None:
        key = _version_key("1.0.0-rc.1")
        # Should contain both numeric and string parts
        assert len(key) > 3

    def test_sorting_order(self) -> None:
        versions = ["1.0.0", "0.9.0", "1.1.0", "0.10.0"]
        sorted_versions = sorted(versions, key=_version_key)
        assert sorted_versions == ["0.9.0", "0.10.0", "1.0.0", "1.1.0"]


# ---------------------------------------------------------------------------
# check_duplicates
# ---------------------------------------------------------------------------


class TestCheckDuplicates:
    """Tests for check_duplicates()."""

    def test_no_duplicates(self) -> None:
        assert check_duplicates(["1.0.0", "0.9.0", "0.8.0"]) == []

    def test_finds_duplicates(self) -> None:
        result = check_duplicates(["1.0.0", "0.9.0", "1.0.0"])
        assert result == ["1.0.0"]

    def test_empty_list(self) -> None:
        assert check_duplicates([]) == []


# ---------------------------------------------------------------------------
# check_ordering
# ---------------------------------------------------------------------------


class TestCheckOrdering:
    """Tests for check_ordering()."""

    def test_correct_descending_order(self) -> None:
        assert check_ordering(["1.2.0", "1.1.0", "1.0.0"]) is True

    def test_wrong_order(self) -> None:
        assert check_ordering(["1.0.0", "1.1.0", "1.2.0"]) is False

    def test_single_version(self) -> None:
        assert check_ordering(["1.0.0"]) is True

    def test_empty_list(self) -> None:
        assert check_ordering([]) is True
