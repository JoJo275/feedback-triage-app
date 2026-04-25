"""Unit tests for scripts/_imports.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# scripts/ is not an installed package — add it to sys.path so we can import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from _imports import SCRIPT_VERSION, find_repo_root, import_sibling

# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


class TestMetadata:
    """Verify module-level metadata."""

    def test_version_is_string(self) -> None:
        assert isinstance(SCRIPT_VERSION, str)

    def test_version_format(self) -> None:
        parts = SCRIPT_VERSION.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)


# ---------------------------------------------------------------------------
# find_repo_root
# ---------------------------------------------------------------------------


class TestFindRepoRoot:
    """Tests for find_repo_root()."""

    def test_finds_root_from_default(self) -> None:
        root = find_repo_root()
        assert root.is_dir()
        assert (root / "pyproject.toml").is_file()

    def test_finds_root_from_nested_dir(self, tmp_path: Path) -> None:
        # Create a nested structure with pyproject.toml at the top
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")
        nested = tmp_path / "a" / "b" / "c"
        nested.mkdir(parents=True)
        root = find_repo_root(start=nested)
        assert root == tmp_path

    def test_raises_if_no_pyproject(self, tmp_path: Path) -> None:
        isolated = tmp_path / "empty"
        isolated.mkdir()
        with pytest.raises(FileNotFoundError, match="Cannot find repo root"):
            find_repo_root(start=isolated)


# ---------------------------------------------------------------------------
# import_sibling
# ---------------------------------------------------------------------------


class TestImportSibling:
    """Tests for import_sibling()."""

    def test_imports_colors_module(self) -> None:
        mod = import_sibling("_colors")
        assert hasattr(mod, "Colors")

    def test_imports_progress_module(self) -> None:
        mod = import_sibling("_progress")
        assert hasattr(mod, "ProgressBar")

    def test_cached_module_returned(self) -> None:
        mod1 = import_sibling("_colors")
        mod2 = import_sibling("_colors")
        assert mod1 is mod2

    def test_nonexistent_module_raises(self) -> None:
        with pytest.raises(ImportError, match="Cannot find module"):
            import_sibling("_nonexistent_module_xyz")
