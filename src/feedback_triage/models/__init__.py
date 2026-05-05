"""SQLModel ORM models for the Feedback Triage App.

The current v1.0 schema ships a single ``feedback_item`` table whose
mapping lives in :mod:`feedback_triage.models.feedback`. This package
re-exports :class:`FeedbackItem` so the historical
``from feedback_triage.models import FeedbackItem`` import path keeps
working.

The split into a package (rather than a single ``models.py``) is
preparatory scaffolding for the v2.0 jump — see PR 1.3a / PR 1.3b in
``docs/project/spec/v2/implementation.md``. Empty stub modules
(``users``, ``sessions``, ``tokens``, ``workspaces``, ``memberships``,
``invitations``, ``auth_rate_limits``, ``email_log``) sit alongside
``feedback`` and are filled in by PR 1.3b together with the matching
Alembic Migration A.
"""

from __future__ import annotations

from feedback_triage.models.feedback import SOURCE_ENUM, STATUS_ENUM, FeedbackItem

__all__ = ["SOURCE_ENUM", "STATUS_ENUM", "FeedbackItem"]
