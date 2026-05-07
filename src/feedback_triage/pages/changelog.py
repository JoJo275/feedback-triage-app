"""Management changelog page (PR 3.3).

Mounted at ``/w/{slug}/changelog``. Authenticated; resolves through
:class:`WorkspaceContextDep` so cross-tenant probes 404 (ADR 060).

Reverse-chronological list of ``status='shipped'`` items with an
inline release-note editor and a publish-to-changelog toggle. The
shell is server-rendered; ``static/js/changelog.js`` boots the
fetch + edit-on-blur flow against ``PATCH /api/v1/feedback/{id}``.

Per ``docs/project/spec/v2/pages.md`` -- Changelog (management).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session as DbSession
from starlette.requests import Request

from feedback_triage.database import get_db
from feedback_triage.models import Workspace
from feedback_triage.templating import templates
from feedback_triage.tenancy import WorkspaceContextDep

router = APIRouter(include_in_schema=False)

DbDep = Annotated[DbSession, Depends(get_db)]


@router.get(
    "/w/{slug}/changelog",
    summary="Workspace changelog (management view)",
)
def changelog_page(
    request: Request,
    ctx: WorkspaceContextDep,
    db: DbDep,
) -> HTMLResponse:
    """Render the changelog management shell for workspace ``slug``."""
    workspace = db.get(Workspace, ctx.id)
    assert workspace is not None
    return templates.TemplateResponse(
        request,
        "pages/changelog.html",
        {
            "workspace_slug": workspace.slug,
            "workspace_name": workspace.name,
            "active": "changelog",
        },
    )
