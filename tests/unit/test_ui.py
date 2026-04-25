"""Unit tests for scripts/_ui.py shared dashboard UI utilities."""

from __future__ import annotations

import sys
from pathlib import Path

# scripts/ is not an installed package — add it to sys.path so we can import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from _ui import RECOMMENDED_SCRIPTS, UI

# ---------------------------------------------------------------------------
# RECOMMENDED_SCRIPTS registry
# ---------------------------------------------------------------------------


class TestRecommendedScriptsRegistry:
    """Tests for the shared RECOMMENDED_SCRIPTS dict."""

    def test_registry_is_non_empty(self) -> None:
        assert len(RECOMMENDED_SCRIPTS) > 0

    def test_entries_are_tuples_of_two_strings(self) -> None:
        for key, entry in RECOMMENDED_SCRIPTS.items():
            assert isinstance(entry, tuple), f"{key}: expected tuple"
            assert len(entry) == 2, f"{key}: expected 2-element tuple"
            cmd, desc = entry
            assert isinstance(cmd, str) and cmd, f"{key}: command must be non-empty str"
            assert isinstance(desc, str) and desc, (
                f"{key}: description must be non-empty str"
            )

    def test_known_keys_present(self) -> None:
        """Core scripts should always be in the registry."""
        expected = {"doctor", "repo_sauron", "bootstrap", "clean", "customize"}
        assert expected.issubset(RECOMMENDED_SCRIPTS.keys())


# ---------------------------------------------------------------------------
# UI.recommended_scripts()
# ---------------------------------------------------------------------------


class TestRecommendedScripts:
    """Tests for UI.recommended_scripts() output."""

    def test_prints_heading_and_preamble(self, capsys: object) -> None:
        ui = UI(title="Test", version="0.0.0", theme="cyan", no_color=True)
        ui.recommended_scripts(["doctor"], preamble="Test preamble")
        captured = capsys.readouterr()  # type: ignore[union-attr]
        output = captured.out
        assert "Recommended Scripts" in output
        assert "Test preamble" in output

    def test_custom_heading(self, capsys: object) -> None:
        ui = UI(title="Test", version="0.0.0", theme="cyan", no_color=True)
        ui.recommended_scripts(["doctor"], heading="Custom Heading")
        captured = capsys.readouterr()  # type: ignore[union-attr]
        assert "Custom Heading" in captured.out

    def test_displays_script_command_and_description(self, capsys: object) -> None:
        ui = UI(title="Test", version="0.0.0", theme="cyan", no_color=True)
        ui.recommended_scripts(["doctor"])
        captured = capsys.readouterr()  # type: ignore[union-attr]
        output = captured.out
        cmd, desc = RECOMMENDED_SCRIPTS["doctor"]
        assert cmd in output
        assert desc in output

    def test_skips_unknown_keys(self, capsys: object) -> None:
        ui = UI(title="Test", version="0.0.0", theme="cyan", no_color=True)
        ui.recommended_scripts(["nonexistent_key_xyz", "doctor"])
        captured = capsys.readouterr()  # type: ignore[union-attr]
        output = captured.out
        # Should still show doctor, not crash on unknown key
        cmd, _ = RECOMMENDED_SCRIPTS["doctor"]
        assert cmd in output
        assert "nonexistent_key_xyz" not in output

    def test_attribution_lines_present(self, capsys: object) -> None:
        ui = UI(title="Test", version="0.0.0", theme="cyan", no_color=True)
        ui.recommended_scripts(["doctor"])
        captured = capsys.readouterr()  # type: ignore[union-attr]
        output = captured.out
        assert "JoJo275" in output
        assert "simple-python-boilerplate" in output

    def test_empty_keys_shows_heading_only(self, capsys: object) -> None:
        ui = UI(title="Test", version="0.0.0", theme="cyan", no_color=True)
        ui.recommended_scripts([])
        captured = capsys.readouterr()  # type: ignore[union-attr]
        output = captured.out
        assert "Recommended Scripts" in output
        # No script commands should appear
        for cmd, _ in RECOMMENDED_SCRIPTS.values():
            assert cmd not in output

    def test_multiple_scripts_all_shown(self, capsys: object) -> None:
        keys = ["doctor", "repo_sauron", "clean"]
        ui = UI(title="Test", version="0.0.0", theme="cyan", no_color=True)
        ui.recommended_scripts(keys)
        captured = capsys.readouterr()  # type: ignore[union-attr]
        output = captured.out
        for key in keys:
            cmd, desc = RECOMMENDED_SCRIPTS[key]
            assert cmd in output
            assert desc in output

    def test_description_appears_before_command(self, capsys: object) -> None:
        """Mini colored title (description) should appear above the command."""
        ui = UI(title="Test", version="0.0.0", theme="cyan", no_color=True)
        ui.recommended_scripts(["doctor"])
        captured = capsys.readouterr()  # type: ignore[union-attr]
        output = captured.out
        cmd, desc = RECOMMENDED_SCRIPTS["doctor"]
        desc_pos = output.index(desc)
        cmd_pos = output.index(cmd)
        assert desc_pos < cmd_pos, "Description should appear before command"


# ---------------------------------------------------------------------------
# UI basic output
# ---------------------------------------------------------------------------


class TestUIBasicOutput:
    """Tests for core UI layout methods."""

    def test_header_contains_title_and_version(self, capsys: object) -> None:
        ui = UI(title="My Tool", version="1.2.3", theme="cyan", no_color=True)
        ui.header()
        captured = capsys.readouterr()  # type: ignore[union-attr]
        output = captured.out
        assert "My Tool" in output
        assert "1.2.3" in output

    def test_section_contains_title(self, capsys: object) -> None:
        ui = UI(title="Test", version="0.0.0", theme="cyan", no_color=True)
        ui.section("My Section")
        captured = capsys.readouterr()  # type: ignore[union-attr]
        assert "My Section" in captured.out

    def test_kv_output(self, capsys: object) -> None:
        ui = UI(title="Test", version="0.0.0", theme="cyan", no_color=True)
        ui.kv("Label", "Value")
        captured = capsys.readouterr()  # type: ignore[union-attr]
        assert "Label:" in captured.out
        assert "Value" in captured.out

    def test_status_line(self, capsys: object) -> None:
        ui = UI(title="Test", version="0.0.0", theme="cyan", no_color=True)
        ui.status_line("check", "All good", "green")
        captured = capsys.readouterr()  # type: ignore[union-attr]
        assert "All good" in captured.out

    def test_footer_shows_counts(self, capsys: object) -> None:
        ui = UI(title="Test", version="0.0.0", theme="cyan", no_color=True)
        ui.footer(passed=5, failed=1, warned=2)
        captured = capsys.readouterr()  # type: ignore[union-attr]
        output = captured.out
        assert "5 passed" in output
        assert "1 failed" in output
        assert "2 warned" in output
