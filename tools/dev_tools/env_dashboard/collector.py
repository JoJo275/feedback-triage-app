"""Caching adapter for environment data collection.

Wraps ``_env_collectors.gather_env_info()`` with an in-memory cache
and TTL. Stores one previous scan for diff comparison.

Performance notes:
    - ``gather_env_info()`` is CPU/IO-bound (subprocess calls, filesystem
      scans). It runs in a thread-pool executor to avoid blocking the
      async event loop.
    - A background warmup task populates the cache at startup so the
      first page load is instant.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import time
from typing import Any

from _env_collectors import Tier, gather_env_info
from _env_collectors._redact import RedactLevel

_DEFAULT_TTL = 30  # seconds

# Thread pool for running blocking collector calls off the event loop
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)


class _CacheEntry:
    """Single cache entry for a (tier, redact_level) combination."""

    __slots__ = ("current", "previous", "timestamp")

    def __init__(self) -> None:
        self.current: dict[str, Any] | None = None
        self.previous: dict[str, Any] | None = None
        self.timestamp: float = 0.0

    def is_stale(self, ttl: float) -> bool:
        return self.current is None or (time.monotonic() - self.timestamp) > ttl

    def update(self, data: dict[str, Any]) -> None:
        self.previous = self.current
        self.current = data
        self.timestamp = time.monotonic()


class _Cache:
    """In-memory cache keyed by (tier, redact_level) with TTL."""

    def __init__(self) -> None:
        self._entries: dict[tuple[object, RedactLevel], _CacheEntry] = {}
        self.ttl: float = _DEFAULT_TTL

    def _key(
        self, tier: object, redact_level: RedactLevel
    ) -> tuple[object, RedactLevel]:
        return (tier, redact_level)

    def get_entry(self, tier: object, redact_level: RedactLevel) -> _CacheEntry:
        key = self._key(tier, redact_level)
        if key not in self._entries:
            self._entries[key] = _CacheEntry()
        return self._entries[key]

    def is_stale(self, tier: object, redact_level: RedactLevel) -> bool:
        return self.get_entry(tier, redact_level).is_stale(self.ttl)

    def update(
        self, tier: object, redact_level: RedactLevel, data: dict[str, Any]
    ) -> None:
        self.get_entry(tier, redact_level).update(data)

    def invalidate(self) -> None:
        for entry in self._entries.values():
            entry.timestamp = 0.0


_cache = _Cache()


def _collect_sync(
    tier: Tier,
    redact_level: RedactLevel,
) -> dict[str, Any]:
    """Blocking collection — runs in thread pool."""
    return gather_env_info(tier=tier, redact_level=redact_level)


def get_report(
    *,
    tier: Tier = Tier.STANDARD,
    redact_level: RedactLevel = RedactLevel.SECRETS,
    force: bool = False,
) -> dict[str, Any]:
    """Get environment report, using cache if not stale.

    Args:
        tier: Collection tier.
        redact_level: Redaction level.
        force: Force fresh scan (ignore cache).

    Returns:
        Full environment report dict.
    """
    if force or _cache.is_stale(tier, redact_level):
        data = gather_env_info(tier=tier, redact_level=redact_level)
        _cache.update(tier, redact_level, data)
    return _cache.get_entry(tier, redact_level).current  # type: ignore[return-value]


async def get_report_async(
    *,
    tier: Tier = Tier.STANDARD,
    redact_level: RedactLevel = RedactLevel.SECRETS,
    force: bool = False,
) -> dict[str, Any]:
    """Async version — runs collection in thread pool to avoid blocking.

    Args:
        tier: Collection tier.
        redact_level: Redaction level.
        force: Force fresh scan (ignore cache).

    Returns:
        Full environment report dict.
    """
    if force or _cache.is_stale(tier, redact_level):
        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(_executor, _collect_sync, tier, redact_level)
        _cache.update(tier, redact_level, data)
    return _cache.get_entry(tier, redact_level).current  # type: ignore[return-value]


def get_previous(
    tier: Tier = Tier.STANDARD,
    redact_level: RedactLevel = RedactLevel.SECRETS,
) -> dict[str, Any] | None:
    """Return the previous scan result (for diff)."""
    return _cache.get_entry(tier, redact_level).previous


def invalidate_cache() -> None:
    """Force the next ``get_report()`` call to re-scan."""
    _cache.invalidate()


async def warmup_cache(
    tier: Tier = Tier.STANDARD,
    redact_level: RedactLevel = RedactLevel.SECRETS,
) -> None:
    """Pre-populate cache in background so first page load is instant."""
    await get_report_async(tier=tier, redact_level=redact_level)
