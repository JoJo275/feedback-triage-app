"""SQLAlchemy engine, session factory, and request-scoped dependency.

One engine per process; one session per request. ``get_db`` is the only
sanctioned way to obtain a session inside a route handler — sessions are
never stored on ``app.state``, in module globals, or in background-task
closures that outlive the request. See spec — Database session
lifecycle for the full invariant and the canary test that protects it.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from feedback_triage.config import Settings, get_settings


def make_engine(settings: Settings | None = None) -> Engine:
    """Build the process-wide SQLAlchemy engine.

    Connection-pool sizing follows
    [`v2/railway-optimization.md`](../../docs/project/spec/v2/railway-optimization.md):
    ``pool_size=5, max_overflow=0`` per worker (10 connections in
    steady state across two Uvicorn workers; hard ceiling of 15 with
    cron + migration overlap, well under Railway Hobby Postgres's
    connection cap). ``pool_pre_ping=True`` keeps stale connections
    out of request handlers; ``pool_timeout=2`` makes the readiness
    probe fail fast instead of blocking Railway's healthcheck.
    """
    settings = settings or get_settings()
    return create_engine(
        settings.database_url.get_secret_value(),
        pool_size=5,
        max_overflow=0,
        pool_pre_ping=True,
        pool_timeout=2,
        future=True,
    )


engine: Engine = make_engine()

# ``expire_on_commit=False`` is safe ONLY because every session is
# request-scoped via ``get_db``. See spec — Database session lifecycle.
SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    future=True,
    class_=Session,
)


def get_db() -> Iterator[Session]:
    """Yield a request-scoped SQLAlchemy session.

    Commit on success, rollback on exception, always close. Handlers
    must not call ``session.commit()`` themselves — the transaction
    boundary lives here.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
