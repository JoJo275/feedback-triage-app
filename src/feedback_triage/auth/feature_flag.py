"""``FEATURE_AUTH`` startup gate.

Per ``docs/project/spec/v2/auth.md`` and PR 1.9 in
``docs/project/spec/v2/implementation.md``: when ``FEATURE_AUTH`` is
false the v2 auth surface is dormant — ``/api/v1/auth/*`` returns
``503 Service Unavailable`` and the auth page routes (``/login``,
``/signup``, ``/forgot-password``, ``/reset-password``,
``/verify-email``, ``/invitations/<token>``) render a "coming soon"
notice with the same status code.

The flag is read once at startup; flipping it requires a redeploy.
That contract is what lets us gate via a single middleware rather
than wiring a dependency into every endpoint.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from feedback_triage.templating import templates

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from starlette.requests import Request
    from starlette.responses import Response

_API_PREFIX = "/api/v1/auth"
_PAGE_PATHS = frozenset(
    {
        "/login",
        "/signup",
        "/forgot-password",
        "/reset-password",
        "/verify-email",
    },
)
_INVITATION_PAGE_PREFIX = "/invitations/"

_API_BODY = {
    "detail": (
        "Authentication is not enabled on this deployment. "
        "Set FEATURE_AUTH=true and redeploy."
    ),
}


class FeatureAuthGateMiddleware(BaseHTTPMiddleware):
    """Short-circuit the v2 auth surface when ``FEATURE_AUTH`` is off."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Return 503 for gated paths; pass everything else through."""
        path = request.url.path
        if path.startswith(_API_PREFIX):
            return JSONResponse(_API_BODY, status_code=503)
        if path in _PAGE_PATHS or path.startswith(_INVITATION_PAGE_PREFIX):
            return templates.TemplateResponse(
                request,
                "pages/auth/coming_soon.html",
                status_code=503,
            )
        return await call_next(request)
