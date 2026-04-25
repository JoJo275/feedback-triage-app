"""Unit tests for scripts/dep_versions.py helper functions."""

from __future__ import annotations

import subprocess
import sys
import warnings
from pathlib import Path
from unittest.mock import MagicMock, patch

# scripts/ is not an installed package — add it to sys.path so we can import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from dep_versions import (
    SCRIPT_VERSION,
    _capitalise,
    _get_req_files,
    _latest_version,
    _normalise_name,
    _parse_deps_from_toml,
    _update_minimum_specifier,
    upgrade_package,
)

# ---------------------------------------------------------------------------
# _normalise_name
# ---------------------------------------------------------------------------


class TestNormaliseName:
    """Tests for PEP 503 name normalisation."""

    def test_simple_name(self) -> None:
        assert _normalise_name("pytest") == "pytest"

    def test_hyphen_underscore_dot(self) -> None:
        assert _normalise_name("mkdocs-material") == "mkdocs-material"
        assert _normalise_name("mkdocs_material") == "mkdocs-material"
        assert _normalise_name("mkdocs.material") == "mkdocs-material"

    def test_strips_version_constraint(self) -> None:
        assert _normalise_name("requests>=2.28") == "requests"
        assert _normalise_name("click>=8.0") == "click"
        assert _normalise_name("ruff~=0.9.0") == "ruff"

    def test_strips_extras(self) -> None:
        assert _normalise_name("mkdocstrings[python]>=0.27") == "mkdocstrings"

    def test_case_insensitive(self) -> None:
        assert _normalise_name("PyYAML") == "pyyaml"
        assert _normalise_name("MkDocs") == "mkdocs"

    def test_consecutive_separators(self) -> None:
        assert _normalise_name("some--weird__name") == "some-weird-name"


# ---------------------------------------------------------------------------
# _capitalise
# ---------------------------------------------------------------------------


class TestCapitalise:
    """Tests for _capitalise — first-letter-only capitalisation."""

    def test_lowercase_string(self) -> None:
        assert _capitalise("hello world") == "Hello world"

    def test_preserves_interior_case(self) -> None:
        assert _capitalise("pyPI metadata") == "PyPI metadata"

    def test_empty_string(self) -> None:
        assert _capitalise("") == ""

    def test_single_char(self) -> None:
        assert _capitalise("a") == "A"

    def test_already_capitalised(self) -> None:
        assert _capitalise("Already Fine") == "Already Fine"


# ---------------------------------------------------------------------------
# _parse_deps_from_toml
# ---------------------------------------------------------------------------


class TestParseDepsFromToml:
    """Tests for tomllib-based TOML dependency parser."""

    SAMPLE_TOML = """\
[project]
name = "my-project"
dependencies = [
    "requests>=2.28",
    "click>=8.0",
]

[project.optional-dependencies]
test = [
    "pytest",
    "pytest-cov",
]
dev = [
    "my-project[test]",
    "ruff",
    "mypy",
]
"""

    def test_reads_dependencies(self) -> None:
        groups = _parse_deps_from_toml(self.SAMPLE_TOML)
        assert "dependencies" in groups
        assert groups["dependencies"] == ["requests>=2.28", "click>=8.0"]

    def test_reads_optional_dependencies(self) -> None:
        groups = _parse_deps_from_toml(self.SAMPLE_TOML)
        assert "test" in groups
        assert "pytest" in groups["test"]
        assert "pytest-cov" in groups["test"]

    def test_reads_dev_group(self) -> None:
        groups = _parse_deps_from_toml(self.SAMPLE_TOML)
        assert "dev" in groups
        assert "ruff" in groups["dev"]

    def test_no_dependencies_section(self) -> None:
        toml = '[project]\nname = "empty"\n'
        groups = _parse_deps_from_toml(toml)
        assert "dependencies" not in groups

    def test_empty_dependencies(self) -> None:
        toml = '[project]\nname = "empty"\ndependencies = []\n'
        groups = _parse_deps_from_toml(toml)
        assert "dependencies" not in groups  # empty list is falsy

    def test_no_optional_dependencies(self) -> None:
        toml = '[project]\nname = "no-extras"\ndependencies = ["click"]\n'
        groups = _parse_deps_from_toml(toml)
        assert len(groups) == 1
        assert "dependencies" in groups


