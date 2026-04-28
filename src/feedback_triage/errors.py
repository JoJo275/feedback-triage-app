"""Global exception handlers for the FastAPI app.

Every error response is shaped as ``{"detail": ..., "request_id": ...}``
so a 500 logged on the server can be cross-referenced against what the
client saw. Stack traces are *never* leaked in the response body; they
are emitted on the server log at ``ERROR`` level instead.

See spec — Error Handling and implementation plan — Phase 5.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from feedback_triage.middleware import REQUEST_ID_HEADER, get_request_id

if TYPE_CHECKING:
    from fastapi import FastAPI, Request

_GENERIC_500_DETAIL = "Internal server error"

logger = logging.getLogger("feedback_triage.errors")


def _request_id_for(request: Request) -> str:
    """Resolve the request ID from ``request.state`` or the contextvar."""
    return getattr(request.state, "request_id", "") or get_request_id()


def _error_response(
    request: Request,
    *,
    status_code: int,
    detail: Any,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Build the standard error envelope and pin the request-id header."""
    request_id = _request_id_for(request)
    merged: dict[str, str] = dict(headers or {})
    if request_id:
        merged[REQUEST_ID_HEADER] = request_id
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail, "request_id": request_id},
        headers=merged or None,
    )


async def http_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Return the standard error envelope for any ``HTTPException``."""
    assert isinstance(exc, StarletteHTTPException)
    return _error_response(
        request,
        status_code=exc.status_code,
        detail=exc.detail,
        headers=getattr(exc, "headers", None),
    )


async def validation_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Return a 422 with the Pydantic error list and the request ID."""
    assert isinstance(exc, RequestValidationError)
    return _error_response(
        request,
        status_code=422,
        detail=jsonable_encoder(exc.errors()),
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Log the stack trace and return a generic 500 to the client."""
    logger.exception(
        "Unhandled exception on %s %s",
        request.method,
        request.url.path,
        exc_info=exc,
    )
    return _error_response(
        request,
        status_code=500,
        detail=_GENERIC_500_DETAIL,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Wire the standard handlers onto a :class:`FastAPI` instance."""
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
