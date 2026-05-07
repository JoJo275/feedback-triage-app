"""Idempotent ``email_log`` post-send-status updater (PR 4.3).

The Resend webhook handler at
:mod:`feedback_triage.api.v1.webhooks.resend` translates each
incoming event into a single call to :func:`apply_provider_event`,
which finds the matching ``email_log`` row by ``provider_id`` and
moves its ``status`` to one of the post-send terminal values:
``delivered`` / ``bounced`` / ``complained``.

Idempotency contract — Resend (like every Standard-Webhooks
provider) retries on non-2xx responses and may also redeliver the
same event to recover from receiver outages. The updater therefore:

* matches on ``provider_id`` (Resend's ``email.id``); a missing row
  returns :data:`EmailLogUpdateOutcome.NOT_FOUND` instead of raising,
  so verification / reset sends that pre-date the webhook secret
  rollout do not 500 the receiver and trigger a redelivery storm;
* never regresses a row — once a row is ``delivered`` we ignore a
  late ``bounced`` (or vice-versa); the event-ordering table below
  is the canonical precedence.

Precedence (highest → lowest):

1. ``complained`` — recipient marked the message as spam.
2. ``bounced``    — provider permanently failed delivery.
3. ``delivered``  — message reached the inbox.

Higher-precedence states never roll back to lower-precedence states;
lower-precedence events arriving after a higher-precedence event are
ignored (returns :data:`EmailLogUpdateOutcome.IGNORED`).
"""

from __future__ import annotations

import logging
from enum import StrEnum

from sqlalchemy.orm import Session as DbSession
from sqlmodel import col, select

from feedback_triage.enums import EmailStatus
from feedback_triage.models import EmailLog

logger = logging.getLogger(__name__)


_POST_SEND_PRECEDENCE: dict[EmailStatus, int] = {
    EmailStatus.DELIVERED: 1,
    EmailStatus.BOUNCED: 2,
    EmailStatus.COMPLAINED: 3,
}


class EmailLogUpdateOutcome(StrEnum):
    """Result of :func:`apply_provider_event`.

    Surfaced to the webhook handler so it can emit a structured log
    line (and decide an HTTP status) without re-querying the row.
    """

    UPDATED = "updated"
    IGNORED = "ignored"
    NOT_FOUND = "not_found"


def apply_provider_event(
    db: DbSession,
    *,
    provider_id: str,
    new_status: EmailStatus,
) -> EmailLogUpdateOutcome:
    """Apply ``new_status`` to the ``email_log`` row keyed by ``provider_id``.

    Args:
        db: SQLAlchemy session (caller owns commit / rollback).
        provider_id: Resend ``email.id`` from the webhook payload.
        new_status: Mapped :class:`EmailStatus` (one of
            ``DELIVERED`` / ``BOUNCED`` / ``COMPLAINED``).

    Returns:
        :class:`EmailLogUpdateOutcome` — ``UPDATED`` if the row moved,
        ``IGNORED`` if a higher-precedence terminal state already
        held, or ``NOT_FOUND`` if no row matches.

    Raises:
        ValueError: if ``new_status`` is not one of the post-send
            terminal values. The webhook handler maps unsupported
            event types before calling, so this is a programmer
            error, not a runtime one.
    """
    if new_status not in _POST_SEND_PRECEDENCE:
        msg = (
            f"apply_provider_event called with non-post-send status "
            f"{new_status.value!r}; expected one of "
            f"{[s.value for s in _POST_SEND_PRECEDENCE]}"
        )
        raise ValueError(msg)

    row = db.execute(
        select(EmailLog).where(col(EmailLog.provider_id) == provider_id),
    ).scalar_one_or_none()
    if row is None:
        logger.info(
            "resend.webhook.no_match provider_id=%s status=%s",
            provider_id,
            new_status.value,
        )
        return EmailLogUpdateOutcome.NOT_FOUND

    incoming_rank = _POST_SEND_PRECEDENCE[new_status]
    current_rank = _POST_SEND_PRECEDENCE.get(row.status, 0)
    if current_rank >= incoming_rank:
        logger.info(
            "resend.webhook.ignored log_id=%s current=%s incoming=%s",
            row.id,
            row.status.value,
            new_status.value,
        )
        return EmailLogUpdateOutcome.IGNORED

    row.status = new_status
    db.add(row)
    db.flush()
    logger.info(
        "resend.webhook.updated log_id=%s status=%s",
        row.id,
        new_status.value,
    )
    return EmailLogUpdateOutcome.UPDATED
