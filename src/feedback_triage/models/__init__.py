"""SQLModel ORM models for the Feedback Triage App.

The v1.0 schema's single ``feedback_item`` table mapping lives in
:mod:`feedback_triage.models.feedback`. The v2.0 jump introduces auth,
tenancy, and email-log tables across several sibling modules; PR 1.3b
fills those in alongside Alembic Migration A
(``alembic/versions/0002_v2_a_auth_tenancy_email_log.py``).

This package re-exports every ORM class so the historical
``from feedback_triage.models import FeedbackItem`` import path keeps
working and so ``alembic/env.py`` populates ``SQLModel.metadata`` with
a single ``import feedback_triage.models``.
"""

from __future__ import annotations

from feedback_triage.models.auth_rate_limits import AuthRateLimit
from feedback_triage.models.email_log import EmailLog
from feedback_triage.models.feedback import SOURCE_ENUM, STATUS_ENUM, FeedbackItem
from feedback_triage.models.invitations import WorkspaceInvitation
from feedback_triage.models.memberships import WorkspaceMembership
from feedback_triage.models.sessions import UserSession
from feedback_triage.models.tokens import EmailVerificationToken, PasswordResetToken
from feedback_triage.models.users import User
from feedback_triage.models.workspaces import Workspace

__all__ = [
    "SOURCE_ENUM",
    "STATUS_ENUM",
    "AuthRateLimit",
    "EmailLog",
    "EmailVerificationToken",
    "FeedbackItem",
    "PasswordResetToken",
    "User",
    "UserSession",
    "Workspace",
    "WorkspaceInvitation",
    "WorkspaceMembership",
]
