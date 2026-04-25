"""Unit tests for scripts/doctor.py helper and formatting functions."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# scripts/ is not an installed package — add it to sys.path so we can import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from doctor import (
    SCRIPT_VERSION,
    _collect_problems,
    _git_info,
    _supports_color,
    check_path_exists,
    format_json,
    format_markdown,
    format_plain,
    get_package_version,
    get_version,
)

# ---------------------------------------------------------------------------
# SCRIPT_VERSION
# ---------------------------------------------------------------------------


class TestScriptVersion:
    """Validate version constant is well-formed."""

    def test_version_is_string(self) -> None:
        assert isinstance(SCRIPT_VERSION, str)

    def test_version_format(self) -> None:
        parts = SCRIPT_VERSION.split(".")
        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)


# ---------------------------------------------------------------------------
# get_version
# ---------------------------------------------------------------------------


class TestGetVersion:
    """Tests for CLI version detection."""

    def test_returns_not_found_for_missing_command(self) -> None:
        with patch("doctor.shutil.which", return_value=None):
            assert get_version(["nonexistent-tool", "--version"]) == "not found"

    def test_handles_absolute_path_directly(self) -> None:
        """Should skip shutil.which when cmd[0] is an existing absolute path."""
        mock_result = MagicMock()
        mock_result.stdout = "pip 24.3.1 from /some/path"
        mock_result.stderr = ""

        with (
            patch("doctor.Path.is_absolute", return_value=True),
            patch("doctor.Path.exists", return_value=True),
            patch("doctor.subprocess.run", return_value=mock_result),
            patch("doctor.shutil.which") as mock_which,
        ):
            result = get_version(["/usr/bin/python", "-m", "pip", "--version"])

        # shutil.which should NOT have been called for absolute paths
        mock_which.assert_not_called()
        assert "pip 24.3.1" in result

    def test_returns_stdout_first_line(self) -> None:
        mock_result = MagicMock()
        mock_result.stdout = "tool 1.2.3\nsome other info"
        mock_result.stderr = ""

        with (
            patch("doctor.shutil.which", return_value="/usr/bin/tool"),
            patch("doctor.subprocess.run", return_value=mock_result),
        ):
            result = get_version(["tool", "--version"])

        assert result == "tool 1.2.3"

    def test_falls_back_to_stderr(self) -> None:
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = "tool 2.0.0 from stderr"

        with (
            patch("doctor.shutil.which", return_value="/usr/bin/tool"),
            patch("doctor.subprocess.run", return_value=mock_result),
        ):
            result = get_version(["tool", "--version"])

        assert result == "tool 2.0.0 from stderr"

    def test_returns_error_on_timeout(self) -> None:
        with (
            patch("doctor.shutil.which", return_value="/usr/bin/tool"),
            patch(
                "doctor.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="tool", timeout=10),
            ),
        ):
            assert get_version(["tool", "--version"]) == "error"

    def test_returns_error_on_os_error(self) -> None:
        with (
            patch("doctor.shutil.which", return_value="/usr/bin/tool"),
            patch("doctor.subprocess.run", side_effect=OSError("permission denied")),
        ):
            assert get_version(["tool", "--version"]) == "error"


# ---------------------------------------------------------------------------
# get_package_version
# ---------------------------------------------------------------------------


class TestGetPackageVersion:
    """Tests for installed package version lookup."""

    def test_returns_version_for_installed_package(self) -> None:
        # pytest is always installed in the test environment
        result = get_package_version("pytest")
        assert result != "not installed"
        assert "." in result  # version string contains dots

    def test_returns_not_installed_for_missing_package(self) -> None:
        assert get_package_version("nonexistent-pkg-xyz-123") == "not installed"


# ---------------------------------------------------------------------------
# check_path_exists
# ---------------------------------------------------------------------------


class TestCheckPathExists:
    """Tests for path existence checker."""

    def test_returns_directory_for_dir(self, tmp_path: Path) -> None:
        assert check_path_exists(tmp_path) == "directory"

    def test_returns_file_for_file(self, tmp_path: Path) -> None:
        f = tmp_path / "test.txt"
        f.write_text("hello")
        assert check_path_exists(f) == "file"

    def test_returns_missing_for_nonexistent(self, tmp_path: Path) -> None:
        assert check_path_exists(tmp_path / "nope") == "missing"


# ---------------------------------------------------------------------------
# format_plain
# ---------------------------------------------------------------------------

SAMPLE_INFO: dict[str, str | dict[str, str]] = {
    "timestamp": "2026-02-25T12:00:00+00:00",
    "system": {
        "os": "Windows 10",
        "python_version": "3.13.5",
    },
    "tools": {
        "hatch": "Hatch, version 1.14.0",
        "git": "git version 2.47.1",
    },
}


class TestFormatPlain:
    """Tests for plain-text formatting."""

    def test_contains_header(self) -> None:
        output = format_plain(SAMPLE_INFO)
        assert "Timestamp" in output

    def test_contains_section_names(self) -> None:
        output = format_plain(SAMPLE_INFO)
        assert "Timestamp" in output
        assert "System Information" in output
        assert "Tool Versions" in output

    def test_contains_values(self) -> None:
        output = format_plain(SAMPLE_INFO)
        assert "python_version:" in output
        assert "3.13.5" in output
        assert "Windows 10" in output

    def test_scalar_values_rendered(self) -> None:
        output = format_plain(SAMPLE_INFO)
        assert "2026-02-25T12:00:00+00:00" in output


# ---------------------------------------------------------------------------
# format_markdown
# ---------------------------------------------------------------------------


class TestFormatMarkdown:
    """Tests for markdown formatting."""

    def test_wraps_in_details_tag(self) -> None:
        output = format_markdown(SAMPLE_INFO)
        assert output.startswith("<details>")
        assert "</details>" in output

    def test_contains_code_block(self) -> None:
        output = format_markdown(SAMPLE_INFO)
        assert "```" in output

    def test_contains_values(self) -> None:
        output = format_markdown(SAMPLE_INFO)
        assert "python_version: 3.13.5" in output


# ---------------------------------------------------------------------------
# format_json
# ---------------------------------------------------------------------------


class TestFormatJson:
    """Tests for JSON formatting."""

    def test_valid_json(self) -> None:
        output = format_json(SAMPLE_INFO)
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_roundtrips_data(self) -> None:
        output = format_json(SAMPLE_INFO)
        parsed = json.loads(output)
        assert parsed["timestamp"] == "2026-02-25T12:00:00+00:00"
        assert parsed["system"]["python_version"] == "3.13.5"

    def test_pretty_printed(self) -> None:
        output = format_json(SAMPLE_INFO)
        # json.dumps with indent=2 produces multi-line output
        assert "\n" in output


# ---------------------------------------------------------------------------
# _git_info (mocked)
# ---------------------------------------------------------------------------


class TestGitInfo:
    """Tests for git repository info collection."""

    def test_returns_dict(self) -> None:
        result = _git_info()
        assert isinstance(result, dict)

    def test_contains_expected_keys(self) -> None:
        result = _git_info()
        # If git is available (it should be in dev), we get branch/commit/dirty
        if "status" not in result:  # git found
            assert "branch" in result
            assert "commit" in result
            assert "dirty" in result

    def test_returns_status_when_git_missing(self) -> None:
        with patch("doctor.shutil.which", return_value=None):
            result = _git_info()

        assert result == {"status": "git not found"}

    def test_handles_subprocess_failure(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""

        with (
            patch("doctor.shutil.which", return_value="/usr/bin/git"),
            patch("doctor.subprocess.run", return_value=mock_result),
        ):
            result = _git_info()

        assert result["branch"] == "unknown"
        assert result["commit"] == "unknown"


# ---------------------------------------------------------------------------
# collect_diagnostics (parallel tools)
# ---------------------------------------------------------------------------


class TestCollectDiagnostics:
    """Tests for the full diagnostics collector."""

    def test_tools_include_actionlint_and_cz(self) -> None:
        """actionlint and cz should appear in the tools section."""
        from doctor import collect_diagnostics

        info = collect_diagnostics()
        tools = info["tools"]
        assert isinstance(tools, dict)
        assert "actionlint" in tools
        assert "cz" in tools

    def test_all_tool_values_are_strings(self) -> None:
        """Every tool version should be a string (not an exception)."""
        from doctor import collect_diagnostics

        info = collect_diagnostics()
        tools = info["tools"]
        assert isinstance(tools, dict)
        for name, value in tools.items():
            assert isinstance(value, str), f"tools[{name!r}] is {type(value)}"

    def test_timestamp_is_utc(self) -> None:
        """Timestamp should contain UTC offset (+00:00)."""
        from doctor import collect_diagnostics

        info = collect_diagnostics()
        ts = info["timestamp"]
        assert isinstance(ts, str)
        assert "+00:00" in ts

    def test_problems_section_present(self) -> None:
        """Diagnostics should include a 'problems' summary section."""
        from doctor import collect_diagnostics

        info = collect_diagnostics()
        assert "problems" in info
        assert isinstance(info["problems"], dict)

    def test_tools_include_bandit_and_deptry(self) -> None:
        """bandit and deptry should appear in the tools section."""
        from doctor import collect_diagnostics

        info = collect_diagnostics()
        tools = info["tools"]
        assert isinstance(tools, dict)
        assert "bandit" in tools
        assert "deptry" in tools


# ---------------------------------------------------------------------------
# _collect_problems
# ---------------------------------------------------------------------------


class TestCollectProblems:
    """Tests for the problems summary collector."""

    def test_no_problems_returns_status_key(self) -> None:
        """When everything is fine, should report 'no problems detected'."""
        info: dict[str, str | dict[str, str]] = {
            "environment": {"activated": "yes"},
            "pip_install": {"installed": "yes"},
            "python_compat": {"compatible": "yes"},
            "hooks": {
                "pre-commit": "installed",
                "commit-msg": "installed",
                "pre-push": "installed",
            },
            "config_files": {"pyproject.toml": "present"},
            "tools": {"ruff": "ruff 0.9.0"},
        }
        result = _collect_problems(info)
        assert result == {"status": "no problems detected"}

    def test_detects_no_venv(self) -> None:
        info: dict[str, str | dict[str, str]] = {
            "environment": {"activated": "no"},
            "pip_install": {"installed": "yes"},
            "python_compat": {},
            "hooks": {},
            "config_files": {},
            "tools": {},
        }
        result = _collect_problems(info)
        assert "no_venv" in result

    def test_detects_missing_install(self) -> None:
        info: dict[str, str | dict[str, str]] = {
            "environment": {"activated": "yes"},
            "pip_install": {"installed": "no"},
            "python_compat": {},
            "hooks": {},
            "config_files": {},
            "tools": {},
        }
        result = _collect_problems(info)
        assert "not_installed" in result

    def test_detects_python_compat_failure(self) -> None:
        info: dict[str, str | dict[str, str]] = {
            "environment": {"activated": "yes"},
            "pip_install": {"installed": "yes"},
            "python_compat": {"compatible": "NO (need >=3.11)"},
            "hooks": {},
            "config_files": {},
            "tools": {},
        }
        result = _collect_problems(info)
        assert "python_compat" in result

    def test_detects_missing_hooks(self) -> None:
        info: dict[str, str | dict[str, str]] = {
            "environment": {"activated": "yes"},
            "pip_install": {"installed": "yes"},
            "python_compat": {},
            "hooks": {"pre-commit": "missing", "commit-msg": "installed"},
            "config_files": {},
            "tools": {},
        }
        result = _collect_problems(info)
        assert "hooks_missing" in result
        assert "pre-commit" in result["hooks_missing"]

    def test_detects_missing_config_files(self) -> None:
        info: dict[str, str | dict[str, str]] = {
            "environment": {"activated": "yes"},
            "pip_install": {"installed": "yes"},
            "python_compat": {},
            "hooks": {},
            "config_files": {"mkdocs.yml": "MISSING"},
            "tools": {},
        }
        result = _collect_problems(info)
        assert "config_missing" in result

    def test_detects_missing_tools(self) -> None:
        info: dict[str, str | dict[str, str]] = {
            "environment": {"activated": "yes"},
            "pip_install": {"installed": "yes"},
            "python_compat": {},
            "hooks": {},
            "config_files": {},
            "tools": {"ruff": "ruff 0.9.0", "mypy": "not found"},
        }
        result = _collect_problems(info)
        assert "tools_missing" in result
        assert "mypy" in result["tools_missing"]

    def test_actionlint_missing_is_optional(self) -> None:
        """actionlint is optional — should not appear in tools_missing."""
        info: dict[str, str | dict[str, str]] = {
            "environment": {"activated": "yes"},
            "pip_install": {"installed": "yes"},
            "python_compat": {},
            "hooks": {},
            "config_files": {},
            "tools": {"ruff": "ruff 0.9.0", "actionlint": "not found"},
        }
        result = _collect_problems(info)
        assert "tools_missing" not in result
        assert "tools_optional" in result
        assert "actionlint" in result["tools_optional"]


# ---------------------------------------------------------------------------
# _supports_color
# ---------------------------------------------------------------------------


class TestSupportsColor:
    """Tests for color detection."""

    def test_no_color_env_disables(self) -> None:
        stream = MagicMock()
        stream.isatty.return_value = True
        with patch.dict(os.environ, {"NO_COLOR": "1"}, clear=False):
            assert _supports_color(stream) is False

    def test_force_color_env_enables(self) -> None:
        stream = MagicMock()
        stream.isatty.return_value = False
        with patch.dict(os.environ, {"FORCE_COLOR": "1"}, clear=False):
            # Remove NO_COLOR if set
            env = os.environ.copy()
            env.pop("NO_COLOR", None)
            with patch.dict(os.environ, env, clear=True):
                assert _supports_color(stream) is True

    def test_tty_stream_returns_true(self) -> None:
        stream = MagicMock()
        stream.isatty.return_value = True
        with patch.dict(os.environ, {}, clear=False):
            env = os.environ.copy()
            env.pop("NO_COLOR", None)
            env.pop("FORCE_COLOR", None)
            with (
                patch.dict(os.environ, env, clear=True),
                patch("_colors._enable_windows_ansi", return_value=True),
            ):
                assert _supports_color(stream) is True
