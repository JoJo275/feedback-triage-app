"""Page routes for the submitters list and detail (PR 2.6).

Renders ``/w/{slug}/submitters`` (list) and
``/w/{slug}/submitters/{submitter_id}`` (detail). Both pages are
served from page routes with tenant guards; the submitters list route
mounts the shared React shell and the detail route keeps a dedicated
template flow.

Spec: ``docs/project/spec/v2/information-architecture.md`` —
Submitters list / Submitter detail.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session as DbSession
from starlette.requests import Request
from starlette.responses import Response

from feedback_triage.database import get_db
from feedback_triage.models import Submitter, Workspace
from feedback_triage.pages.react_shell import maybe_render_workspace_react_shell
from feedback_triage.templating import templates
from feedback_triage.tenancy import WorkspaceContextDep

router = APIRouter(include_in_schema=False)

DbDep = Annotated[DbSession, Depends(get_db)]


@router.get("/w/{slug}/submitters", summary="Submitters list")
def submitters_list_page(
    request: Request,
    ctx: WorkspaceContextDep,
    db: DbDep,
) -> Response:
    """Render the submitters-list shell for workspace ``slug``."""
    workspace = db.get(Workspace, ctx.id)
    assert workspace is not None

    return maybe_render_workspace_react_shell(
        request,
        workspace_slug=workspace.slug,
        workspace_name=workspace.name,
        active_section="submitters",
        page_key="submitters",
        page_title="Submitters",
    )


@router.get(
    "/w/{slug}/submitters/{submitter_id}",
    summary="Submitter detail",
)
def submitter_detail_page(
    submitter_id: uuid.UUID,
    request: Request,
    ctx: WorkspaceContextDep,
    db: DbDep,
) -> HTMLResponse:
    """Render the submitter-detail shell."""
    workspace = db.get(Workspace, ctx.id)
    assert workspace is not None
    submitter = db.get(Submitter, submitter_id)
    # Cross-tenant access must look identical to a missing row, per
    # ADR 060 — never disclose existence of a row in another tenant.
    if submitter is None or submitter.workspace_id != ctx.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submitter not found",
        )
    return templates.TemplateResponse(
        request,
        "pages/submitters/detail.html",
        {
            "workspace_slug": workspace.slug,
            "workspace_name": workspace.name,
            "submitter_id": str(submitter.id),
            "active": "submitters",
        },
    )