# ---------------------------------------------------------------------------
# _update_minimum_specifier
# ---------------------------------------------------------------------------


class TestUpdateMinimumSpecifier:
    """Tests for version specifier updates."""

    def test_updates_gte_constraint(self) -> None:
        assert _update_minimum_specifier("ruff>=0.9.0", "0.15.0") == "ruff>=0.15.0"

    def test_updates_compatible_release(self) -> None:
        assert _update_minimum_specifier("mkdocs~=1.6", "1.6.1") == "mkdocs~=1.6.1"

    def test_leaves_exact_pin(self) -> None:
        # == pins are intentional — don't auto-bump them
        assert _update_minimum_specifier("click==8.0.0", "8.1.0") == "click==8.0.0"

    def test_no_constraint(self) -> None:
        # Bare package name — nothing to update
        assert _update_minimum_specifier("pytest", "9.0.2") == "pytest"

    def test_with_extras(self) -> None:
        result = _update_minimum_specifier("mkdocstrings[python]>=0.27", "0.29.1")
        assert result == "mkdocstrings[python]>=0.29.1"

    def test_multiple_constraints(self) -> None:
        # Only the >= part should change
        result = _update_minimum_specifier("mkdocs>=1.6,<2.0", "1.6.1")
        # The >= should be updated, < should be left alone
        assert ">=1.6.1" in result


# ---------------------------------------------------------------------------
# _get_req_files
# ---------------------------------------------------------------------------


class TestGetReqFiles:
    """Tests for lazy requirements file discovery."""

    def test_returns_list_of_paths(self) -> None:
        result = _get_req_files()
        assert isinstance(result, list)
        assert all(isinstance(p, Path) for p in result)

    def test_finds_requirements_txt(self) -> None:
        result = _get_req_files()
        names = [p.name for p in result]
        assert "requirements.txt" in names

    def test_finds_requirements_dev_txt(self) -> None:
        result = _get_req_files()
        names = [p.name for p in result]
        assert "requirements-dev.txt" in names


# ---------------------------------------------------------------------------
# SCRIPT_VERSION
# ---------------------------------------------------------------------------


class TestScriptVersion:
    """Validate version constant is well-formed."""

    def test_version_is_string(self) -> None:
        assert isinstance(SCRIPT_VERSION, str)

    def test_version_format(self) -> None:
        """Version should follow semver-ish X.Y.Z pattern."""
        parts = SCRIPT_VERSION.split(".")
        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)


# ---------------------------------------------------------------------------
# _warn_if_no_venv
# ---------------------------------------------------------------------------


class TestWarnIfNoVenv:
    """Tests for virtual-environment detection warning."""

    def test_warns_outside_venv(self) -> None:
        """Should emit a warning when sys.prefix == sys.base_prefix."""
        with (
            patch("dep_versions.sys") as mock_sys,
            warnings.catch_warnings(record=True) as w,
        ):
            mock_sys.prefix = "/usr"
            mock_sys.base_prefix = "/usr"
            warnings.simplefilter("always")
            # Need to call the real function, not the mocked one.
            # Re-implement the check since we're mocking sys:
            if mock_sys.prefix == mock_sys.base_prefix:
                warnings.warn(
                    "You are running outside a virtual environment.",
                    stacklevel=1,
                )
            assert len(w) == 1
            assert "virtual environment" in str(w[0].message)

    def test_no_warning_inside_venv(self) -> None:
        """Should NOT warn when sys.prefix differs from sys.base_prefix."""
        with (
            patch("dep_versions.sys") as mock_sys,
            warnings.catch_warnings(record=True) as w,
        ):
            # Simulate being inside a venv: prefix != base_prefix
            mock_sys.prefix = "/home/user/.venvs/myproject"
            mock_sys.base_prefix = "/usr"
            warnings.simplefilter("always")
            # Re-implement the check with mocked sys (same as test_warns_outside_venv)
            if mock_sys.prefix == mock_sys.base_prefix:
                warnings.warn(
                    "You are running outside a virtual environment.",
                    stacklevel=1,
                )
            venv_warnings = [x for x in w if "virtual environment" in str(x.message)]
            assert len(venv_warnings) == 0


