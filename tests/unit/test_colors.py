"""Unit tests for scripts/_colors.py shared color utilities."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# scripts/ is not an installed package — add it to sys.path so we can import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from _colors import Colors, colorize, status_icon, supports_color

# ---------------------------------------------------------------------------
# supports_color
# ---------------------------------------------------------------------------


class TestSupportsColor:
    """Tests for TTY / env-var color detection."""

    def test_no_color_env_disables(self) -> None:
        stream = MagicMock()
        stream.isatty.return_value = True
        with patch.dict(os.environ, {"NO_COLOR": "1"}, clear=False):
            assert supports_color(stream) is False

    def test_force_color_env_enables(self) -> None:
        stream = MagicMock()
        stream.isatty.return_value = False
        env = os.environ.copy()
        env.pop("NO_COLOR", None)
        env["FORCE_COLOR"] = "1"
        with patch.dict(os.environ, env, clear=True):
            assert supports_color(stream) is True

    def test_tty_stream_returns_true(self) -> None:
        stream = MagicMock()
        stream.isatty.return_value = True
        env = os.environ.copy()
        env.pop("NO_COLOR", None)
        env.pop("FORCE_COLOR", None)
        with (
            patch.dict(os.environ, env, clear=True),
            patch("_colors._enable_windows_ansi", return_value=True),
        ):
            assert supports_color(stream) is True

    def test_non_tty_stream_returns_false(self) -> None:
        stream = MagicMock()
        stream.isatty.return_value = False
        env = os.environ.copy()
        env.pop("NO_COLOR", None)
        env.pop("FORCE_COLOR", None)
        with patch.dict(os.environ, env, clear=True):
            assert supports_color(stream) is False

    def test_defaults_to_stdout(self) -> None:
        """When no stream argument, uses sys.stdout."""
        env = os.environ.copy()
        env.pop("NO_COLOR", None)
        env.pop("FORCE_COLOR", None)
        mock_stdout = MagicMock()
        mock_stdout.isatty.return_value = True
        with (
            patch.dict(os.environ, env, clear=True),
            patch.object(sys, "stdout", mock_stdout),
            patch("_colors._enable_windows_ansi", return_value=True),
        ):
            assert supports_color() is True

    def test_stream_without_isatty(self) -> None:
        """Streams without isatty attribute should return False."""
        stream = object()  # no isatty
        env = os.environ.copy()
        env.pop("NO_COLOR", None)
        env.pop("FORCE_COLOR", None)
        with patch.dict(os.environ, env, clear=True):
            assert supports_color(stream) is False

    def test_windows_vt_fallback(self) -> None:
        """On Windows, if VT processing can't be enabled, color is disabled."""
        stream = MagicMock()
        stream.isatty.return_value = True
        env = os.environ.copy()
        env.pop("NO_COLOR", None)
        env.pop("FORCE_COLOR", None)
        with (
            patch.dict(os.environ, env, clear=True),
            patch("_colors.sys") as mock_sys,
            patch("_colors._enable_windows_ansi", return_value=False),
        ):
            mock_sys.platform = "win32"
            mock_sys.stdout = stream
            assert supports_color(stream) is False


# ---------------------------------------------------------------------------
# colorize
# ---------------------------------------------------------------------------


class TestColorize:
    """Tests for the low-level colorize helper."""

    def test_enabled_wraps_with_ansi(self) -> None:
        result = colorize("hello", "32", use_color=True)
        assert result == "\033[32mhello\033[0m"

    def test_disabled_returns_plain(self) -> None:
        result = colorize("hello", "32", use_color=False)
        assert result == "hello"

    def test_bold_red_combo(self) -> None:
        result = colorize("error", "1;31", use_color=True)
        assert result == "\033[1;31merror\033[0m"

    def test_empty_text(self) -> None:
        result = colorize("", "32", use_color=True)
        assert result == "\033[32m\033[0m"


# ---------------------------------------------------------------------------
# status_icon
# ---------------------------------------------------------------------------


class TestStatusIcon:
    """Tests for PASS/FAIL/WARN status labels."""

    def test_pass_green(self) -> None:
        result = status_icon("PASS", use_color=True)
        assert "\033[32m" in result
        assert "PASS" in result

    def test_fail_red(self) -> None:
        result = status_icon("FAIL", use_color=True)
        assert "\033[31m" in result
        assert "FAIL" in result

    def test_warn_yellow(self) -> None:
        result = status_icon("WARN", use_color=True)
        assert "\033[33m" in result
        assert "WARN" in result

    def test_no_color_returns_plain(self) -> None:
        for label in ("PASS", "FAIL", "WARN"):
            result = status_icon(label, use_color=False)
            assert result == label
            assert "\033[" not in result

    def test_unknown_status_no_crash(self) -> None:
        result = status_icon("UNKNOWN", use_color=True)
        assert "UNKNOWN" in result


# ---------------------------------------------------------------------------
# Colors class
# ---------------------------------------------------------------------------


class TestColors:
    """Tests for the Colors convenience class."""

    def test_enabled_bold(self) -> None:
        c = Colors(enabled=True)
        assert c.bold("text") == "\033[1mtext\033[0m"

    def test_enabled_dim(self) -> None:
        c = Colors(enabled=True)
        assert c.dim("text") == "\033[2mtext\033[0m"

    def test_enabled_red(self) -> None:
        c = Colors(enabled=True)
        assert c.red("text") == "\033[31mtext\033[0m"

    def test_enabled_green(self) -> None:
        c = Colors(enabled=True)
        assert c.green("text") == "\033[32mtext\033[0m"

    def test_enabled_yellow(self) -> None:
        c = Colors(enabled=True)
        assert c.yellow("text") == "\033[33mtext\033[0m"

    def test_enabled_blue(self) -> None:
        c = Colors(enabled=True)
        assert c.blue("text") == "\033[34mtext\033[0m"

    def test_enabled_cyan(self) -> None:
        c = Colors(enabled=True)
        assert c.cyan("text") == "\033[36mtext\033[0m"

    def test_enabled_white(self) -> None:
        c = Colors(enabled=True)
        assert c.white("text") == "\033[37mtext\033[0m"

    def test_disabled_returns_plain(self) -> None:
        c = Colors(enabled=False)
        assert c.bold("text") == "text"
        assert c.red("text") == "text"
        assert c.green("text") == "text"
        assert c.yellow("text") == "text"
        assert c.blue("text") == "text"
        assert c.cyan("text") == "text"
        assert c.dim("text") == "text"
        assert c.white("text") == "text"

    def test_icon_delegates_to_status_icon(self) -> None:
        c = Colors(enabled=True)
        result = c.icon("PASS")
        assert "\033[32m" in result
        assert "PASS" in result

    def test_icon_disabled(self) -> None:
        c = Colors(enabled=False)
        assert c.icon("FAIL") == "FAIL"

    def test_auto_detect_default(self) -> None:
        """Constructor without enabled= uses supports_color()."""
        env = os.environ.copy()
        env.pop("NO_COLOR", None)
        env["FORCE_COLOR"] = "1"
        with patch.dict(os.environ, env, clear=True):
            c = Colors()
            assert c.enabled is True

    def test_auto_detect_no_color(self) -> None:
        with patch.dict(os.environ, {"NO_COLOR": "1"}, clear=False):
            c = Colors()
            assert c.enabled is False
