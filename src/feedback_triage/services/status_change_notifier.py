"""Status-change → submitter email notifier (PR 3.1).

Hooks ``feedback_item.status`` transitions: when an item moves into a
status configured by ``EMAIL_NOTIFY_ON_STATUSES`` (default
``shipped``), this module resolves the linked submitter's email and
asks :class:`feedback_triage.email.client.EmailClient` to send a
``status_change.html`` notification.

Fail-soft contract from ADR 061 applies — :meth:`EmailClient.send`
swallows provider errors after writing a terminal ``email_log`` row,
so the originating PATCH never sees provider state. Items without a
linked submitter (``submitter_id IS NULL``) or with an anonymous
submitter (``submitters.email IS NULL``) silently skip the send.

Spec: ``docs/project/spec/v2/email.md``,
``docs/project/spec/v2/implementation.md`` — PR 3.1.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session as DbSession

from feedback_triage.config import Settings
from feedback_triage.email import get_email_client
from feedback_triage.email.client import EmailClient
from feedback_triage.enums import EmailPurpose, Status
from feedback_triage.models import FeedbackItem, Submitter, Workspace

logger = logging.getLogger(__name__)


def notify_status_change(
    *,
    db: DbSession,
    settings: Settings,
    item: FeedbackItem,
    old_status: Status,
    new_status: Status,
    email_client: EmailClient | None = None,
) -> None:
    """Send a status-change email if policy + recipient allow it.

    No-op (returns silently) when:

    - ``old_status == new_status`` — PATCH didn't move the row.
    - ``new_status`` is not in
      :attr:`Settings.notify_on_statuses`.
    - The item has no ``submitter_id`` (team-authored row).
    - The submitter row has ``email IS NULL`` (anonymous public
      submission per ``v2/email.md``).
    """
    if old_status == new_status:
        return
    if new_status.value not in settings.notify_on_statuses:
        return
    if item.submitter_id is None:
        return

    submitter = db.get(Submitter, item.submitter_id)
    if submitter is None or not submitter.email:
        return

    workspace = db.get(Workspace, item.workspace_id)
    workspace_name = workspace.name if workspace is not None else None

    client = email_client if email_client is not None else get_email_client()

    base = settings.app_base_url.rstrip("/")
    changelog_url = (
        f"{base}/w/{workspace.slug}/changelog/public"
        if workspace is not None and new_status is Status.SHIPPED
        else None
    )

    context = {
        "workspace_name": workspace_name,
        "feedback_title": item.title,
        "status_label": _status_label(new_status),
        "release_note": item.release_note,
        "changelog_url": changelog_url,
    }

    subject = _subject_for(workspace_name, new_status)

    client.send(
        purpose=EmailPurpose.STATUS_CHANGE,
        to=submitter.email,
        context=context,
        workspace_id=item.workspace_id,
        subject_override=subject,
    )


def _status_label(status: Status) -> str:
    """Human-readable label for the status surfaced in email copy."""
    return {
        Status.ACCEPTED: "accepted",
        Status.PLANNED: "planned",
        Status.IN_PROGRESS: "in progress",
        Status.SHIPPED: "shipped",
    }.get(status, status.value.replace("_", " "))


def _subject_for(workspace_name: str | None, status: Status) -> str:
    """Inbox-friendly subject line; carries the new status verbatim."""
    label = _status_label(status)
    if workspace_name:
        return f"[{workspace_name}] Your feedback is now {label}"
    return f"Your feedback is now {label}"
