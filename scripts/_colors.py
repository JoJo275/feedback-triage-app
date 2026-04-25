"""Shared ANSI color utilities for scripts.

Provides terminal color detection, colorization helpers, and a
convenience class for styled output.  All scripts that produce
colored terminal output should import from here instead of
re-implementing color logic.

The module respects the ``NO_COLOR`` / ``FORCE_COLOR`` environment
variables (see https://no-color.org/) and auto-detects TTY support.

Usage::

    from _colors import Colors, supports_color

    # Quick one-off colorization
    c = Colors()                       # auto-detect TTY
    print(c.green("All checks passed!"))
    print(c.bold("Section Header"))

    # Force color on/off via CLI flag
    c = Colors(enabled=not args.no_color)

    # Low-level: wrap text with a raw ANSI code
    from _colors import colorize
    print(colorize("warning text", "33", use_color=True))

    # Status icons for pass/fail/warn output
    from _colors import status_icon
    print(f"  [{status_icon('PASS', use_color=True)}] check passed")

.. note::
    This is a shared internal module (prefixed with ``_``). It is excluded
    from the command reference generator and is not intended as a standalone
    CLI. See ADR 031 for script conventions.
"""

from __future__ import annotations

import os
import re
import sys
from typing import TextIO

__all__ = [
    "Colors",
    "colorize",
    "status_icon",
    "strip_ansi",
    "supports_color",
    "supports_unicode",
    "unicode_symbols",
]

SCRIPT_VERSION = "1.2.0"


# ---------------------------------------------------------------------------
# Windows ANSI support
# ---------------------------------------------------------------------------

_win_vt_enabled: bool | None = None  # sentinel: None = not yet tried


def _enable_windows_ansi() -> bool:
    """Try to enable Virtual Terminal Processing on Windows.

    On Windows 10 1607+ the console supports ANSI escape sequences, but
    the feature must be explicitly enabled via ``SetConsoleMode``.  If the
    call fails (older Windows, or redirected handle), we return False so
    callers can fall back to plain text.

    Returns:
        True if ANSI escapes should work, False otherwise.
    """
    global _win_vt_enabled
    if _win_vt_enabled is not None:
        return _win_vt_enabled

    try:
        import ctypes
        import ctypes.wintypes

        STD_OUTPUT_HANDLE = -11
        ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        if handle == -1:
            _win_vt_enabled = False
            return False

        mode = ctypes.wintypes.DWORD()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            _win_vt_enabled = False
            return False

        new_mode = mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING
        result = kernel32.SetConsoleMode(handle, new_mode)
        _win_vt_enabled = bool(result)
    except (AttributeError, OSError, ValueError):
        # Not Windows, or ctypes unavailable, or console not available
        _win_vt_enabled = False

    return _win_vt_enabled


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------


def supports_color(stream: TextIO | None = None) -> bool:
    """Detect whether *stream* supports ANSI color escape sequences.

    Checks (in order):
    1. ``NO_COLOR`` env var → disable
    2. ``FORCE_COLOR`` env var → enable
    3. On Windows, attempt to enable Virtual Terminal Processing;
       if it fails the console cannot render ANSI codes → disable.
    4. Stream is a TTY → enable

    Args:
        stream: Output stream to test.  Defaults to ``sys.stdout``.

    Returns:
        True if color is likely supported.
    """
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    s = stream or sys.stdout
    if not (hasattr(s, "isatty") and s.isatty()):
        return False
    # On Windows, ANSI support requires VT processing to be enabled
    if sys.platform == "win32":
        return _enable_windows_ansi()
    return True


def supports_unicode(stream: TextIO | None = None) -> bool:
    """Detect whether *stream* can render Unicode characters beyond ASCII/Latin-1.

    On Windows, PowerShell and cmd.exe often default to legacy code pages
    (e.g. CP1252, CP437) that cannot render box-drawing characters (─),
    check marks (✓), or em-dashes (—).  This function checks the stream's
    encoding to decide whether Unicode decorations are safe.

    Args:
        stream: Output stream to test.  Defaults to ``sys.stdout``.

    Returns:
        True if the stream encoding supports full Unicode output.
    """
    # TODO (template users): If your project targets only modern terminals
    #   (e.g. Windows Terminal, Linux, macOS), you may not need this guard.
    #   Remove calls to supports_unicode() and use Unicode symbols directly.
    s = stream or sys.stdout
    encoding = getattr(s, "encoding", "") or ""
    if not encoding:
        # Fallback: check locale preferred encoding (useful when stream
        # encoding is unavailable, e.g. in some embedded/CI environments).
        import locale

        encoding = locale.getpreferredencoding(False)
    normalized = encoding.lower().replace("-", "").replace("_", "")
    return normalized in ("utf8", "utf16", "utf32", "utf8sig")


# ---------------------------------------------------------------------------
# Unicode symbol map
# ---------------------------------------------------------------------------

# Cached result so supports_unicode() is called at most once per process.
_cached_symbols: dict[str, str] | None = None


