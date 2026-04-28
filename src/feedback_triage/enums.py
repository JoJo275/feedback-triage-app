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
