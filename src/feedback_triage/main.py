"""FastAPI application factory.

Building the app via :func:`create_app` (rather than at import time)
keeps tests cheap to spin up and lets settings be overridden per
environment. The factory is the single composition root: middleware,
routers, and OpenAPI metadata are all wired here.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from feedback_triage import __version__
from feedback_triage.config import Settings, get_settings
from feedback_triage.errors import register_exception_handlers
from feedback_triage.middleware import (
    RequestIDLogFilter,
    RequestIDMiddleware,
    RequestLoggingMiddleware,
)
from feedback_triage.routes import feedback, health, pages
from feedback_triage.routes.pages import STATIC_DIR


def _configure_logging(settings: Settings) -> None:
    level = logging.getLevelName(settings.log_level.upper())
    if not isinstance(level, int):
        level = logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s [%(request_id)s] %(message)s",
        force=True,
    )
    # Attach the request-id filter to the root logger so every record
    # gains a ``request_id`` attribute (defaults to "-" outside a request).
    request_id_filter = RequestIDLogFilter()
    root_logger = logging.getLogger()
    # Replace any existing instance of our filter to keep idempotency
    # across repeated ``create_app`` calls in tests.
    root_logger.filters = [
        f for f in root_logger.filters if not isinstance(f, RequestIDLogFilter)
    ]
    root_logger.addFilter(request_id_filter)
    for handler in root_logger.handlers:
        handler.filters = [
            f for f in handler.filters if not isinstance(f, RequestIDLogFilter)
        ]
        handler.addFilter(request_id_filter)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and return a configured :class:`FastAPI` instance."""
    settings = settings or get_settings()
    _configure_logging(settings)

    app = FastAPI(
        title="Feedback Triage App",
        version=__version__,
        docs_url="/api/v1/docs",
        redoc_url=None,
        openapi_url="/api/v1/openapi.json",
    )

    # Order matters: outermost middleware runs first on the way in. The
    # request-ID middleware must wrap logging so the access log carries
    # the ID; both wrap CORS so preflights are still logged with an ID.
    app.add_middleware(
        RequestLoggingMiddleware,
        json_format=settings.is_production,
    )
    app.add_middleware(RequestIDMiddleware)

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=False,
            allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=["*"],
        )

    app.include_router(health.router)
    app.include_router(feedback.router)
    app.include_router(pages.router)

    register_exception_handlers(app)

    app.mount(
        "/static",
        StaticFiles(directory=STATIC_DIR),
        name="static",
    )

    return app


app = create_app()
