"""``/api/v1/dashboard`` JSON endpoints.

These routes expose the pre-aggregated dashboard summary so React pages can
render KPI widgets from one tenant-scoped API call instead of reconstructing
derived metrics client-side.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DbSession

from feedback_triage.api.v1._dashboard_schemas import (
    DashboardCountsResponse,
    DashboardIntakePointResponse,
    DashboardSummaryResponse,
    DashboardTotalSignalsWidgetResponse,
)
from feedback_triage.database import get_db
from feedback_triage.services import dashboard_aggregator
from feedback_triage.tenancy import WorkspaceContextDep

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])

DbDep = Annotated[DbSession, Depends(get_db)]


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    summary="Return dashboard KPI and intake summary",
)
def get_dashboard_summary(
    ctx: WorkspaceContextDep,
    db: DbDep,
) -> DashboardSummaryResponse:
    """Return dashboard summary data for the active workspace."""
    summary = dashboard_aggregator.get_summary(
        db,
        workspace_id=ctx.id,
        role=ctx.role,
    )

    widget = summary.total_signals_widget
    return DashboardSummaryResponse(
        counts=DashboardCountsResponse(
            total_signals=summary.kpi.total_signals,
            needs_action=summary.kpi.needs_action,
            high_pain_signals=summary.kpi.high_pain_signals,
        ),
        intake_30d=[
            DashboardIntakePointResponse(day=point.day, received=point.received)
            for point in summary.throughput.points
        ],
        total_signals_widget=DashboardTotalSignalsWidgetResponse(
            value=widget.value,
            delta_pct=widget.delta_pct,
            delta_direction=widget.delta_direction,
            comparison_label=widget.comparison_label,
            sparkline_points=list(widget.sparkline_points),
            sparkline_date_labels=list(widget.sparkline_date_labels),
        ),
    )
