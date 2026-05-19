"""Shared helpers for React page routes.

Phase 4 decommissions legacy page fallback for migrated routes. These
helpers centralize the common behavior:

- resolve app-bound settings
- resolve Vite manifest assets
- apply optional CSP policy on React shell responses
"""

from __future__ import annotations

import json
import logging
from typing import Any

from starlette.requests import Request
from starlette.responses import Response

from feedback_triage.config import Settings, get_settings
from feedback_triage.frontend_assets import resolve_react_entry
from feedback_triage.templating import templates

logger = logging.getLogger(__name__)


def get_runtime_settings(request: Request) -> Settings:
    """Return app-bound settings, falling back to cached global settings."""
    configured = getattr(request.app.state, "settings", None)
    return configured if isinstance(configured, Settings) else get_settings()


def maybe_render_workspace_react_shell(
    request: Request,
    *,
    workspace_slug: str,
    workspace_name: str,
    active_section: str,
    page_key: str,
    page_title: str,
) -> Response:
    """Render the shared React shell for authenticated page routes."""
    settings = get_runtime_settings(request)
    entry_assets = resolve_react_entry(settings.react_dashboard_entrypoint)
    if entry_assets is None:
        message = (
            "React entrypoint "
            f"'{settings.react_dashboard_entrypoint}' missing from manifest."
        )
        logger.error(message)
        return Response(
            content="React frontend assets are unavailable.",
            media_type="text/plain",
            status_code=503,
        )

    response = templates.TemplateResponse(
        request,
        "pages/react/workspace_shell.html",
        {
            "workspace_slug": workspace_slug,
            "workspace_name": workspace_name,
            "active": active_section,
            "react_page_key": page_key,
            "react_page_title": page_title,
            "react_script_url": entry_assets.script_url,
            "react_css_urls": entry_assets.css_urls,
            "react_client_release": entry_assets.script_url.rsplit("/", 1)[-1],
        },
    )

    if settings.react_csp_enabled:
        response.headers["Content-Security-Policy"] = settings.react_csp_policy

    return response


def _serialize_react_payload(payload: dict[str, Any]) -> str:
    """Serialize route payload for in-page JSON bootstrap script tags."""
    # Escape '<' so user-authored strings cannot terminate the JSON script tag.
    return json.dumps(payload, separators=(",", ":")).replace("<", "\\u003c")


def maybe_render_public_react_shell(
    request: Request,
    *,
    page_key: str,
    page_title: str,
    route_payload: dict[str, Any],
) -> Response:
    """Render the shared React shell for public routes."""
    settings = get_runtime_settings(request)
    entry_assets = resolve_react_entry(settings.react_dashboard_entrypoint)
    if entry_assets is None:
        message = (
            "React entrypoint "
            f"'{settings.react_dashboard_entrypoint}' missing from manifest."
        )
        logger.error(message)
        return Response(
            content="React frontend assets are unavailable.",
            media_type="text/plain",
            status_code=503,
        )

    response = templates.TemplateResponse(
        request,
        "pages/react/public_shell.html",
        {
            "react_page_key": page_key,
            "react_page_title": page_title,
            "react_script_url": entry_assets.script_url,
            "react_css_urls": entry_assets.css_urls,
            "react_client_release": entry_assets.script_url.rsplit("/", 1)[-1],
            "react_route_payload_json": _serialize_react_payload(route_payload),
        },
    )

    if settings.react_csp_enabled:
        response.headers["Content-Security-Policy"] = settings.react_csp_policy

    return response
