"""``/api/v1/users/*`` JSON endpoints (PR 4.1).

Currently exposes a single endpoint — ``PATCH /api/v1/users/me`` —
that updates per-user UI preferences. The first preference is
``theme_preference``, stored on ``users.theme_preference`` and
written by the sidebar dark-mode toggle once a user is signed in.

The endpoint sits behind :data:`CurrentUserDep` so anonymous callers
see the standard ``not_authenticated`` envelope (the toggle still
works visually for them via ``localStorage``; the JS client only
calls this endpoint when a session cookie is present).

Spec: ``docs/project/spec/v2/auth.md`` — API surface,
``docs/project/spec/v2/css.md`` — theme tokens.
"""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session as DbSession

from feedback_triage.auth.deps import CurrentUserDep
from feedback_triage.auth.schemas import UserResponse
from feedback_triage.database import get_db

router = APIRouter(prefix="/api/v1/users", tags=["users"])

DbDep = Annotated[DbSession, Depends(get_db)]

#: Allowed values for ``users.theme_preference``. Mirrors the
#: ``users_theme_preference_valid`` CHECK constraint and the
#: ``[data-theme]`` selectors in ``static/css/tokens.css``.
ThemePreference = Literal["light", "dark", "system"]


class UserPreferencesUpdate(BaseModel):
    """Partial-update payload for :func:`patch_me`.

    Every field is optional; missing fields leave the column
    untouched. New preferences may be added in subsequent PRs without
    breaking older clients.
    """

    model_config = ConfigDict(extra="forbid")

    theme_preference: ThemePreference | None = None


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update the current user's preferences",
)
def patch_me(
    payload: UserPreferencesUpdate,
    user: CurrentUserDep,
    db: DbDep,
) -> UserResponse:
    """Apply a partial preferences update to the current user.

    The transaction boundary lives in :func:`get_db`; this handler
    only stages the change and flushes so the response can quote
    the post-update value back.
    """
    if payload.theme_preference is not None:
        user.theme_preference = payload.theme_preference

    db.add(user)
    db.flush()
    db.refresh(user)
    return UserResponse.model_validate(user)
