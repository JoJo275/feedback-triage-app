"""Page route for the workspace dashboard.

PR 1.8 shipped an empty-state shell at ``/w/{slug}/dashboard``;
PR 3.4 filled it in. The route resolves the slug through
:class:`WorkspaceContextDep` (cross-tenant probes 404 per ADR 060)
and asks
:func:`feedback_triage.services.dashboard_aggregator.get_summary`
for the dashboard contract (KPI strip, operational health,
themes/impact widgets, execution workload, and urgency-first
action queue).

When the workspace has no feedback yet we keep the original
empty-state template -- it's a richer surface than five zero-cards.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session as DbSession
from starlette.requests import Request
from starlette.responses import Response

from feedback_triage.database import get_db
from feedback_triage.frontend_assets import resolve_react_entry
from feedback_triage.models import Workspace
from feedback_triage.pages.react_shell import (
    get_runtime_settings,
    maybe_render_workspace_react_shell,
)
from feedback_triage.services import dashboard_aggregator
from feedback_triage.templating import templates
from feedback_triage.tenancy import WorkspaceContextDep

router = APIRouter(include_in_schema=False)
logger = logging.getLogger(__name__)

DbDep = Annotated[DbSession, Depends(get_db)]


@router.get("/w/{slug}/dashboard", summary="Workspace dashboard")
def dashboard_page(
    request: Request,
    ctx: WorkspaceContextDep,
    db: DbDep,
) -> Response:
    """Render the dashboard for workspace ``slug``."""
    workspace = db.get(Workspace, ctx.id)
    assert workspace is not None

    settings = get_runtime_settings(request)
    react_response = maybe_render_workspace_react_shell(
        request,
        enabled=settings.feature_react_dashboard,
        workspace_slug=workspace.slug,
        workspace_name=workspace.name,
        active_section="dashboard",
        page_key="dashboard",
        page_title="Dashboard",
    )
    if react_response is not None:
        return react_response

    summary = dashboard_aggregator.get_summary(
        db,
        workspace_id=ctx.id,
        role=ctx.role,
    )

    if summary.total_items == 0:
        return templates.TemplateResponse(
            request,
            "pages/dashboard/empty.html",
            {
                "workspace_slug": workspace.slug,
                "workspace_name": workspace.name,
                "active": "dashboard",
            },
        )

    return templates.TemplateResponse(
        request,
        "pages/dashboard/index.html",
        {
            "workspace_slug": workspace.slug,
            "workspace_name": workspace.name,
            "active": "dashboard",
            "summary": summary,
        },
    )


@router.get(
    "/w/{slug}/dashboard/react",
    summary="Workspace dashboard (React widgets pilot)",
)
def dashboard_react_widgets_page(
    request: Request,
    ctx: WorkspaceContextDep,
    db: DbDep,
) -> Response:
    """Render the React dashboard page for workspace ``slug``."""
    workspace = db.get(Workspace, ctx.id)
    assert workspace is not None

    settings = get_runtime_settings(request)

    if not settings.feature_react_dashboard:
        return templates.TemplateResponse(
            request,
            "pages/dashboard/react_widgets.html",
            {
                "workspace_slug": workspace.slug,
                "workspace_name": workspace.name,
                "active": "dashboard",
            },
        )

    entry_assets = resolve_react_entry(settings.react_dashboard_entrypoint)
    if entry_assets is None:
        logger.error(
            "React dashboard entrypoint '%s' missing from manifest; "
            "falling back to legacy dashboard route.",
            settings.react_dashboard_entrypoint,
        )
        return RedirectResponse(
            url=f"/w/{workspace.slug}/dashboard",
            status_code=307,
        )

    response = templates.TemplateResponse(
        request,
        "pages/dashboard/react_shell.html",
        {
            "workspace_slug": workspace.slug,
            "workspace_name": workspace.name,
            "active": "dashboard",
            "react_script_url": entry_assets.script_url,
            "react_css_urls": entry_assets.css_urls,
            "react_client_release": entry_assets.script_url.rsplit("/", 1)[-1],
        },
    )

    if settings.react_csp_enabled:
        response.headers["Content-Security-Policy"] = settings.react_csp_policy

    return response
