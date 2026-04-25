"""Unit tests for scripts/bootstrap.py helper functions."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

# scripts/ is not an installed package — add it to sys.path so we can import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from bootstrap import (
    MIN_PYTHON,
    SCRIPT_VERSION,
    TOTAL_STEPS,
    check_python,
    run_cmd,
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

    def test_total_steps_positive(self) -> None:
        assert TOTAL_STEPS > 0

    def test_min_python_is_tuple(self) -> None:
        assert isinstance(MIN_PYTHON, tuple)
        assert len(MIN_PYTHON) == 2


# ---------------------------------------------------------------------------
# run_cmd
# ---------------------------------------------------------------------------


class TestRunCmd:
    """Tests for run_cmd()."""

    def test_dry_run_returns_zero_exit(self) -> None:
        result = run_cmd(["echo", "hello"], dry_run=True)
        assert result.returncode == 0
        assert result.stdout == ""

    @patch("bootstrap.subprocess.run")
    def test_captures_stdout(self, mock_run) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            ["echo"], 0, stdout="output\n", stderr=""
        )
        result = run_cmd(["echo", "test"], capture=True, check=False)
        assert result.stdout == "output\n"

    @patch("bootstrap.subprocess.run")
    def test_nonzero_exit_with_check_false(self, mock_run) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            ["false"], 1, stdout="", stderr="fail"
        )
        result = run_cmd(["false"], check=False, capture=True)
        assert result.returncode == 1


# ---------------------------------------------------------------------------
# check_python
# ---------------------------------------------------------------------------


class TestCheckPython:
    """Tests for check_python()."""

    def test_current_python_passes(self) -> None:
        # We're running on Python 3.11+, so this should pass
        assert check_python() is True

    @patch("bootstrap.sys")
    def test_old_python_fails(self, mock_sys) -> None:
        mock_sys.version_info = (3, 9, 0, "final", 0)
        assert check_python() is False
