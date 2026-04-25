"""Unit tests for scripts/env_inspect.py."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from env_inspect import (
    SCRIPT_VERSION,
    _all_installed_packages,
    _deduplicate_packages,
    _git_info,
    _python_info,
)

# ---------------------------------------------------------------------------
# SCRIPT_VERSION
# ---------------------------------------------------------------------------


class TestScriptVersion:
    """Validate version constant."""

    def test_version_is_string(self) -> None:
        assert isinstance(SCRIPT_VERSION, str)

    def test_version_format(self) -> None:
        parts = SCRIPT_VERSION.split(".")
        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)


# ---------------------------------------------------------------------------
# _python_info
# ---------------------------------------------------------------------------


class TestPythonInfo:
    """Tests for _python_info()."""

    def test_returns_dict(self) -> None:
        info = _python_info()
        assert isinstance(info, dict)

    def test_has_version(self) -> None:
        info = _python_info()
        assert "version" in info
        assert isinstance(info["version"], str)

    def test_has_executable(self) -> None:
        info = _python_info()
        assert "executable" in info
        assert Path(info["executable"]).exists()

    def test_has_in_venv(self) -> None:
        info = _python_info()
        assert "in_venv" in info
        assert isinstance(info["in_venv"], bool)

    def test_has_architecture(self) -> None:
        info = _python_info()
        assert "architecture" in info


# ---------------------------------------------------------------------------
# _git_info
# ---------------------------------------------------------------------------


class TestGitInfo:
    """Tests for _git_info()."""

    def test_returns_dict(self) -> None:
        info = _git_info()
        assert isinstance(info, dict)

    def test_has_available_key(self) -> None:
        info = _git_info()
        assert "available" in info
        assert isinstance(info["available"], bool)

    def test_has_version_when_available(self) -> None:
        info = _git_info()
        if info["available"]:
            assert "version" in info


# ---------------------------------------------------------------------------
# _deduplicate_packages
# ---------------------------------------------------------------------------


class TestDeduplicatePackages:
    """Tests for _deduplicate_packages()."""

    def test_removes_duplicates(self) -> None:
        packages = [
            {"name": "foo", "version": "1.0", "summary": "", "location": "/a"},
            {"name": "foo", "version": "2.0", "summary": "", "location": "/b"},
        ]
        result = _deduplicate_packages(packages)
        assert len(result) == 1
        assert result[0]["version"] == "1.0"  # keeps first

    def test_preserves_unique(self) -> None:
        packages = [
            {"name": "foo", "version": "1.0", "summary": "", "location": "/a"},
            {"name": "bar", "version": "2.0", "summary": "", "location": "/b"},
        ]
        result = _deduplicate_packages(packages)
        assert len(result) == 2

    def test_empty_list(self) -> None:
        assert _deduplicate_packages([]) == []

    def test_case_insensitive(self) -> None:
        packages = [
            {"name": "Foo", "version": "1.0", "summary": "", "location": "/a"},
            {"name": "foo", "version": "2.0", "summary": "", "location": "/b"},
        ]
        result = _deduplicate_packages(packages)
        assert len(result) == 1


# ---------------------------------------------------------------------------
# _all_installed_packages
# ---------------------------------------------------------------------------


class TestAllInstalledPackages:
    """Tests for _all_installed_packages()."""

    def test_returns_list(self) -> None:
        result = _all_installed_packages()
        assert isinstance(result, list)

    def test_packages_have_required_keys(self) -> None:
        result = _all_installed_packages()
        if result:
            pkg = result[0]
            assert "name" in pkg
            assert "version" in pkg

    def test_sorted_by_name(self) -> None:
        result = _all_installed_packages()
        if len(result) >= 2:
            names = [(p["name"] or "").lower() for p in result]
            assert names == sorted(names)
