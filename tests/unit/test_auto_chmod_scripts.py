"""Unit tests for scripts/precommit/auto_chmod_scripts.py."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from precommit.auto_chmod_scripts import (
    SCRIPT_VERSION,
    _has_shebang,
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
# _has_shebang
# ---------------------------------------------------------------------------


class TestHasShebang:
    """Tests for _has_shebang()."""

    def test_python_shebang(self, tmp_path) -> None:
        f = tmp_path / "script.py"
        f.write_text("#!/usr/bin/env python3\nprint('hi')\n")
        assert _has_shebang(f) is True

    def test_bash_shebang(self, tmp_path) -> None:
        f = tmp_path / "script.sh"
        f.write_text("#!/bin/bash\necho hi\n")
        assert _has_shebang(f) is True

    def test_no_shebang(self, tmp_path) -> None:
        f = tmp_path / "module.py"
        f.write_text("import sys\n")
        assert _has_shebang(f) is False

    def test_empty_file(self, tmp_path) -> None:
        f = tmp_path / "empty.py"
        f.write_text("")
        assert _has_shebang(f) is False

    def test_nonexistent_file(self, tmp_path) -> None:
        f = tmp_path / "missing.py"
        assert _has_shebang(f) is False
