"""Unit tests for scripts/_progress.py."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add scripts/ to path so we can import _progress
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from _progress import (
    SCRIPT_VERSION,
    ProgressBar,
    Spinner,
    _is_interactive,
    _pick_bar_style,
    _pick_spinner_frames,
    _supports_unicode,
    _terminal_width,
    _truncate,
)

# ---------------------------------------------------------------------------
# Module-level metadata
# ---------------------------------------------------------------------------


class TestMetadata:
    """Verify module metadata."""

    def test_version_is_string(self) -> None:
        assert isinstance(SCRIPT_VERSION, str)

    def test_version_is_semver(self) -> None:
        parts = SCRIPT_VERSION.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


class TestTerminalWidth:
    """Tests for _terminal_width()."""

    def test_returns_positive_int(self) -> None:
        width = _terminal_width()
        assert isinstance(width, int)
        assert width > 0

    def test_fallback_when_no_terminal(self) -> None:
        import os

        fake_size = os.terminal_size((80, 24))
        with patch("_progress.shutil.get_terminal_size", return_value=fake_size):
            assert _terminal_width() == 80


class TestIsInteractive:
    """Tests for _is_interactive()."""

    def test_returns_bool(self) -> None:
        assert isinstance(_is_interactive(), bool)

    def test_false_when_no_isatty(self) -> None:
        with patch.object(sys, "stdout") as mock_stdout:
            del mock_stdout.isatty
            assert _is_interactive() is False


class TestSupportsUnicode:
    """Tests for _supports_unicode()."""

    def test_returns_bool(self) -> None:
        assert isinstance(_supports_unicode(), bool)

    def test_utf8_detected(self) -> None:
        mock_stdout = MagicMock()
        mock_stdout.encoding = "utf-8"
        with patch("_progress.sys.stdout", mock_stdout):
            assert _supports_unicode() is True

    def test_ascii_not_unicode(self) -> None:
        mock_stdout = MagicMock()
        mock_stdout.encoding = "ascii"
        with patch("_progress.sys.stdout", mock_stdout):
            assert _supports_unicode() is False


class TestTruncate:
    """Tests for _truncate()."""

    def test_short_text_unchanged(self) -> None:
        assert _truncate("hello", 10) == "hello"

    def test_exact_length_unchanged(self) -> None:
        assert _truncate("hello", 5) == "hello"

    def test_long_text_truncated(self) -> None:
        result = _truncate("hello world", 8)
        assert len(result) <= 8
        assert result.endswith("...") or result.endswith("\u2026")

    def test_empty_string(self) -> None:
        assert _truncate("", 5) == ""


class TestBarStylePicker:
    """Tests for _pick_bar_style()."""

    def test_returns_4_tuple(self) -> None:
        style = _pick_bar_style()
        assert isinstance(style, tuple)
        assert len(style) == 4

    def test_all_strings(self) -> None:
        assert all(isinstance(s, str) for s in _pick_bar_style())


class TestSpinnerFrames:
    """Tests for _pick_spinner_frames()."""

    def test_returns_list(self) -> None:
        frames = _pick_spinner_frames()
        assert isinstance(frames, list)
        assert len(frames) >= 2

    def test_all_strings(self) -> None:
        assert all(isinstance(f, str) for f in _pick_spinner_frames())


# ---------------------------------------------------------------------------
# ProgressBar
# ---------------------------------------------------------------------------


class TestProgressBar:
    """Tests for ProgressBar class."""

    def test_initial_state(self) -> None:
        bar = ProgressBar(total=10, label="Test")
        assert bar.total == 10
        assert bar.label == "Test"
        assert bar.current == 0

    def test_update_increments(self) -> None:
        bar = ProgressBar(total=10)
        bar.update()
        assert bar.current == 1
        bar.update()
        assert bar.current == 2

    def test_update_caps_at_total(self) -> None:
        bar = ProgressBar(total=3)
        for _ in range(10):
            bar.update()
        assert bar.current == 3

    def test_reset(self) -> None:
        bar = ProgressBar(total=5)
        bar.update()
        bar.update()
        bar.reset()
        assert bar.current == 0

    def test_context_manager(self) -> None:
        with ProgressBar(total=3, label="CTX") as bar:
            bar.update()
            bar.update()
            assert bar.current == 2

    def test_zero_total_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        with caplog.at_level(logging.WARNING):
            ProgressBar(total=0)
        assert "total=0" in caplog.text

    def test_negative_total_logs_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.WARNING):
            ProgressBar(total=-5)
        assert "total=-5" in caplog.text

    def test_log_interval_default_off(self) -> None:
        bar = ProgressBar(total=10)
        assert bar._log_interval == 0

    def test_log_interval_configurable(self) -> None:
        bar = ProgressBar(total=100, log_interval=10)
        assert bar._log_interval == 10

    @patch("_progress._is_interactive", return_value=False)
    def test_ci_logging_emits_at_interval(self, _mock: object) -> None:
        """In non-interactive mode, log.info is called every N steps."""
        with patch("_progress.logger") as mock_log:
            bar = ProgressBar(total=20, label="CI", log_interval=5)
            bar._interactive = False  # force non-interactive
            for _ in range(20):
                bar.update()
            # Should log at steps 5, 10, 15, 20 = 4 calls
            assert mock_log.info.call_count == 4


# ---------------------------------------------------------------------------
# Spinner
# ---------------------------------------------------------------------------


class TestSpinner:
    """Tests for Spinner class."""

    def test_initial_state(self) -> None:
        spin = Spinner(label="Test")
        assert spin.label == "Test"
        assert spin.count == 0

    def test_update_increments(self) -> None:
        spin = Spinner()
        spin.update()
        assert spin.count == 1
        spin.update()
        assert spin.count == 2

    def test_reset(self) -> None:
        spin = Spinner()
        spin.update()
        spin.update()
        spin.reset()
        assert spin.count == 0

    def test_context_manager(self) -> None:
        with Spinner("CTX") as spin:
            spin.update("item1")
            spin.update("item2")
            assert spin.count == 2

    def test_log_interval_configurable(self) -> None:
        spin = Spinner(log_interval=25)
        assert spin._log_interval == 25

    @patch("_progress._is_interactive", return_value=False)
    def test_ci_logging_emits_at_interval(self, _mock: object) -> None:
        with patch("_progress.logger") as mock_log:
            spin = Spinner(label="CI", log_interval=3)
            spin._interactive = False
            for _ in range(9):
                spin.update()
            # Steps 3, 6, 9 = 3 calls
            assert mock_log.info.call_count == 3
