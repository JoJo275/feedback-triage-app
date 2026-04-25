"""Unit tests for scripts/repo_sauron.py."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from repo_sauron import SCRIPT_VERSION, SKIP_DIRS

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
# SKIP_DIRS
# ---------------------------------------------------------------------------


class TestSkipDirs:
    """Validate directory skip list."""

    def test_is_set(self) -> None:
        assert isinstance(SKIP_DIRS, set)

    def test_contains_common_dirs(self) -> None:
        assert ".git" in SKIP_DIRS
        assert "__pycache__" in SKIP_DIRS
        assert "node_modules" in SKIP_DIRS

    def test_contains_build_dirs(self) -> None:
        assert "dist" in SKIP_DIRS
        assert "build" in SKIP_DIRS

    def test_contains_venv_dirs(self) -> None:
        assert ".venv" in SKIP_DIRS or "venv" in SKIP_DIRS
