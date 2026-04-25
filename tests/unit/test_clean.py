"""Unit tests for scripts/clean.py."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

# scripts/ is not an installed package — add it to sys.path so we can import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from clean import (
    BUILD_DIRS,
    CACHE_DIRS,
    CACHE_FILES,
    FILE_PATTERNS,
    RECURSIVE_DIRS,
    ROOT,
    SCRIPT_VERSION,
    clean,
    main,
    remove_path,
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


class TestConstants:
    """Verify constant lists are non-empty and well-formed."""

    def test_cache_dirs_non_empty(self) -> None:
        assert len(CACHE_DIRS) > 0
        assert all(isinstance(d, str) for d in CACHE_DIRS)

    def test_build_dirs_non_empty(self) -> None:
        assert len(BUILD_DIRS) > 0

    def test_recursive_dirs_non_empty(self) -> None:
        assert len(RECURSIVE_DIRS) > 0

    def test_file_patterns_non_empty(self) -> None:
        assert len(FILE_PATTERNS) > 0

    def test_cache_files_non_empty(self) -> None:
        assert len(CACHE_FILES) > 0

    def test_root_is_directory(self) -> None:
        assert ROOT.is_dir()


# ---------------------------------------------------------------------------
# remove_path
# ---------------------------------------------------------------------------


class TestRemovePath:
    """Tests for remove_path()."""

    def test_remove_file(self, tmp_path: Path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("hello")
        result = remove_path(f)
        assert result is True
        assert not f.exists()

    def test_remove_directory(self, tmp_path: Path) -> None:
        d = tmp_path / "subdir"
        d.mkdir()
        (d / "file.txt").write_text("content")
        result = remove_path(d)
        assert result is True
        assert not d.exists()

    def test_nonexistent_returns_false(self, tmp_path: Path) -> None:
        missing = tmp_path / "does_not_exist"
        result = remove_path(missing)
        assert result is False

    def test_dry_run_file_not_deleted(self, tmp_path: Path) -> None:
        f = tmp_path / "keep.txt"
        f.write_text("keep me")
        result = remove_path(f, dry_run=True)
        assert result is True  # reports it *would be* removed
        assert f.exists()  # but still exists

    def test_dry_run_directory_not_deleted(self, tmp_path: Path) -> None:
        d = tmp_path / "keepdir"
        d.mkdir()
        result = remove_path(d, dry_run=True)
        assert result is True
        assert d.exists()

    def test_permission_error_returns_none(self, tmp_path: Path) -> None:
        f = tmp_path / "locked.txt"
        f.write_text("locked")
        with (
            patch("clean.shutil.rmtree", side_effect=PermissionError("nope")),
            patch.object(Path, "is_dir", return_value=True),
        ):
            result = remove_path(f)
        assert result is None


# ---------------------------------------------------------------------------
# clean()
# ---------------------------------------------------------------------------


class TestClean:
    """Tests for clean() orchestration function."""

    def test_dry_run_returns_tuple(self) -> None:
        removed, errors = clean(dry_run=True)
        assert isinstance(removed, int)
        assert isinstance(errors, int)
        assert errors == 0

    def test_dry_run_no_errors(self) -> None:
        _, errors = clean(dry_run=True)
        assert errors == 0

    def test_clean_removes_nothing_when_clean(self, tmp_path: Path) -> None:
        """When there are no artifacts, removed should be 0."""
        with patch("clean.ROOT", tmp_path):
            removed, errors = clean(dry_run=False)
        assert removed == 0
        assert errors == 0

    def test_clean_removes_cache_dirs(self, tmp_path: Path) -> None:
        """Cache directories present in tmp_path get removed."""
        cache = tmp_path / ".pytest_cache"
        cache.mkdir()
        (cache / "somefile").write_text("data")
        with patch("clean.ROOT", tmp_path):
            removed, errors = clean(dry_run=False)
        assert not cache.exists()
        assert removed >= 1
        assert errors == 0

    def test_clean_removes_build_dirs(self, tmp_path: Path) -> None:
        dist = tmp_path / "dist"
        dist.mkdir()
        (dist / "package.tar.gz").write_text("fake")
        with patch("clean.ROOT", tmp_path):
            removed, _errors = clean(dry_run=False)
        assert not dist.exists()
        assert removed >= 1

    def test_clean_removes_pycache_recursively(self, tmp_path: Path) -> None:
        nested = tmp_path / "src" / "pkg" / "__pycache__"
        nested.mkdir(parents=True)
        (nested / "mod.pyc").write_bytes(b"\x00")
        with patch("clean.ROOT", tmp_path):
            removed, _ = clean(dry_run=False)
        assert not nested.exists()
        assert removed >= 1

    def test_clean_removes_egg_info(self, tmp_path: Path) -> None:
        egg = tmp_path / "src" / "pkg.egg-info"
        egg.mkdir(parents=True)
        (egg / "PKG-INFO").write_text("meta")
        with patch("clean.ROOT", tmp_path):
            removed, _ = clean(dry_run=False)
        assert not egg.exists()
        assert removed >= 1

    def test_clean_removes_stale_files(self, tmp_path: Path) -> None:
        pyc = tmp_path / "module.pyc"
        pyc.write_bytes(b"\x00")
        with patch("clean.ROOT", tmp_path):
            removed, _ = clean(dry_run=False)
        assert not pyc.exists()
        assert removed >= 1

    def test_clean_skips_venv_by_default(self, tmp_path: Path) -> None:
        venv = tmp_path / ".venv"
        venv.mkdir()
        (venv / "pyvenv.cfg").write_text("home = /usr")
        # Also add a __pycache__ inside .venv to test skipping
        pycache = venv / "lib" / "__pycache__"
        pycache.mkdir(parents=True)
        with patch("clean.ROOT", tmp_path):
            _removed, _ = clean(dry_run=False, include_venv=False)
        assert venv.exists()  # venv should still be there

    def test_clean_removes_venv_when_requested(self, tmp_path: Path) -> None:
        venv = tmp_path / ".venv"
        venv.mkdir()
        (venv / "pyvenv.cfg").write_text("home = /usr")
        with patch("clean.ROOT", tmp_path):
            removed, _ = clean(dry_run=False, include_venv=True)
        assert not venv.exists()
        assert removed >= 1

    def test_clean_removes_coverage_file(self, tmp_path: Path) -> None:
        cov = tmp_path / ".coverage"
        cov.write_text("coverage data")
        with patch("clean.ROOT", tmp_path):
            removed, _ = clean(dry_run=False)
        assert not cov.exists()
        assert removed >= 1

    def test_dry_run_preserves_all(self, tmp_path: Path) -> None:
        """Dry run should report removals but leave everything in place."""
        cache = tmp_path / ".pytest_cache"
        cache.mkdir()
        dist = tmp_path / "dist"
        dist.mkdir()
        pyc = tmp_path / "test.pyc"
        pyc.write_bytes(b"\x00")
        with patch("clean.ROOT", tmp_path):
            removed, errors = clean(dry_run=True)
        assert cache.exists()
        assert dist.exists()
        assert pyc.exists()
        assert removed >= 3
        assert errors == 0


# ---------------------------------------------------------------------------
# CLI (main)
# ---------------------------------------------------------------------------


class TestMain:
    """Tests for the CLI entry point."""

    def test_main_dry_run_exits_zero(self) -> None:
        with patch("sys.argv", ["clean", "--dry-run"]):
            result = main()
        assert result == 0

    def test_main_quiet_mode(self) -> None:
        with patch("sys.argv", ["clean", "--dry-run", "--quiet"]):
            result = main()
        assert result == 0

    def test_include_venv_without_yes_and_no_tty(self) -> None:
        """--include-venv without --yes and non-TTY stdin should exit 1."""
        with (
            patch("sys.argv", ["clean", "--include-venv"]),
            patch("sys.stdin") as mock_stdin,
        ):
            mock_stdin.isatty.return_value = False
            result = main()
        assert result == 1

    def test_include_venv_aborted_by_user(self) -> None:
        """User types 'n' at confirmation prompt."""
        with (
            patch("sys.argv", ["clean", "--include-venv"]),
            patch("sys.stdin") as mock_stdin,
            patch("builtins.input", return_value="n"),
        ):
            mock_stdin.isatty.return_value = True
            result = main()
        assert result == 0

    def test_include_venv_with_yes_flag(self) -> None:
        """--yes skips the confirmation prompt."""
        with patch("sys.argv", ["clean", "--include-venv", "--yes", "--dry-run"]):
            result = main()
        assert result == 0
