"""Look up or create a :class:`Submitter` for an inbound submission.

Anonymous submissions (no email) **never** create a submitter row —
the ``feedback_item.submitter_id`` is left ``NULL`` and the
inbox / detail pages render the row as "Anonymous". Submissions that
include an email dedupe by ``(workspace_id, email)`` per the
``submitters_workspace_email_uq`` unique constraint, increment
``submission_count``, and bump ``last_seen_at``.

This is one half of PR 2.4's deliverable; the other half is the
public form + rate-limit + honeypot in
:mod:`feedback_triage.api.v1.public_feedback`.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session as DbSession
from sqlmodel import col, select

from feedback_triage.models import Submitter


def link_or_create_submitter(
    db: DbSession,
    *,
    workspace_id: uuid.UUID,
    email: str | None,
    name: str | None,
    now: datetime | None = None,
) -> Submitter | None:
    """Return the submitter for ``(workspace_id, email)`` or ``None``.

    ``None`` is returned when ``email`` is missing — anonymous
    submissions don't create a submitter row.

    On a hit, ``submission_count`` is incremented, ``last_seen_at``
    is bumped to ``now``, and ``name`` is filled in if the existing
    row had it blank (we never overwrite a stored name with a fresh
    one from the form because the team may have curated it).
    """
    if not email:
        return None

    when = now or datetime.now(tz=UTC)
    row = db.execute(
        select(Submitter).where(
            col(Submitter.workspace_id) == workspace_id,
            col(Submitter.email) == email,
        ),
    ).scalar_one_or_none()

    if row is None:
        row = Submitter(
            workspace_id=workspace_id,
            email=email,
            name=name,
            submission_count=1,
            first_seen_at=when,
            last_seen_at=when,
        )
        db.add(row)
        db.flush()
        return row

    row.submission_count += 1
    row.last_seen_at = when
    if not row.name and name:
        row.name = name
    db.add(row)
    db.flush()
    return row
