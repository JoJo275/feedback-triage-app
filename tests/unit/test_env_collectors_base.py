"""Tests for _env_collectors._base — BaseCollector, _Timeout, safe_collect."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from _env_collectors._base import BaseCollector, _Timeout

# ── Concrete subclass for testing ────────────────────────────


class _StubCollector(BaseCollector):
    name = "stub"
    timeout = 2.0

    def __init__(
        self, *, result: dict[str, Any] | None = None, error: Exception | None = None
    ):
        self._result = result or {"ok": True}
        self._error = error

    @property
    def tier(self):
        from _env_collectors import Tier

        return Tier.MINIMAL

    def collect(self) -> dict[str, Any]:
        if self._error:
            raise self._error
        return self._result


# ── BaseCollector ────────────────────────────────────────────


class TestBaseCollector:
    """Tests for the abstract base collector."""

    def test_safe_collect_returns_result(self):
        c = _StubCollector(result={"key": "val"})
        result = c.safe_collect()
        assert result["key"] == "val"
        assert result["error"] is None

    def test_safe_collect_sets_error_none_by_default(self):
        c = _StubCollector(result={"data": 1})
        result = c.safe_collect()
        assert result["error"] is None

    def test_safe_collect_does_not_overwrite_existing_error_key(self):
        c = _StubCollector(result={"error": None, "data": 1})
        result = c.safe_collect()
        assert result["error"] is None

    def test_safe_collect_catches_generic_exception(self):
        c = _StubCollector(error=RuntimeError("boom"))
        result = c.safe_collect()
        assert "failed" in result["error"]
        assert result["partial"] is True

    def test_safe_collect_catches_timeout_error(self):
        c = _StubCollector(error=TimeoutError("too slow"))
        result = c.safe_collect()
        assert "Timed out" in result["error"]
        assert result["partial"] is True

    def test_safe_collect_catches_keyboard_interrupt_as_exception(self):
        """KeyboardInterrupt is NOT caught (it's BaseException, not Exception)."""
        c = _StubCollector(error=ValueError("nope"))
        result = c.safe_collect()
        assert result["partial"] is True


# ── _Timeout context manager ────────────────────────────────


class TestTimeout:
    """Tests for the _Timeout context manager."""

    def test_timeout_enters_and_exits(self):
        """_Timeout context manager completes without error."""
        with _Timeout(5):
            pass  # Should not raise

    def test_timeout_supported_flag(self):
        import signal

        t = _Timeout(5)
        expected = hasattr(signal, "SIGALRM")
        assert t._supported == expected

    @pytest.mark.skipif(sys.platform == "win32", reason="SIGALRM not on Windows")
    def test_timeout_raises_on_alarm(self):
        """On Unix, _Timeout should raise TimeoutError when elapsed."""
        with pytest.raises(TimeoutError, match="timed out"):
            _Timeout._handler(0, None)
