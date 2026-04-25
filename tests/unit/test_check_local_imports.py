"""Unit tests for scripts/precommit/check_local_imports.py."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from precommit.check_local_imports import (
    _MARKER,
    SCRIPT_VERSION,
    check_file,
)

# ---------------------------------------------------------------------------
# SCRIPT_VERSION
# ---------------------------------------------------------------------------


class TestScriptVersion:
    """Validate version constant."""

    def test_version_is_string(self) -> None:
        assert isinstance(SCRIPT_VERSION, str)

    def test_version_format(self) -> None:
        parts = SCRIPT_VERSION.split(".")
        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)


# ---------------------------------------------------------------------------
# check_file
# ---------------------------------------------------------------------------


class TestCheckFile:
    """Tests for check_file()."""

    def test_compliant_file_with_marker(self, tmp_path) -> None:
        f = tmp_path / "script.py"
        f.write_text(
            "import sys\n"
            "# -- Local script modules (not third-party; live in scripts/) ----\n"
            "from _colors import Colors\n"
        )
        assert check_file(f) is True

    def test_non_compliant_file_missing_marker(self, tmp_path) -> None:
        f = tmp_path / "script.py"
        f.write_text("from _colors import Colors\n")
        assert check_file(f) is False

    def test_no_local_imports_no_marker_needed(self, tmp_path) -> None:
        f = tmp_path / "script.py"
        f.write_text("import sys\nimport os\n")
        assert check_file(f) is True

    def test_empty_file(self, tmp_path) -> None:
        f = tmp_path / "empty.py"
        f.write_text("")
        assert check_file(f) is True

    def test_nonexistent_file(self, tmp_path) -> None:
        f = tmp_path / "missing.py"
        # Should return True (skip unreadable)
        assert check_file(f) is True

    def test_marker_constant(self) -> None:
        assert "Local script modules" in _MARKER
