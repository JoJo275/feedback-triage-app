"""Unit tests for scripts/check_known_issues.py."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

# scripts/ is not an installed package — add it to sys.path so we can import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from check_known_issues import (
    DEFAULT_MAX_AGE_DAYS,
    SCRIPT_VERSION,
    build_parser,
    find_stale_entries,
    main,
    parse_resolved_entries,
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

    def test_default_max_age_is_positive(self) -> None:
        assert DEFAULT_MAX_AGE_DAYS > 0


# ---------------------------------------------------------------------------
# parse_resolved_entries
# ---------------------------------------------------------------------------

_SAMPLE_MD = """\
# Known Issues

## Active

| Area | Issue | Workaround |
| :--- | :---- | :--------- |
| CI   | Flaky test | Re-run     |

## Resolved

| Area | Issue | Resolution | Date |
| :--- | :---- | :--------- | :--- |
| CI   | Old bug | Fixed in v2 | 2024-01-15 |
| Docs | Typo   | Corrected   | 2024-06-01 |

## Another Section

Something else.
"""

_EMPTY_RESOLVED = """\
## Resolved

| Area | Issue | Resolution | Date |
| :--- | :---- | :--------- | :--- |

## Next
"""

_NO_RESOLVED = """\
# Known Issues

## Active

