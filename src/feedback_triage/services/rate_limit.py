"""Fixed-window rate limiter backed by ``auth_rate_limits``.

Keeps a single counter per ``(bucket_key, window_start)`` pair. The
window is a fixed wall-clock minute (``UTC``); rolling-window /
sliding-window math is intentionally out of scope for v2.0 because
fixed-window is enough to dampen public-form abuse and keeps the
SQL trivially indexable.

Used by:
- :mod:`feedback_triage.api.v1.public_feedback` — public submission
  form per workspace + IP (PR 2.4).
- The auth rate limits referenced in ``docs/project/spec/v2/auth.md``
  will reuse this helper when they ship.

The bucket key is constructed by the caller and capped at 128 chars
by the table's ``CHECK`` constraint; do **not** put PII or anything
secret in the key — bucket keys are visible in logs and DB dumps.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import NamedTuple

from sqlalchemy import text
from sqlalchemy.orm import Session as DbSession


class RateLimitDecision(NamedTuple):
    """Outcome of a single :func:`check_and_increment` call."""

    allowed: bool
    current_count: int
    limit: int


def _floor_to_window(now: datetime, window_seconds: int) -> datetime:
    """Round ``now`` down to the nearest window boundary (UTC)."""
    epoch = int(now.replace(tzinfo=UTC).timestamp())
    boundary = (epoch // window_seconds) * window_seconds
    return datetime.fromtimestamp(boundary, tz=UTC)


def check_and_increment(
    db: DbSession,
    *,
    bucket_key: str,
    limit: int,
    window_seconds: int = 60,
    now: datetime | None = None,
) -> RateLimitDecision:
    """Atomically increment the counter and return whether it's allowed.

    ``allowed`` is ``True`` when the post-increment count is still
    within ``limit``. Caller decides what to do with a denial — most
    use sites raise ``HTTPException(429, …)``.

    The ``INSERT … ON CONFLICT … DO UPDATE`` is one round-trip and
    serializes per row; that's the only correctness guarantee we
    need here. The query is intentionally Postgres-specific to keep
    the increment atomic.
    """
    when = now or datetime.now(tz=UTC)
    if len(bucket_key) > 128:
        msg = "bucket_key is capped at 128 chars by the DB CHECK constraint"
        raise ValueError(msg)
    window_start = _floor_to_window(when, window_seconds)
    row = db.execute(
        text(
            """
            INSERT INTO auth_rate_limits (bucket_key, window_start, count)
            VALUES (:k, :w, 1)
            ON CONFLICT (bucket_key, window_start)
            DO UPDATE SET count = auth_rate_limits.count + 1
            RETURNING count
            """,
        ),
        {"k": bucket_key, "w": window_start},
    ).scalar_one()
    return RateLimitDecision(allowed=row <= limit, current_count=int(row), limit=limit)
