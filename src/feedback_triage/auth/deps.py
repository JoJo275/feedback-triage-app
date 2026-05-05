"""FastAPI dependencies for the auth surface.

Three request-scoped dependencies are exposed:

- :func:`current_user_optional` - returns the :class:`User` for the
  caller's session cookie, or ``None`` if anonymous / expired /
  revoked. Used by routes that render differently for signed-in users
  but do not require a session.
- :func:`current_user_required` - same lookup, but raises ``401`` when
  no session is present. The default for protected JSON endpoints.
- :func:`require_role` - dependency *factory* that returns a callable
  rejecting any user whose ``role`` is not in the allow-list. Used by
  admin-only routes.

Both ``current_user_*`` dependencies perform sliding-window
``last_seen_at`` renewal (auth.md - last_seen_at write cadence) and
re-set the session cookie with a fresh ``Max-Age`` so the cookie's
client-side expiry matches the server-side ``expires_at``.

The auth surface is gated behind ``settings.feature_auth``: when the
flag is off (v2.0-alpha pre-launch), the ``current_user_*`` deps
behave as if every caller were anonymous, and ``current_user_required``
raises ``503``. The HTTP route layer (PR 1.7) gates ``/login`` etc.
with the same flag - see ``docs/project/spec/v2/auth.md`` - Feature flag.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session as DbSession

from feedback_triage.auth import sessions
from feedback_triage.auth.cookies import (
    SESSION_COOKIE_NAME,
    set_session_cookie,
)
from feedback_triage.config import Settings, get_settings
from feedback_triage.database import get_db
from feedback_triage.enums import UserRole
from feedback_triage.models import User, UserSession

DbDep = Annotated[DbSession, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionCookieDep = Annotated[
    str | None,
    Cookie(default=None, alias=SESSION_COOKIE_NAME),
]


def _slide_cookie_and_session(
    *,
    db: DbSession,
    response: Response,
    raw_token: str,
    user_session: UserSession,
    secure: bool,
) -> None:
    """Run the sliding-renewal write + re-set the cookie.

    The DB row is updated at most once per 5 minutes (cadence handled
    by :func:`sessions.renew_if_stale`); the cookie is re-set on every
    authenticated request because re-setting is free and keeps the
    client-side expiry honest even when the DB write was skipped.
    """
    sessions.renew_if_stale(db, user_session)
    set_session_cookie(response, raw_token=raw_token, secure=secure)


def current_user_optional(
    response: Response,
    db: DbDep,
    settings: SettingsDep,
    raw_token: SessionCookieDep,
) -> User | None:
    """Return the :class:`User` for the caller's session, or ``None``."""
    if not settings.feature_auth or not raw_token:
        return None
    user_session = sessions.lookup_session(db, raw_token=raw_token)
    if user_session is None:
        return None
    user = db.get(User, user_session.user_id)
    if user is None:
        return None
    _slide_cookie_and_session(
        db=db,
        response=response,
        raw_token=raw_token,
        user_session=user_session,
        secure=settings.secure_cookies,
    )
    return user


CurrentUserOptionalDep = Annotated[User | None, Depends(current_user_optional)]


def current_user_required(
    user: CurrentUserOptionalDep,
    settings: SettingsDep,
) -> User:
    """Return the current :class:`User` or raise ``401``.

    The ``WWW-Authenticate`` header is **not** set: we are not using
    HTTP auth, and including it would invite a browser auth dialog on
    a missing-cookie failure.
    """
    if not settings.feature_auth:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Sign-in is launching soon.",
        )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )
    return user


CurrentUserDep = Annotated[User, Depends(current_user_required)]


def require_role(*allowed: UserRole) -> Callable[[User], User]:
    """Return a dependency that 403s users outside ``allowed``.

    Usage::

        @router.get(
            "/admin/things",
            dependencies=[Depends(require_role(UserRole.ADMIN))],
        )

    The factory shape (rather than a single dependency that reads the
    role from a closure) is so callers can mix-and-match roles per
    route without subclassing.
    """
    allowed_set: frozenset[UserRole] = frozenset(_coerce_roles(allowed))

    def _dep(user: CurrentUserDep) -> User:
        if user.role not in allowed_set:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient privileges.",
            )
        return user

    return _dep


def _coerce_roles(roles: Iterable[UserRole | str]) -> Iterable[UserRole]:
    """Accept either ``UserRole`` enum members or their string values.

    Defensive helper - keeps caller sites readable when a role list is
    pulled from config.
    """
    for r in roles:
        yield r if isinstance(r, UserRole) else UserRole(r)
