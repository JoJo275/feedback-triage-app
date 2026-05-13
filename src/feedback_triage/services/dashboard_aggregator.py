"""Dashboard aggregation service.

Single read-side surface for the workspace dashboard at
``/w/<slug>/dashboard``.

The summary contract in this module tracks
``docs/project/spec/v2/layouts/dashboard.md`` and provides all values
needed by the dense/medium/light dashboard presets:

* KPI strip (total, needs action, high pain, triage latency,
  backlog delta),
* operational health (received/triaged/resolved throughput,
  status mix, aging/SLA),
* themes and impact (tags, pain distribution, segment/source impact),
* execution (team workload, backlog categories),
* workbench (urgency-sorted action queue + quick views).

Per ``docs/project/spec/v2/performance-budgets.md`` -- *Dashboard
cache*: results are memoised in a per-process
:class:`cachetools.TTLCache` keyed by ``(workspace_id, role)`` with
a **60-second TTL** and a 200-entry ceiling (matches the v2.0
workspace cap). Writes do *not* bust the cache; users see fresh
numbers within a minute, which is the documented trade-off.
"""

from __future__ import annotations

import threading
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from statistics import median
from typing import Literal

from cachetools import TTLCache
from sqlalchemy import and_, case, func
from sqlalchemy import select as sa_select
from sqlalchemy.orm import Session as DbSession
from sqlmodel import col, select

from feedback_triage.enums import Priority, Status, WorkspaceRole
from feedback_triage.models import FeedbackItem, FeedbackTag, Submitter, Tag, User

#: Throughput window and intake trend span.
THROUGHPUT_DAYS = 30

#: Backward-compatible alias kept for historical imports/tests.
SPARKLINE_DAYS = THROUGHPUT_DAYS

#: Number of tags shown in the *Top tags* card.
TOP_TAGS_LIMIT = 5

#: Number of source rows shown in the *Source breakdown* card.
SOURCE_BREAKDOWN_LIMIT = 6

#: Number of rows in the *Action queue* table.
ACTION_QUEUE_LIMIT = 8

#: Backward-compatible alias kept for historical imports/tests.
RECENT_ACTIVITY_LIMIT = ACTION_QUEUE_LIMIT

#: Age threshold used for SLA and stale-risk checks.
SLA_DAYS = 14

#: Pain level threshold used for "high pain" widgets.
HIGH_PAIN_LEVEL = 4

#: TTL in seconds for the per-workspace summary cache.
CACHE_TTL_SECONDS = 60

#: Hard cap on cached entries -- one per workspace, ~200 in v2.0.
CACHE_MAX_ENTRIES = 200

CANONICAL_STATUS_ORDER: tuple[Status, ...] = (
    Status.NEW,
    Status.NEEDS_INFO,
    Status.REVIEWING,
    Status.ACCEPTED,
    Status.PLANNED,
    Status.IN_PROGRESS,
    Status.SHIPPED,
    Status.CLOSED,
    Status.SPAM,
)

NEEDS_ACTION_STATUSES: tuple[Status, ...] = (
    Status.NEW,
    Status.NEEDS_INFO,
    Status.REVIEWING,
)

OPEN_STATUSES: tuple[Status, ...] = (
    Status.NEW,
    Status.NEEDS_INFO,
    Status.REVIEWING,
    Status.ACCEPTED,
    Status.PLANNED,
    Status.IN_PROGRESS,
)

RESOLVED_STATUSES: tuple[Status, ...] = (
    Status.SHIPPED,
    Status.CLOSED,
    Status.SPAM,
)

TRIAGED_STATUSES: tuple[Status, ...] = tuple(
    status for status in CANONICAL_STATUS_ORDER if status != Status.NEW
)

NEEDS_ACTION_VALUES: tuple[str, ...] = tuple(
    status.value for status in NEEDS_ACTION_STATUSES
)
OPEN_STATUS_VALUES: tuple[str, ...] = tuple(status.value for status in OPEN_STATUSES)
RESOLVED_STATUS_VALUES: tuple[str, ...] = tuple(
    status.value for status in RESOLVED_STATUSES
)
TRIAGED_STATUS_VALUES: tuple[str, ...] = tuple(
    status.value for status in TRIAGED_STATUSES
)

CacheKey = tuple[uuid.UUID, str]
RoleLike = WorkspaceRole | Literal["admin"]


@dataclass(frozen=True, slots=True)
class KpiMetrics:
    """Top-row KPI values."""

    total_signals: int
    needs_action: int
    high_pain_signals: int
    median_time_to_triage_hours: float | None
    net_backlog_change: int


@dataclass(frozen=True, slots=True)
class ThroughputPoint:
    """Daily received/triaged/resolved counts."""

    day: date
    received: int
    triaged: int
    resolved: int


@dataclass(frozen=True, slots=True)
class ThroughputSummary:
    """Time-series and totals for the operational throughput chart."""

    points: list[ThroughputPoint]
    peak: int
    received_total: int
    triaged_total: int
    resolved_total: int


