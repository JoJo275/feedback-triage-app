"""Shared dashboard UI utilities for scripts.

Provides a uniform output layout based on the ``git_doctor.py`` dashboard
style: box-drawing headers, section dividers, key-value pairs, and
summary footers.  Every CLI script imports from here so output has a
consistent, professional look with a per-script color theme.

The module respects terminal capabilities (Unicode/ASCII fallback) and
integrates with :mod:`_colors` for color detection and styling.

Usage::

    from _ui import UI

    ui = UI(title="Python Support", version="1.0.0", theme="green")
    ui.header()                          # ╔══ Python Support  v1.0.0 ══╗
    ui.section("Sources")                # ┌── Sources ──────────────────┐
    ui.kv("requires-python", ">=3.11")   #     requires-python:   >=3.11
    ui.kv("Hatch matrix", "3.11, 3.12, 3.13")
    ui.status_line("check", "All sources consistent", "green")
    ui.footer(passed=5, failed=0, warned=0)

.. note::
    This is a shared internal module (prefixed with ``_``). It is excluded
    from the command reference generator and is not intended as a standalone
    CLI. See ADR 031 for script conventions.
"""

from __future__ import annotations

import re
import shutil
import textwrap
import tomllib
from collections.abc import Callable
from typing import ClassVar

from _colors import Colors, strip_ansi, supports_unicode, unicode_symbols
from _imports import find_repo_root

__all__ = ["RECOMMENDED_SCRIPTS", "UI", "Spacing"]

SCRIPT_VERSION = "1.4.0"

# ---------------------------------------------------------------------------
# Shared recommended-scripts registry
# ---------------------------------------------------------------------------
# Each entry: (command, description).  Scripts select a subset by key
# when calling ``UI.recommended_scripts()``.  The registry is the single
# source of truth so descriptions stay consistent across all scripts.

RECOMMENDED_SCRIPTS: dict[str, tuple[str, str]] = {
    "repo_sauron": (
        "python scripts/repo_sauron.py",
        "Repository statistics Markdown report",
    ),
    "env_inspect": (
        "python scripts/env_inspect.py",
        "Environment, packages, PATH inspection",
    ),
    "check_python_support": (
        "python scripts/check_python_support.py",
        "Python version consistency across configs",
    ),
    "repo_doctor": (
        "python scripts/repo_doctor.py",
        "Repository structure health checks",
    ),
    "dep_versions": (
        "python scripts/dep_versions.py show",
        "Dependency versions and update status",
    ),
    "env_doctor": (
        "python scripts/env_doctor.py",
        "Development environment diagnostics",
    ),
    "doctor": (
        "python scripts/doctor.py",
        "Unified health check (runs all doctors)",
    ),
    "workflow_versions": (
        "python scripts/workflow_versions.py",
        "GitHub Actions SHA-pinned version status",
    ),
    "git_doctor": (
        "python scripts/git_doctor.py",
        "Git health dashboard, config, branch ops",
    ),
    "bootstrap": (
        "python scripts/bootstrap.py",
        "One-command project setup for fresh clones",
    ),
    "customize": (
        "python scripts/customize.py",
        "Interactive template customization wizard",
    ),
    "clean": (
        "python scripts/clean.py",
        "Remove build artifacts and caches",
    ),
    "archive_todos": (
        "python scripts/archive_todos.py",
        "Archive resolved TODO comments",
    ),
    "apply_labels": (
        "python scripts/apply_labels.py",
        "Apply GitHub labels from JSON definitions",
    ),
    "changelog_check": (
        "python scripts/changelog_check.py",
        "Validate changelog format and entries",
    ),
    "check_known_issues": (
        "python scripts/check_known_issues.py",
        "Verify known-issues status and links",
    ),
    "check_todos": (
        "python scripts/check_todos.py",
        "Scan codebase for TODO/FIXME comments",
    ),
    "generate_command_reference": (
        "python scripts/generate_command_reference.py",
        "Auto-generate CLI command reference docs",
    ),
    "test_containerfile": (
        "python scripts/test_containerfile.py",
        "Validate Containerfile build and structure",
    ),
    "test_docker_compose": (
        "python scripts/test_docker_compose.py",
        "Validate docker-compose configuration",
    ),
}

