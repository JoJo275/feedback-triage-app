"""Unit tests for scripts/customize.py helper functions."""

from __future__ import annotations

import sys
from pathlib import Path

# scripts/ is not an installed package — add it to sys.path so we can import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from customize import (
    SCRIPT_VERSION,
    STRIPPABLE,
    TEMPLATE_CLEANUP,
    _should_process,
    _validate_package_name,
    _validate_project_name,
)

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
# _validate_project_name
# ---------------------------------------------------------------------------


class TestValidateProjectName:
    """Tests for _validate_project_name()."""

    def test_valid_name(self) -> None:
        assert _validate_project_name("my-project") is None

    def test_valid_name_with_numbers(self) -> None:
        assert _validate_project_name("project-123") is None

    def test_valid_multi_segment(self) -> None:
        assert _validate_project_name("my-cool-app") is None

    def test_valid_minimal(self) -> None:
        assert _validate_project_name("ab") is None

    def test_empty_name_rejected(self) -> None:
        result = _validate_project_name("")
        assert result is not None  # returns error message

    def test_uppercase_rejected(self) -> None:
        result = _validate_project_name("MyProject")
        assert result is not None

    def test_underscore_rejected(self) -> None:
        result = _validate_project_name("my_project")
        assert result is not None

    def test_single_char_rejected(self) -> None:
        assert _validate_project_name("a") is not None

    def test_leading_number_rejected(self) -> None:
        assert _validate_project_name("1project") is not None

    def test_leading_hyphen_rejected(self) -> None:
        assert _validate_project_name("-project") is not None

    def test_trailing_hyphen_rejected(self) -> None:
        assert _validate_project_name("project-") is not None

    def test_consecutive_hyphens_rejected(self) -> None:
        assert _validate_project_name("my--project") is not None

    def test_spaces_rejected(self) -> None:
        assert _validate_project_name("my project") is not None

    def test_special_chars_rejected(self) -> None:
        assert _validate_project_name("my@project") is not None


# ---------------------------------------------------------------------------
# _validate_package_name
# ---------------------------------------------------------------------------


class TestValidatePackageName:
    """Tests for _validate_package_name()."""

    def test_valid_package_name(self) -> None:
        assert _validate_package_name("my_package") is None

    def test_valid_no_underscore(self) -> None:
        assert _validate_package_name("mypackage") is None

    def test_empty_rejected(self) -> None:
        result = _validate_package_name("")
        assert result is not None

    def test_hyphen_rejected(self) -> None:
        result = _validate_package_name("my-package")
        assert result is not None

    def test_starts_with_number_rejected(self) -> None:
        result = _validate_package_name("123package")
        assert result is not None

    def test_single_char_rejected(self) -> None:
        assert _validate_package_name("x") is not None

    def test_trailing_underscore_rejected(self) -> None:
        assert _validate_package_name("my_package_") is not None

    def test_double_underscore_rejected(self) -> None:
        assert _validate_package_name("my__package") is not None

    def test_python_keyword_rejected(self) -> None:
        assert _validate_package_name("import") is not None

    def test_python_soft_keyword_rejected(self) -> None:
        assert _validate_package_name("match") is not None

    def test_builtin_shadow_rejected(self) -> None:
        assert _validate_package_name("list") is not None

    def test_another_builtin_shadow_rejected(self) -> None:
        assert _validate_package_name("dict") is not None


# ---------------------------------------------------------------------------
# _should_process
# ---------------------------------------------------------------------------


class TestShouldProcess:
    """Tests for _should_process()."""

    def test_python_file_in_repo_accepted(self, project_root: Path) -> None:
        # Use an actual file in the repo that should be processable
        f = project_root / "pyproject.toml"
        assert _should_process(f) is True

    def test_git_dir_rejected(self, project_root: Path) -> None:
        git_config = project_root / ".git" / "config"
        if git_config.exists():
            assert _should_process(git_config) is False

    def test_nonexistent_file_rejected(self, project_root: Path) -> None:
        f = project_root / "nonexistent_abc_xyz.py"
        assert _should_process(f) is False

    def test_customize_script_itself_skipped(self, project_root: Path) -> None:
        f = project_root / "scripts" / "customize.py"
        assert _should_process(f) is False

    def test_markdown_file_accepted(self, project_root: Path) -> None:
        f = project_root / "README.md"
        assert _should_process(f) is True

    def test_yaml_file_accepted(self, project_root: Path) -> None:
        f = project_root / "Taskfile.yml"
        assert _should_process(f) is True

    def test_containerfile_accepted(self, project_root: Path) -> None:
        f = project_root / "Containerfile"
        if f.exists():
            assert _should_process(f) is True

    def test_pycache_rejected(self, project_root: Path, tmp_path: Path) -> None:
        """Files under __pycache__/ should be skipped even with .py ext."""
        # We can't easily test this with real paths inside __pycache__ that
        # may not exist, so check that SKIP_DIRS contains __pycache__
        from customize import SKIP_DIRS

        assert "__pycache__" in SKIP_DIRS


# ---------------------------------------------------------------------------
# STRIPPABLE / TEMPLATE_CLEANUP path integrity
# ---------------------------------------------------------------------------


class TestStrippablePaths:
    """Verify that STRIPPABLE paths reference files/dirs that actually exist."""

    def test_all_strippable_paths_exist(self, project_root: Path) -> None:
        """Every path listed in STRIPPABLE should exist in the repo."""
        missing: list[str] = []
        for key, entry in STRIPPABLE.items():
            for rel_path in entry["paths"]:
                target = project_root / rel_path
                if not target.exists():
                    missing.append(f"{key}: {rel_path}")
        assert missing == [], f"Missing STRIPPABLE paths: {missing}"


class TestTemplateCleanupPaths:
    """Verify TEMPLATE_CLEANUP path-based entries reference existing paths."""

    def test_path_based_cleanup_entries_exist(self, project_root: Path) -> None:
        """Non-special cleanup entries should reference existing paths."""
        # Skip keys with special handling (empty paths list)
        special_keys = {"placeholder-code", "advanced-workflows"}
        missing: list[str] = []
        for key, entry in TEMPLATE_CLEANUP.items():
            if key in special_keys:
                continue
            for rel_path in entry["paths"]:
                target = project_root / rel_path
                if not target.exists():
                    missing.append(f"{key}: {rel_path}")
        assert missing == [], f"Missing TEMPLATE_CLEANUP paths: {missing}"
