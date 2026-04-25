"""Unit tests for mkdocs-hooks/generate_commands.py."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# mkdocs-hooks/ is not an installed package — add it to sys.path so we can
# import the module directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "mkdocs-hooks"))

import generate_commands
from generate_commands import (
    _GENERATOR_SCRIPT,
    _OUTPUT,
    _ROOT,
    HOOK_VERSION,
    _load_generator,
    on_pre_build,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a minimal dict that behaves like ``MkDocsConfig``."""
    return {
        "extra": extra or {},
    }


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


class TestHookVersion:
    """Validate the version constant."""

    def test_version_is_string(self) -> None:
        assert isinstance(HOOK_VERSION, str)

    def test_version_format(self) -> None:
        parts = HOOK_VERSION.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)


class TestConstants:
    """Validate module-level constants."""

    def test_root_is_directory(self) -> None:
        assert _ROOT.is_dir()

    def test_generator_script_exists(self) -> None:
        assert _GENERATOR_SCRIPT.exists()

    def test_output_is_under_root(self) -> None:
        assert str(_OUTPUT).startswith(str(_ROOT))


# ---------------------------------------------------------------------------
# _load_generator
# ---------------------------------------------------------------------------


class TestLoadGenerator:
    """Tests for _load_generator()."""

    def setup_method(self) -> None:
        """Clear the module cache before each test."""
        generate_commands._cached_generator = None

    def test_loads_module(self) -> None:
        module = _load_generator()
        assert module is not None
        assert hasattr(module, "_generate")

    def test_caches_module(self) -> None:
        first = _load_generator()
        second = _load_generator()
        assert first is second

    def test_cache_cleared_loads_fresh(self) -> None:
        first = _load_generator()
        generate_commands._cached_generator = None
        second = _load_generator()
        # Both should have _generate, though they may or may not be the same object
        assert hasattr(first, "_generate")
        assert hasattr(second, "_generate")

    def test_raises_on_missing_script(self) -> None:
        with (
            patch.object(
                generate_commands,
                "_GENERATOR_SCRIPT",
                Path("/nonexistent/path/to/script.py"),
            ),
            pytest.raises((ImportError, FileNotFoundError)),
        ):
            _load_generator()


# ---------------------------------------------------------------------------
# on_pre_build — disabled
# ---------------------------------------------------------------------------


class TestOnPreBuildDisabled:
    """Test the hook when disabled via extra config."""

    def test_disabled_via_config(self) -> None:
        config = _make_config(extra={"generate_commands": False})
        # Should return without error (no file I/O)
        on_pre_build(config=config)

    def test_enabled_by_default(self) -> None:
        """With no extra key, the hook is enabled (default behavior)."""
        config = _make_config()
        # This will actually try to run — we mock _load_generator
        with patch.object(generate_commands, "_load_generator") as mock_load:
            mock_gen = MagicMock()
            mock_gen._generate.return_value = "# Commands\n"
            mock_load.return_value = mock_gen
            with patch.object(generate_commands, "_OUTPUT") as mock_output:
                mock_output.exists.return_value = False
                mock_output.parent.mkdir = MagicMock()
                on_pre_build(config=config)
            mock_load.assert_called_once()


# ---------------------------------------------------------------------------
# on_pre_build — generator script missing
# ---------------------------------------------------------------------------


class TestOnPreBuildMissingScript:
    """Test the hook when the generator script is missing."""

    def test_missing_script_logs_warning(self) -> None:
        config = _make_config()
        with patch.object(
            generate_commands,
            "_GENERATOR_SCRIPT",
            Path("/nonexistent/script.py"),
        ):
            # Should not raise — just warn and return
            on_pre_build(config=config)


# ---------------------------------------------------------------------------
# on_pre_build — content unchanged
# ---------------------------------------------------------------------------


class TestOnPreBuildContentUnchanged:
    """Test that the hook skips writing when content matches."""

    def setup_method(self) -> None:
        generate_commands._cached_generator = None

    def test_skips_write_when_unchanged(self) -> None:
        config = _make_config()
        content = "# Commands\nGenerated content\n"

        with patch.object(generate_commands, "_load_generator") as mock_load:
            mock_gen = MagicMock()
            mock_gen._generate.return_value = content
            mock_load.return_value = mock_gen

            with patch.object(generate_commands, "_OUTPUT") as mock_output:
                mock_output.exists.return_value = True
                mock_output.read_text.return_value = content
                mock_output.parent.mkdir = MagicMock()

                on_pre_build(config=config)

                mock_output.write_text.assert_not_called()


class TestOnPreBuildContentChanged:
    """Test that the hook writes when content differs."""

    def setup_method(self) -> None:
        generate_commands._cached_generator = None

    def test_writes_when_content_changed(self) -> None:
        config = _make_config()
        old_content = "# Old Commands\n"
        new_content = "# New Commands\n"

        with patch.object(generate_commands, "_load_generator") as mock_load:
            mock_gen = MagicMock()
            mock_gen._generate.return_value = new_content
            # Identity function so strip(old) != strip(new) triggers a write
            mock_gen._strip_volatile_lines.side_effect = lambda text: text
            mock_load.return_value = mock_gen

            with patch.object(generate_commands, "_OUTPUT") as mock_output:
                mock_output.exists.return_value = True
                mock_output.read_text.return_value = old_content
                mock_output.parent.mkdir = MagicMock()
                mock_output.relative_to.return_value = "docs/reference/commands.md"

                on_pre_build(config=config)

                mock_output.write_text.assert_called_once_with(
                    new_content, encoding="utf-8"
                )

    def test_writes_when_file_missing(self) -> None:
        config = _make_config()
        new_content = "# Commands\n"

        with patch.object(generate_commands, "_load_generator") as mock_load:
            mock_gen = MagicMock()
            mock_gen._generate.return_value = new_content
            mock_load.return_value = mock_gen

            with patch.object(generate_commands, "_OUTPUT") as mock_output:
                mock_output.exists.return_value = False
                mock_output.parent.mkdir = MagicMock()
                mock_output.relative_to.return_value = "docs/reference/commands.md"

                on_pre_build(config=config)

                mock_output.write_text.assert_called_once()


# ---------------------------------------------------------------------------
# on_pre_build — generator error
# ---------------------------------------------------------------------------


class TestOnPreBuildGeneratorError:
    """Test that exceptions in the generator are caught gracefully."""

    def setup_method(self) -> None:
        generate_commands._cached_generator = None

    def test_generator_exception_caught(self) -> None:
        config = _make_config()
        with patch.object(generate_commands, "_load_generator") as mock_load:
            mock_load.side_effect = RuntimeError("Generator broke")
            # Should not raise
            on_pre_build(config=config)

    def test_generate_function_missing(self) -> None:
        config = _make_config()
        with patch.object(generate_commands, "_load_generator") as mock_load:
            mock_gen = MagicMock(spec=[])  # empty spec = no _generate attr
            mock_load.return_value = mock_gen
            # Should not raise
            on_pre_build(config=config)
