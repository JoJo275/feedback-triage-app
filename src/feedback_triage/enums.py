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

from sqlalchemy.dialects.postgresql import ENUM as PgEnum


class Source(StrEnum):
    """Where a feedback item originated."""

    EMAIL = "email"
    INTERVIEW = "interview"
    REDDIT = "reddit"
    SUPPORT = "support"
    APP_STORE = "app_store"
    TWITTER = "twitter"
    WEB_FORM = "web_form"
    OTHER = "other"


class Status(StrEnum):
    """Triage state of a feedback item.

    The v2.0 workflow adds ``needs_info``, ``accepted``, ``in_progress``,
    ``shipped``, ``closed``, and ``spam`` (per ADR 063). ``rejected``
    is retained as an enum label only because Postgres has no
    ``ALTER TYPE … DROP VALUE`` in stable releases; a ``CHECK`` added
    in Migration B forbids the application from writing it, and the
    backfill rewrites every legacy row to ``closed``.
    """

    NEW = "new"
    NEEDS_INFO = "needs_info"
    REVIEWING = "reviewing"
    ACCEPTED = "accepted"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    SHIPPED = "shipped"
    CLOSED = "closed"
    SPAM = "spam"
    REJECTED = "rejected"  # deprecated; never written by v2 code (ADR 063)


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


class FeedbackType(StrEnum):
    """Classification of a feedback item.

    Values match ``type_enum`` in
    ``docs/project/spec/v2/schema.md``. Stored on
    ``feedback_item.type``; ``other`` requires a non-null
    ``type_other`` free-text field (DB ``CHECK`` constraint).
    """

    BUG = "bug"
    FEATURE_REQUEST = "feature_request"
    COMPLAINT = "complaint"
    PRAISE = "praise"
    QUESTION = "question"
    OTHER = "other"


class Priority(StrEnum):
    """Priority assigned by the team during triage.

    Values match ``priority_enum`` in
    ``docs/project/spec/v2/schema.md``. Stored on
    ``feedback_item.priority`` (nullable until set).
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# Native Postgres ENUM types for the v2 enums.
# ---------------------------------------------------------------------------
# ``create_type=False`` because the migration owns the CREATE TYPE / DROP TYPE
# lifecycle (see ``alembic/versions/0002_v2_a_auth_tenancy_email_log.py``).
# These are imported by the v2 model modules so the SQLModel column types
# resolve to the matching native Postgres enum.

USER_ROLE_ENUM = PgEnum(
    UserRole,
    name="user_role_enum",
    values_callable=lambda enum_cls: [m.value for m in enum_cls],
    create_type=False,
)

WORKSPACE_ROLE_ENUM = PgEnum(
    WorkspaceRole,
    name="workspace_role_enum",
    values_callable=lambda enum_cls: [m.value for m in enum_cls],
    create_type=False,
)

EMAIL_STATUS_ENUM = PgEnum(
    EmailStatus,
    name="email_status_enum",
    values_callable=lambda enum_cls: [m.value for m in enum_cls],
    create_type=False,
)

EMAIL_PURPOSE_ENUM = PgEnum(
    EmailPurpose,
    name="email_purpose_enum",
    values_callable=lambda enum_cls: [m.value for m in enum_cls],
    create_type=False,
)

# v2 workflow enums on ``feedback_item``. Created by Migration B
# (``alembic/versions/0003_v2_b_workflow_tables.py``).
TYPE_ENUM = PgEnum(
    FeedbackType,
    name="type_enum",
    values_callable=lambda enum_cls: [m.value for m in enum_cls],
    create_type=False,
)

PRIORITY_ENUM = PgEnum(
    Priority,
    name="priority_enum",
    values_callable=lambda enum_cls: [m.value for m in enum_cls],
    create_type=False,
)
