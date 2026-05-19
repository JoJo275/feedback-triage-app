"""Pydantic response schemas for dashboard summary APIs.

The dashboard aggregator in :mod:`feedback_triage.services.dashboard_aggregator`
returns rich dataclass objects. These models define the JSON boundary for
``/api/v1/dashboard/summary`` so frontend clients can consume a stable,
typed contract.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DashboardCountsResponse(BaseModel):
    """Top-level KPI counts for the current workspace."""

    model_config = ConfigDict(extra="forbid")

    total_signals: int = Field(ge=0)
    needs_action: int = Field(ge=0)
    high_pain_signals: int = Field(ge=0)


class DashboardIntakePointResponse(BaseModel):
    """One intake-series point in the current 30-day window."""

    model_config = ConfigDict(extra="forbid")

    day: date
    received: int = Field(ge=0)


class DashboardTotalSignalsWidgetResponse(BaseModel):
    """Display contract payload for the Total signals widget."""

    model_config = ConfigDict(extra="forbid")

    widget_id: Literal["kpi-total-signals"] = "kpi-total-signals"
    label: Literal["Total signals"] = "Total signals"
    value: int = Field(ge=0)
    delta_pct: int
    delta_direction: Literal["up", "down", "flat"]
    comparison_label: str = Field(min_length=1)
    sparkline_points: list[int]
    sparkline_date_labels: list[str]


class DashboardSummaryResponse(BaseModel):
    """Response envelope for ``GET /api/v1/dashboard/summary``."""

    model_config = ConfigDict(extra="forbid")

    counts: DashboardCountsResponse
    intake_30d: list[DashboardIntakePointResponse]
    total_signals_widget: DashboardTotalSignalsWidgetResponse


__all__ = [
    "DashboardCountsResponse",
    "DashboardIntakePointResponse",
    "DashboardSummaryResponse",
    "DashboardTotalSignalsWidgetResponse",
]
