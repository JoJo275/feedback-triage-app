"""FastAPI application factory.

Building the app via :func:`create_app` (rather than at import time)
keeps tests cheap to spin up and lets settings be overridden per
environment. The factory is the single composition root: middleware,
routers, and OpenAPI metadata are all wired here.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from feedback_triage import __version__
from feedback_triage.api.v1 import auth as auth_api
from feedback_triage.api.v1 import feedback as feedback_api
from feedback_triage.api.v1 import invitations as invitations_api
from feedback_triage.api.v1 import public_feedback as public_feedback_api
from feedback_triage.api.v1 import submitters as submitters_api
from feedback_triage.api.v1 import tags as tags_api
from feedback_triage.api.v1 import users as users_api
from feedback_triage.api.v1 import workspaces as workspaces_api
from feedback_triage.auth import hashing as auth_hashing
from feedback_triage.auth.feature_flag import FeatureAuthGateMiddleware
from feedback_triage.config import Settings, get_settings
from feedback_triage.errors import register_exception_handlers
from feedback_triage.middleware import (
    RequestIDLogFilter,
    RequestIDMiddleware,
    RequestLoggingMiddleware,
)
from feedback_triage.pages import auth as auth_pages
from feedback_triage.pages import changelog as changelog_pages
from feedback_triage.pages import dashboard as dashboard_pages
from feedback_triage.pages import feedback_detail as feedback_detail_pages
from feedback_triage.pages import inbox as inbox_pages
from feedback_triage.pages import insights as insights_pages
from feedback_triage.pages import landing as landing_pages
from feedback_triage.pages import legal as legal_pages
from feedback_triage.pages import public_changelog as public_changelog_pages
from feedback_triage.pages import public_roadmap as public_roadmap_pages
from feedback_triage.pages import public_submit as public_submit_pages
from feedback_triage.pages import roadmap as roadmap_pages
from feedback_triage.pages import settings as settings_pages
from feedback_triage.pages import submitters as submitters_pages
from feedback_triage.routes import health, pages
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

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        # Warm Argon2's native lib so the first sign-in after a cold
        # boot doesn't pay the 50-200 ms first-verify tax on top of the
        # 150 ms hash itself. Skipped when the auth surface is gated
        # off so v2.0-alpha boots don't load ``argon2-cffi`` for no
        # reason. See ``docs/project/spec/v2/railway-optimization.md``
        # - Cold-path inventory.
        if settings.feature_auth:
            auth_hashing.warmup()
        yield

    app = FastAPI(
        title="Feedback Triage App",
        version=__version__,
        docs_url="/api/v1/docs",
        redoc_url=None,
        openapi_url="/api/v1/openapi.json",
        lifespan=lifespan,
    )

    # Starlette's ``add_middleware`` *prepends* — the LAST class added is
    # the OUTERMOST wrapper at runtime. We want the request-ID middleware
    # outermost so it sets ``request.state.request_id`` (and the
    # contextvar) before the logging middleware runs, and so it is the
    # last thing to clean up on the way out.
    app.add_middleware(
        RequestLoggingMiddleware,
        json_format=settings.is_production,
    )
    app.add_middleware(RequestIDMiddleware)

    # ``FEATURE_AUTH`` gate (PR 1.9). Mounted only when the flag is
    # off so the auth surface (``/api/v1/auth/*`` and the auth page
    # routes) short-circuits with 503. Read once at startup; flipping
    # the flag requires a redeploy. Sits *inside* the request-id and
    # logging middlewares so gated requests still log and still echo
    # an ``X-Request-ID``.
    if not settings.feature_auth:
        app.add_middleware(FeatureAuthGateMiddleware)

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=False,
            allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=["*"],
        )

    app.include_router(health.router)
    app.include_router(feedback_api.router)
    app.include_router(tags_api.router)
    app.include_router(submitters_api.router)
    app.include_router(public_feedback_api.router)
    app.include_router(auth_api.router)
    app.include_router(workspaces_api.router)
    app.include_router(invitations_api.ws_invitations_router)
    app.include_router(invitations_api.accept_router)
    app.include_router(users_api.router)
    app.include_router(auth_pages.router)
    app.include_router(landing_pages.router)
    app.include_router(legal_pages.router)
    app.include_router(dashboard_pages.router)
    app.include_router(inbox_pages.router)
    app.include_router(public_submit_pages.router)
    app.include_router(public_roadmap_pages.router)
    app.include_router(public_changelog_pages.router)
    app.include_router(roadmap_pages.router)
    app.include_router(changelog_pages.router)
    app.include_router(insights_pages.router)
    app.include_router(feedback_detail_pages.router)
    app.include_router(settings_pages.router)
    app.include_router(submitters_pages.router)
    app.include_router(pages.router)

    register_exception_handlers(app)

    app.mount(
        "/static",
        StaticFiles(directory=STATIC_DIR),
        name="static",
    )

    return app


app = create_app()
