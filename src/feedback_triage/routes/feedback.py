"""HTTP handlers for ``/api/v1/feedback``.

Thin layer over :mod:`feedback_triage.crud`: every route declares an
explicit ``response_model``, every error returns the documented body
shape, and the transaction boundary lives in ``get_db`` (see spec —
Database session lifecycle).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from feedback_triage import crud
from feedback_triage.config import Settings, get_settings
from feedback_triage.database import get_db
from feedback_triage.enums import Source, Status
from feedback_triage.schemas import (
    SORTABLE_FIELDS,
    FeedbackCreate,
    FeedbackListEnvelope,
    FeedbackResponse,
    FeedbackUpdate,
)

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])

_NOT_FOUND_DETAIL = "Feedback item not found"


def _not_found() -> HTTPException:
    return HTTPException(status_code=404, detail=_NOT_FOUND_DETAIL)


@router.post(
    "",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a feedback item",
)
def create_feedback(
    payload: FeedbackCreate,
    response: Response,
    session: Annotated[Session, Depends(get_db)],
) -> FeedbackResponse:
    """Create a new feedback item and return it with a ``Location`` header."""
    item = crud.create_item(session, payload)
    response.headers["Location"] = f"/api/v1/feedback/{item.id}"
    return FeedbackResponse.model_validate(item)


@router.get(
    "",
    response_model=FeedbackListEnvelope,
    summary="List feedback items",
)
def list_feedback(
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int | None, Query(ge=1, le=1000)] = None,
    status_filter: Annotated[Status | None, Query(alias="status")] = None,
    source: Annotated[Source | None, Query()] = None,
    sort_by: Annotated[str, Query()] = "-created_at",
) -> FeedbackListEnvelope:
    """Return the paginated envelope of feedback items."""
    if sort_by not in SORTABLE_FIELDS:
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "loc": ["query", "sort_by"],
                    "msg": f"sort_by must be one of {sorted(SORTABLE_FIELDS)}",
                    "type": "value_error",
                }
            ],
        )

    effective_limit = min(
        limit if limit is not None else settings.page_size_default,
        settings.page_size_max,
    )

    items, total = crud.list_items(
        session,
        skip=skip,
        limit=effective_limit,
        status=status_filter,
        source=source,
        sort_by=sort_by,
    )
    return FeedbackListEnvelope(
        items=[FeedbackResponse.model_validate(i) for i in items],
        total=total,
        skip=skip,
        limit=effective_limit,
    )


@router.get(
    "/{item_id}",
    response_model=FeedbackResponse,
    summary="Get one feedback item",
)
def get_feedback(
    item_id: int,
    session: Annotated[Session, Depends(get_db)],
) -> FeedbackResponse:
    """Return a single feedback item or ``404``."""
    item = crud.get_item(session, item_id)
    if item is None:
        raise _not_found()
    return FeedbackResponse.model_validate(item)


@router.patch(
    "/{item_id}",
    response_model=FeedbackResponse,
    summary="Partially update a feedback item",
)
def patch_feedback(
    item_id: int,
    payload: FeedbackUpdate,
    session: Annotated[Session, Depends(get_db)],
) -> FeedbackResponse:
    """Apply a partial update; missing fields are left untouched."""
    item = crud.get_item(session, item_id)
    if item is None:
        raise _not_found()
    updated = crud.update_item(session, item, payload)
    return FeedbackResponse.model_validate(updated)


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a feedback item",
)
def delete_feedback(
    item_id: int,
    session: Annotated[Session, Depends(get_db)],
) -> Response:
    """Delete a feedback item; ``404`` if it doesn't exist."""
    item = crud.get_item(session, item_id)
    if item is None:
        raise _not_found()
    crud.delete_item(session, item)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
