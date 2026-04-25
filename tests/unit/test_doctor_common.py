"""Unit tests for scripts/_doctor_common.py shared helpers."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from _doctor_common import (
    HOOK_STAGES,
    SCRIPT_VERSION,
    check_hook_installed,
    check_path_exists,
    get_package_version,
    get_version,
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
# HOOK_STAGES
# ---------------------------------------------------------------------------


class TestHookStages:
    """Validate hook stages constant."""

    def test_contains_expected_stages(self) -> None:
        assert "pre-commit" in HOOK_STAGES
        assert "commit-msg" in HOOK_STAGES
        assert "pre-push" in HOOK_STAGES

    def test_is_tuple(self) -> None:
        assert isinstance(HOOK_STAGES, tuple)


# ---------------------------------------------------------------------------
# get_version
# ---------------------------------------------------------------------------


class TestGetVersion:
    """Tests for command version extraction."""

    def test_not_found_when_missing(self) -> None:
        with patch("_doctor_common.shutil.which", return_value=None):
            assert get_version(["nonexistent-tool", "--version"]) == "not found"

    def test_returns_first_line_of_stdout(self) -> None:
        mock_result = MagicMock()
        mock_result.stdout = "tool 1.2.3\nextra output\n"
        mock_result.stderr = ""
        with (
            patch("_doctor_common.shutil.which", return_value="/usr/bin/tool"),
            patch("_doctor_common.subprocess.run", return_value=mock_result),
        ):
            result = get_version(["tool", "--version"])
        assert result == "tool 1.2.3"

    def test_returns_stderr_when_stdout_empty(self) -> None:
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = "version info from stderr\n"
        with (
            patch("_doctor_common.shutil.which", return_value="/usr/bin/tool"),
            patch("_doctor_common.subprocess.run", return_value=mock_result),
        ):
            result = get_version(["tool", "--version"])
        assert result == "version info from stderr"

    def test_returns_error_on_timeout(self) -> None:
        import subprocess

        with (
            patch("_doctor_common.shutil.which", return_value="/usr/bin/tool"),
            patch(
                "_doctor_common.subprocess.run",
                side_effect=subprocess.TimeoutExpired("tool", 10),
            ),
        ):
            assert get_version(["tool", "--version"]) == "error"

    def test_returns_error_on_oserror(self) -> None:
        with (
            patch("_doctor_common.shutil.which", return_value="/usr/bin/tool"),
            patch(
                "_doctor_common.subprocess.run",
                side_effect=OSError("exec failed"),
            ),
        ):
            assert get_version(["tool", "--version"]) == "error"

    def test_absolute_path_skips_which(self) -> None:
        mock_result = MagicMock()
        mock_result.stdout = "python 3.13.5\n"
        mock_result.stderr = ""
        with (
            patch("_doctor_common.Path.is_absolute", return_value=True),
            patch("_doctor_common.Path.exists", return_value=True),
            patch("_doctor_common.subprocess.run", return_value=mock_result),
        ):
            result = get_version([sys.executable, "--version"])
        assert "python" in result.lower() or "3." in result

    def test_custom_timeout(self) -> None:
        mock_result = MagicMock()
        mock_result.stdout = "v1.0\n"
        mock_result.stderr = ""
        with (
            patch("_doctor_common.shutil.which", return_value="/usr/bin/tool"),
            patch(
                "_doctor_common.subprocess.run", return_value=mock_result
            ) as mock_run,
        ):
            get_version(["tool", "--version"], timeout=30)
        mock_run.assert_called_once()
        assert mock_run.call_args[1]["timeout"] == 30


# ---------------------------------------------------------------------------
# get_package_version
# ---------------------------------------------------------------------------


class TestGetPackageVersion:
    """Tests for package version lookup."""

    def test_returns_version_for_installed_package(self) -> None:
        # pytest is always installed in the test environment
        result = get_package_version("pytest")
        assert result != "not installed"

    def test_returns_not_installed_for_missing_package(self) -> None:
        assert get_package_version("nonexistent-pkg-xyz-123") == "not installed"


# ---------------------------------------------------------------------------
# check_path_exists
# ---------------------------------------------------------------------------


class TestCheckPathExists:
    """Tests for path existence check."""

    def test_directory(self, tmp_path) -> None:
        assert check_path_exists(tmp_path) == "directory"

    def test_file(self, tmp_path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("hello", encoding="utf-8")
        assert check_path_exists(f) == "file"

    def test_missing(self, tmp_path) -> None:
        assert check_path_exists(tmp_path / "nope") == "missing"


# ---------------------------------------------------------------------------
# check_hook_installed
# ---------------------------------------------------------------------------


class TestCheckHookInstalled:
    """Tests for pre-commit hook detection."""

    def test_missing_file(self, tmp_path) -> None:
        assert check_hook_installed(tmp_path / "pre-commit") == "missing"

    def test_precommit_managed_hook(self, tmp_path) -> None:
        hook = tmp_path / "pre-commit"
        hook.write_text("#!/bin/sh\n# File generated by pre-commit\n", encoding="utf-8")
        assert check_hook_installed(hook) == "installed"

    def test_sample_hook(self, tmp_path) -> None:
        hook = tmp_path / "pre-commit.sample"
        hook.write_text("#!/bin/sh\n# This sample hook\n", encoding="utf-8")
        assert check_hook_installed(hook) == "sample"

    def test_custom_hook(self, tmp_path) -> None:
        hook = tmp_path / "pre-commit"
        hook.write_text("#!/bin/sh\necho custom\n", encoding="utf-8")
        assert check_hook_installed(hook) == "custom"

    def test_empty_file_is_custom(self, tmp_path) -> None:
        hook = tmp_path / "pre-commit"
        hook.write_text("", encoding="utf-8")
        assert check_hook_installed(hook) == "custom"

    def test_unreadable_file(self, tmp_path) -> None:
        hook = tmp_path / "pre-commit"
        hook.write_text("content", encoding="utf-8")
        with patch.object(Path, "read_text", side_effect=OSError("permission denied")):
            assert check_hook_installed(hook) == "missing"
