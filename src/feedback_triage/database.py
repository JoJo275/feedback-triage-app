"""SQLAlchemy engine and session plumbing.

Phase 1 only needs the engine for the readiness probe. Phase 2 will add
``SessionLocal`` and the ``get_db`` FastAPI dependency that scopes a
session to a single request (see spec — Database session lifecycle).
"""

from __future__ import annotations

from sqlalchemy import Engine, create_engine

from feedback_triage.config import Settings, get_settings


def make_engine(settings: Settings | None = None) -> Engine:
    """Build the process-wide SQLAlchemy engine.

    Connection-pool sizing follows the spec: ``pool_size=5``,
    ``max_overflow=5``, ``pool_pre_ping=True``. ``pool_timeout`` is held
    to 2 seconds so the readiness probe fails fast instead of blocking
    Railway's healthcheck.
    """
    settings = settings or get_settings()
    return create_engine(
        settings.database_url,
        pool_size=5,
        max_overflow=5,
        pool_pre_ping=True,
        pool_timeout=2,
        future=True,
    )


engine: Engine = make_engine()
