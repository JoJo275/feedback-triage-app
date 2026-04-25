"""Tests for simple_python_boilerplate.engine module."""

from __future__ import annotations

from unittest.mock import patch

from simple_python_boilerplate.engine import (
    diagnose_environment,
    get_version_info,
)


class TestGetVersionInfo:
    """Tests for get_version_info()."""

    def test_returns_expected_keys(self) -> None:
        info = get_version_info()
        assert "package_version" in info
        assert "python_version" in info
        assert "python_full" in info
        assert "platform" in info

    def test_fallback_when_package_not_installed(self) -> None:
        with patch(
            "simple_python_boilerplate.engine.version",
            side_effect=__import__(
                "importlib.metadata", fromlist=["PackageNotFoundError"]
            ).PackageNotFoundError,
        ):
            info = get_version_info()
            assert isinstance(info["package_version"], str)


class TestDiagnoseEnvironment:
    """Tests for diagnose_environment()."""

    def test_returns_expected_keys(self) -> None:
        diag = diagnose_environment()
        assert "version" in diag
        assert "executable" in diag
        assert "prefix" in diag
        assert "in_virtual_env" in diag
        assert "tools" in diag
        assert "config_files" in diag

    def test_tools_contains_expected_entries(self) -> None:
        diag = diagnose_environment()
        for tool in ("pytest", "ruff", "mypy", "pre-commit"):
            assert tool in diag["tools"]

    def test_in_virtual_env_is_bool(self) -> None:
        diag = diagnose_environment()
        assert isinstance(diag["in_virtual_env"], bool)
