"""SQLModel ORM model for the ``email_log`` table.

**Stub.** Filled in by PR 1.3b alongside Migration A. Records every
outbound transactional email and its delivery status (``email_status_enum``)
and purpose (``email_purpose_enum``); see ADR 061 (Resend, fail-soft) and
``docs/project/spec/v2/email.md``.
"""

from __future__ import annotations
