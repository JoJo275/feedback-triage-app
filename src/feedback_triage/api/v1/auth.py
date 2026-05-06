"""``/api/v1/auth/*`` JSON endpoints.

Thin glue between the Pydantic schemas in
:mod:`feedback_triage.auth.schemas` and the auth primitives in
:mod:`feedback_triage.auth` (hashing, sessions, tokens, service).
The transaction boundary lives in ``get_db``; this module never opens
its own ``SessionLocal`` outside of the email client (which uses its
own session for the ``email_log`` write).

Email enumeration posture (``docs/project/spec/v2/auth.md``):
- ``signup`` returns the same 201 shape whether the email existed or
  not; the duplicate path triggers the *"you already have an account"*
  email instead of a verification email.
- ``forgot-password`` always returns 202 regardless of email existence.
- ``login`` returns 400 ``invalid credentials`` without distinguishing
  no-such-email from wrong-password.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession
from sqlmodel import col

from feedback_triage.auth import sessions as auth_sessions
from feedback_triage.auth import tokens as auth_tokens
from feedback_triage.auth.cookies import (
    clear_session_cookie,
    set_session_cookie,
)
from feedback_triage.auth.deps import CurrentUserDep, SessionCookieDep
from feedback_triage.auth.hashing import (
    hash_password,
    needs_rehash,
    verify_password,
)
from feedback_triage.auth.schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    MembershipResponse,
    MeResponse,
    ResendVerificationRequest,
    ResetPasswordRequest,
    SignupRequest,
    SignupResponse,
    UserResponse,
    VerifyEmailRequest,
    WorkspaceResponse,
)
from feedback_triage.auth.service import (
    list_memberships,
    signup_user,
)
from feedback_triage.config import Settings, get_settings
from feedback_triage.database import get_db
from feedback_triage.email import get_email_client
from feedback_triage.enums import EmailPurpose
from feedback_triage.models import User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

DbDep = Annotated[DbSession, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


_INVALID_CREDENTIALS = "Invalid email or password."
_ACCEPTED_BODY = {"status": "accepted"}


def _build_login_response(db: DbSession, user: User) -> LoginResponse:
    rows = list_memberships(db, user_id=user.id)  # type: ignore[arg-type]
    return LoginResponse(
        user=UserResponse.model_validate(user),
        memberships=[
            MembershipResponse(
                workspace_id=ws.id,  # type: ignore[arg-type]
                workspace_slug=ws.slug,
                workspace_name=ws.name,
                role=m.role,
            )
            for m, ws in rows
        ],
    )


def _verify_url(settings: Settings, raw_token: str) -> str:
    return f"{settings.app_base_url.rstrip('/')}/verify-email?token={raw_token}"


def _reset_url(settings: Settings, raw_token: str) -> str:
    return f"{settings.app_base_url.rstrip('/')}/reset-password?token={raw_token}"


# ---------------------------------------------------------------------------
# Signup
# ---------------------------------------------------------------------------


@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new account + first workspace",
)
def signup(
    payload: SignupRequest,
    db: DbDep,
    settings: SettingsDep,
) -> SignupResponse:
    """Create user + workspace + owner membership atomically.

    No-enumeration: a duplicate email returns the *same* 201 shape and
    triggers the ``verification_already`` email rather than the
    verification email. The two response bodies are byte-equivalent
    apart from row ids that already existed.
    """
    result = signup_user(
        db,
        email=payload.email,
        password=payload.password,
        workspace_name=payload.workspace_name,
    )

    raw_verify_token: str | None = None
    if not result.existed:
        issued = auth_tokens.mint_verification_token(
            db,
            user_id=result.user.id,  # type: ignore[arg-type]
        )
        raw_verify_token = issued.raw_token

    # The email client writes ``email_log`` on its own ``SessionLocal``
    # to survive a request rollback (ADR 061). That session sees only
    # *committed* rows, so the user / token rows the FK points at must
    # be flushed to disk before the send. Commit here and let
    # ``get_db`` see a no-op commit on the way out.
    db.commit()

    email_client = get_email_client()
    if result.existed:
        email_client.send(
            purpose=EmailPurpose.VERIFICATION,
            to=payload.email,
            context={
                "email": payload.email,
                "login_url": f"{settings.app_base_url.rstrip('/')}/login",
            },
            user_id=result.user.id,
            template_override="verification_already.html",
            subject_override="You already have a SignalNest account",
        )
    else:
        assert raw_verify_token is not None
        email_client.send(
            purpose=EmailPurpose.VERIFICATION,
            to=payload.email,
            context={
                "email": payload.email,
                "verification_url": _verify_url(settings, raw_verify_token),
            },
            user_id=result.user.id,
        )

    return SignupResponse(
        user=UserResponse.model_validate(result.user),
        workspace=WorkspaceResponse.model_validate(result.workspace),
    )


# ---------------------------------------------------------------------------
# Login / logout
# ---------------------------------------------------------------------------


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Exchange credentials for a session cookie",
)
def login(
    payload: LoginRequest,
    response: Response,
    db: DbDep,
    settings: SettingsDep,
) -> LoginResponse:
    """Issue a session cookie when credentials are valid; ``400`` otherwise.

    The 400 is shape-identical for ``no-such-email`` and
    ``wrong-password`` so the response cannot enumerate addresses.
    """
    user = db.execute(
        select(User).where(col(User.email) == payload.email),
    ).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_INVALID_CREDENTIALS,
        )

    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(payload.password)
        db.add(user)
        db.flush()

    issued = auth_sessions.create_session(db, user_id=user.id)  # type: ignore[arg-type]
    set_session_cookie(
        response,
        raw_token=issued.raw_token,
        secure=settings.secure_cookies,
    )
    return _build_login_response(db, user)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke the current session",
)
def logout(
    response: Response,
    db: DbDep,
    settings: SettingsDep,
    user: CurrentUserDep,
    raw_token: SessionCookieDep = None,
) -> Response:
    """Revoke the session row backing the current cookie and clear it."""
    del user  # ``current_user_required`` already validated; row id from cookie.
    if raw_token:
        session_row = auth_sessions.lookup_session(db, raw_token=raw_token)
        if session_row is not None:
            auth_sessions.revoke_session(db, session_id=session_row.id)  # type: ignore[arg-type]
    clear_session_cookie(response, secure=settings.secure_cookies)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.post(
    "/logout-everywhere",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke every session for the current user",
)
def logout_everywhere(
    response: Response,
    db: DbDep,
    settings: SettingsDep,
    user: CurrentUserDep,
) -> Response:
    """Revoke every live session for the caller and clear their cookie."""
    auth_sessions.revoke_all_sessions_for_user(db, user_id=user.id)  # type: ignore[arg-type]
    clear_session_cookie(response, secure=settings.secure_cookies)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


# ---------------------------------------------------------------------------
# Me
# ---------------------------------------------------------------------------


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Return the current user + their memberships",
)
def me(
    db: DbDep,
    user: CurrentUserDep,
) -> MeResponse:
    """Return the signed-in user and the workspaces they belong to."""
    rows = list_memberships(db, user_id=user.id)  # type: ignore[arg-type]
    return MeResponse(
        user=UserResponse.model_validate(user),
        memberships=[
            MembershipResponse(
                workspace_id=ws.id,  # type: ignore[arg-type]
                workspace_slug=ws.slug,
                workspace_name=ws.name,
                role=m.role,
            )
            for m, ws in rows
        ],
    )


# ---------------------------------------------------------------------------
# Email verification
# ---------------------------------------------------------------------------


@router.post(
    "/verify-email",
    summary="Consume an email-verification token",
)
def verify_email(
    payload: VerifyEmailRequest,
    db: DbDep,
) -> dict[str, str]:
    """Flip ``users.is_verified=true`` if the token is live, else 410."""
    status_, user_id = auth_tokens.consume_verification_token(
        db,
        raw_token=payload.token,
    )
    if status_ is not auth_tokens.TokenStatus.OK:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This verification link is no longer valid.",
        )
    assert user_id is not None
    user = db.get(User, user_id)
    if user is not None and not user.is_verified:
        user.is_verified = True
        db.add(user)
        db.flush()
    return {"status": "verified"}


@router.post(
    "/resend-verification",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Re-mail a verification token (no-enumeration)",
)
def resend_verification(
    payload: ResendVerificationRequest,
    db: DbDep,
    settings: SettingsDep,
    raw_token: SessionCookieDep = None,
) -> dict[str, str]:
    """Re-mail a verification token. Always returns 202.

    Resolves the target email from the session cookie when present,
    falling back to the body. Silent on every error path (unknown
    email, already-verified, rate-limit) — the user-facing copy on
    the page acknowledges the request without confirming the address.
    """
    target_user: User | None = None
    if raw_token:
        sess = auth_sessions.lookup_session(db, raw_token=raw_token)
        if sess is not None:
            target_user = db.get(User, sess.user_id)
    if target_user is None and payload.email is not None:
        target_user = db.execute(
            select(User).where(col(User.email) == payload.email),
        ).scalar_one_or_none()

    if target_user is not None and not target_user.is_verified:
        issued = auth_tokens.mint_verification_token(
            db,
            user_id=target_user.id,  # type: ignore[arg-type]
        )
        # See signup() for the commit-before-send rationale.
        db.commit()
        get_email_client().send(
            purpose=EmailPurpose.VERIFICATION,
            to=target_user.email,
            context={
                "email": target_user.email,
                "verification_url": _verify_url(settings, issued.raw_token),
            },
            user_id=target_user.id,
        )
    return _ACCEPTED_BODY


# ---------------------------------------------------------------------------
# Password reset
# ---------------------------------------------------------------------------


@router.post(
    "/forgot-password",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request a password-reset email (no-enumeration)",
)
def forgot_password(
    payload: ForgotPasswordRequest,
    db: DbDep,
    settings: SettingsDep,
) -> dict[str, str]:
    """Always returns 202. Mints + emails a token only if the email exists."""
    user = db.execute(
        select(User).where(col(User.email) == payload.email),
    ).scalar_one_or_none()
    if user is not None:
        issued = auth_tokens.mint_password_reset_token(
            db,
            user_id=user.id,  # type: ignore[arg-type]
        )
        # See signup() for the commit-before-send rationale.
        db.commit()
        get_email_client().send(
            purpose=EmailPurpose.PASSWORD_RESET,
            to=user.email,
            context={
                "email": user.email,
                "reset_url": _reset_url(settings, issued.raw_token),
            },
            user_id=user.id,
        )
    return _ACCEPTED_BODY


@router.post(
    "/reset-password",
    summary="Consume a password-reset token + set a new password",
)
def reset_password(
    payload: ResetPasswordRequest,
    db: DbDep,
) -> dict[str, str]:
    """Set a new password and revoke every session for the user.

    Per ``auth.md`` state machine, a successful reset revokes
    **every** session (including the active one) — the assumption is
    account compromise; the user logs in fresh.
    """
    status_, user_id = auth_tokens.consume_password_reset_token(
        db,
        raw_token=payload.token,
    )
    if status_ is not auth_tokens.TokenStatus.OK:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This reset link is no longer valid.",
        )
    assert user_id is not None
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This reset link is no longer valid.",
        )
    user.password_hash = hash_password(payload.new_password)
    db.add(user)
    auth_sessions.revoke_all_sessions_for_user(db, user_id=user.id)  # type: ignore[arg-type]
    db.flush()
    return {"status": "reset"}


@router.post(
    "/change-password",
    summary="Change password while signed in",
)
def change_password(
    payload: ChangePasswordRequest,
    response: Response,
    db: DbDep,
    settings: SettingsDep,
    user: CurrentUserDep,
    raw_token: SessionCookieDep = None,
) -> dict[str, str]:
    """Verify the old password, write the new hash, revoke siblings.

    Per ``auth.md``: revokes every session **other than** the one the
    request came from — the user keeps their cookie.
    """
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )
    user.password_hash = hash_password(payload.new_password)
    db.add(user)

    keep_session_id = None
    if raw_token:
        sess = auth_sessions.lookup_session(db, raw_token=raw_token)
        if sess is not None:
            keep_session_id = sess.id
    auth_sessions.revoke_all_sessions_for_user(
        db,
        user_id=user.id,  # type: ignore[arg-type]
        except_session_id=keep_session_id,
    )
    db.flush()
    # Re-set the cookie so the client-side ``Max-Age`` stays in sync.
    if raw_token:
        set_session_cookie(
            response,
            raw_token=raw_token,
            secure=settings.secure_cookies,
        )
    return {"status": "changed"}
