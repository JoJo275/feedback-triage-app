"""ASGI middleware: request IDs and structured request logging.

The stack is intentionally tiny:

* :class:`RequestIDMiddleware` accepts an inbound ``X-Request-ID`` header
  or mints a new UUID4. The ID is stashed on ``request.state.request_id``
  so handlers and exception handlers can echo it, and is also written
  back as a response header.
* :class:`RequestLoggingMiddleware` emits one log line per request with
  the method, path, status code, duration, and request ID. Format
  switches to JSON when ``APP_ENV=production``.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from starlette.requests import Request
    from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"

logger = logging.getLogger("feedback_triage.access")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach an ``X-Request-ID`` to every request and response."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Set ``request.state.request_id`` and echo the header back."""
        incoming = request.headers.get(REQUEST_ID_HEADER)
        request_id = incoming or uuid.uuid4().hex
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Emit one structured log line per HTTP request."""

    def __init__(self, app: ASGIApp, *, json_format: bool = False) -> None:
        """Initialize the middleware.

        Args:
            app: The wrapped ASGI app.
            json_format: When True, emit the access log line as JSON;
                otherwise emit a short human-readable line.
        """
        super().__init__(app)
        self._json = json_format

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Time the downstream call and log the outcome."""
        start = time.perf_counter()
        try:
            response = await call_next(request)
            status = response.status_code
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            self._log(request, status=500, duration_ms=duration_ms)
            raise
        duration_ms = (time.perf_counter() - start) * 1000
        self._log(request, status=status, duration_ms=duration_ms)
        return response

    def _log(self, request: Request, *, status: int, duration_ms: float) -> None:
        request_id = getattr(request.state, "request_id", "")
        payload = {
            "method": request.method,
            "path": request.url.path,
            "status": status,
            "duration_ms": round(duration_ms, 2),
            "request_id": request_id,
        }
        if self._json:
            logger.info(json.dumps(payload, separators=(",", ":")))
        else:
            logger.info(
                "%s %s -> %d (%.2fms) request_id=%s",
                payload["method"],
                payload["path"],
                payload["status"],
                duration_ms,
                request_id,
            )