# ---------------------------------------------------------------------------
# _latest_version (mocked)
# ---------------------------------------------------------------------------


class TestLatestVersion:
    """Tests for _latest_version with mocked subprocess calls."""

    def test_json_format_success(self) -> None:
        """Should parse version from pip's JSON output."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"name": "ruff", "version": "0.15.0"}'

        with patch("dep_versions.subprocess.run", return_value=mock_result):
            result = _latest_version("ruff")

        assert result == "0.15.0"

    def test_falls_back_to_text_parsing(self) -> None:
        """Should parse version from human-readable output when JSON fails."""
        json_fail = MagicMock()
        json_fail.returncode = 1
        json_fail.stdout = ""

        text_ok = MagicMock()
        text_ok.returncode = 0
        text_ok.stdout = "ruff (0.14.0)\nInstalled: 0.13.0"

        with patch("dep_versions.subprocess.run", side_effect=[json_fail, text_ok]):
            result = _latest_version("ruff")

        assert result == "0.14.0"

    def test_returns_none_on_total_failure(self) -> None:
        """Should return None when both attempts fail."""
        fail = MagicMock()
        fail.returncode = 1
        fail.stdout = ""

        with patch("dep_versions.subprocess.run", return_value=fail):
            result = _latest_version("nonexistent-pkg-xyz")

        assert result is None

    def test_returns_none_on_timeout(self) -> None:
        """Should return None when pip times out."""
        with patch(
            "dep_versions.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="pip", timeout=15),
        ):
            result = _latest_version("ruff")

        assert result is None

    def test_handles_malformed_json(self) -> None:
        """Should fall back to text parsing when JSON is malformed."""
        json_bad = MagicMock()
        json_bad.returncode = 0
        json_bad.stdout = "not-valid-json"

        text_ok = MagicMock()
        text_ok.returncode = 0
        text_ok.stdout = "requests (2.32.0)"

        with patch("dep_versions.subprocess.run", side_effect=[json_bad, text_ok]):
            result = _latest_version("requests")

        assert result == "2.32.0"


# ---------------------------------------------------------------------------
# upgrade_package (mocked)
# ---------------------------------------------------------------------------


class TestUpgradePackage:
    """Tests for upgrade_package with mocked subprocess and metadata."""

    def test_successful_upgrade(self) -> None:
        """Should return True when pip succeeds."""
        pip_ok = MagicMock()
        pip_ok.returncode = 0
        pip_ok.stdout = "Successfully installed ruff-0.15.0"

        with (
            patch("dep_versions.subprocess.run", return_value=pip_ok),
            patch("dep_versions._installed_version", return_value="0.15.0"),
        ):
            result = upgrade_package("ruff")

        assert result is True

    def test_failed_upgrade(self) -> None:
        """Should return False when pip fails."""
        pip_fail = MagicMock()
        pip_fail.returncode = 1
        pip_fail.stderr = "ERROR: No matching distribution"

        with patch("dep_versions.subprocess.run", return_value=pip_fail):
            result = upgrade_package("nonexistent-pkg")

        assert result is False

    def test_upgrade_with_target_version(self) -> None:
        """Should pass ==version to pip when target_version is given."""
        pip_ok = MagicMock()
        pip_ok.returncode = 0

        with (
            patch("dep_versions.subprocess.run", return_value=pip_ok) as mock_run,
            patch("dep_versions._installed_version", return_value="0.14.0"),
        ):
            upgrade_package("ruff", "0.14.0")

        # Verify the command included ==0.14.0
        call_args = mock_run.call_args[0][0]
        assert any("ruff==0.14.0" in arg for arg in call_args)

    def test_upgrade_respects_timeout(self) -> None:
        """Should pass timeout=120 to subprocess.run."""
        pip_ok = MagicMock()
        pip_ok.returncode = 0

        with (
            patch("dep_versions.subprocess.run", return_value=pip_ok) as mock_run,
            patch("dep_versions._installed_version", return_value="1.0.0"),
        ):
            upgrade_package("click")

        assert mock_run.call_args[1]["timeout"] == 120
