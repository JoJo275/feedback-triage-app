"""Public, unauthenticated feedback submission endpoint (PR 2.4).

Mounted at ``/api/v1/public/feedback/{slug}``. The only write surface
in v2.0 that does not require a session cookie. All three security
guards in the spec live here and are tested as deliverables of this
PR, not as follow-ups:

* **Honeypot** -- the form ships a hidden ``website`` text field that
  legitimate submissions leave blank. Filled-in honeypot returns the
  same 200 envelope as the happy path so a bot can't probe for
  detection, but no row is written.
* **Rate limit** -- per ``(workspace_id, ip)`` bucket, fixed 60s
  window, max 5 submissions. Tripped requests return 429 with the
  ``code=rate_limited`` envelope from the error catalog.
* **Slug isolation** -- an unknown / mistyped slug returns 404 with
  the same shape as a private cross-tenant 404; we never confirm
  workspace existence to anonymous callers via a different status.

Submitter dedupe is delegated to
:func:`feedback_triage.services.submitter_link.link_or_create_submitter`;
rate limiting to :func:`feedback_triage.services.rate_limit.check_and_increment`.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from sqlalchemy.orm import Session as DbSession
from sqlmodel import col, select

from feedback_triage.database import get_db
from feedback_triage.enums import FeedbackType, Source, Status
from feedback_triage.models import FeedbackItem, Workspace
from feedback_triage.services.rate_limit import check_and_increment
from feedback_triage.services.submitter_link import link_or_create_submitter

router = APIRouter(prefix="/api/v1/public", tags=["public"])

DbDep = Annotated[DbSession, Depends(get_db)]

# Tunable. Five submissions / minute / IP / workspace is enough head-
# room for a real user filling the form twice and noticing a typo,
# while still capping a naive bot at one row before throttling.
PUBLIC_SUBMIT_LIMIT = 5
PUBLIC_SUBMIT_WINDOW_SECONDS = 60

# Sources that an anonymous public submitter is allowed to claim.
# Internal sources (``support``, ``interview``) are team-only.
_ALLOWED_PUBLIC_SOURCES: frozenset[Source] = frozenset(
    {Source.WEB_FORM, Source.EMAIL, Source.OTHER},
)

_NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail={"code": "not_found", "message": "Workspace not found."},
)
_RATE_LIMITED = HTTPException(
    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    detail={
        "code": "rate_limited",
        "message": (
            "Too many submissions from this address. Wait a minute and try again."
        ),
    },
)
_ACCEPTED_BODY: dict[str, object] = {"status": "accepted"}


class PublicFeedbackCreate(BaseModel):
    """Request body for ``POST /api/v1/public/feedback/{slug}``.

    Note ``website`` -- the honeypot. A legitimate browser submission
    leaves it untouched; bots that auto-fill every visible input
    will populate it and trip the silent-discard branch.
    """

    model_config = ConfigDict(extra="forbid")

    title: Annotated[str, Field(min_length=1, max_length=200)]
    description: Annotated[str | None, Field(default=None, max_length=5000)] = None
    source: Source = Source.WEB_FORM
    source_other: Annotated[str | None, Field(default=None, max_length=60)] = None
    pain_level: Annotated[int, Field(ge=1, le=5)]
    type: FeedbackType = FeedbackType.OTHER
    type_other: Annotated[str | None, Field(default=None, max_length=60)] = None
    submitter_email: EmailStr | None = None
    submitter_name: Annotated[str | None, Field(default=None, max_length=120)] = None
    website: Annotated[str, Field(default="", max_length=200)] = ""

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title must not be blank")
        return value

    @field_validator("source")
    @classmethod
    def _public_source_only(cls, value: Source) -> Source:
        if value not in _ALLOWED_PUBLIC_SOURCES:
            msg = "source must be one of: " + ", ".join(
                sorted(s.value for s in _ALLOWED_PUBLIC_SOURCES)
            )
            raise ValueError(msg)
        return value


def _client_ip(request: Request) -> str:
    """Best-effort client IP for the rate-limit bucket key.

    Honours ``X-Forwarded-For`` (Railway terminates TLS at its edge
    proxy) but falls back to the direct peer if the header is absent
    or empty. Splitting on ``,`` and taking the first value matches
    the convention in ``docs/project/spec/v2/security.md``.
    """
    forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    if forwarded:
        return forwarded
    if request.client is not None:
        return request.client.host
    return "unknown"


@router.post(
    "/feedback/{slug}",
    status_code=status.HTTP_201_CREATED,
    summary="Public, unauthenticated feedback submission",
)
def submit_public_feedback(
    slug: str,
    payload: PublicFeedbackCreate,
    request: Request,
    db: DbDep,
) -> dict[str, object]:
    """Create a feedback item from an anonymous public submitter."""
    workspace = db.execute(
        select(Workspace).where(col(Workspace.slug) == slug),
    ).scalar_one_or_none()
    if workspace is None:
        raise _NOT_FOUND

    # Honeypot tripped: 200 with the same envelope a real success
    # would return. Never 4xx -- leaks detection signal to bots.
    if payload.website.strip():
        return _ACCEPTED_BODY

    bucket_key = f"public_submit:{workspace.id}:{_client_ip(request)}"
    decision = check_and_increment(
        db,
        bucket_key=bucket_key,
        limit=PUBLIC_SUBMIT_LIMIT,
        window_seconds=PUBLIC_SUBMIT_WINDOW_SECONDS,
    )
    if not decision.allowed:
        raise _RATE_LIMITED

    submitter = link_or_create_submitter(
        db,
        workspace_id=workspace.id,  # type: ignore[arg-type]
        email=payload.submitter_email,
        name=payload.submitter_name,
    )
    item = FeedbackItem(
        workspace_id=workspace.id,
        submitter_id=submitter.id if submitter is not None else None,
        title=payload.title,
        description=payload.description,
        source=payload.source,
        source_other=payload.source_other,
        pain_level=payload.pain_level,
        type=payload.type,
        type_other=payload.type_other,
        status=Status.NEW,
    )
    db.add(item)
    db.flush()
    return {"status": "accepted", "id": item.id}
