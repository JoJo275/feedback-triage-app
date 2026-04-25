"""Unit tests for mkdocs-hooks/include_templates.py."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

# mkdocs-hooks/ is not an installed package — use importlib to load
# the module without mutating sys.path (avoids leaking state across tests).
_HOOK_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "mkdocs-hooks"
    / "include_templates.py"
)
_spec = importlib.util.spec_from_file_location("include_templates", _HOOK_PATH)
assert _spec is not None and _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
sys.modules["include_templates"] = _mod
_spec.loader.exec_module(_mod)

from include_templates import (
    _TEMPLATES_DIR,
    HOOK_VERSION,
    on_files,
)

# ---------------------------------------------------------------------------
# Helpers — lightweight fakes for MkDocs types
# ---------------------------------------------------------------------------


def _make_config(
    docs_dir: str | Path = "/docs",
    site_dir: str | Path = "/site",
    use_directory_urls: bool = True,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a minimal dict that behaves like ``MkDocsConfig``."""
    return {
        "docs_dir": str(docs_dir),
        "site_dir": str(site_dir),
        "use_directory_urls": use_directory_urls,
        "extra": extra or {},
    }


class _FakeFiles:
    """Lightweight fake for MkDocs Files collection.

    Provides real ``__iter__`` and ``append`` so Python's iteration
    protocol works without MagicMock special-method pitfalls.
    """

    def __init__(self, src_paths: list[str] | None = None) -> None:
        self._files: list[MagicMock] = []
        self._appended: list[object] = []
        for src in src_paths or []:
            f = MagicMock()
            f.src_path = src
            self._files.append(f)

    def __iter__(self):
        return iter(self._files)

    def append(self, item: object) -> None:
        self._appended.append(item)

    @property
    def append_call_count(self) -> int:
        return len(self._appended)

    def assert_not_appended(self) -> None:
        assert self._appended == [], f"Expected no appends, got {len(self._appended)}"

    def assert_appended_once(self) -> None:
        assert len(self._appended) == 1, f"Expected 1 append, got {len(self._appended)}"


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


class TestTemplatesDir:
    """Validate the templates directory constant."""

    def test_is_string(self) -> None:
        assert isinstance(_TEMPLATES_DIR, str)

    def test_is_templates(self) -> None:
        assert _TEMPLATES_DIR == "templates"


# ---------------------------------------------------------------------------
# on_files — disabled
# ---------------------------------------------------------------------------


class TestOnFilesDisabled:
    """Test the hook when it's disabled via extra config."""

    def test_disabled_returns_files_unchanged(self) -> None:
        files = _FakeFiles()
        config = _make_config(extra={"include_templates": False})
        result = on_files(files, config=config)
        assert result is files

    def test_enabled_by_default(self, tmp_path: Path) -> None:
        """With no extra key, the hook runs (enabled is the default)."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        files = _FakeFiles()
        config = _make_config(docs_dir=docs_dir)
        result = on_files(files, config=config)
        assert result is files


# ---------------------------------------------------------------------------
# on_files — no templates directory
# ---------------------------------------------------------------------------


class TestOnFilesNoTemplatesDir:
    """Test when templates/ directory doesn't exist."""

    def test_returns_files_unchanged(self, tmp_path: Path) -> None:
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        # No templates/ subdirectory
        files = _FakeFiles()
        config = _make_config(docs_dir=docs_dir)
        result = on_files(files, config=config)
        assert result is files
        files.assert_not_appended()


# ---------------------------------------------------------------------------
# on_files — with templates
# ---------------------------------------------------------------------------


class TestOnFilesWithTemplates:
    """Test when templates/ directory exists with files."""

    def test_adds_missing_files(self, tmp_path: Path) -> None:
        docs_dir = tmp_path / "docs"
        tpl_dir = docs_dir / "templates"
        tpl_dir.mkdir(parents=True)
        (tpl_dir / "example.md").write_text("# Template")

        files = _FakeFiles([])  # empty collection — template is missing
        config = _make_config(docs_dir=docs_dir, site_dir=tmp_path / "site")

        with patch("mkdocs.structure.files.File") as MockFile:
            MockFile.return_value = MagicMock()
            result = on_files(files, config=config)

        files.assert_appended_once()
        assert result is files

    def test_skips_already_included_files(self, tmp_path: Path) -> None:
        docs_dir = tmp_path / "docs"
        tpl_dir = docs_dir / "templates"
        tpl_dir.mkdir(parents=True)
        (tpl_dir / "example.md").write_text("# Template")

        # File already in collection
        files = _FakeFiles(["templates/example.md"])
        config = _make_config(docs_dir=docs_dir, site_dir=tmp_path / "site")

        result = on_files(files, config=config)
        files.assert_not_appended()
        assert result is files

    def test_adds_multiple_missing_files(self, tmp_path: Path) -> None:
        docs_dir = tmp_path / "docs"
        tpl_dir = docs_dir / "templates"
        tpl_dir.mkdir(parents=True)
        (tpl_dir / "a.md").write_text("A")
        (tpl_dir / "b.md").write_text("B")

        files = _FakeFiles([])
        config = _make_config(docs_dir=docs_dir, site_dir=tmp_path / "site")

        with patch("mkdocs.structure.files.File") as MockFile:
            MockFile.return_value = MagicMock()
            on_files(files, config=config)

        assert files.append_call_count == 2

    def test_skips_subdirectories(self, tmp_path: Path) -> None:
        """Directories inside templates/ should not be added (only files)."""
        docs_dir = tmp_path / "docs"
        tpl_dir = docs_dir / "templates"
        sub_dir = tpl_dir / "subdir"
        sub_dir.mkdir(parents=True)
        # Only a directory, no files
        files = _FakeFiles([])
        config = _make_config(docs_dir=docs_dir, site_dir=tmp_path / "site")
        on_files(files, config=config)
        files.assert_not_appended()

    def test_nested_files_added(self, tmp_path: Path) -> None:
        """Files in subdirectories of templates/ should be added."""
        docs_dir = tmp_path / "docs"
        sub = docs_dir / "templates" / "subdir"
        sub.mkdir(parents=True)
        (sub / "nested.md").write_text("Nested")

        files = _FakeFiles([])
        config = _make_config(docs_dir=docs_dir, site_dir=tmp_path / "site")

        with patch("mkdocs.structure.files.File") as MockFile:
            MockFile.return_value = MagicMock()
            on_files(files, config=config)

        files.assert_appended_once()