@dataclass(frozen=True, slots=True)
class StatusMixSlice:
    """One status slice in the canonical v2 workflow mix."""

    status: Status
    count: int
    percent: int


@dataclass(frozen=True, slots=True)
class AgingBucket:
    """One age bucket in the SLA/aging health panel."""

    label: str
    count: int


@dataclass(frozen=True, slots=True)
class AgingHealth:
    """Operational age/SLA metrics for open items."""

    average_age_hours: float | None
    median_age_hours: float | None
    buckets: list[AgingBucket]
    oldest_untriaged_hours: float | None
    high_pain_over_sla: int


@dataclass(frozen=True, slots=True)
class TopTag:
    """One row in the *Top tags* widget."""

    name: str
    color: str
    count: int
    percentage: int
    period_delta: int
    unresolved_count: int


@dataclass(frozen=True, slots=True)
class PainDistribution:
    """Low/medium/high pain breakdown plus high-pain risk counts."""

    low: int
    medium: int
    high: int
    high_pain_unresolved: int
    high_pain_unassigned: int


@dataclass(frozen=True, slots=True)
class SegmentImpactRow:
    """One segment impact row (source is the current segment proxy)."""

    segment: str
    total: int
    high_pain: int


@dataclass(frozen=True, slots=True)
class SegmentImpact:
    """Segment-impact summary surface."""

    rows: list[SegmentImpactRow]
    top_affected_segment: str | None
    repeat_submitter_pain_count: int
    repeat_submitter_pain_percent: int


@dataclass(frozen=True, slots=True)
class SourceBreakdownEntry:
    """One row in the source breakdown card."""

    source: str
    label: str
    count: int
    percent: int


@dataclass(frozen=True, slots=True)
class TeamWorkloadRow:
    """One row in the team workload table."""

    owner: str
    open_count: int
    high_pain_count: int
    overdue_count: int


@dataclass(frozen=True, slots=True)
class TeamWorkload:
    """Execution workload metrics split by owner."""

    rows: list[TeamWorkloadRow]
    unassigned_open: int
    unassigned_high_pain: int
    unassigned_overdue: int


@dataclass(frozen=True, slots=True)
class SignalQuality:
    """Quality/risk indicators used by attention widgets."""

    duplicate_candidates: int
    missing_submitter: int
    waiting_on_submitter: int


@dataclass(frozen=True, slots=True)
class AttentionCategory:
    """One row in backlog/quick-view lists."""

    key: str
    label: str
    count: int


@dataclass(frozen=True, slots=True)
class ActionQueueEntry:
    """One urgency-ranked row in the action queue table."""

    feedback_id: int
    type_label: str
    title: str
    submitter: str
    source_label: str
    pain_level: int
    priority_label: str
    status: Status
    owner: str
    age_label: str
    tags: tuple[str, ...]
    is_high_pain: bool
    is_unassigned: bool
    is_over_sla: bool
    urgency_rank: int


@dataclass(frozen=True, slots=True)
class ActionQueue:
    """Workbench queue + urgency sorting metadata."""

    entries: list[ActionQueueEntry]
    quick_views: list[AttentionCategory]
    default_rows: int
    urgency_rules: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DashboardSummary:
    """Bundle of every value the dashboard template needs."""

    kpi: KpiMetrics
    throughput: ThroughputSummary
    status_mix: list[StatusMixSlice]
    aging_health: AgingHealth
    top_tags: list[TopTag]
    pain_distribution: PainDistribution
    segment_impact: SegmentImpact
    source_breakdown: list[SourceBreakdownEntry]
    team_workload: TeamWorkload
    signal_quality: SignalQuality
    backlog_categories: list[AttentionCategory]
    action_queue: ActionQueue
    total_items: int


# Module-level cache. Tests may call :func:`reset_cache` to start
# clean; production code never invalidates manually.
#
# ``cachetools.TTLCache`` is **not** thread-safe, but FastAPI's sync
# routes execute on a thread pool, so concurrent dashboard requests
# can race on the underlying ``OrderedDict``. ``_cache_lock`` guards
# every read/write/clear so corruption can't happen under load.
_cache: TTLCache[CacheKey, DashboardSummary] = TTLCache(
    maxsize=CACHE_MAX_ENTRIES,
    ttl=CACHE_TTL_SECONDS,
)
_cache_lock = threading.Lock()


def reset_cache() -> None:
    """Drop every cached summary. Test-only seam."""
    with _cache_lock:
        _cache.clear()


def _period_start(now: datetime) -> datetime:
    start_day = now.date() - timedelta(days=THROUGHPUT_DAYS - 1)
    return datetime.combine(start_day, time.min, tzinfo=UTC)


def _to_int(value: object | None) -> int:
    if value is None:
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float | str):
        return int(value)
    raise TypeError(f"value {value!r} cannot be converted to int")


def _to_date(day_value: date | datetime) -> date:
    return day_value.date() if isinstance(day_value, datetime) else day_value


