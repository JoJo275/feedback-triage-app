"""Add ``theme_preference`` column to ``users``.

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-07

PR 4.1 — dark mode (FD). Persists each user's theme choice so the
sidebar toggle survives logout, device changes, and ``localStorage``
loss. Three values are accepted:

- ``light`` — explicit light theme (overrides system preference).
- ``dark``  — explicit dark theme (overrides system preference).
- ``system`` — defer to ``prefers-color-scheme`` on the device.

``system`` is the default for new and existing users so the rollout
has zero visible effect until a user clicks the sidebar toggle. The
value is stored as plain ``text`` with a ``CHECK (… IN (...))``
constraint rather than a native enum — the set is small, never
queried as an enum, and the CHECK keeps the schema honest without
the ``ALTER TYPE … ADD VALUE`` ceremony.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | Sequence[str] | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "theme_preference",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'system'"),
        ),
    )
    op.create_check_constraint(
        "users_theme_preference_valid",
        "users",
        "theme_preference IN ('light', 'dark', 'system')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "users_theme_preference_valid",
        "users",
        type_="check",
    )
    op.drop_column("users", "theme_preference")
