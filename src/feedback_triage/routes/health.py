"""Liveness (`/health`) and readiness (`/ready`) probes.

Liveness is a pure process-alive signal — it never touches the database.
Readiness verifies the app can reach Postgres within a hard 2-second
budget so Railway's healthcheck gets a fast, deterministic answer when
the DB is sick (see spec — Health and readiness).
"""

from __future__ import annotations

import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from feedback_triage.database import engine

router = APIRouter(tags=["health"])

logger = logging.getLogger(__name__)

# Hard ceiling for the readiness DB probe, in milliseconds. Set on the
# session via Postgres' `statement_timeout` GUC so the SELECT 1 cannot
# hang past the engine's pool_timeout=2.
_READINESS_STATEMENT_TIMEOUT_MS = 2000


@router.get("/health", summary="Liveness probe")
def health() -> dict[str, str]:
    """Return ``{"status": "ok"}`` without touching the database."""
    return {"status": "ok"}


@router.get("/ready", summary="Readiness probe")
def ready() -> JSONResponse:
    """Verify the database is reachable within a 2-second budget."""
    try:
        with engine.connect() as conn:
            conn.execute(
                text(f"SET LOCAL statement_timeout = {_READINESS_STATEMENT_TIMEOUT_MS}")
            )
            conn.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.warning("readiness probe failed: %s", exc)
        return JSONResponse(
            status_code=503,
            content={"status": "degraded"},
        )
    return JSONResponse(status_code=200, content={"status": "ok"})
