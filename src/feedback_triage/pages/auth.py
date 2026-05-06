"""Page routes for the v2.0 auth flow.

Each route serves a Jinja-rendered shell that POSTs to its
``/api/v1/auth/*`` counterpart via ``static/js/auth.js``. The pages
read query-string tokens (``?token=...``) for verify-email and
reset-password and pass them to the JS layer via a hidden ``<input>``.

Per [ADR 014](../../../docs/adr/014-no-template-engine.md) (v2.0
amendment), Jinja is allowed for application HTML in v2.0 — the
``_base.html`` skeleton + Tailwind pipeline is shared with
``/styleguide``. v1.0 pages remain static for now (they're owned by
:mod:`feedback_triage.routes.pages` and migrated case-by-case).
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from feedback_triage.templating import templates

router = APIRouter(include_in_schema=False)


@router.get("/login", summary="Sign-in page")
def login_page(request: Request) -> HTMLResponse:
    """Render the sign-in form."""
    return templates.TemplateResponse(request, "pages/auth/login.html")


@router.get("/signup", summary="Sign-up page")
def signup_page(request: Request) -> HTMLResponse:
    """Render the sign-up form."""
    return templates.TemplateResponse(request, "pages/auth/signup.html")


@router.get("/forgot-password", summary="Forgot-password page")
def forgot_password_page(request: Request) -> HTMLResponse:
    """Render the forgot-password form."""
    return templates.TemplateResponse(
        request,
        "pages/auth/forgot_password.html",
    )


@router.get("/reset-password", summary="Reset-password page")
def reset_password_page(request: Request) -> HTMLResponse:
    """Render the reset-password form (token comes from ``?token=``)."""
    token = request.query_params.get("token", "")
    return templates.TemplateResponse(
        request,
        "pages/auth/reset_password.html",
        {"token": token},
    )


@router.get("/verify-email", summary="Verify-email page")
def verify_email_page(request: Request) -> HTMLResponse:
    """Render the verify-email landing page (token from ``?token=``)."""
    token = request.query_params.get("token", "")
    return templates.TemplateResponse(
        request,
        "pages/auth/verify_email.html",
        {"token": token},
    )


@router.get("/invitations/{token}", summary="Accept-invitation page")
def invitation_page(request: Request, token: str) -> HTMLResponse:
    """Render the accept-invitation page.

    Workspace invitation acceptance requires a session, so this page
    pushes the user to ``/login?next=...`` when they're anonymous.
    The actual ``POST /api/v1/invitations/{token}/accept`` lives in
    PR 1.8.
    """
    return templates.TemplateResponse(
        request,
        "pages/auth/invitation.html",
        {"token": token},
    )
