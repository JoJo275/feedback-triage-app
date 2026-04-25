"""Unit tests for tools/dev_tools/env_dashboard/api.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add scripts/ to sys.path so _env_collectors can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

pytest.importorskip("fastapi", reason="fastapi not installed (dashboard env only)")

from _env_collectors import Tier
from tools.dev_tools.env_dashboard.api import _parse_tier

# ---------------------------------------------------------------------------
# _parse_tier
# ---------------------------------------------------------------------------


class TestParseTier:
    """Tests for the _parse_tier helper."""

    def test_minimal(self) -> None:
        assert _parse_tier("minimal") == Tier.MINIMAL

    def test_standard(self) -> None:
        assert _parse_tier("standard") == Tier.STANDARD

    def test_full(self) -> None:
        assert _parse_tier("full") == Tier.FULL

    def test_case_insensitive(self) -> None:
        assert _parse_tier("FULL") == Tier.FULL
        assert _parse_tier("Standard") == Tier.STANDARD

    def test_whitespace_stripped(self) -> None:
        assert _parse_tier("  minimal  ") == Tier.MINIMAL

    def test_invalid_falls_back_to_standard(self) -> None:
        assert _parse_tier("bogus") == Tier.STANDARD

    def test_empty_falls_back_to_standard(self) -> None:
        assert _parse_tier("") == Tier.STANDARD
