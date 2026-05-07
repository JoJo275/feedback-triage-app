"""Extend ``email_status_enum`` with the Resend-webhook terminal states.

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-07

PR 4.3 — Resend webhook ingestion. Adds three values to
``email_status_enum`` so the webhook handler can map provider events
onto the existing ``email_log.status`` column without inventing a
parallel table:

- ``delivered``  — Resend's ``email.delivered`` event (terminal,
  positive).
- ``bounced``    — ``email.bounced`` (terminal, negative; SMTP
  refused or the inbox does not exist).
- ``complained`` — ``email.complained`` (terminal; recipient hit
  the "report spam" button).

Each ``ALTER TYPE … ADD VALUE`` runs in its own ``autocommit_block``
because Postgres forbids mixing enum mutations with other DDL inside
the same transaction. Adding values is purely additive: existing rows
keep their current status, and the in-process send loop continues to
only ever write ``queued`` / ``sent`` / ``retrying`` / ``failed``.

Downgrade is a no-op — Postgres does not support
``ALTER TYPE … DROP VALUE``. Rolling back this migration is therefore
safe for the schema (the new values simply remain unused) and we
intentionally do not synthesise a rebuild-the-type ceremony for it.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0007"
down_revision: str | Sequence[str] | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


NEW_EMAIL_STATUS_VALUES = ("delivered", "bounced", "complained")


def upgrade() -> None:
    for value in NEW_EMAIL_STATUS_VALUES:
        with op.get_context().autocommit_block():
            op.execute(
                f"ALTER TYPE email_status_enum ADD VALUE IF NOT EXISTS '{value}'",
            )


def downgrade() -> None:
    # Postgres does not support ``ALTER TYPE … DROP VALUE``. Leaving
    # the values in place is harmless — application code never writes
    # them when the webhook route is unmounted (no
    # ``RESEND_WEBHOOK_SECRET`` configured).
    pass
