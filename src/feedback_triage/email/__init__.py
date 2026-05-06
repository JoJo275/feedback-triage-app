"""Transactional email surface (PR 1.6 / v2.0-alpha).

Owns the Resend HTTP wrapper, the fail-soft retry loop, and the
``email_log`` writes that back every send attempt. The HTTP routes
that *call* this surface (``/api/v1/auth/*``) land in PR 1.7; the
status-change template + send path lands in PR 3.1.

Canonical contract: ADR 061 and ``docs/project/spec/v2/email.md``.
"""

from __future__ import annotations

from feedback_triage.email.client import (
    EmailClient,
    EmailSendResult,
    get_email_client,
)

__all__ = [
    "EmailClient",
    "EmailSendResult",
    "get_email_client",
]
