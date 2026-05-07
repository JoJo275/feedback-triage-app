"""Management roadmap kanban page (PR 3.3).

Mounted at ``/w/{slug}/roadmap``. Authenticated; resolves through
:class:`WorkspaceContextDep` so cross-tenant probes 404 (ADR 060).

The shell is server-rendered and seeds the workspace slug into the
DOM; ``static/js/roadmap.js`` boots the kanban, fetches feedback in
the three roadmap statuses (``planned`` / ``in_progress`` /
``shipped``), renders cards, and wires the column-move + publish
toggle controls against ``PATCH /api/v1/feedback/{id}``.

Per ``docs/project/spec/v2/pages.md`` -- Roadmap (management).
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
    "/w/{slug}/roadmap",
    summary="Workspace roadmap kanban (management view)",
)
def roadmap_page(
    request: Request,
    ctx: WorkspaceContextDep,
    db: DbDep,
) -> HTMLResponse:
    """Render the roadmap kanban shell for workspace ``slug``."""
    workspace = db.get(Workspace, ctx.id)
    assert workspace is not None
    return templates.TemplateResponse(
        request,
        "pages/roadmap.html",
        {
            "workspace_slug": workspace.slug,
            "workspace_name": workspace.name,
            "active": "roadmap",
        },
    )
