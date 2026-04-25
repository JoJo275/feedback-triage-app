"""Unit tests for scripts/check_python_support.py."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from check_python_support import (
    SCRIPT_VERSION,
    _extract_classifier_versions,
    _extract_hatch_matrix,
    _fmt_version,
    _fmt_versions,
    _parse_requires_python,
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
# _parse_requires_python
# ---------------------------------------------------------------------------


class TestParseRequiresPython:
    """Tests for requires-python spec parser."""

    def test_standard_spec(self) -> None:
        assert _parse_requires_python(">=3.11") == (3, 11)

    def test_with_whitespace(self) -> None:
        assert _parse_requires_python(">= 3.12") == (3, 12)

    def test_returns_none_for_invalid(self) -> None:
        assert _parse_requires_python("==3.11") is None

    def test_returns_none_for_empty(self) -> None:
        assert _parse_requires_python("") is None


# ---------------------------------------------------------------------------
# _extract_classifier_versions
# ---------------------------------------------------------------------------


class TestExtractClassifiers:
    """Tests for PyPI classifier version extraction."""

    def test_extracts_versions(self) -> None:
        classifiers = [
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.11",
            "Programming Language :: Python :: 3.12",
        ]
        result = _extract_classifier_versions(classifiers)
        assert result == [(3, 11), (3, 12)]

    def test_empty_classifiers(self) -> None:
        assert _extract_classifier_versions([]) == []

    def test_ignores_non_version_classifiers(self) -> None:
        classifiers = [
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3",
        ]
        assert _extract_classifier_versions(classifiers) == []


# ---------------------------------------------------------------------------
# _extract_hatch_matrix
# ---------------------------------------------------------------------------


class TestExtractHatchMatrix:
    """Tests for Hatch test matrix extraction."""

    def test_extracts_versions(self) -> None:
        data = {
            "tool": {
                "hatch": {
                    "envs": {"test": {"matrix": [{"python": ["3.11", "3.12", "3.13"]}]}}
                }
            }
        }
        result = _extract_hatch_matrix(data)
        assert result == [(3, 11), (3, 12), (3, 13)]

    def test_empty_when_no_matrix(self) -> None:
        assert _extract_hatch_matrix({}) == []

    def test_empty_when_no_python_key(self) -> None:
        data = {"tool": {"hatch": {"envs": {"test": {"matrix": [{}]}}}}}
        assert _extract_hatch_matrix(data) == []


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


class TestFormatHelpers:
    """Tests for version formatting functions."""

    def test_fmt_version(self) -> None:
        assert _fmt_version((3, 11)) == "3.11"

    def test_fmt_versions(self) -> None:
        result = _fmt_versions([(3, 11), (3, 12)])
        assert result == "3.11, 3.12"

    def test_fmt_versions_empty(self) -> None:
        assert _fmt_versions([]) == ""
