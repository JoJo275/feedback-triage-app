"""Unit tests for scripts/precommit/check_nul_bytes.py."""

from __future__ import annotations

import sys
from pathlib import Path

# Add precommit dir to sys.path
sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent.parent / "scripts" / "precommit")
)

from check_nul_bytes import SCRIPT_VERSION, check_file, main

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
# check_file
# ---------------------------------------------------------------------------


class TestCheckFile:
    """Tests for check_file()."""

    def test_clean_file_returns_false(self, tmp_path: Path) -> None:
        f = tmp_path / "clean.txt"
        f.write_text("hello world\n")
        assert check_file(str(f)) is False

    def test_nul_byte_returns_true(self, tmp_path: Path) -> None:
        f = tmp_path / "corrupted.txt"
        f.write_bytes(b"hello\x00world\n")
        assert check_file(str(f)) is True

    def test_nonexistent_file_returns_true(self, tmp_path: Path) -> None:
        assert check_file(str(tmp_path / "missing.txt")) is True

    def test_empty_file_returns_false(self, tmp_path: Path) -> None:
        f = tmp_path / "empty.txt"
        f.write_bytes(b"")
        assert check_file(str(f)) is False


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


class TestMain:
    """Tests for main()."""

    def test_no_files_returns_zero(self) -> None:
        assert main([]) == 0

    def test_clean_files_returns_zero(self, tmp_path: Path) -> None:
        f = tmp_path / "clean.txt"
        f.write_text("ok\n")
        assert main([str(f)]) == 0

    def test_nul_file_returns_one(self, tmp_path: Path) -> None:
        f = tmp_path / "bad.txt"
        f.write_bytes(b"bad\x00data")
        assert main([str(f)]) == 1

    def test_mixed_files(self, tmp_path: Path) -> None:
        clean = tmp_path / "clean.txt"
        clean.write_text("ok\n")
        bad = tmp_path / "bad.txt"
        bad.write_bytes(b"\x00")
        assert main([str(clean), str(bad)]) == 1
