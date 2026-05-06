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
(``docs/project/spec/v2/pages.md`` — Settings).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session as DbSession
from starlette.requests import Request

from feedback_triage.database import get_db
from feedback_triage.enums import WorkspaceRole
from feedback_triage.models import Workspace
from feedback_triage.templating import templates
from feedback_triage.tenancy import WorkspaceContextDep

router = APIRouter(include_in_schema=False)

DbDep = Annotated[DbSession, Depends(get_db)]


@router.get("/w/{slug}/settings", summary="Workspace settings")
def settings_page(
    request: Request,
    ctx: WorkspaceContextDep,
    db: DbDep,
) -> HTMLResponse:
    """Render the settings page for workspace ``slug``."""
    workspace = db.get(Workspace, ctx.id)
    assert workspace is not None
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
