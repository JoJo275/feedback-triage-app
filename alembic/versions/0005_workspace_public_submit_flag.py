"""Add ``public_submit_enabled`` toggle to ``workspaces``.

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-06

PR 2.5 — settings page. Adds a per-workspace kill switch for the
public submission form (``/w/<slug>/submit``). Defaults to ``true``
so existing workspaces keep their current behaviour after the
deploy.

The flag is checked both by the page route (renders a "form is
closed" notice) and by the ``POST /api/v1/public/feedback/{slug}``
write endpoint (returns 404 — same shape as an unknown slug, so
flipping the switch off cannot be used as a probe for slug
existence).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | Sequence[str] | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "workspaces",
        sa.Column(
            "public_submit_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )


def downgrade() -> None:
    op.drop_column("workspaces", "public_submit_enabled")
