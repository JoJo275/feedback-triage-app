"""Add assignee_user_id to feedback_item.

Revision ID: 0008
Revises: 0007
Create Date: 2026-05-13

Adds nullable ``feedback_item.assignee_user_id`` so workspace teams can
explicitly assign ownership. The column references ``users.id`` with
``ON DELETE SET NULL`` and includes a partial index for assignment
filters/workload queries.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008"
down_revision: str | Sequence[str] | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "feedback_item",
        sa.Column(
            "assignee_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "feedback_item_assignee_user_id_fkey",
        "feedback_item",
        "users",
        ["assignee_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "feedback_assignee_idx",
        "feedback_item",
        ["assignee_user_id"],
        unique=False,
        postgresql_where=sa.text("assignee_user_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("feedback_assignee_idx", table_name="feedback_item")
    op.drop_constraint(
        "feedback_item_assignee_user_id_fkey",
        "feedback_item",
        type_="foreignkey",
    )
    op.drop_column("feedback_item", "assignee_user_id")
