"""Shared helpers for feature-flagged React workspace page routes.

Phase 2 routes keep the legacy Jinja pages as fallback while React
rolls out by page group. These helpers centralize the common behavior:

- resolve app-bound settings
- honor ``?view=legacy`` parity fallback
- resolve Vite manifest assets
- apply optional CSP policy on React shell responses
"""

from __future__ import annotations

import json
import logging
from typing import Any
from urllib.parse import urlencode

from starlette.requests import Request
from starlette.responses import Response

from feedback_triage.config import Settings, get_settings
from feedback_triage.frontend_assets import resolve_react_entry
from feedback_triage.templating import templates

logger = logging.getLogger(__name__)

_LEGACY_VIEW_PARAM = "view"
_LEGACY_VIEW_VALUE = "legacy"


def get_runtime_settings(request: Request) -> Settings:
    """Return app-bound settings, falling back to cached global settings."""
    configured = getattr(request.app.state, "settings", None)
    return configured if isinstance(configured, Settings) else get_settings()


def _legacy_view_requested(request: Request) -> bool:
    """Return ``True`` when the caller explicitly requests legacy rendering."""
    requested = request.query_params.get(_LEGACY_VIEW_PARAM, "")
    return requested.strip().lower() == _LEGACY_VIEW_VALUE


def _build_legacy_url(request: Request) -> str:
    """Return current path + query with ``view=legacy`` applied."""
    pairs = [
        (key, value)
        for key, value in request.query_params.multi_items()
        if key.lower() != _LEGACY_VIEW_PARAM
    ]
    pairs.append((_LEGACY_VIEW_PARAM, _LEGACY_VIEW_VALUE))
    query = urlencode(pairs)
    return f"{request.url.path}?{query}" if query else request.url.path


def maybe_render_workspace_react_shell(
    request: Request,
    *,
    enabled: bool,
    workspace_slug: str,
    workspace_name: str,
    active_section: str,
    page_key: str,
    page_title: str,
) -> Response | None:
    """Render the shared React shell when route flag + request allow it.

    Returns ``None`` when React should not render so the caller can fall
    back to the legacy template path.
    """
    if not enabled or _legacy_view_requested(request):
        return None

    settings = get_runtime_settings(request)
    entry_assets = resolve_react_entry(settings.react_dashboard_entrypoint)
    if entry_assets is None:
        logger.error(
            "React entrypoint '%s' missing from manifest; falling back to "
            "legacy workspace page route.",
            settings.react_dashboard_entrypoint,
        )
        return None

    response = templates.TemplateResponse(
        request,
        "pages/react/workspace_shell.html",
        {
            "workspace_slug": workspace_slug,
            "workspace_name": workspace_name,
            "active": active_section,
            "react_page_key": page_key,
            "react_page_title": page_title,
            "react_legacy_url": _build_legacy_url(request),
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
    enabled: bool,
    page_key: str,
    page_title: str,
    route_payload: dict[str, Any],
) -> Response | None:
    """Render the shared React shell for public routes when enabled."""
    if not enabled or _legacy_view_requested(request):
        return None

    settings = get_runtime_settings(request)
    entry_assets = resolve_react_entry(settings.react_dashboard_entrypoint)
    if entry_assets is None:
        logger.error(
            "React entrypoint '%s' missing from manifest; falling back to "
            "legacy public page route.",
            settings.react_dashboard_entrypoint,
        )
        return None

    response = templates.TemplateResponse(
        request,
        "pages/react/public_shell.html",
        {
            "react_page_key": page_key,
            "react_page_title": page_title,
            "react_legacy_url": _build_legacy_url(request),
            "react_script_url": entry_assets.script_url,
            "react_css_urls": entry_assets.css_urls,
            "react_client_release": entry_assets.script_url.rsplit("/", 1)[-1],
            "react_route_payload_json": _serialize_react_payload(route_payload),
        },
    )

    if settings.react_csp_enabled:
        response.headers["Content-Security-Policy"] = settings.react_csp_policy

    return response
