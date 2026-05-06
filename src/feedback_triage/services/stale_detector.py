"""Stale-feedback detector (PR 2.6).

A feedback item is **stale** when both:

* ``created_at < now() - interval '14 days'``, and
* ``status IN ('new', 'needs_info')``.

The definition lives in
[`docs/project/spec/v2/schema.md`](../../../docs/project/spec/v2/schema.md)
and [`glossary.md`](../../../docs/project/spec/v2/glossary.md). It is
exposed in two surfaces:

* a SQL clause used by ``GET /api/v1/feedback?stale=true`` (Inbox
  summary card and stale-only filter), and
* a Python predicate used by the Inbox row badge so the JS row
  renderer can decide whether to add the badge from a single
  feedback DTO.

Anything that needs the rule should import from this module so the
threshold and statuses move in lockstep across SQL and Python.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import ColumnElement, and_
from sqlmodel import col

from feedback_triage.enums import Status
from feedback_triage.models import FeedbackItem

#: Items older than this in a stale status are flagged.
STALE_THRESHOLD = timedelta(days=14)

#: The two statuses that can go stale.
STALE_STATUSES: frozenset[Status] = frozenset({Status.NEW, Status.NEEDS_INFO})


def stale_cutoff(now: datetime | None = None) -> datetime:
    """Return the ``created_at`` cut-off for staleness.

    Items strictly older than this are stale, provided their status
    is in :data:`STALE_STATUSES`.
    """
    return (now or datetime.now(UTC)) - STALE_THRESHOLD


def is_stale(
    *,
    created_at: datetime,
    status: Status | str,
    now: datetime | None = None,
) -> bool:
    """Return ``True`` when ``(created_at, status)`` flags as stale."""
    return created_at < stale_cutoff(now) and Status(status) in STALE_STATUSES


def stale_clause(now: datetime | None = None) -> ColumnElement[bool]:
    """Return a SQLAlchemy boolean clause for the staleness predicate.

    Used by ``list_feedback`` in ``api/v1/feedback.py`` when the
    ``stale=true`` query parameter is set. Bound with parameters,
    never string-interpolated.
    """
    cutoff = stale_cutoff(now)
    return and_(
        col(FeedbackItem.created_at) < cutoff,
        col(FeedbackItem.status).in_([s.value for s in STALE_STATUSES]),
    )


__all__ = [
    "STALE_STATUSES",
    "STALE_THRESHOLD",
    "is_stale",
    "stale_clause",
    "stale_cutoff",
]
