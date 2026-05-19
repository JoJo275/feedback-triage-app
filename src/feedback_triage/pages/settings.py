"""Page route for the workspace settings page (PR 2.5).

Renders ``/w/{slug}/settings``. The page is a server-rendered shell;
the workspace-info form, members table, tags CRUD widget, and
public-submit toggle are wired client-side by
``static/js/settings.js`` against the existing
``/api/v1/workspaces/{slug}*`` and ``/api/v1/tags`` endpoints.

Owner-only sections are gated server-side: the template only emits
the *Members* table and the *Public submit* toggle when the
caller's role is ``owner`` (or site-wide ``admin``). Non-owners get
a single read-only *Workspace* card. This mirrors the spec's
"hidden, not just disabled, for non-owners" requirement
(``docs/project/spec/v2/information-architecture.md`` — Settings).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DbSession
from starlette.requests import Request
from starlette.responses import Response

from feedback_triage.database import get_db
from feedback_triage.enums import WorkspaceRole
from feedback_triage.models import Workspace
from feedback_triage.pages.react_shell import (
    get_runtime_settings,
    maybe_render_workspace_react_shell,
)
from feedback_triage.templating import templates
from feedback_triage.tenancy import WorkspaceContextDep

router = APIRouter(include_in_schema=False)

DbDep = Annotated[DbSession, Depends(get_db)]


@router.get("/w/{slug}/settings", summary="Workspace settings")
def settings_page(
    request: Request,
    ctx: WorkspaceContextDep,
    db: DbDep,
) -> Response:
    """Render the settings page for workspace ``slug``."""
    workspace = db.get(Workspace, ctx.id)
    assert workspace is not None

    settings = get_runtime_settings(request)
    react_response = maybe_render_workspace_react_shell(
        request,
        enabled=settings.feature_react_settings,
        workspace_slug=workspace.slug,
        workspace_name=workspace.name,
        active_section="settings",
        page_key="settings",
        page_title="Settings",
    )
    if react_response is not None:
        return react_response

    is_owner = ctx.role in (WorkspaceRole.OWNER, "admin")
    return templates.TemplateResponse(
        request,
        "pages/settings/index.html",
        {
            "workspace_slug": workspace.slug,
            "workspace_name": workspace.name,
            "workspace_public_submit_enabled": workspace.public_submit_enabled,
            "active": "settings",
            "is_owner": is_owner,
        },
    )
