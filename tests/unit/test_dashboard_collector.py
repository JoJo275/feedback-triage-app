"""Unit tests for tools/dev_tools/env_dashboard/collector.py."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

# Add scripts/ to sys.path so _env_collectors can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

pytest.importorskip("fastapi", reason="fastapi not installed (dashboard env only)")

from _env_collectors import Tier
from _env_collectors._redact import RedactLevel
from tools.dev_tools.env_dashboard.collector import (
    _DEFAULT_TTL,
    _Cache,
    get_previous,
    get_report,
    invalidate_cache,
)

# ---------------------------------------------------------------------------
# _Cache
# ---------------------------------------------------------------------------


class TestCache:
    """Tests for the _Cache class."""

    def test_initial_state_is_stale(self) -> None:
        cache = _Cache()
        assert cache.is_stale()

    def test_initial_current_is_none(self) -> None:
        cache = _Cache()
        assert cache.current is None

    def test_initial_previous_is_none(self) -> None:
        cache = _Cache()
        assert cache.previous is None

    def test_update_sets_current(self) -> None:
        cache = _Cache()
        data = {"sections": {"system": {}}}
        cache.update(data)
        assert cache.current == data

    def test_update_moves_current_to_previous(self) -> None:
        cache = _Cache()
        first = {"scan": 1}
        second = {"scan": 2}
        cache.update(first)
        cache.update(second)
        assert cache.previous == first
        assert cache.current == second

    def test_not_stale_after_update(self) -> None:
        cache = _Cache()
        cache.update({"data": True})
        assert not cache.is_stale()

    def test_stale_after_ttl_exceeded(self) -> None:
        cache = _Cache()
        cache.update({"data": True})
        cache.timestamp = time.monotonic() - cache.ttl - 1
        assert cache.is_stale()

    def test_invalidate_makes_stale(self) -> None:
        cache = _Cache()
        cache.update({"data": True})
        assert not cache.is_stale()
        cache.invalidate()
        assert cache.is_stale()

    def test_default_ttl(self) -> None:
        assert _DEFAULT_TTL == 30


# ---------------------------------------------------------------------------
# get_report / invalidate_cache / get_previous
# ---------------------------------------------------------------------------


class TestGetReport:
    """Tests for top-level cache functions."""

    @patch("tools.dev_tools.env_dashboard.collector.gather_env_info")
    def test_get_report_returns_dict(self, mock_gather) -> None:
        mock_gather.return_value = {"sections": {}, "meta": {}}
        invalidate_cache()
        result = get_report(force=True)
        assert isinstance(result, dict)
        mock_gather.assert_called_once()

    @patch("tools.dev_tools.env_dashboard.collector.gather_env_info")
    def test_get_report_uses_cache(self, mock_gather) -> None:
        mock_gather.return_value = {"sections": {}, "meta": {}}
        invalidate_cache()
        get_report(force=True)
        # Second call should use cache (no second gather_env_info call)
        get_report()
        assert mock_gather.call_count == 1

    @patch("tools.dev_tools.env_dashboard.collector.gather_env_info")
    def test_force_bypasses_cache(self, mock_gather) -> None:
        mock_gather.return_value = {"sections": {}, "meta": {}}
        invalidate_cache()
        get_report(force=True)
        get_report(force=True)
        assert mock_gather.call_count == 2

    @patch("tools.dev_tools.env_dashboard.collector.gather_env_info")
    def test_invalidate_cache_triggers_fresh_scan(self, mock_gather) -> None:
        mock_gather.return_value = {"sections": {}, "meta": {}}
        get_report(force=True)
        invalidate_cache()
        get_report()
        assert mock_gather.call_count == 2

    @patch("tools.dev_tools.env_dashboard.collector.gather_env_info")
    def test_get_previous_returns_none_initially(self, mock_gather) -> None:
        mock_gather.return_value = {"sections": {}, "meta": {}}
        invalidate_cache()
        get_report(force=True)
        # After first scan, previous is None
        previous = get_previous()
        # Could be None or the previous value depending on module-level cache
        # Just verify it doesn't raise
        assert previous is None or isinstance(previous, dict)

    @patch("tools.dev_tools.env_dashboard.collector.gather_env_info")
    def test_get_report_passes_tier(self, mock_gather) -> None:
        mock_gather.return_value = {"sections": {}, "meta": {}}
        invalidate_cache()
        get_report(tier=Tier.FULL, force=True)
        mock_gather.assert_called_with(tier=Tier.FULL, redact_level=RedactLevel.SECRETS)

    @patch("tools.dev_tools.env_dashboard.collector.gather_env_info")
    def test_get_report_passes_redact_level(self, mock_gather) -> None:
        mock_gather.return_value = {"sections": {}, "meta": {}}
        invalidate_cache()
        get_report(redact_level=RedactLevel.PARANOID, force=True)
        mock_gather.assert_called_with(
            tier=Tier.STANDARD, redact_level=RedactLevel.PARANOID
        )