# ---------------------------------------------------------------------------
# Repo metadata helpers
# ---------------------------------------------------------------------------

_DEFAULT_REPO_URL = "https://github.com/JoJo275/simple-python-boilerplate"


def _resolve_repo_info() -> tuple[str, str, str]:
    """Read repo URL, name, and owner from pyproject.toml.

    Falls back to hardcoded defaults if parsing fails.

    Returns:
        ``(repo_url, repo_name, owner)``
    """
    try:
        root = find_repo_root()
        pyproject = root / "pyproject.toml"
        if pyproject.is_file():
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            urls = data.get("project", {}).get("urls", {})
            url = urls.get("Repository") or urls.get("Homepage") or ""
            if url:
                m = re.search(r"github\.com/([^/]+)/([^/]+?)(?:\.git)?$", url)
                if m:
                    return url.rstrip("/"), m.group(2), m.group(1)
            # Fallback: project name from metadata
            name = data.get("project", {}).get("name", "")
            if name:
                return _DEFAULT_REPO_URL, name, "unknown"
    except (OSError, KeyError, ValueError, tomllib.TOMLDecodeError):
        pass
    return _DEFAULT_REPO_URL, "simple-python-boilerplate", "JoJo275"


class Spacing:
    """Vertical and horizontal spacing conventions for dashboard output.

    Provides standardised gap sizes so all scripts produce consistently
    spaced output without overlapping text.  Scripts can override the
    defaults by passing custom values at construction time.

    Attributes:
        section_above: Blank lines before a section header.
        section_below: Blank lines after a section header.
        kv_gap: Blank lines between key-value pairs.  ``0`` (default)
            prints them back-to-back (compact); ``1`` adds a blank line
            between each pair (airy).
        block_gap: Blank lines between major blocks (e.g. after a table).
        indent: Number of spaces for primary indentation.
        nested_indent: Number of spaces for nested indentation.
        label_width: Default column width for key-value label alignment.
            Use :meth:`auto_label_width` to compute from actual keys.
        kv_gutter: Number of spaces between the label column and the
            value column.  Increase for more breathing room; decrease
            to keep output tight.
        kv_compact: If True, key-value lines are printed without
            any inter-line gap (default).  If False, a blank line
            is inserted between each pair.
        progress_pulse: If True, progress bars should use smooth
            pulse animation between ``update()`` calls.  Scripts
            reference this when creating :class:`ProgressBar` instances.
        command_wrap: If True, long command / value text is soft-wrapped
            to fit the terminal width using :meth:`wrap_value`.
    """

    def __init__(
        self,
        *,
        section_above: int = 1,
        section_below: int = 1,
        kv_gap: int = 0,
        block_gap: int = 1,
        indent: int = 4,
        nested_indent: int = 6,
        label_width: int = 22,
        kv_gutter: int = 1,
        kv_compact: bool = True,
        progress_pulse: bool = False,
        command_wrap: bool = True,
    ) -> None:
        self.section_above = section_above
        self.section_below = section_below
        self.kv_gap = kv_gap
        self.block_gap = block_gap
        self.indent = indent
        self.nested_indent = nested_indent
        self.label_width = label_width
        self.kv_gutter = kv_gutter
        self.kv_compact = kv_compact
        self.progress_pulse = progress_pulse
        self.command_wrap = command_wrap

    @property
    def pad(self) -> str:
        """Primary indent string."""
        return " " * self.indent

    @property
    def nested_pad(self) -> str:
        """Nested indent string."""
        return " " * self.nested_indent

    @staticmethod
    def auto_label_width(
        labels: list[str],
        *,
        min_width: int = 14,
        max_width: int = 38,
        extra: int = 2,
    ) -> int:
        """Compute an optimal label column width from a list of labels.

        Finds the longest label (plus colon suffix), adds *extra* padding
        characters, and clamps to ``[min_width, max_width]``.

        Args:
            labels: Key strings (without trailing colon).
            min_width: Floor for the returned width.
            max_width: Ceiling for the returned width.
            extra: Extra padding chars beyond the longest label.

        Returns:
            Computed label width in characters.
        """
        if not labels:
            return min_width
        longest = max(len(lab) + 1 for lab in labels)  # +1 for ':'
        return max(min_width, min(longest + extra, max_width))

    @staticmethod
    def wrap_value(
        value: str,
        *,
        indent: int,
        label_width: int,
        gutter: int = 1,
        max_width: int | None = None,
    ) -> str:
        """Soft-wrap a long value string to fit within the terminal.

        The first line is returned as-is (it will be placed after the
        label by the caller).  Continuation lines are indented so text
        aligns under the first character of the value column.

        Args:
            value: The raw value string to wrap.
            indent: Leading spaces before the label (e.g. 4).
            label_width: Width of the formatted label column.
            gutter: Spaces between label and value columns.
            max_width: Available terminal width.  Defaults to
                ``shutil.get_terminal_size().columns``.

        Returns:
            The wrapped string, ready to print (no leading indent —
            the caller prepends its own).
        """
        if max_width is None:
            max_width = shutil.get_terminal_size().columns
        # How much room is left for the value on each line?
        prefix_len = indent + label_width + gutter
        avail = max_width - prefix_len
        if avail < 20:
            # Terminal too narrow to wrap meaningfully — return raw.
            return value
        lines = textwrap.wrap(value, width=avail, break_on_hyphens=False)
        if not lines:
            return value
        continuation_pad = " " * prefix_len
        return ("\n" + continuation_pad).join(lines)


