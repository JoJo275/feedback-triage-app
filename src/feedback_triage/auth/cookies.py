"""Centralized cookie writer for auth.

Per ``docs/project/spec/v2/auth.md`` — Session cookie: **no other code
sets ``Set-Cookie``**. Routes call into this module so the cookie
attributes (``HttpOnly``, ``Secure``, ``SameSite=Lax``, ``Path``,
``Max-Age``) cannot drift between the create / renew / clear paths.
"""

from __future__ import annotations

from fastapi import Response

SESSION_COOKIE_NAME = "signalnest_session"
SESSION_COOKIE_PATH = "/"

# 7 days, in seconds. Kept here (not in ``sessions.py``) because the
# cookie's ``Max-Age`` and the DB row's ``expires_at`` are the same
# duration; the single source of truth lives next to the cookie writer.
SESSION_MAX_AGE_SECONDS = 7 * 24 * 60 * 60


def set_session_cookie(
    response: Response,
    *,
    raw_token: str,
    secure: bool,
) -> None:
    """Attach the session cookie to ``response``.

    ``raw_token`` is the un-hashed token returned by
    :func:`feedback_triage.auth.sessions.create_session`. The server
    keeps only ``sha256(raw_token)``; the raw value lives in this
    cookie and never in the DB.
    """
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=raw_token,
        max_age=SESSION_MAX_AGE_SECONDS,
        path=SESSION_COOKIE_PATH,
        secure=secure,
        httponly=True,
        samesite="lax",
    )


def clear_session_cookie(response: Response, *, secure: bool) -> None:
    """Remove the session cookie on logout.

    ``secure`` matches the value used at creation time so the same
    cookie identity is targeted; mismatched ``Secure`` would leave a
    second cookie behind on clients that respect the difference.
    """
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path=SESSION_COOKIE_PATH,
        secure=secure,
        httponly=True,
        samesite="lax",
    )
