"""Unit tests for scripts/check_todos.py."""

from __future__ import annotations

import sys
from pathlib import Path

# scripts/ is not an installed package — add it to sys.path so we can import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from check_todos import (
    DEFAULT_PATTERN,
    SCRIPT_VERSION,
    _is_excluded,
    find_todos,
    format_report,
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

    def test_default_pattern(self) -> None:
        assert "TODO" in DEFAULT_PATTERN


# ---------------------------------------------------------------------------
# _is_excluded
# ---------------------------------------------------------------------------


class TestIsExcluded:
    """Tests for _is_excluded()."""

    def test_exact_match_excludes(self) -> None:
        path = Path("project/.git/config")
        assert _is_excluded(path, {".git"}, set()) is True

    def test_suffix_match_excludes(self) -> None:
        path = Path("project/foo.egg-info/PKG-INFO")
        assert _is_excluded(path, set(), {".egg-info"}) is True

    def test_no_match_passes(self) -> None:
        path = Path("project/src/module.py")
        assert _is_excluded(path, {".git"}, {".egg-info"}) is False

    def test_cache_dir_excluded(self) -> None:
        path = Path("project/__pycache__/module.pyc")
        assert _is_excluded(path, {"__pycache__"}, set()) is True


# ---------------------------------------------------------------------------
# find_todos
# ---------------------------------------------------------------------------


class TestFindTodos:
    """Tests for find_todos()."""

    def test_finds_todos_in_files(self, tmp_path: Path) -> None:
        py_file = tmp_path / "example.py"
        py_file.write_text("# TODO (template users): Fix this\ncode = 1\n")
        results, _scanned = find_todos(tmp_path, "TODO (template users)", set())
        assert len(results) == 1
        matches = next(iter(results.values()))
        assert len(matches) == 1
        assert matches[0][0] == 1  # line number

    def test_no_todos_returns_empty(self, tmp_path: Path) -> None:
        py_file = tmp_path / "clean.py"
        py_file.write_text("# No todos here\ncode = 1\n")
        results, _scanned = find_todos(tmp_path, "TODO (template users)", set())
        assert len(results) == 0

    def test_excludes_directories(self, tmp_path: Path) -> None:
        excluded = tmp_path / ".git"
        excluded.mkdir()
        (excluded / "config.py").write_text("# TODO (template users): test\n")
        results, _scanned = find_todos(tmp_path, "TODO (template users)", {".git"})
        assert len(results) == 0

    def test_case_insensitive_search(self, tmp_path: Path) -> None:
        py_file = tmp_path / "example.py"
        py_file.write_text("# todo (TEMPLATE USERS): Fix this\n")
        results, _scanned = find_todos(tmp_path, "TODO (template users)", set())
        assert len(results) == 1


# ---------------------------------------------------------------------------
# format_report
# ---------------------------------------------------------------------------


class TestFormatReport:
    """Tests for format_report()."""

    def test_count_only_output(self, tmp_path: Path) -> None:
        results = {tmp_path / "a.py": [(1, "# TODO: fix")]}
        report = format_report(results, tmp_path, count_only=True)
        assert "1" in report

    def test_json_output(self, tmp_path: Path) -> None:
        results = {tmp_path / "a.py": [(1, "# TODO: fix")]}
        report = format_report(results, tmp_path, as_json=True)
        import json

        data = json.loads(report)
        assert data["total"] == 1
        assert data["file_count"] == 1

    def test_empty_results(self, tmp_path: Path) -> None:
        report = format_report({}, tmp_path)
        assert "0" in report or "no" in report.lower()