class UI:
    """Uniform dashboard output matching the git_doctor.py style.

    Args:
        title: Dashboard title shown in the header box.
        version: Script version shown dimmed next to the title.
        theme: Color name for the main border/accent color.
            One of: ``"cyan"``, ``"blue"``, ``"green"``, ``"yellow"``,
            ``"magenta"``, ``"red"``, ``"white"``.
        no_color: Force disable colors (e.g. from ``--no-color`` flag).
        spacing: Optional :class:`Spacing` instance for layout control.
    """

    # Map from color name to Colors method name
    _THEME_METHODS: ClassVar[dict[str, str]] = {
        "cyan": "cyan",
        "blue": "blue",
        "green": "green",
        "yellow": "yellow",
        "magenta": "magenta",
        "red": "red",
        "white": "white",
    }

    # For each theme, pick a command-text color that's visually distinct.
    _COMMAND_COLORS: ClassVar[dict[str, str]] = {
        "cyan": "magenta",
        "blue": "green",
        "green": "cyan",
        "yellow": "cyan",
        "magenta": "cyan",
        "red": "cyan",
        "white": "cyan",
    }

    def __init__(
        self,
        title: str,
        version: str,
        theme: str = "cyan",
        *,
        no_color: bool = False,
        spacing: Spacing | None = None,
    ) -> None:
        self.title = title
        self.version = version
        self.theme = theme
        self.c = Colors(enabled=not no_color)
        self.sym = unicode_symbols()
        self._use_unicode = supports_unicode()
        self.spacing = spacing or Spacing()

        # Box-drawing characters (Unicode with ASCII fallback)
        u = self._use_unicode
        self.h_line = "\u2500" if u else "-"  # ─
        self.h_double = "\u2550" if u else "="  # ═
        self.tl = "\u250c" if u else "+"  # ┌
        self.tr = "\u2510" if u else "+"  # ┐
        self.bl = "\u2514" if u else "+"  # └
        self.br = "\u2518" if u else "+"  # ┘
        self.tl_d = "\u2554" if u else "+"  # ╔
        self.tr_d = "\u2557" if u else "+"  # ╗
        self.bl_d = "\u255a" if u else "+"  # ╚
        self.br_d = "\u255d" if u else "+"  # ╝
        self.vl = "\u2502" if u else "|"  # │
        self.vl_d = "\u2551" if u else "|"  # ║
        self.dot = "\u2022" if u else "*"  # •

    @property
    def _accent(self) -> str:
        """Return the method name for the theme color."""
        return self._THEME_METHODS.get(self.theme, "cyan")

    def _themed(self, text: str) -> str:
        """Apply the theme color to *text*."""
        fn: Callable[[str], str] = getattr(self.c, self._accent)
        return fn(text)

    def _command_styled(self, text: str) -> str:
        """Apply the command-highlight color (distinct from theme) to *text*."""
        color_name = self._COMMAND_COLORS.get(self.theme, "cyan")
        fn: Callable[[str], str] = getattr(self.c, color_name)
        return fn(text)

    # ── Layout elements ────────────────────────────────────────

    def header(self, *, width: int = 60) -> None:
        """Print the main dashboard header with double-border box."""
        border = self.h_double * width
        print()
        print(self.c.bold(self._themed(f"  {self.tl_d}{border}{self.tr_d}")))
        print(
            f"  {self.c.bold(self._themed(self.vl_d))} "
            f"{self.c.bold(self._themed(self.title))}  "
            f"{self.c.dim(f'v{self.version}')}"
        )
        print(self.c.bold(self._themed(f"  {self.bl_d}{border}{self.br_d}")))

    def section(self, title: str, *, width: int = 60, compact: bool = False) -> None:
        """Print a section header with single-border box.

        Args:
            title: Section title text.
            width: Border width.
            compact: If True, omit the trailing blank line.
        """
        border = self.h_line * width
        print()
        print(self._themed(f"  {self.tl}{border}{self.tr}"))
        print(f"  {self._themed(self.vl)} {self.c.bold(self._themed(title))}")
        print(self._themed(f"  {self.bl}{border}{self.br}"))
        if not compact:
            print()

    def kv(
        self,
        label: str,
        value: str,
        *,
        width: int = 22,
        hint: str = "",
    ) -> None:
        """Print a key-value pair with consistent alignment.

        Args:
            label: Left-side label.
            value: Right-side value.
            width: Column width for label alignment.
            hint: Optional hint shown dimmed below the value.
        """
        print(f"    {label + ':':{width}s} {value}")
        if hint:
            print(f"    {'':{width}s} {self.c.dim(hint)}")
        for _ in range(self.spacing.kv_gap):
            print()

    def status_line(
        self,
        icon_name: str,
        message: str,
        color: str = "green",
    ) -> None:
        """Print a status indicator line (e.g. ✓ All checks passed).

        Args:
            icon_name: Symbol key from ``unicode_symbols()`` —
                ``"check"``, ``"cross"``, ``"warn"``, ``"info"``.
            message: Status message text.
            color: Color for both icon and message.
        """
        icon = self.sym.get(icon_name, icon_name)
        color_fn = getattr(self.c, color, self.c.green)
        print(f"  {color_fn(icon)} {color_fn(message)}")

    def info_line(self, message: str) -> None:
        """Print a dimmed informational line (indented)."""
        print(f"    {self.c.dim(message)}")

    def separator(
        self, *, width: int = 60, double: bool = False, themed: bool = False
    ) -> None:
        """Print a horizontal separator line."""
        char = self.h_double if double else self.h_line
        line = char * width
        print(f"  {self._themed(line) if themed else self.c.dim(line)}")

    def blank(self) -> None:
        """Print a blank line."""
        print()

    def table_header(
        self,
        columns: list[tuple[str, int]],
        *,
        themed: bool = False,
    ) -> None:
        """Print a table header row with underlines.

        Args:
            columns: List of ``(header_text, column_width)`` tuples.
            themed: If True, apply the theme accent color to header text.
        """
        hdr_parts = []
        line_parts = []
        for i, (text, w) in enumerate(columns):
            styled = self._themed(text) if themed else self.c.dim(text)
            visible_len = len(strip_ansi(styled))
            if i < len(columns) - 1:
                padding = max(w - visible_len, 0)
                hdr_parts.append(styled + " " * padding)
                line_parts.append(self.c.dim(self.h_line * w))
            else:
                hdr_parts.append(styled)
                line_parts.append(self.c.dim(self.h_line * w))
        print(f"    {' '.join(hdr_parts)}")
        print(f"    {' '.join(line_parts)}")

    def table_row(
        self,
        cells: list[tuple[str, int]],
    ) -> None:
        """Print a table data row.

        Args:
            cells: List of ``(cell_text, column_width)`` tuples.
                Cell text may contain ANSI codes; alignment uses
                the raw width.
        """
        parts = []
        for i, (text, w) in enumerate(cells):
            # Pad based on visible length (strip ANSI for measurement)
            visible_len = len(strip_ansi(text))
            # Skip right-padding on the last column to avoid line wrapping
            if i < len(cells) - 1:
                padding = max(w - visible_len, 0)
                parts.append(text + " " * padding)
            else:
                parts.append(text)
        print(f"    {' '.join(parts)}")

    def footer(
        self,
        passed: int,
        failed: int,
        warned: int = 0,
        *,
        elapsed: float | None = None,
    ) -> None:
        """Print a summary footer with pass/fail/warn counts.

        Args:
            passed: Number of passed checks.
            failed: Number of failed checks.
            warned: Number of warnings.
            elapsed: Optional elapsed time in seconds.
        """
        total = passed + failed + warned
        print()
        self.separator(double=True)

        parts = [self.c.green(f"{passed} passed")]
        if warned:
            parts.append(self.c.yellow(f"{warned} warned"))
        if failed:
            parts.append(self.c.red(f"{failed} failed"))

        summary = f"  {self.c.bold('Summary:')} {', '.join(parts)} / {total} total"
        print(summary)

        if elapsed is not None:
            print(f"  {self.c.dim(f'Completed in {elapsed:.1f}s')}")
        print()

    # ── Convenience: quick status bar ──────────────────────────

    def quick_status(
        self,
        items: list[tuple[str, str, str]],
        *,
        label_width: int = 22,
    ) -> None:
        """Print a quick status bar (like git_doctor's top indicators).

        Args:
            items: List of ``(label, status_text, color)`` tuples.
                ``color`` is a Colors method name.
            label_width: Padding width for labels.
        """
        print()
        for label, status_text, color in items:
            icon_name = {
                "green": "check",
                "yellow": "warn",
                "red": "cross",
            }.get(color, "info")
            icon = self.sym.get(icon_name, "?")
            color_fn = getattr(self.c, color, self.c.green)
            print(
                f"  {color_fn(icon)} "
                f"{self.c.dim(label.ljust(label_width))} "
                f"{color_fn(status_text)}"
            )

    # ── Rules summary bar ───────────────────────────────────────

    def rules_summary(
        self,
        passed: int,
        total: int,
        *,
        bar_width: int = 24,
    ) -> None:
        """Print an inline rules-upheld bar (e.g. ``41/47 rules upheld``).

        Args:
            passed: Number of rules that passed.
            total: Total number of rules evaluated.
            bar_width: Width of the inline progress bar in characters.
        """
        pct = (passed / total * 100) if total > 0 else 0
        filled = int(bar_width * passed / total) if total > 0 else 0
        fill_char = "\u2588" if self._use_unicode else "#"
        empty_char = "\u2591" if self._use_unicode else "-"

        bar_fill = fill_char * filled
        bar_empty = empty_char * (bar_width - filled)

        # Color the bar green if all pass, yellow if most pass, red otherwise
        if pct >= 100:
            bar_str = self.c.green(bar_fill) + self.c.dim(bar_empty)
            pct_str = self.c.green(f"{pct:.0f}%")
            count_str = self.c.green(f"{passed}/{total}")
        elif pct >= 70:
            bar_str = self.c.yellow(bar_fill) + self.c.dim(bar_empty)
            pct_str = self.c.yellow(f"{pct:.0f}%")
            count_str = self.c.yellow(f"{passed}/{total}")
        else:
            bar_str = self.c.red(bar_fill) + self.c.dim(bar_empty)
            pct_str = self.c.red(f"{pct:.0f}%")
            count_str = self.c.red(f"{passed}/{total}")

        label = self.c.bold("rules upheld")
        print(f"  {count_str} {label}  [{bar_str}]  {pct_str}")

    # ── Recommended Scripts ────────────────────────────────────

    def recommended_scripts(
        self,
        keys: list[str],
        *,
        heading: str = "Recommended Scripts",
        preamble: str = "Scripts that expand on this tool's output.",
    ) -> None:
        """Print a standardised recommended-scripts section.

        Pulls entries from the shared :data:`RECOMMENDED_SCRIPTS` registry
        so descriptions stay consistent across all scripts.

        The repo URL and owner are read dynamically from pyproject.toml
        ``[project.urls].Repository`` so they stay correct after template
        customisation.

        Args:
            keys: Registry keys to display (e.g. ``["repo_sauron", "doctor"]``).
            heading: Section title.
            preamble: Short description shown under the heading.
        """
        self.section(heading)
        print(f"    {self.c.green(self.c.bold(preamble))}")
        print()

        # Dynamically resolve repo metadata from pyproject.toml
        repo_url, repo_name, repo_owner = _resolve_repo_info()

        print(
            f"    {self.c.dim('Source:')}    {self._themed(repo_name)}"
            f" by {self.c.bold(repo_owner)} on GitHub"
        )
        print()
        print(
            f"    {self.c.dim('Repo:')}      "
            f"{self._themed(self.c.link(repo_url, repo_url))}"
        )
        print()
        print(f"    {self.c.dim('Location:')}  scripts/ directory")
        print()
        print(
            f"    {self.c.white('These scripts may already exist in this')}"
            f" {self._themed('repo')} {self.c.white('if it was')}"
        )
        print(f"    {self.c.white('forked from or based on the source.')}")
        print()
        repo_link = self._themed(self.c.link("repo", repo_url))
        print(
            f"    {self.c.white('If not, visit the source')} {repo_link} "
            f"{self.c.white(f'by {repo_owner} to obtain them.')}"
        )
        print()
        for i, key in enumerate(keys):
            entry = RECOMMENDED_SCRIPTS.get(key)
            if entry is None:
                continue
            cmd, desc = entry
            if i > 0:
                print()
            # Use dotted separator (·) to distinguish from solid box lines
            dot = "\u00b7" if self._use_unicode else "."
            sep_str = (f"{dot} " * ((len(desc) + 1) // 2))[: len(desc)]
            print(f"      {self._themed(desc)}")
            print(f"      {self.c.dim(sep_str)}")
            print(f"        {self.c.bold(self._command_styled(cmd))}")

    # ── Spacing convenience ─────────────────────────────────────

    def gap(self, lines: int = 1) -> None:
        """Print *lines* blank lines (default 1)."""
        for _ in range(lines):
            print()

    def padded(self, text: str, *, indent: int | None = None) -> None:
        """Print *text* with configurable left-indent.

        Uses ``self.spacing.indent`` by default.
        """
        pad = " " * (indent if indent is not None else self.spacing.indent)
        print(f"{pad}{text}")
