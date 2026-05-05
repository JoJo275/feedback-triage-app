"""Domain enums for the Feedback Triage App.

Single source of truth for ``source`` and ``status`` values. Imported by
both the SQLModel model (`models.py`) and the request/response schemas
(`schemas.py`) so Pydantic validation, the ORM, and the native Postgres
enum types in `source_enum` / `status_enum` cannot drift apart.

The string values here MUST match the Postgres enum labels created in
the first Alembic migration. Renaming a member without a planned
data-migration is a breaking change — see spec — Enum migration policy.
"""

from __future__ import annotations

from enum import StrEnum


class Source(StrEnum):
    """Where a feedback item originated."""

    EMAIL = "email"
    INTERVIEW = "interview"
    REDDIT = "reddit"
    SUPPORT = "support"
    APP_STORE = "app_store"
    TWITTER = "twitter"
    OTHER = "other"


class Status(StrEnum):
    """Triage state of a feedback item."""

    NEW = "new"
    REVIEWING = "reviewing"
    PLANNED = "planned"
    REJECTED = "rejected"


# ---------------------------------------------------------------------------
# v2 enums
# ---------------------------------------------------------------------------
# Python-side mirrors of the four new native Postgres enum types added in
# the v2.0 jump. **The Postgres types are created in PR 1.3b's Migration
# A**; this module ships the Python enums first so PR 1.3b can wire
# ``PgEnum(..., create_type=False)`` to them without a circular dep.
# Keep the string values in lock-step with the migration's CREATE TYPE
# labels — renaming a member without a planned data-migration is a
# breaking change.


class UserRole(StrEnum):
    """Site-wide role on the ``users`` table.

    Values match ``user_role_enum`` in
    ``docs/project/spec/v2/schema.md``. Distinct from
    :class:`WorkspaceRole`, which scopes a user's privileges inside a
    single workspace via the ``memberships`` table. See ADR 060 and
    ``docs/project/spec/v2/multi-tenancy.md``.
    """

    ADMIN = "admin"
    TEAM_MEMBER = "team_member"
    DEMO = "demo"


class WorkspaceRole(StrEnum):
    """Per-workspace role stored on ``memberships.role``.

    Values match ``workspace_role_enum`` in ADR 060 and
    ``docs/project/spec/v2/schema.md``.
    """

    OWNER = "owner"
    TEAM_MEMBER = "team_member"


class EmailStatus(StrEnum):
    """Delivery state of a row in the ``email_log`` table.

    Values match ``email_status_enum`` in ADR 061; the Resend-webhook
    surface (delivered / bounced / complained) is intentionally not
    modelled in v2.0 — webhook ingestion lands later.
    """

    QUEUED = "queued"
    SENT = "sent"
    RETRYING = "retrying"
    FAILED = "failed"


class EmailPurpose(StrEnum):
    """Why a row was written to ``email_log``.

    Values match ``email_purpose_enum`` in ADR 061. ``status_change``
    backs the Phase 3 status-change notification surface.
    """

    VERIFICATION = "verification"
    PASSWORD_RESET = "password_reset"  # nosec B105 - enum label, not a credential
    INVITATION = "invitation"
    STATUS_CHANGE = "status_change"
