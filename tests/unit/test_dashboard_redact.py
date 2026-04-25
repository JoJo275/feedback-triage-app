"""Unit tests for tools/dev_tools/env_dashboard/redact.py."""

from __future__ import annotations

import sys
from pathlib import Path

# Add scripts/ to sys.path so _env_collectors can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from _env_collectors._redact import RedactLevel
from tools.dev_tools.env_dashboard.redact import (
    DEFAULT_EXPORT_LEVEL,
    DEFAULT_VIEW_LEVEL,
    parse_redact_param,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestDefaults:
    """Validate default redaction level constants."""

    def test_default_view_level_is_secrets(self) -> None:
        assert DEFAULT_VIEW_LEVEL == RedactLevel.SECRETS

    def test_default_export_level_is_pii(self) -> None:
        assert DEFAULT_EXPORT_LEVEL == RedactLevel.PII


# ---------------------------------------------------------------------------
# parse_redact_param
# ---------------------------------------------------------------------------


class TestParseRedactParam:
    """Tests for parse_redact_param()."""

    def test_none_returns_view_default(self) -> None:
        assert parse_redact_param(None) == RedactLevel.SECRETS

    def test_none_export_returns_export_default(self) -> None:
        assert parse_redact_param(None, export=True) == RedactLevel.PII

    def test_empty_string_returns_default(self) -> None:
        assert parse_redact_param("") == RedactLevel.SECRETS

    def test_valid_none_level(self) -> None:
        assert parse_redact_param("none") == RedactLevel.NONE

    def test_valid_secrets_level(self) -> None:
        assert parse_redact_param("secrets") == RedactLevel.SECRETS

    def test_valid_pii_level(self) -> None:
        assert parse_redact_param("pii") == RedactLevel.PII

    def test_valid_paranoid_level(self) -> None:
        assert parse_redact_param("paranoid") == RedactLevel.PARANOID

    def test_case_insensitive(self) -> None:
        assert parse_redact_param("SECRETS") == RedactLevel.SECRETS
        assert parse_redact_param("Pii") == RedactLevel.PII

    def test_whitespace_stripped(self) -> None:
        assert parse_redact_param("  secrets  ") == RedactLevel.SECRETS

    def test_invalid_falls_back_to_default(self) -> None:
        assert parse_redact_param("bogus") == RedactLevel.SECRETS

    def test_invalid_falls_back_to_export_default(self) -> None:
        assert parse_redact_param("bogus", export=True) == RedactLevel.PII