| Area | Issue | Workaround |
| :--- | :---- | :--------- |
| CI   | Flaky test | Re-run  |
"""


class TestParseResolvedEntries:
    """Tests for parse_resolved_entries()."""

    def test_extracts_entries(self) -> None:
        entries = parse_resolved_entries(_SAMPLE_MD)
        assert len(entries) == 2

    def test_entry_fields(self) -> None:
        entries = parse_resolved_entries(_SAMPLE_MD)
        assert entries[0]["area"] == "CI"
        assert entries[0]["issue"] == "Old bug"
        assert entries[0]["resolution"] == "Fixed in v2"
        assert entries[0]["date"] == "2024-01-15"

    def test_second_entry(self) -> None:
        entries = parse_resolved_entries(_SAMPLE_MD)
        assert entries[1]["area"] == "Docs"
        assert entries[1]["date"] == "2024-06-01"

    def test_empty_resolved_table(self) -> None:
        entries = parse_resolved_entries(_EMPTY_RESOLVED)
        assert entries == []

    def test_no_resolved_section(self) -> None:
        entries = parse_resolved_entries(_NO_RESOLVED)
        assert entries == []

    def test_stops_at_next_heading(self) -> None:
        """Entries after '## Another Section' should not be included."""
        md = _SAMPLE_MD + "| Extra | Should not appear | Nope | 2024-07-01 |\n"
        entries = parse_resolved_entries(md)
        # The extra row is after "## Another Section" so it shouldn't be parsed
        assert len(entries) == 2

    def test_case_insensitive_heading(self) -> None:
        md = _SAMPLE_MD.replace("## Resolved", "## RESOLVED")
        entries = parse_resolved_entries(md)
        assert len(entries) == 2

    def test_heading_variant_resolved_issues(self) -> None:
        md = _SAMPLE_MD.replace("## Resolved", "## Resolved Issues")
        entries = parse_resolved_entries(md)
        assert len(entries) == 2

    def test_skips_separator_rows(self) -> None:
        """Separator rows (| :--- | :--- |) should be skipped."""
        entries = parse_resolved_entries(_SAMPLE_MD)
        # No entry should have "area" of ":---" or similar
        for entry in entries:
            assert not entry["area"].startswith(":")

    def test_skips_header_row(self) -> None:
        """The header row (Area | Issue | ...) should be skipped."""
        entries = parse_resolved_entries(_SAMPLE_MD)
        for entry in entries:
            assert entry["area"].lower() != "area"

    def test_empty_string(self) -> None:
        assert parse_resolved_entries("") == []


# ---------------------------------------------------------------------------
# find_stale_entries
# ---------------------------------------------------------------------------


class TestFindStaleEntries:
    """Tests for find_stale_entries()."""

    def test_finds_stale_entry(self) -> None:
        entries = [
            {
                "area": "CI",
                "issue": "Old bug",
                "resolution": "Fixed",
                "date": "2024-01-15",
            },
        ]
        stale = find_stale_entries(entries, max_age_days=90, today=date(2024, 12, 1))
        assert len(stale) == 1
        assert stale[0]["area"] == "CI"
        assert "age_days" in stale[0]

    def test_fresh_entry_not_stale(self) -> None:
        entries = [
            {
                "area": "CI",
                "issue": "Fresh",
                "resolution": "Fixed",
                "date": "2024-11-20",
            },
        ]
        stale = find_stale_entries(entries, max_age_days=90, today=date(2024, 12, 1))
        assert stale == []

    def test_boundary_exactly_at_threshold(self) -> None:
        """An entry exactly at the threshold should NOT be stale."""
        entries = [
            {
                "area": "CI",
                "issue": "Edge",
                "resolution": "Fixed",
                "date": "2024-09-02",
            },
        ]
        stale = find_stale_entries(entries, max_age_days=90, today=date(2024, 12, 1))
        assert stale == []

    def test_boundary_one_day_past(self) -> None:
        """An entry one day past the threshold should be stale."""
        entries = [
            {
                "area": "CI",
                "issue": "Edge",
                "resolution": "Fixed",
                "date": "2024-09-01",
            },
        ]
        stale = find_stale_entries(entries, max_age_days=90, today=date(2024, 12, 1))
        assert len(stale) == 1

    def test_unparsable_date_skipped(self) -> None:
        entries = [
            {"area": "CI", "issue": "Bad", "resolution": "Fixed", "date": "not-a-date"},
        ]
        stale = find_stale_entries(entries, max_age_days=90, today=date(2024, 12, 1))
        assert stale == []

    def test_empty_date_skipped(self) -> None:
        entries = [
            {"area": "CI", "issue": "Empty", "resolution": "Fixed", "date": ""},
        ]
        stale = find_stale_entries(entries, max_age_days=90, today=date(2024, 12, 1))
        assert stale == []

    def test_multiple_entries_mixed(self) -> None:
        entries = [
            {"area": "CI", "issue": "Old", "resolution": "Fixed", "date": "2024-01-01"},
            {
                "area": "Docs",
                "issue": "New",
                "resolution": "Fixed",
                "date": "2024-11-25",
            },
        ]
        stale = find_stale_entries(entries, max_age_days=90, today=date(2024, 12, 1))
        assert len(stale) == 1
        assert stale[0]["area"] == "CI"

    def test_age_days_calculation(self) -> None:
        entries = [
            {
                "area": "CI",
                "issue": "Test",
                "resolution": "Fixed",
                "date": "2024-06-01",
            },
        ]
        stale = find_stale_entries(entries, max_age_days=90, today=date(2024, 12, 1))
        assert stale[0]["age_days"] == (date(2024, 12, 1) - date(2024, 6, 1)).days

    def test_empty_entries_list(self) -> None:
        assert find_stale_entries([], max_age_days=90) == []

    def test_parsed_date_field_added(self) -> None:
        entries = [
            {
                "area": "CI",
                "issue": "Test",
                "resolution": "Fixed",
                "date": "2024-01-15",
            },
        ]
        stale = find_stale_entries(entries, max_age_days=90, today=date(2024, 12, 1))
        assert stale[0]["parsed_date"] == "2024-01-15"


# ---------------------------------------------------------------------------
# build_parser
# ---------------------------------------------------------------------------


class TestBuildParser:
    """Tests for build_parser()."""

    def test_returns_parser(self) -> None:
        parser = build_parser()
        assert hasattr(parser, "parse_args")

    def test_defaults(self) -> None:
        parser = build_parser()
        args = parser.parse_args([])
        assert args.days == DEFAULT_MAX_AGE_DAYS
        assert args.json_output is False
        assert args.quiet is False

    def test_days_override(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["--days", "30"])
        assert args.days == 30

    def test_json_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["--json"])
        assert args.json_output is True

    def test_quiet_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["--quiet"])
        assert args.quiet is True

    def test_quiet_short_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["-q"])
        assert args.quiet is True


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------


class TestMain:
    """Tests for main() entry point."""

    def test_file_not_found_exits_2(self, tmp_path: Path) -> None:
        result = main(["--issues-path", str(tmp_path / "missing.md")])
        assert result == 2

    def test_no_resolved_entries_exits_0(self, tmp_path: Path) -> None:
        f = tmp_path / "known-issues.md"
        f.write_text(_NO_RESOLVED)
        result = main(["--issues-path", str(f)])
        assert result == 0

    def test_stale_entries_exits_1(self, tmp_path: Path) -> None:
        f = tmp_path / "known-issues.md"
        f.write_text(_SAMPLE_MD)
        # Use a "today" far enough in the future that the entries are stale
        with patch("check_known_issues.date") as mock_date:
            mock_date.today.return_value = date(2025, 6, 1)
            mock_date.fromisoformat = date.fromisoformat
            result = main(["--issues-path", str(f), "--days", "90"])
        assert result == 1

    def test_fresh_entries_exits_0(self, tmp_path: Path) -> None:
        md = """\
## Resolved

| Area | Issue | Resolution | Date |
| :--- | :---- | :--------- | :--- |
| CI   | Recent | Fixed | 2025-05-20 |
"""
        f = tmp_path / "known-issues.md"
        f.write_text(md)
        with patch("check_known_issues.date") as mock_date:
            mock_date.today.return_value = date(2025, 6, 1)
            mock_date.fromisoformat = date.fromisoformat
            result = main(["--issues-path", str(f), "--days", "90"])
        assert result == 0

    def test_json_output(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        f = tmp_path / "known-issues.md"
        f.write_text(_SAMPLE_MD)
        with patch("check_known_issues.date") as mock_date:
            mock_date.today.return_value = date(2025, 6, 1)
            mock_date.fromisoformat = date.fromisoformat
            main(["--issues-path", str(f), "--json"])
        output = capsys.readouterr().out
        assert '"stale_count"' in output
        assert '"stale_entries"' in output

    def test_quiet_mode(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        f = tmp_path / "known-issues.md"
        f.write_text(_SAMPLE_MD)
        main(["--issues-path", str(f), "--quiet"])
        output = capsys.readouterr().out
        assert output == ""
