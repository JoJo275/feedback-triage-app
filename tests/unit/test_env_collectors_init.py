"""Tests for _env_collectors.__init__ — Tier, gather_env_info, _build_summary."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from _env_collectors import (
    SCHEMA_VERSION,
    Tier,
    _build_summary,
    _discover_collectors,
    gather_env_info,
)
from _env_collectors._redact import RedactLevel

# ── Tier enum ────────────────────────────────────────────────


class TestTier:
    def test_minimal_value(self):
        assert Tier.MINIMAL.value == "minimal"

    def test_standard_value(self):
        assert Tier.STANDARD.value == "standard"

    def test_full_value(self):
        assert Tier.FULL.value == "full"

    def test_tier_members(self):
        assert set(Tier) == {Tier.MINIMAL, Tier.STANDARD, Tier.FULL}


# ── _discover_collectors ─────────────────────────────────────


class TestDiscoverCollectors:
    def test_returns_list(self):
        result = _discover_collectors()
        assert isinstance(result, list)
        assert len(result) == 20

    def test_all_are_basecollector_subclasses(self):
        from _env_collectors._base import BaseCollector

        for cls in _discover_collectors():
            assert issubclass(cls, BaseCollector)

    def test_insights_is_last(self):
        classes = _discover_collectors()
        assert classes[-1].__name__ == "InsightsCollector"

    def test_each_has_name_and_tier(self):
        for cls in _discover_collectors():
            assert hasattr(cls, "name")
            assert hasattr(cls, "tier")

    def test_unique_names(self):
        names = [cls.name for cls in _discover_collectors()]
        assert len(names) == len(set(names))


# ── _build_summary ───────────────────────────────────────────


class TestBuildSummary:
    def test_returns_expected_keys(self):
        sections = {
            "system": {
                "os": "Linux",
                "hostname": "dev",
                "username": "user",
                "shell": "/bin/bash",
            },
            "runtimes": {"python": {"version": "3.12.0"}},
            "git": {"repo_detected": True},
            "container": {"detected": False},
        }
        summary = _build_summary(sections, [])
        assert summary["os"] == "Linux"
        assert summary["python_version"] == "3.12.0"
        assert summary["git_repo_detected"] is True
        assert summary["container_detected"] is False
        assert summary["warnings_count"] == 0

    def test_defaults_on_empty_sections(self):
        summary = _build_summary({}, [{"severity": "warn", "message": "test"}])
        assert summary["os"] == "unknown"
        assert summary["python_version"] == "unknown"
        assert summary["warnings_count"] == 1


# ── gather_env_info ──────────────────────────────────────────


class TestGatherEnvInfo:
    @patch("_env_collectors._discover_collectors")
    def test_returns_schema_keys(self, mock_discover):
        """gather_env_info returns expected top-level keys."""
        mock_cls = MagicMock()
        mock_cls.__name__ = "FakeCollector"
        mock_cls.name = "fake"
        mock_cls.tier = Tier.MINIMAL
        instance = MagicMock()
        instance.name = "fake"
        instance.safe_collect.return_value = {"data": True, "error": None}
        mock_cls.return_value = instance

        mock_discover.return_value = [mock_cls]

        result = gather_env_info(tier=Tier.MINIMAL, redact_level=RedactLevel.NONE)

        assert "schema_version" in result
        assert "meta" in result
        assert "summary" in result
        assert "warnings" in result
        assert "sections" in result
        assert result["schema_version"] == SCHEMA_VERSION

    @patch("_env_collectors._discover_collectors")
    def test_meta_reflects_tier_and_redact(self, mock_discover):
        mock_discover.return_value = []
        result = gather_env_info(tier=Tier.FULL, redact_level=RedactLevel.PII)
        assert result["meta"]["tier"] == "full"
        assert result["meta"]["redact_level"] == "pii"

    @patch("_env_collectors._discover_collectors")
    def test_excludes_collectors_above_tier(self, mock_discover):
        """FULL-tier collectors should be excluded when tier=MINIMAL."""
        full_cls = MagicMock()
        full_cls.__name__ = "FullCollector"
        full_cls.name = "full_data"
        full_cls.tier = Tier.FULL
        full_cls.return_value.name = "full_data"
        full_cls.return_value.safe_collect.return_value = {"data": True}

        mock_discover.return_value = [full_cls]

        result = gather_env_info(tier=Tier.MINIMAL, redact_level=RedactLevel.NONE)
        assert "full_data" not in result["sections"]