def unicode_symbols(stream: TextIO | None = None) -> dict[str, str]:
    """Return a dict of display symbols appropriate for the terminal.

    If the output stream supports Unicode, returns symbols like ``\u2713``
    (check mark). Otherwise falls back to safe ASCII equivalents.

    The result is cached after the first call (per-process), so repeated
    calls are free.

    Keys returned::

        check  ✓ / OK     success indicator
        cross  ✗ / X      failure indicator
        warn   ⚠ / !!     warning indicator
        info   ℹ / i      informational indicator
        dash   — / --     em-dash separator
        sep    ─ / -      horizontal rule character
        sep2   ═ / =      double horizontal rule character
        arrow  → / ->     arrow / pointer
        flag   ⚑ / !      flag / attention marker
        bullet ● / *      bullet point
        ellip  … / ...    ellipsis

    Args:
        stream: Output stream to test.  Defaults to ``sys.stdout``.

    Returns:
        Dict mapping symbol names to their string representations.
    """
    global _cached_symbols
    if _cached_symbols is not None:
        return _cached_symbols

    if supports_unicode(stream):
        _cached_symbols = {
            "check": "\u2713",  # ✓
            "cross": "\u2717",  # ✗
            "warn": "\u26a0",  # ⚠
            "info": "\u2139",  # ℹ
            "dash": "\u2014",  # —
            "sep": "\u2500",  # ─
            "sep2": "\u2550",  # ═
            "arrow": "\u2192",  # →
            "flag": "\u2691",  # ⚑
            "bullet": "\u25cf",  # ●
            "ellip": "\u2026",  # …
        }
    else:
        _cached_symbols = {
            "check": "OK",
            "cross": "X",
            "warn": "!!",
            "info": "i",
            "dash": "--",
            "sep": "-",
            "sep2": "=",
            "arrow": "->",
            "flag": "!",
            "bullet": "*",
            "ellip": "...",
        }
    return _cached_symbols


_ANSI_RE = re.compile(r"\033\[[0-9;]*m")


def strip_ansi(text: str) -> str:
    """Remove all ANSI escape sequences from *text*.

    Useful for writing colored output to files or comparing
    strings that may contain escape codes.

    Args:
        text: String potentially containing ANSI codes.

    Returns:
        Plain text with all ``\\033[…m`` sequences removed.
    """
    return _ANSI_RE.sub("", text)


def colorize(text: str, code: str, *, use_color: bool) -> str:
    """Wrap *text* in ANSI escape codes when *use_color* is True.

    Args:
        text: The text to colorize.
        code: ANSI SGR code string (e.g. ``"32"`` for green,
              ``"1;31"`` for bold red).
        use_color: Whether to actually apply the escape codes.

    Returns:
        Colorized string, or plain *text* when color is disabled.
    """
    if not use_color:
        return text
    return f"\033[{code}m{text}\033[0m"


def status_icon(status: str, *, use_color: bool) -> str:
    """Return a colored PASS / FAIL / WARN label.

    Args:
        status: One of ``"PASS"``, ``"FAIL"``, ``"WARN"``.
        use_color: Whether to apply color.

    Returns:
        The status string, optionally wrapped in green/red/yellow.
    """
    codes = {"PASS": "32", "FAIL": "31", "WARN": "33"}  # nosec B105
    return colorize(status, codes.get(status, "0"), use_color=use_color)


# ---------------------------------------------------------------------------
# High-level Colors class
# ---------------------------------------------------------------------------


class Colors:
    """Convenience wrapper for named ANSI styles with auto-detection.

    Instantiate once and call methods to wrap text::

        c = Colors()              # auto-detect
        c = Colors(enabled=True)  # force on
        print(c.green("ok"), c.red("fail"))

    When ``enabled`` is False every method returns its input unchanged,
    so callers don't need conditional logic.
    """

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # TODO (template users): Add bright/high-intensity variants (e.g.
    #   BRIGHT_RED = "\033[91m") if you need them for your output styling.

    def __init__(self, *, enabled: bool | None = None) -> None:
        if enabled is None:
            enabled = supports_color()
        self.enabled = enabled

    # -- internal ------------------------------------------------------------

    def _wrap(self, code: str, text: str) -> str:
        if not self.enabled:
            return text
        return f"{code}{text}{self.RESET}"

    # -- public convenience --------------------------------------------------

    def bold(self, text: str) -> str:
        """Bold text."""
        return self._wrap(self.BOLD, text)

    def dim(self, text: str) -> str:
        """Dim / faint text."""
        return self._wrap(self.DIM, text)

    def red(self, text: str) -> str:
        """Red text (errors, failures)."""
        return self._wrap(self.RED, text)

    def green(self, text: str) -> str:
        """Green text (success, pass)."""
        return self._wrap(self.GREEN, text)

    def yellow(self, text: str) -> str:
        """Yellow text (warnings)."""
        return self._wrap(self.YELLOW, text)

    def blue(self, text: str) -> str:
        """Blue text (info, headers)."""
        return self._wrap(self.BLUE, text)

    def magenta(self, text: str) -> str:
        """Magenta text."""
        return self._wrap(self.MAGENTA, text)

    def cyan(self, text: str) -> str:
        """Cyan text (hints, links)."""
        return self._wrap(self.CYAN, text)

    def white(self, text: str) -> str:
        """Explicit white text."""
        return self._wrap(self.WHITE, text)

    def link(self, text: str, url: str) -> str:
        """Wrap *text* in an OSC 8 terminal hyperlink to *url*.

        Falls back to plain *text* when color/escape output is disabled.
        """
        if not self.enabled:
            return text
        return f"\033]8;;{url}\033\\{text}\033]8;;\033\\"

    def icon(self, status: str) -> str:
        """Colored PASS / FAIL / WARN label.

        Convenience alias for :func:`status_icon` using this
        instance's ``enabled`` flag.
        """
        return status_icon(status, use_color=self.enabled)
