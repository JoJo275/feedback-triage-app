"""Dashboard aggregation service (PR 3.4).

Single read-side surface for the workspace dashboard at
``/w/<slug>/dashboard``. The page renders five summary counts, an
intake sparkline (last 30 days), the top five tags, and the ten
most recent activity events; all of those are computed here so the
template stays dumb.

Per ``docs/project/spec/v2/performance-budgets.md`` -- *Dashboard
cache*: results are memoised in a per-process
:class:`cachetools.TTLCache` keyed by ``(workspace_id, role)`` with
a **60-second TTL** and a 200-entry ceiling (matches the v2.0
workspace cap). Writes do *not* bust the cache; users see fresh
numbers within a minute, which is the documented trade-off.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Literal

from cachetools import TTLCache
from sqlalchemy import func
from sqlalchemy.orm import Session as DbSession
from sqlmodel import col, select

from feedback_triage.enums import Priority, Status, WorkspaceRole
from feedback_triage.models import FeedbackItem, FeedbackTag, Tag
from feedback_triage.services.stale_detector import stale_clause

#: Length of the intake sparkline window.
SPARKLINE_DAYS = 30

#: Number of tags shown in the *Top tags* card.
TOP_TAGS_LIMIT = 5

#: Number of activity rows shown in the *Recent activity* card.
RECENT_ACTIVITY_LIMIT = 10

#: TTL in seconds for the per-workspace summary cache.
CACHE_TTL_SECONDS = 60

#: Hard cap on cached entries -- one per workspace, ~200 in v2.0.
CACHE_MAX_ENTRIES = 200

CacheKey = tuple[uuid.UUID, str]
RoleLike = WorkspaceRole | Literal["admin"]


@dataclass(frozen=True, slots=True)
class SummaryCard:
    """One of the five top-row counts."""

    key: str
    label: str
    count: int


@dataclass(frozen=True, slots=True)
class SparklineBar:
    """One day in the 30-day intake sparkline."""

    day: date
    count: int


@dataclass(frozen=True, slots=True)
class TopTag:
    """One row in the *Top tags* card."""

    name: str
    color: str
    count: int


@dataclass(frozen=True, slots=True)
class RecentActivityEntry:
    """One row in the *Recent activity* card."""

    feedback_id: int
    title: str
    status: Status
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class DashboardSummary:
    """Bundle of every value the dashboard template needs."""

    cards: list[SummaryCard]
    sparkline: list[SparklineBar]
    sparkline_max: int
    top_tags: list[TopTag]
    recent_activity: list[RecentActivityEntry]
    total_items: int


# Module-level cache. Tests may call :func:`reset_cache` to start
# clean; production code never invalidates manually.
_cache: TTLCache[CacheKey, DashboardSummary] = TTLCache(
    maxsize=CACHE_MAX_ENTRIES,
    ttl=CACHE_TTL_SECONDS,
)


def reset_cache() -> None:
    """Drop every cached summary. Test-only seam."""
    _cache.clear()


def _summary_cards(db: DbSession, workspace_id: uuid.UUID) -> list[SummaryCard]:
    counts: dict[str, int] = {}

    for status in (Status.NEW, Status.NEEDS_INFO, Status.REVIEWING):
        counts[status.value] = db.execute(
            select(func.count())
            .select_from(FeedbackItem)
            .where(col(FeedbackItem.workspace_id) == workspace_id)
            .where(col(FeedbackItem.status) == status),
        ).scalar_one()

    counts["high_priority"] = db.execute(
        select(func.count())
        .select_from(FeedbackItem)
        .where(col(FeedbackItem.workspace_id) == workspace_id)
        .where(col(FeedbackItem.priority) == Priority.HIGH),
    ).scalar_one()

    counts["stale"] = db.execute(
        select(func.count())
        .select_from(FeedbackItem)
        .where(col(FeedbackItem.workspace_id) == workspace_id)
        .where(stale_clause()),
    ).scalar_one()

    return [
        SummaryCard(key="new", label="New", count=counts["new"]),
        SummaryCard(
            key="needs_info",
            label="Needs info",
            count=counts["needs_info"],
        ),
        SummaryCard(key="reviewing", label="Reviewing", count=counts["reviewing"]),
        SummaryCard(
            key="high_priority",
            label="High priority",
            count=counts["high_priority"],
        ),
        SummaryCard(key="stale", label="Stale", count=counts["stale"]),
    ]


def _sparkline(
    db: DbSession,
    workspace_id: uuid.UUID,
    *,
    now: datetime | None = None,
) -> tuple[list[SparklineBar], int]:
    today = (now or datetime.now(UTC)).date()
    start = today - timedelta(days=SPARKLINE_DAYS - 1)

    bucket = func.date_trunc("day", col(FeedbackItem.created_at)).label("day")
    rows = db.execute(
        select(bucket, func.count())
        .where(col(FeedbackItem.workspace_id) == workspace_id)
        .where(col(FeedbackItem.created_at) >= start)
        .group_by(bucket)
        .order_by(bucket),
    ).all()

    by_day: dict[date, int] = {}
    for day_value, count in rows:
        # ``date_trunc('day', ...)`` returns a tz-aware ``datetime`` on
        # Postgres; coerce to ``date`` so the dict key matches the
        # iteration below regardless of dialect quirks.
        as_date = day_value.date() if isinstance(day_value, datetime) else day_value
        by_day[as_date] = int(count)

    bars = [
        SparklineBar(
            day=start + timedelta(days=offset),
            count=by_day.get(start + timedelta(days=offset), 0),
        )
        for offset in range(SPARKLINE_DAYS)
    ]
    peak = max((bar.count for bar in bars), default=0)
    return bars, peak


def _top_tags(db: DbSession, workspace_id: uuid.UUID) -> list[TopTag]:
    rows = db.execute(
        select(
            Tag.name,
            Tag.color,
            func.count(col(FeedbackTag.feedback_id)).label("uses"),
        )
        .join(FeedbackTag, col(FeedbackTag.tag_id) == col(Tag.id))
        .where(col(Tag.workspace_id) == workspace_id)
        .group_by(col(Tag.id), col(Tag.name), col(Tag.color))
        .order_by(func.count(col(FeedbackTag.feedback_id)).desc(), col(Tag.name))
        .limit(TOP_TAGS_LIMIT),
    ).all()
    return [
        TopTag(name=name, color=color, count=int(uses)) for name, color, uses in rows
    ]


def _recent_activity(
    db: DbSession,
    workspace_id: uuid.UUID,
) -> list[RecentActivityEntry]:
    items = db.execute(
        select(
            col(FeedbackItem.id),
            col(FeedbackItem.title),
            col(FeedbackItem.status),
            col(FeedbackItem.updated_at),
        )
        .where(col(FeedbackItem.workspace_id) == workspace_id)
        .order_by(col(FeedbackItem.updated_at).desc())
        .limit(RECENT_ACTIVITY_LIMIT),
    ).all()
    return [
        RecentActivityEntry(
            feedback_id=int(item_id),
            title=title,
            status=Status(status),
            updated_at=updated_at,
        )
        for item_id, title, status, updated_at in items
    ]


def _total_items(db: DbSession, workspace_id: uuid.UUID) -> int:
    return int(
        db.execute(
            select(func.count())
            .select_from(FeedbackItem)
            .where(col(FeedbackItem.workspace_id) == workspace_id),
        ).scalar_one()
    )


def get_summary(
    db: DbSession,
    *,
    workspace_id: uuid.UUID,
    role: RoleLike,
) -> DashboardSummary:
    """Return a (possibly cached) :class:`DashboardSummary`.

    ``role`` is part of the cache key for safety -- v2.0 owners and
    team members see identical numbers, but keying by role means a
    later policy change (e.g. team members hide spam counts) cannot
    accidentally leak privileged values through the cache.
    """
    role_value = role.value if isinstance(role, WorkspaceRole) else str(role)
    key: CacheKey = (workspace_id, role_value)
    cached = _cache.get(key)
    if cached is not None:
        return cached

    cards = _summary_cards(db, workspace_id)
    sparkline, sparkline_max = _sparkline(db, workspace_id)
    top_tags = _top_tags(db, workspace_id)
    recent = _recent_activity(db, workspace_id)
    total = _total_items(db, workspace_id)

    summary = DashboardSummary(
        cards=cards,
        sparkline=sparkline,
        sparkline_max=sparkline_max,
        top_tags=top_tags,
        recent_activity=recent,
        total_items=total,
    )
    _cache[key] = summary
    return summary


__all__ = [
    "CACHE_MAX_ENTRIES",
    "CACHE_TTL_SECONDS",
    "RECENT_ACTIVITY_LIMIT",
    "SPARKLINE_DAYS",
    "TOP_TAGS_LIMIT",
    "DashboardSummary",
    "RecentActivityEntry",
    "SparklineBar",
    "SummaryCard",
    "TopTag",
    "get_summary",
    "reset_cache",
]