def _percent(*, count: int, total: int) -> int:
    if total <= 0:
        return 0
    return round((count / total) * 100)


def _hours_between(*, now: datetime, then: datetime) -> float:
    then_utc = then.replace(tzinfo=UTC) if then.tzinfo is None else then.astimezone(UTC)
    diff = now - then_utc
    return max(diff.total_seconds() / 3600.0, 0.0)


def _format_age_label(hours: float) -> str:
    if hours < 24:
        return f"{int(hours)}h"
    days = int(hours // 24)
    return f"{days}d"


def _enum_value(value: object) -> str:
    return value.value if isinstance(value, Status | Priority) else str(value)


def _title_case(value: object) -> str:
    return _enum_value(value).replace("_", " ").title()


def _source_label(source_value: str) -> str:
    labels = {
        "app_store": "App Store",
        "web_form": "Public form",
    }
    if source_value in labels:
        return labels[source_value]
    return source_value.replace("_", " ").title()


def _total_items(db: DbSession, workspace_id: uuid.UUID) -> int:
    return int(
        db.execute(
            select(func.count())
            .select_from(FeedbackItem)
            .where(col(FeedbackItem.workspace_id) == workspace_id),
        ).scalar_one()
    )


def _kpi(
    db: DbSession, workspace_id: uuid.UUID, *, period_start: datetime
) -> KpiMetrics:
    row = db.execute(
        sa_select(
            func.count().label("total"),
            func.sum(
                case(
                    (col(FeedbackItem.status).in_(NEEDS_ACTION_VALUES), 1),
                    else_=0,
                )
            ).label("needs_action"),
            func.sum(
                case((col(FeedbackItem.pain_level) >= HIGH_PAIN_LEVEL, 1), else_=0)
            ).label("high_pain"),
            func.sum(
                case((col(FeedbackItem.created_at) >= period_start, 1), else_=0)
            ).label("received_period"),
            func.sum(
                case(
                    (
                        and_(
                            col(FeedbackItem.updated_at) >= period_start,
                            col(FeedbackItem.status).in_(RESOLVED_STATUS_VALUES),
                        ),
                        1,
                    ),
                    else_=0,
                )
            ).label("resolved_period"),
        ).where(col(FeedbackItem.workspace_id) == workspace_id)
    ).one()
    total, needs_action, high_pain, received_period, resolved_period = row

    triage_seconds = db.execute(
        select(
            func.percentile_cont(0.5).within_group(
                func.extract(
                    "epoch",
                    col(FeedbackItem.updated_at) - col(FeedbackItem.created_at),
                ),
            )
        )
        .where(col(FeedbackItem.workspace_id) == workspace_id)
        .where(col(FeedbackItem.status).in_(TRIAGED_STATUS_VALUES))
        .where(col(FeedbackItem.updated_at) > col(FeedbackItem.created_at))
    ).scalar_one()

    median_hours = None
    if triage_seconds is not None:
        median_hours = round(float(triage_seconds) / 3600.0, 2)

    received_total = _to_int(received_period)
    resolved_total = _to_int(resolved_period)
    return KpiMetrics(
        total_signals=_to_int(total),
        needs_action=_to_int(needs_action),
        high_pain_signals=_to_int(high_pain),
        median_time_to_triage_hours=median_hours,
        net_backlog_change=received_total - resolved_total,
    )


def _throughput(
    db: DbSession,
    workspace_id: uuid.UUID,
    *,
    now: datetime,
) -> ThroughputSummary:
    start = _period_start(now)
    first_day = start.date()

    created_bucket = func.date_trunc("day", col(FeedbackItem.created_at)).label("day")
    updated_bucket = func.date_trunc("day", col(FeedbackItem.updated_at)).label("day")

    received_rows = db.execute(
        sa_select(created_bucket, func.count(col(FeedbackItem.id)))
        .where(col(FeedbackItem.workspace_id) == workspace_id)
        .where(col(FeedbackItem.created_at) >= start)
        .group_by(created_bucket)
        .order_by(created_bucket)
    ).all()
    triaged_rows = db.execute(
        sa_select(updated_bucket, func.count(col(FeedbackItem.id)))
        .where(col(FeedbackItem.workspace_id) == workspace_id)
        .where(col(FeedbackItem.updated_at) >= start)
        .where(col(FeedbackItem.status).in_(TRIAGED_STATUS_VALUES))
        .group_by(updated_bucket)
        .order_by(updated_bucket)
    ).all()
    resolved_rows = db.execute(
        sa_select(updated_bucket, func.count(col(FeedbackItem.id)))
        .where(col(FeedbackItem.workspace_id) == workspace_id)
        .where(col(FeedbackItem.updated_at) >= start)
        .where(col(FeedbackItem.status).in_(RESOLVED_STATUS_VALUES))
        .group_by(updated_bucket)
        .order_by(updated_bucket)
    ).all()

    received_by_day = {_to_date(day): int(count) for day, count in received_rows}
    triaged_by_day = {_to_date(day): int(count) for day, count in triaged_rows}
    resolved_by_day = {_to_date(day): int(count) for day, count in resolved_rows}

    points: list[ThroughputPoint] = []
    for offset in range(THROUGHPUT_DAYS):
        day = first_day + timedelta(days=offset)
        points.append(
            ThroughputPoint(
                day=day,
                received=received_by_day.get(day, 0),
                triaged=triaged_by_day.get(day, 0),
                resolved=resolved_by_day.get(day, 0),
            )
        )

    peak = max(
        (max(point.received, point.triaged, point.resolved) for point in points),
        default=0,
    )
    return ThroughputSummary(
        points=points,
        peak=peak,
        received_total=sum(point.received for point in points),
        triaged_total=sum(point.triaged for point in points),
        resolved_total=sum(point.resolved for point in points),
    )


def _status_mix(
    db: DbSession, workspace_id: uuid.UUID, *, total_items: int
) -> list[StatusMixSlice]:
    rows = db.execute(
        select(col(FeedbackItem.status), func.count())
        .where(col(FeedbackItem.workspace_id) == workspace_id)
        .group_by(col(FeedbackItem.status))
    ).all()
    counts: dict[Status, int] = {}
    for status_raw, count in rows:
        counts[Status(status_raw)] = int(count)

    return [
        StatusMixSlice(
            status=status,
            count=counts.get(status, 0),
            percent=_percent(count=counts.get(status, 0), total=total_items),
        )
        for status in CANONICAL_STATUS_ORDER
    ]


def _aging_health(
    db: DbSession,
    workspace_id: uuid.UUID,
    *,
    now: datetime,
    sla_cutoff: datetime,
) -> AgingHealth:
    rows = db.execute(
        select(
            col(FeedbackItem.status),
            col(FeedbackItem.pain_level),
            col(FeedbackItem.created_at),
        )
        .where(col(FeedbackItem.workspace_id) == workspace_id)
        .where(col(FeedbackItem.status).in_(OPEN_STATUS_VALUES))
    ).all()

    bucket_counts = {
        "0-24h": 0,
        "1-3d": 0,
        "4-7d": 0,
        "8-14d": 0,
        "14d+": 0,
    }
    ages: list[float] = []
    untriaged_ages: list[float] = []
    high_pain_over_sla = 0

    for status_raw, pain_level, created_at in rows:
        status = Status(status_raw)
        age_hours = _hours_between(now=now, then=created_at)
        ages.append(age_hours)
        if status == Status.NEW:
            untriaged_ages.append(age_hours)

        if age_hours < 24:
            bucket_counts["0-24h"] += 1
        elif age_hours < 72:
            bucket_counts["1-3d"] += 1
        elif age_hours < 168:
            bucket_counts["4-7d"] += 1
        elif age_hours < 336:
            bucket_counts["8-14d"] += 1
        else:
            bucket_counts["14d+"] += 1

        if pain_level >= HIGH_PAIN_LEVEL and created_at < sla_cutoff:
            high_pain_over_sla += 1

    average_hours = round(sum(ages) / len(ages), 2) if ages else None
    median_hours = round(float(median(ages)), 2) if ages else None
    oldest_untriaged = max(untriaged_ages) if untriaged_ages else None

    return AgingHealth(
        average_age_hours=average_hours,
        median_age_hours=median_hours,
        buckets=[
            AgingBucket(label=label, count=count)
            for label, count in bucket_counts.items()
        ],
        oldest_untriaged_hours=oldest_untriaged,
        high_pain_over_sla=high_pain_over_sla,
    )


def _top_tags(
    db: DbSession,
    workspace_id: uuid.UUID,
    *,
    period_start: datetime,
    total_items: int,
) -> list[TopTag]:
    previous_start = period_start - timedelta(days=THROUGHPUT_DAYS)
    uses = func.count(col(FeedbackTag.feedback_id)).label("uses")
    current_period = func.sum(
        case((col(FeedbackItem.created_at) >= period_start, 1), else_=0)
    ).label("current_period")
    previous_period = func.sum(
        case(
            (
                and_(
                    col(FeedbackItem.created_at) >= previous_start,
                    col(FeedbackItem.created_at) < period_start,
                ),
                1,
            ),
            else_=0,
        )
    ).label("previous_period")
    unresolved = func.sum(
        case((col(FeedbackItem.status).in_(OPEN_STATUS_VALUES), 1), else_=0)
    ).label("unresolved")

    rows = db.execute(
        sa_select(
            col(Tag.name),
            col(Tag.color),
            uses,
            current_period,
            previous_period,
            unresolved,
        )
        .join(FeedbackTag, col(FeedbackTag.tag_id) == col(Tag.id))
        .join(FeedbackItem, col(FeedbackItem.id) == col(FeedbackTag.feedback_id))
        .where(col(Tag.workspace_id) == workspace_id)
        .where(col(FeedbackItem.workspace_id) == workspace_id)
        .group_by(col(Tag.id), col(Tag.name), col(Tag.color))
        .order_by(uses.desc(), col(Tag.name))
        .limit(TOP_TAGS_LIMIT)
    ).all()

    out: list[TopTag] = []
    for name, color, count, current, previous, unresolved_count in rows:
        count_int = _to_int(count)
        out.append(
            TopTag(
                name=name,
                color=color,
                count=count_int,
                percentage=_percent(count=count_int, total=total_items),
                period_delta=_to_int(current) - _to_int(previous),
                unresolved_count=_to_int(unresolved_count),
            )
        )
    return out


def _pain_distribution(db: DbSession, workspace_id: uuid.UUID) -> PainDistribution:
    rows = db.execute(
        select(
            col(FeedbackItem.pain_level),
            col(FeedbackItem.status),
            col(FeedbackItem.assignee_user_id),
        ).where(col(FeedbackItem.workspace_id) == workspace_id)
    ).all()

    low = 0
    medium = 0
    high = 0
    high_pain_unresolved = 0
    high_pain_unassigned = 0

    for pain_level, status_raw, assignee_user_id in rows:
        status = Status(status_raw)
        pain = int(pain_level)
        if pain <= 2:
            low += 1
        elif pain == 3:
            medium += 1
        else:
            high += 1

        if pain >= HIGH_PAIN_LEVEL and status in OPEN_STATUSES:
            high_pain_unresolved += 1
            if assignee_user_id is None:
                high_pain_unassigned += 1

    return PainDistribution(
        low=low,
        medium=medium,
        high=high,
        high_pain_unresolved=high_pain_unresolved,
        high_pain_unassigned=high_pain_unassigned,
    )


def _segment_impact(
    db: DbSession,
    workspace_id: uuid.UUID,
    *,
    high_pain_total: int,
) -> SegmentImpact:
    high_pain_case = case((col(FeedbackItem.pain_level) >= HIGH_PAIN_LEVEL, 1), else_=0)
    rows = db.execute(
        select(
            col(FeedbackItem.source),
            func.count(),
            func.sum(high_pain_case),
        )
        .where(col(FeedbackItem.workspace_id) == workspace_id)
        .group_by(col(FeedbackItem.source))
        .order_by(
            func.sum(high_pain_case).desc(),
            func.count().desc(),
            col(FeedbackItem.source),
        )
    ).all()

    segment_rows = [
        SegmentImpactRow(
            segment=_source_label(str(source_value)),
            total=_to_int(total),
            high_pain=_to_int(high_pain),
        )
        for source_value, total, high_pain in rows
    ]
    top_segment = segment_rows[0].segment if segment_rows else None

    repeat_submitter_high_pain = _to_int(
        db.execute(
            select(func.count())
            .select_from(FeedbackItem)
            .join(
                Submitter,
                col(Submitter.id) == col(FeedbackItem.submitter_id),
                isouter=True,
            )
            .where(col(FeedbackItem.workspace_id) == workspace_id)
            .where(col(FeedbackItem.pain_level) >= HIGH_PAIN_LEVEL)
            .where(col(Submitter.submission_count) > 1)
        ).scalar_one()
    )

    return SegmentImpact(
        rows=segment_rows,
        top_affected_segment=top_segment,
        repeat_submitter_pain_count=repeat_submitter_high_pain,
        repeat_submitter_pain_percent=_percent(
            count=repeat_submitter_high_pain,
            total=high_pain_total,
        ),
    )


def _source_breakdown(
    db: DbSession,
    workspace_id: uuid.UUID,
    *,
    total_items: int,
) -> list[SourceBreakdownEntry]:
    if total_items == 0:
        return []

    rows = db.execute(
        select(col(FeedbackItem.source), func.count())
        .where(col(FeedbackItem.workspace_id) == workspace_id)
        .group_by(col(FeedbackItem.source))
        .order_by(func.count().desc(), col(FeedbackItem.source))
        .limit(SOURCE_BREAKDOWN_LIMIT)
    ).all()

    out: list[SourceBreakdownEntry] = []
    for source_value, count in rows:
        source_key = str(source_value)
        count_int = _to_int(count)
        out.append(
            SourceBreakdownEntry(
                source=source_key,
                label=_source_label(source_key),
                count=count_int,
                percent=_percent(count=count_int, total=total_items),
            )
        )
    return out


def _team_workload(
    db: DbSession,
    workspace_id: uuid.UUID,
    *,
    sla_cutoff: datetime,
) -> TeamWorkload:
    high_pain_case = case((col(FeedbackItem.pain_level) >= HIGH_PAIN_LEVEL, 1), else_=0)
    overdue_case = case((col(FeedbackItem.created_at) < sla_cutoff, 1), else_=0)

    assigned_rows = db.execute(
        sa_select(
            col(User.email),
            func.count(col(FeedbackItem.id)),
            func.sum(high_pain_case),
            func.sum(overdue_case),
        )
        .select_from(FeedbackItem)
        .join(User, col(User.id) == col(FeedbackItem.assignee_user_id))
        .where(col(FeedbackItem.workspace_id) == workspace_id)
        .where(col(FeedbackItem.status).in_(OPEN_STATUS_VALUES))
        .group_by(col(User.email))
        .order_by(func.count(col(FeedbackItem.id)).desc(), col(User.email))
    ).all()

    rows: list[TeamWorkloadRow] = []
    for owner_email, open_count, high_pain_count, overdue_count in assigned_rows:
        rows.append(
            TeamWorkloadRow(
                owner=str(owner_email),
                open_count=_to_int(open_count),
                high_pain_count=_to_int(high_pain_count),
                overdue_count=_to_int(overdue_count),
            )
        )

    unassigned_open, unassigned_high_pain, unassigned_overdue = db.execute(
        sa_select(
            func.count(col(FeedbackItem.id)),
            func.sum(high_pain_case),
            func.sum(overdue_case),
        )
        .select_from(FeedbackItem)
        .where(col(FeedbackItem.workspace_id) == workspace_id)
        .where(col(FeedbackItem.status).in_(OPEN_STATUS_VALUES))
        .where(col(FeedbackItem.assignee_user_id).is_(None))
    ).one()
    unassigned_row = TeamWorkloadRow(
        owner="Unassigned",
        open_count=_to_int(unassigned_open),
        high_pain_count=_to_int(unassigned_high_pain),
        overdue_count=_to_int(unassigned_overdue),
    )
    rows.append(unassigned_row)

    return TeamWorkload(
        rows=rows,
        unassigned_open=unassigned_row.open_count,
        unassigned_high_pain=unassigned_row.high_pain_count,
        unassigned_overdue=unassigned_row.overdue_count,
    )


def _signal_quality(db: DbSession, workspace_id: uuid.UUID) -> SignalQuality:
    missing_submitter = _to_int(
        db.execute(
            select(func.count())
            .select_from(FeedbackItem)
            .where(col(FeedbackItem.workspace_id) == workspace_id)
            .where(col(FeedbackItem.submitter_id).is_(None))
        ).scalar_one()
    )
    waiting_on_submitter = _to_int(
        db.execute(
            select(func.count())
            .select_from(FeedbackItem)
            .where(col(FeedbackItem.workspace_id) == workspace_id)
            .where(col(FeedbackItem.status) == Status.NEEDS_INFO)
        ).scalar_one()
    )

    duplicate_groups = db.execute(
        select(func.count().label("group_size"))
        .where(col(FeedbackItem.workspace_id) == workspace_id)
        .where(col(FeedbackItem.status).in_(OPEN_STATUS_VALUES))
        .group_by(func.lower(func.trim(col(FeedbackItem.title))))
        .having(func.count() > 1)
    ).all()
    duplicate_candidates = sum(
        _to_int(group_size) for (group_size,) in duplicate_groups
    )

    return SignalQuality(
        duplicate_candidates=duplicate_candidates,
        missing_submitter=missing_submitter,
        waiting_on_submitter=waiting_on_submitter,
    )


def _backlog_categories(
    db: DbSession,
    workspace_id: uuid.UUID,
    *,
    sla_cutoff: datetime,
    team_workload: TeamWorkload,
    signal_quality: SignalQuality,
) -> list[AttentionCategory]:
    new_untriaged = _to_int(
        db.execute(
            select(func.count())
            .select_from(FeedbackItem)
            .where(col(FeedbackItem.workspace_id) == workspace_id)
            .where(col(FeedbackItem.status) == Status.NEW)
        ).scalar_one()
    )
    over_sla = _to_int(
        db.execute(
            select(func.count())
            .select_from(FeedbackItem)
            .where(col(FeedbackItem.workspace_id) == workspace_id)
            .where(col(FeedbackItem.status).in_(OPEN_STATUS_VALUES))
            .where(col(FeedbackItem.created_at) < sla_cutoff)
        ).scalar_one()
    )
    returning_customer_pain = _to_int(
        db.execute(
            select(func.count())
            .select_from(FeedbackItem)
            .join(
                Submitter,
                col(Submitter.id) == col(FeedbackItem.submitter_id),
                isouter=True,
            )
            .where(col(FeedbackItem.workspace_id) == workspace_id)
            .where(col(FeedbackItem.status).in_(OPEN_STATUS_VALUES))
            .where(col(FeedbackItem.pain_level) >= HIGH_PAIN_LEVEL)
            .where(col(Submitter.submission_count) > 1)
        ).scalar_one()
    )
    escalated = _to_int(
        db.execute(
            select(func.count())
            .select_from(FeedbackItem)
            .where(col(FeedbackItem.workspace_id) == workspace_id)
            .where(col(FeedbackItem.status).in_(OPEN_STATUS_VALUES))
            .where(col(FeedbackItem.priority) == Priority.CRITICAL)
        ).scalar_one()
    )

    return [
        AttentionCategory(
            key="unassigned_high_pain",
            label="Unassigned high pain",
            count=team_workload.unassigned_high_pain,
        ),
        AttentionCategory(
            key="new_untriaged",
            label="New and untriaged",
            count=new_untriaged,
        ),
        AttentionCategory(
            key="over_sla",
            label="Over SLA",
            count=over_sla,
        ),
        AttentionCategory(
            key="returning_customer_pain",
            label="Returning customer pain",
            count=returning_customer_pain,
        ),
        AttentionCategory(
            key="escalated",
            label="Escalated",
            count=escalated,
        ),
        AttentionCategory(
            key="potential_duplicates",
            label="Potential duplicates",
            count=signal_quality.duplicate_candidates,
        ),
        AttentionCategory(
            key="waiting_on_submitter",
            label="Waiting on submitter",
            count=signal_quality.waiting_on_submitter,
        ),
    ]


def _quick_views(
    db: DbSession,
    workspace_id: uuid.UUID,
    *,
    now: datetime,
    sla_cutoff: datetime,
    kpi: KpiMetrics,
    team_workload: TeamWorkload,
    signal_quality: SignalQuality,
) -> list[AttentionCategory]:
    recent_window_start = now - timedelta(days=7)
    recent = _to_int(
        db.execute(
            select(func.count())
            .select_from(FeedbackItem)
            .where(col(FeedbackItem.workspace_id) == workspace_id)
            .where(col(FeedbackItem.created_at) >= recent_window_start)
            .where(col(FeedbackItem.status).in_(OPEN_STATUS_VALUES))
        ).scalar_one()
    )
    high_pain = _to_int(
        db.execute(
            select(func.count())
            .select_from(FeedbackItem)
            .where(col(FeedbackItem.workspace_id) == workspace_id)
            .where(col(FeedbackItem.status).in_(OPEN_STATUS_VALUES))
            .where(col(FeedbackItem.pain_level) >= HIGH_PAIN_LEVEL)
        ).scalar_one()
    )
    stale = _to_int(
        db.execute(
            select(func.count())
            .select_from(FeedbackItem)
            .where(col(FeedbackItem.workspace_id) == workspace_id)
            .where(col(FeedbackItem.status).in_(OPEN_STATUS_VALUES))
            .where(col(FeedbackItem.created_at) < sla_cutoff)
        ).scalar_one()
    )

    return [
        AttentionCategory(
            key="needs_action",
            label="Needs action",
            count=kpi.needs_action,
        ),
        AttentionCategory(
            key="recent",
            label="Recent",
            count=recent,
        ),
        AttentionCategory(
            key="high_pain",
            label="High pain",
            count=high_pain,
        ),
        AttentionCategory(
            key="unassigned",
            label="Unassigned",
            count=team_workload.unassigned_open,
        ),
        AttentionCategory(
            key="stale",
            label="Stale",
            count=stale,
        ),
        AttentionCategory(
            key="duplicates",
            label="Duplicates",
            count=signal_quality.duplicate_candidates,
        ),
    ]


def _action_queue(
    db: DbSession,
    workspace_id: uuid.UUID,
    *,
    now: datetime,
    sla_cutoff: datetime,
    quick_views: list[AttentionCategory],
) -> ActionQueue:
    needs_info_reviewing = [Status.NEEDS_INFO.value, Status.REVIEWING.value]
    rows = db.execute(
        sa_select(
            col(FeedbackItem.id),
            col(FeedbackItem.type),
            col(FeedbackItem.title),
            col(FeedbackItem.source),
            col(FeedbackItem.pain_level),
            col(FeedbackItem.priority),
            col(FeedbackItem.status),
            col(FeedbackItem.assignee_user_id),
            col(FeedbackItem.created_at),
            col(Submitter.name),
            col(Submitter.email),
            col(User.email),
        )
        .select_from(FeedbackItem)
        .join(
            Submitter,
            col(Submitter.id) == col(FeedbackItem.submitter_id),
            isouter=True,
        )
        .join(
            User,
            col(User.id) == col(FeedbackItem.assignee_user_id),
            isouter=True,
        )
        .where(col(FeedbackItem.workspace_id) == workspace_id)
        .where(col(FeedbackItem.status).in_(OPEN_STATUS_VALUES))
        .order_by(
            case((col(FeedbackItem.pain_level) >= HIGH_PAIN_LEVEL, 0), else_=1),
            case((col(FeedbackItem.assignee_user_id).is_(None), 0), else_=1),
            case((col(FeedbackItem.created_at) < sla_cutoff, 0), else_=1),
            case((col(FeedbackItem.status).in_(needs_info_reviewing), 0), else_=1),
            col(FeedbackItem.updated_at).desc(),
        )
        .limit(ACTION_QUEUE_LIMIT)
    ).all()

    feedback_ids = [int(item_id) for item_id, *_ in rows]
    tags_by_feedback: dict[int, list[str]] = defaultdict(list)
    if feedback_ids:
        tag_rows = db.execute(
            select(col(FeedbackTag.feedback_id), col(Tag.name))
            .join(Tag, col(Tag.id) == col(FeedbackTag.tag_id))
            .where(col(FeedbackTag.feedback_id).in_(feedback_ids))
            .order_by(col(Tag.name))
        ).all()
        for feedback_id, tag_name in tag_rows:
            tags_by_feedback[int(feedback_id)].append(tag_name)

    entries: list[ActionQueueEntry] = []
    for index, row in enumerate(rows, start=1):
        (
            item_id,
            type_raw,
            title,
            source_raw,
            pain_level,
            priority_raw,
            status_raw,
            assignee_user_id,
            created_at,
            submitter_name,
            submitter_email,
            assignee_email,
        ) = row
        status = Status(status_raw)
        source_value = str(source_raw)
        pain = int(pain_level)
        age_hours = _hours_between(now=now, then=created_at)
        submitter = submitter_name or submitter_email or "Anonymous"
        is_unassigned = assignee_user_id is None
        entries.append(
            ActionQueueEntry(
                feedback_id=int(item_id),
                type_label=_title_case(type_raw),
                title=title,
                submitter=submitter,
                source_label=_source_label(source_value),
                pain_level=pain,
                priority_label=_title_case(priority_raw)
                if priority_raw is not None
                else "—",
                status=status,
                owner=str(assignee_email)
                if assignee_email is not None
                else "Unassigned",
                age_label=_format_age_label(age_hours),
                tags=tuple(tags_by_feedback.get(int(item_id), [])),
                is_high_pain=pain >= HIGH_PAIN_LEVEL,
                is_unassigned=is_unassigned,
                is_over_sla=created_at < sla_cutoff,
                urgency_rank=index,
            )
        )

    return ActionQueue(
        entries=entries,
        quick_views=quick_views,
        default_rows=ACTION_QUEUE_LIMIT,
        urgency_rules=(
            "high_pain",
            "unassigned",
            "over_sla",
            "needs_info_reviewing",
            "recency",
        ),
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
    with _cache_lock:
        cached = _cache.get(key)
    if cached is not None:
        return cached

    now = datetime.now(UTC)
    period_start = _period_start(now)
    sla_cutoff = now - timedelta(days=SLA_DAYS)
    total = _total_items(db, workspace_id)

    kpi = _kpi(db, workspace_id, period_start=period_start)
    throughput = _throughput(db, workspace_id, now=now)
    status_mix = _status_mix(db, workspace_id, total_items=total)
    aging_health = _aging_health(
        db,
        workspace_id,
        now=now,
        sla_cutoff=sla_cutoff,
    )
    top_tags = _top_tags(
        db,
        workspace_id,
        period_start=period_start,
        total_items=total,
    )
    pain_distribution = _pain_distribution(db, workspace_id)
    segment_impact = _segment_impact(
        db,
        workspace_id,
        high_pain_total=pain_distribution.high,
    )
    source_breakdown = _source_breakdown(db, workspace_id, total_items=total)
    team_workload = _team_workload(db, workspace_id, sla_cutoff=sla_cutoff)
    signal_quality = _signal_quality(db, workspace_id)
    backlog_categories = _backlog_categories(
        db,
        workspace_id,
        sla_cutoff=sla_cutoff,
        team_workload=team_workload,
        signal_quality=signal_quality,
    )
    quick_views = _quick_views(
        db,
        workspace_id,
        now=now,
        sla_cutoff=sla_cutoff,
        kpi=kpi,
        team_workload=team_workload,
        signal_quality=signal_quality,
    )
    action_queue = _action_queue(
        db,
        workspace_id,
        now=now,
        sla_cutoff=sla_cutoff,
        quick_views=quick_views,
    )

    summary = DashboardSummary(
        kpi=kpi,
        throughput=throughput,
        status_mix=status_mix,
        aging_health=aging_health,
        top_tags=top_tags,
        pain_distribution=pain_distribution,
        segment_impact=segment_impact,
        source_breakdown=source_breakdown,
        team_workload=team_workload,
        signal_quality=signal_quality,
        backlog_categories=backlog_categories,
        action_queue=action_queue,
        total_items=total,
    )

    with _cache_lock:
        _cache[key] = summary
    return summary


__all__ = [
    "ACTION_QUEUE_LIMIT",
    "CACHE_MAX_ENTRIES",
    "CACHE_TTL_SECONDS",
    "RECENT_ACTIVITY_LIMIT",
    "SOURCE_BREAKDOWN_LIMIT",
    "SPARKLINE_DAYS",
    "THROUGHPUT_DAYS",
    "TOP_TAGS_LIMIT",
    "ActionQueue",
    "ActionQueueEntry",
    "AgingBucket",
    "AgingHealth",
    "AttentionCategory",
    "DashboardSummary",
    "KpiMetrics",
    "PainDistribution",
    "SegmentImpact",
    "SegmentImpactRow",
    "SignalQuality",
    "SourceBreakdownEntry",
    "StatusMixSlice",
    "TeamWorkload",
    "TeamWorkloadRow",
    "ThroughputPoint",
    "ThroughputSummary",
    "TopTag",
    "get_summary",
    "reset_cache",
]
