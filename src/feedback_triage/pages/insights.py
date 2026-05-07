"""Insights page (PR 3.4, Should).

Mounted at ``/w/{slug}/insights``. Three inline-SVG charts (no JS
chart library): top tags bar, status mix donut, pain-level
histogram. Per ``docs/project/spec/v2/pages.md`` -- Insights.

The page is server-rendered: insights are read-once on each
request rather than going through the dashboard cache. The query
volume is small (three aggregates, one per chart) and the page is
visited far less often than the dashboard, so the simpler path
beats sharing the TTL store.

When the workspace has fewer than 10 feedback items the page
shows a stub per the spec ("Insights appear once you have at
least 10 feedback items.").
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy import func
from sqlalchemy.orm import Session as DbSession
from sqlmodel import col, select
from starlette.requests import Request

from feedback_triage.database import get_db
from feedback_triage.models import FeedbackItem, FeedbackTag, Tag, Workspace
from feedback_triage.templating import templates
from feedback_triage.tenancy import WorkspaceContextDep

router = APIRouter(include_in_schema=False)

DbDep = Annotated[DbSession, Depends(get_db)]

#: Workspaces with fewer items than this fall into the empty state.
MIN_ITEMS_FOR_INSIGHTS = 10

#: Number of tags shown in the top-tags bar chart.
TOP_TAGS_LIMIT = 10


@dataclass(frozen=True, slots=True)
class TagBar:
    """One row in the top-tags bar chart."""

    name: str
    color: str
    count: int


@dataclass(frozen=True, slots=True)
class StatusSlice:
    """One slice in the status-mix donut."""

    status: str
    label: str
    count: int
    fraction: float
    start_angle: float
    end_angle: float


@dataclass(frozen=True, slots=True)
class PainBucket:
    """One bar in the pain-level histogram."""

    level: int
    count: int


@dataclass(frozen=True, slots=True)
class Insights:
    """Bundle of every value the insights template needs."""

    total_items: int
    top_tags: list[TagBar]
    top_tags_max: int
    status_mix: list[StatusSlice]
    pain_histogram: list[PainBucket]
    pain_histogram_max: int


def _top_tags(db: DbSession, workspace_id: uuid.UUID) -> list[TagBar]:
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
        TagBar(name=name, color=color, count=int(uses)) for name, color, uses in rows
    ]


def _status_mix(db: DbSession, workspace_id: uuid.UUID) -> list[StatusSlice]:
    rows = db.execute(
        select(col(FeedbackItem.status), func.count())
        .where(col(FeedbackItem.workspace_id) == workspace_id)
        .group_by(col(FeedbackItem.status)),
    ).all()

    counts: dict[str, int] = {str(status): int(count) for status, count in rows}
    total = sum(counts.values())

    if total == 0:
        return []

    slices: list[StatusSlice] = []
    angle = 0.0
    # Stable display order so the donut doesn't reshuffle between renders.
    ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    for status_value, count in ordered:
        fraction = count / total
        sweep = fraction * 2 * math.pi
        slices.append(
            StatusSlice(
                status=status_value,
                label=status_value.replace("_", " "),
                count=count,
                fraction=fraction,
                start_angle=angle,
                end_angle=angle + sweep,
            ),
        )
        angle += sweep
    return slices


def _pain_histogram(db: DbSession, workspace_id: uuid.UUID) -> list[PainBucket]:
    rows = db.execute(
        select(col(FeedbackItem.pain_level), func.count())
        .where(col(FeedbackItem.workspace_id) == workspace_id)
        .group_by(col(FeedbackItem.pain_level)),
    ).all()
    by_level: dict[int, int] = {int(level): int(count) for level, count in rows}
    return [
        PainBucket(level=level, count=by_level.get(level, 0)) for level in range(1, 6)
    ]


def _arc_path(cx: float, cy: float, r: float, slice_: StatusSlice) -> str:
    """Build a single donut wedge as an SVG ``<path d="...">`` string."""
    start_x = cx + r * math.sin(slice_.start_angle)
    start_y = cy - r * math.cos(slice_.start_angle)
    end_x = cx + r * math.sin(slice_.end_angle)
    end_y = cy - r * math.cos(slice_.end_angle)
    large_arc = 1 if slice_.fraction > 0.5 else 0
    # Single full-circle slice: use two arcs so the path stays valid
    # (a single 360° arc collapses to a point in SVG).
    if slice_.fraction >= 0.999:
        return f"M {cx:.2f} {cy - r:.2f} A {r} {r} 0 1 1 {cx - 0.01:.2f} {cy - r:.2f} Z"
    return (
        f"M {cx:.2f} {cy:.2f} "
        f"L {start_x:.2f} {start_y:.2f} "
        f"A {r} {r} 0 {large_arc} 1 {end_x:.2f} {end_y:.2f} Z"
    )


@router.get("/w/{slug}/insights", summary="Workspace insights")
def insights_page(
    request: Request,
    ctx: WorkspaceContextDep,
    db: DbDep,
) -> HTMLResponse:
    """Render the insights page for workspace ``slug``."""
    workspace = db.get(Workspace, ctx.id)
    assert workspace is not None

    total_items = int(
        db.execute(
            select(func.count())
            .select_from(FeedbackItem)
            .where(col(FeedbackItem.workspace_id) == ctx.id),
        ).scalar_one()
    )

    if total_items < MIN_ITEMS_FOR_INSIGHTS:
        return templates.TemplateResponse(
            request,
            "pages/insights.html",
            {
                "workspace_slug": workspace.slug,
                "workspace_name": workspace.name,
                "active": "insights",
                "insights": None,
                "min_items": MIN_ITEMS_FOR_INSIGHTS,
                "total_items": total_items,
            },
        )

    top_tags = _top_tags(db, ctx.id)
    status_mix = _status_mix(db, ctx.id)
    pain = _pain_histogram(db, ctx.id)

    insights = Insights(
        total_items=total_items,
        top_tags=top_tags,
        top_tags_max=max((t.count for t in top_tags), default=0),
        status_mix=status_mix,
        pain_histogram=pain,
        pain_histogram_max=max((p.count for p in pain), default=0),
    )

    # Pre-compute the donut arcs so the template stays free of
    # trig — Jinja can express the `_arc_path` math but it would be
    # harder to read than this lookup table.
    cx, cy, radius = 100.0, 100.0, 80.0
    arcs = [(slice_, _arc_path(cx, cy, radius, slice_)) for slice_ in status_mix]

    return templates.TemplateResponse(
        request,
        "pages/insights.html",
        {
            "workspace_slug": workspace.slug,
            "workspace_name": workspace.name,
            "active": "insights",
            "insights": insights,
            "donut_arcs": arcs,
            "donut_inner_r": 45,
            "donut_cx": cx,
            "donut_cy": cy,
            "donut_r": radius,
            "min_items": MIN_ITEMS_FOR_INSIGHTS,
            "total_items": total_items,
        },
    )


__all__ = [
    "MIN_ITEMS_FOR_INSIGHTS",
    "Insights",
    "PainBucket",
    "StatusSlice",
    "TagBar",
    "router",
]
