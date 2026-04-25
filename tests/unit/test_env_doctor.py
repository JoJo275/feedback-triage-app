"""Unit tests for scripts/env_doctor.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# scripts/ is not an installed package — add it to sys.path so we can import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from _colors import colorize as _colorize
from env_doctor import (
    EXPECTED_TOOLS,
    OPTIONAL_TOOLS,
    SCRIPT_VERSION,
    _collect_results,
    _icon,
    _supports_color,
    check_architecture,
    check_editable_install,
    check_git_repo,
    check_git_user_config,
    check_hatch,
    check_pre_commit_hooks,
    check_pyproject_toml,
    check_python_version,
    check_task,
    check_tool_available,
    check_venv_active,
    run_checks,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestExpectedTools:
    """Validate tool lists contain the expected entries."""

    def test_commitizen_in_expected_tools(self) -> None:
        assert "cz" in EXPECTED_TOOLS

    def test_deptry_in_expected_tools(self) -> None:
        assert "deptry" in EXPECTED_TOOLS

    def test_ruff_in_expected_tools(self) -> None:
        assert "ruff" in EXPECTED_TOOLS

    def test_actionlint_in_optional_tools(self) -> None:
        assert "actionlint" in OPTIONAL_TOOLS


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
# check_python_version
# ---------------------------------------------------------------------------


class TestCheckPythonVersion:
    """Tests for Python version check."""

    def test_passes_on_current_python(self) -> None:
        passed, msg = check_python_version()
        # We're running on >= 3.11, so it should pass
        assert passed
        assert "Python" in msg

    def test_message_contains_version(self) -> None:
        _passed, msg = check_python_version()
        major, minor = sys.version_info[:2]
        assert f"{major}.{minor}" in msg


# ---------------------------------------------------------------------------
# check_architecture
# ---------------------------------------------------------------------------


class TestCheckArchitecture:
    """Tests for architecture check."""

    def test_always_passes(self) -> None:
        passed, _ = check_architecture()
        assert passed

    def test_reports_bits(self) -> None:
        _, msg = check_architecture()
        assert "bit" in msg


# ---------------------------------------------------------------------------
# check_venv_active
# ---------------------------------------------------------------------------


class TestCheckVenvActive:
    """Tests for virtual environment detection."""

    def test_passes_when_venv_set(self) -> None:
        with patch.dict("os.environ", {"VIRTUAL_ENV": "/some/venv/path"}):
            passed, msg = check_venv_active()
        assert passed
        assert "path" in msg

    def test_fails_when_no_venv(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            passed, msg = check_venv_active()
        assert not passed
        assert "No virtual environment" in msg


# ---------------------------------------------------------------------------
# check_editable_install
# ---------------------------------------------------------------------------


class TestCheckEditableInstall:
    """Tests for editable install check."""

    def test_passes_when_editable_via_pep610(self) -> None:
        """PEP 610 direct_url.json with editable=True → 'Editable install OK'."""
        mock_dist = MagicMock()
        mock_dist.read_text.return_value = '{"dir_info": {"editable": true}}'
        with (
            patch("env_doctor.get_package_version", return_value="1.0.0"),
            patch("env_doctor.importlib.metadata.distribution", return_value=mock_dist),
        ):
            passed, msg = check_editable_install()
        assert passed
        assert "Editable install OK" in msg
        assert "1.0.0" in msg

    def test_passes_when_installed_non_editable(self) -> None:
        """PEP 610 with editable=False → still passes, notes non-editable."""
        mock_dist = MagicMock()
        mock_dist.read_text.return_value = '{"dir_info": {"editable": false}}'
        with (
            patch("env_doctor.get_package_version", return_value="1.0.0"),
            patch("env_doctor.importlib.metadata.distribution", return_value=mock_dist),
        ):
            passed, msg = check_editable_install()
        assert passed
        assert "non-editable" in msg

    def test_fails_when_not_installed(self) -> None:
        with patch(
            "env_doctor.get_package_version",
            return_value="not installed",
        ):
            passed, _msg = check_editable_install()
        assert not passed

    def test_suggests_hatch_shell(self) -> None:
        """Fix suggestion should mention hatch shell, not just pip."""
        with patch(
            "env_doctor.get_package_version",
            return_value="not installed",
        ):
            _, msg = check_editable_install()
        assert "hatch shell" in msg


# ---------------------------------------------------------------------------
# check_tool_available
# ---------------------------------------------------------------------------


class TestCheckToolAvailable:
    """Tests for tool availability check."""

    def test_passes_when_found(self) -> None:
        with patch("env_doctor.shutil.which", return_value="/usr/bin/ruff"):
            passed, msg = check_tool_available("ruff")
        assert passed
        assert "ruff available" in msg

    def test_fails_when_not_found(self) -> None:
        with patch("env_doctor.shutil.which", return_value=None):
            passed, msg = check_tool_available("somemissingtool")
        assert not passed
        assert "not found" in msg


# ---------------------------------------------------------------------------
# check_hatch
# ---------------------------------------------------------------------------


class TestCheckHatch:
    """Tests for Hatch check."""

    def test_fails_when_not_installed(self) -> None:
        with patch("env_doctor.shutil.which", return_value=None):
            passed, msg = check_hatch()
        assert not passed
        assert "pipx install hatch" in msg

    def test_passes_when_installed(self) -> None:
        mock_result = MagicMock()
        mock_result.stdout = "Hatch, version 1.12.0"
        with (
            patch("env_doctor.shutil.which", return_value="/usr/bin/hatch"),
            patch("env_doctor.subprocess.run", return_value=mock_result),
        ):
            passed, msg = check_hatch()
        assert passed
        assert "1.12.0" in msg

    def test_fails_on_timeout(self) -> None:
        with (
            patch("env_doctor.shutil.which", return_value="/usr/bin/hatch"),
            patch(
                "env_doctor.subprocess.run",
                side_effect=subprocess.TimeoutExpired("hatch", 10),
            ),
        ):
            passed, msg = check_hatch()
        assert not passed
        assert "failed to run" in msg


# ---------------------------------------------------------------------------
# check_task
# ---------------------------------------------------------------------------


class TestCheckTask:
    """Tests for Task runner check."""

    def test_passes_when_found(self) -> None:
        with patch("env_doctor.shutil.which", return_value="/usr/bin/task"):
            passed, _ = check_task()
        assert passed

    def test_fails_when_not_found(self) -> None:
        with patch("env_doctor.shutil.which", return_value=None):
            passed, msg = check_task()
        assert not passed
        assert "optional" in msg.lower()


# ---------------------------------------------------------------------------
# check_git_repo
# ---------------------------------------------------------------------------


class TestCheckGitRepo:
    """Tests for git repository check."""

    def test_passes_when_git_dir_exists(self) -> None:
        with patch("env_doctor.ROOT", Path(__file__).resolve().parent.parent.parent):
            passed, _ = check_git_repo()
        # The actual workspace has .git/, so this should pass
        assert passed

    def test_fails_when_no_git_dir(self, tmp_path) -> None:
        with patch("env_doctor.ROOT", tmp_path):
            passed, msg = check_git_repo()
        assert not passed
        assert "Not a git repository" in msg


# ---------------------------------------------------------------------------
# check_git_user_config
# ---------------------------------------------------------------------------


class TestCheckGitUserConfig:
    """Tests for git user config check."""

    def test_fails_when_git_not_found(self) -> None:
        with patch("env_doctor.shutil.which", return_value=None):
            passed, msg = check_git_user_config()
        assert not passed
        assert "git not found" in msg

    def test_passes_when_both_configured(self) -> None:
        mock_result = MagicMock()
        mock_result.stdout = "John Doe\n"
        with (
            patch("env_doctor.shutil.which", return_value="/usr/bin/git"),
            patch("env_doctor.subprocess.run", return_value=mock_result),
        ):
            passed, msg = check_git_user_config()
        assert passed
        assert "configured" in msg

    def test_fails_when_name_missing(self) -> None:
        def side_effect(cmd, **_kwargs):
            result = MagicMock()
            # user.name returns empty, user.email returns value
            if "user.name" in cmd:
                result.stdout = ""
            else:
                result.stdout = "test@example.com\n"
            return result

        with (
            patch("env_doctor.shutil.which", return_value="/usr/bin/git"),
            patch("env_doctor.subprocess.run", side_effect=side_effect),
        ):
            passed, msg = check_git_user_config()
        assert not passed
        assert "user.name" in msg

    def test_fails_on_timeout(self) -> None:
        with (
            patch("env_doctor.shutil.which", return_value="/usr/bin/git"),
            patch(
                "env_doctor.subprocess.run",
                side_effect=subprocess.TimeoutExpired("git", 5),
            ),
        ):
            passed, msg = check_git_user_config()
        assert not passed
        assert "missing" in msg.lower()


# ---------------------------------------------------------------------------
# check_pyproject_toml
# ---------------------------------------------------------------------------


class TestCheckPyprojectToml:
    """Tests for pyproject.toml existence check."""

    def test_passes_when_file_exists(self) -> None:
        with patch("env_doctor.ROOT", Path(__file__).resolve().parent.parent.parent):
            passed, msg = check_pyproject_toml()
        assert passed
        assert "found" in msg

    def test_fails_when_file_missing(self, tmp_path) -> None:
        with patch("env_doctor.ROOT", tmp_path):
            passed, msg = check_pyproject_toml()
        assert not passed
        assert "missing" in msg


# ---------------------------------------------------------------------------
# check_pre_commit_hooks
# ---------------------------------------------------------------------------


class TestCheckPreCommitHooks:
    """Tests for pre-commit hooks check."""

    def test_fails_when_no_hooks(self, tmp_path) -> None:
        fake_hooks = {
            "pre-commit": tmp_path / "hooks" / "pre-commit",
            "commit-msg": tmp_path / "hooks" / "commit-msg",
            "pre-push": tmp_path / "hooks" / "pre-push",
        }
        with patch("env_doctor.HOOK_FILES", fake_hooks):
            passed, msg = check_pre_commit_hooks()
        assert not passed
        assert "No hooks installed" in msg

    def test_passes_when_all_hooks_exist(self, tmp_path) -> None:
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        for name in ("pre-commit", "commit-msg", "pre-push"):
            (hooks_dir / name).write_text(
                "#!/bin/sh\n# File generated by pre-commit\n", encoding="utf-8"
            )

        fake_hooks = {
            "pre-commit": hooks_dir / "pre-commit",
            "commit-msg": hooks_dir / "commit-msg",
            "pre-push": hooks_dir / "pre-push",
        }
        with patch("env_doctor.HOOK_FILES", fake_hooks):
            passed, msg = check_pre_commit_hooks()
        assert passed
        assert "All hooks installed" in msg


# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------


class TestSupportsColor:
    """Tests for _supports_color."""

    def test_no_color_env_disables(self) -> None:
        mock_stream = MagicMock()
        mock_stream.isatty.return_value = True
        with patch.dict("os.environ", {"NO_COLOR": "1"}):
            assert _supports_color(mock_stream) is False

    def test_force_color_env_enables(self) -> None:
        mock_stream = MagicMock()
        mock_stream.isatty.return_value = False
        with patch.dict("os.environ", {"FORCE_COLOR": "1"}, clear=True):
            assert _supports_color(mock_stream) is True

    def test_tty_enables_color(self) -> None:
        mock_stream = MagicMock()
        mock_stream.isatty.return_value = True
        with (
            patch.dict("os.environ", {}, clear=True),
            patch("_colors._enable_windows_ansi", return_value=True),
        ):
            assert _supports_color(mock_stream) is True

    def test_non_tty_disables_color(self) -> None:
        mock_stream = MagicMock()
        mock_stream.isatty.return_value = False
        with patch.dict("os.environ", {}, clear=True):
            assert _supports_color(mock_stream) is False


class TestColorize:
    """Tests for _colorize."""

    def test_applies_color_when_enabled(self) -> None:
        result = _colorize("hello", "32", use_color=True)
        assert result == "\033[32mhello\033[0m"

    def test_returns_plain_when_disabled(self) -> None:
        result = _colorize("hello", "32", use_color=False)
        assert result == "hello"


class TestIcon:
    """Tests for _icon."""

    @pytest.mark.parametrize("status", ["PASS", "FAIL", "WARN"])
    def test_returns_status_text(self, status) -> None:
        result = _icon(status, use_color=False)
        assert result == status

    def test_pass_is_green(self) -> None:
        result = _icon("PASS", use_color=True)
        assert "\033[32m" in result

    def test_fail_is_red(self) -> None:
        result = _icon("FAIL", use_color=True)
        assert "\033[31m" in result

    def test_warn_is_yellow(self) -> None:
        result = _icon("WARN", use_color=True)
        assert "\033[33m" in result


# ---------------------------------------------------------------------------
# run_checks
# ---------------------------------------------------------------------------


class TestRunChecks:
    """Tests for the run_checks runner."""

    def test_returns_zero_when_all_pass(self) -> None:
        """All checks mocked to pass → exit 0."""
        passing = lambda: (True, "OK")  # noqa: E731

        fake_checks = [("Check 1", passing), ("Check 2", passing)]
        with (
            patch("env_doctor.CHECKS", fake_checks),
            patch("env_doctor.EXPECTED_TOOLS", []),
            patch("env_doctor.OPTIONAL_TOOLS", []),
        ):
            assert run_checks(color=False) == 0

    def test_returns_one_when_check_fails(self) -> None:
        """A failing required check → exit 1."""
        passing = lambda: (True, "OK")  # noqa: E731
        failing = lambda: (False, "broken")  # noqa: E731

        fake_checks = [("Required check", failing), ("Other", passing)]
        with (
            patch("env_doctor.CHECKS", fake_checks),
            patch("env_doctor.EXPECTED_TOOLS", []),
            patch("env_doctor.OPTIONAL_TOOLS", []),
        ):
            assert run_checks(color=False) == 1

    def test_optional_check_does_not_fail_without_strict(self) -> None:
        """Task runner failure is a warning, not a failure, without --strict."""
        failing_task = lambda: (False, "not found")  # noqa: E731

        fake_checks = [("Task runner", failing_task)]
        with (
            patch("env_doctor.CHECKS", fake_checks),
            patch("env_doctor.EXPECTED_TOOLS", []),
            patch("env_doctor.OPTIONAL_TOOLS", []),
        ):
            assert run_checks(strict=False, color=False) == 0

    def test_optional_check_fails_with_strict(self) -> None:
        """Task runner failure IS a failure with --strict."""
        failing_task = lambda: (False, "not found")  # noqa: E731

        fake_checks = [("Task runner", failing_task)]
        with (
            patch("env_doctor.CHECKS", fake_checks),
            patch("env_doctor.EXPECTED_TOOLS", []),
            patch("env_doctor.OPTIONAL_TOOLS", []),
        ):
            # Task runner is in the optional_checks set in run_checks,
            # but when strict=True it should NOT be optional
            # Actually, looking at the code, optional_checks only covers
            # the CHECKS list, not EXPECTED/OPTIONAL tools.
            # Task runner is in optional_checks, so strict makes it fail.
            assert run_checks(strict=True, color=False) == 1

    def test_optional_tool_warns_without_strict(self) -> None:
        """Optional tools warn but don't fail without --strict."""
        with (
            patch("env_doctor.CHECKS", []),
            patch("env_doctor.EXPECTED_TOOLS", []),
            patch("env_doctor.OPTIONAL_TOOLS", ["actionlint"]),
            patch("env_doctor.shutil.which", return_value=None),
        ):
            assert run_checks(strict=False, color=False) == 0

    def test_optional_tool_fails_with_strict(self) -> None:
        """Optional tools fail with --strict."""
        with (
            patch("env_doctor.CHECKS", []),
            patch("env_doctor.EXPECTED_TOOLS", []),
            patch("env_doctor.OPTIONAL_TOOLS", ["actionlint"]),
            patch("env_doctor.shutil.which", return_value=None),
        ):
            assert run_checks(strict=True, color=False) == 1

    def test_json_output(self, capsys) -> None:
        """--json outputs valid JSON with expected structure."""
        passing = lambda: (True, "OK")  # noqa: E731

        fake_checks = [("Check 1", passing)]
        with (
            patch("env_doctor.CHECKS", fake_checks),
            patch("env_doctor.EXPECTED_TOOLS", []),
            patch("env_doctor.OPTIONAL_TOOLS", []),
            patch("env_doctor.OPTIONAL_CHECKS", []),
            patch("env_doctor.EXTENDED_CHECKS", []),
        ):
            result = run_checks(color=False, output_json=True)

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert result == 0
        assert data["version"] == SCRIPT_VERSION
        assert data["total"] == 1
        assert data["passed"] == 1
        assert data["failed"] == 0
        assert len(data["checks"]) == 1
        assert data["checks"][0]["status"] == "PASS"

    def test_json_output_with_failures(self, capsys) -> None:
        """--json reflects failures in output."""
        failing = lambda: (False, "broken")  # noqa: E731

        fake_checks = [("Check 1", failing)]
        with (
            patch("env_doctor.CHECKS", fake_checks),
            patch("env_doctor.EXPECTED_TOOLS", []),
            patch("env_doctor.OPTIONAL_TOOLS", []),
            patch("env_doctor.OPTIONAL_CHECKS", []),
        ):
            result = run_checks(color=False, output_json=True)

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert result == 1
        assert data["failed"] == 1


# ---------------------------------------------------------------------------
# _collect_results
# ---------------------------------------------------------------------------


class TestCollectResults:
    """Tests for _collect_results."""

    def test_returns_results_and_count(self) -> None:
        passing = lambda: (True, "OK")  # noqa: E731

        fake_checks = [("Test", passing)]
        with (
            patch("env_doctor.CHECKS", fake_checks),
            patch("env_doctor.EXPECTED_TOOLS", []),
            patch("env_doctor.OPTIONAL_TOOLS", []),
            patch("env_doctor.OPTIONAL_CHECKS", []),
            patch("env_doctor.EXTENDED_CHECKS", []),
        ):
            results, failures = _collect_results()
        assert failures == 0
        assert len(results) == 1
        assert results[0]["group"] == "core"

    def test_groups_tools_correctly(self) -> None:
        with (
            patch("env_doctor.CHECKS", []),
            patch("env_doctor.EXPECTED_TOOLS", ["ruff"]),
            patch("env_doctor.OPTIONAL_TOOLS", ["actionlint"]),
            patch("env_doctor.shutil.which", return_value="/usr/bin/x"),
        ):
            results, _failures = _collect_results()
        groups = [r["group"] for r in results]
        assert "tools" in groups
        assert "optional" in groups
