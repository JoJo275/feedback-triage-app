"""Base collector ABC and helpers."""

from __future__ import annotations

import logging
import signal
import sys
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from _env_collectors import Tier

log = logging.getLogger(__name__)


class _Timeout:
    """Context manager for per-collector timeouts (Unix only)."""

    def __init__(self, seconds: float) -> None:
        self.seconds = int(seconds)
        self._supported = hasattr(signal, "SIGALRM")

    def __enter__(self) -> _Timeout:
        if self._supported:
            signal.signal(signal.SIGALRM, self._handler)
            signal.alarm(self.seconds)
        return self

    def __exit__(self, *args: object) -> None:
        if self._supported:
            signal.alarm(0)

    @staticmethod
    def _handler(signum: int, frame: Any) -> None:
        msg = "Collector timed out"
        raise TimeoutError(msg)


class BaseCollector(ABC):
    """Abstract base for environment collectors.

    Subclasses must set ``name``, ``tier``, and implement ``collect()``.
    """

    name: str
    tier: Tier
    timeout: float = 10.0

    @abstractmethod
    def collect(self) -> dict[str, Any]:
        """Collect data for this section.

        Returns:
            A dict of collected data. Keys and shape are section-specific.
        """

    def safe_collect(self) -> dict[str, Any]:
        """Run ``collect()`` with timeout and error isolation.

        Returns a dict that always contains at least ``{"error": None}``.
        On failure, ``{"error": "<message>", "partial": True}``.
        """
        try:
            if sys.platform != "win32" and hasattr(signal, "SIGALRM"):
                with _Timeout(self.timeout):
                    result = self.collect()
            else:
                # Windows: no SIGALRM — run without timeout wrapper
                result = self.collect()
            result.setdefault("error", None)
            return result
        except TimeoutError:
            log.warning("Collector %s timed out after %.0fs", self.name, self.timeout)
            return {"error": f"Timed out after {self.timeout}s", "partial": True}
        except Exception:
            log.exception("Collector %s failed", self.name)
            return {"error": f"Collector {self.name} failed", "partial": True}
