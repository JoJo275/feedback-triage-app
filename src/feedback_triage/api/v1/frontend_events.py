"""Frontend telemetry ingestion endpoint for React route rollouts.

React page surfaces report request failures and client-side runtime
errors here so operators can correlate frontend incidents with backend
request ids during canary rollout.
"""

from __future__ import annotations

import logging
from typing import Literal

from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict, Field

from feedback_triage.auth.deps import CurrentUserDep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/frontend-events", tags=["telemetry"])


class FrontendEventRequest(BaseModel):
    """Client-side telemetry payload emitted by React pages."""

    model_config = ConfigDict(extra="forbid")

    event: Literal[
        "api_failure",
        "mutation_failure",
        "window_error",
        "unhandled_rejection",
    ]
    route: str = Field(min_length=1, max_length=200)
    client_release: str = Field(min_length=1, max_length=200)
    path: str | None = Field(default=None, max_length=300)
    method: str | None = Field(default=None, max_length=16)
    status_code: int | None = Field(default=None, ge=0, le=599)
    code: str | None = Field(default=None, max_length=120)
    request_id: str | None = Field(default=None, max_length=120)
    message: str | None = Field(default=None, max_length=500)


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest frontend telemetry event",
)
def ingest_frontend_event(
    payload: FrontendEventRequest,
    _user: CurrentUserDep,
) -> None:
    """Accept and log one frontend telemetry event.

    The endpoint is intentionally fail-soft: events are best effort and
    must never block the user-facing request path.
    """
    logger.warning(
        "frontend.telemetry event=%s status=%d",
        payload.event,
        payload.status_code if payload.status_code is not None else -1,
    )
