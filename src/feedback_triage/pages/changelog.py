"""Management changelog page (PR 3.3).

Mounted at ``/w/{slug}/changelog``. Authenticated; resolves through
:class:`WorkspaceContextDep` so cross-tenant probes 404 (ADR 060).

Phase 4 serves this route through the shared React shell.

Per ``docs/project/spec/v2/information-architecture.md`` -- Changelog (management).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DbSession
from starlette.requests import Request
from starlette.responses import Response

from feedback_triage.database import get_db
from feedback_triage.models import Workspace
from feedback_triage.pages.react_shell import maybe_render_workspace_react_shell
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
) -> Response:
    """Render the changelog management shell for workspace ``slug``."""
    workspace = db.get(Workspace, ctx.id)
    assert workspace is not None

    return maybe_render_workspace_react_shell(
        request,
        workspace_slug=workspace.slug,
        workspace_name=workspace.name,
        active_section="changelog",
        page_key="changelog",
        page_title="Changelog",
    )
