"""v2 Migration B2 — workflow tables + new feedback_item columns.

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-06

Hand-authored. Phase 2's workspace-data half of the v1 → v2 jump:

1. Create the ``type_enum`` and ``priority_enum`` native types.
2. Create the ``submitters``, ``tags``, ``feedback_tags``, and
   ``feedback_notes`` tables (with their indexes + ``updated_at``
   triggers where applicable).
3. Add the workflow columns to ``feedback_item``: ``submitter_id``,
   ``type``, ``priority``, ``source_other``, ``type_other``,
   ``published_to_roadmap``, ``published_to_changelog``,
   ``release_note``.
4. Add the matching CHECK constraints (text-length caps and the
   ``other`` ↔ free-text invariants from
   ``docs/project/spec/v2/schema.md``).
5. Add the ``feedback_submitter_idx`` partial index.

Ships in the same PR as Migration B (revision 0003) per
``docs/project/spec/v2/implementation.md`` PR 2.1. Splitting B and
B2 into separate revisions means a deploy that fails between them
can roll *forward* by re-running ``alembic upgrade head`` rather
than down.

Hand-review checklist (verified before merge):

- every new table has a native enum where the spec calls for one;
- every text column has a ``CHECK length(...) <= N``;
- every FK has explicit ``ON DELETE`` semantics;
- every ``updated_at`` column has a ``BEFORE UPDATE`` trigger that
  reuses the project-wide ``set_updated_at()`` plpgsql function.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | Sequence[str] | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


TYPE_VALUES = (
    "bug",
    "feature_request",
    "complaint",
    "praise",
    "question",
    "other",
)
PRIORITY_VALUES = ("low", "medium", "high", "critical")

TAG_COLOR_PALETTE = (
    "slate",
    "teal",
    "amber",
    "rose",
    "indigo",
    "sky",
    "green",
    "violet",
)


def _create_updated_at_trigger(table: str) -> None:
    """Attach the project-wide ``set_updated_at()`` trigger to ``table``."""
    op.execute(
        f"""
        CREATE TRIGGER {table}_set_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();
        """
    )


def upgrade() -> None:
    bind = op.get_bind()

    # ------------------------------------------------------------------
    # 1. New native enum types.
    # ------------------------------------------------------------------
    postgresql.ENUM(*TYPE_VALUES, name="type_enum").create(bind, checkfirst=False)
    postgresql.ENUM(*PRIORITY_VALUES, name="priority_enum").create(
        bind, checkfirst=False
    )

    type_enum = postgresql.ENUM(name="type_enum", create_type=False)
    priority_enum = postgresql.ENUM(name="priority_enum", create_type=False)
    citext = postgresql.CITEXT()

    # ------------------------------------------------------------------
    # 2. submitters
    # ------------------------------------------------------------------
    op.create_table(
        "submitters",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", citext, nullable=True),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("internal_notes", sa.Text(), nullable=True),
        sa.Column(
            "first_seen_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "last_seen_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "submission_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "workspace_id", "email", name="submitters_workspace_email_uq"
        ),
        sa.CheckConstraint(
            "name IS NULL OR length(name) <= 120",
            name="submitters_name_max_len",
        ),
        sa.CheckConstraint(
            "internal_notes IS NULL OR length(internal_notes) <= 4000",
            name="submitters_internal_notes_max_len",
        ),
        sa.CheckConstraint(
            "submission_count >= 0",
            name="submitters_submission_count_nonneg",
        ),
    )
    op.create_index("submitters_workspace_idx", "submitters", ["workspace_id"])
    _create_updated_at_trigger("submitters")

    # ------------------------------------------------------------------
    # 3. tags
    # ------------------------------------------------------------------
    palette_list = ",".join(f"'{c}'" for c in TAG_COLOR_PALETTE)
    op.create_table(
        "tags",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column(
            "color",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'slate'"),
        ),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("workspace_id", "slug", name="tags_workspace_slug_uq"),
        sa.CheckConstraint(
            "length(name) BETWEEN 1 AND 40",
            name="tags_name_len",
        ),
        sa.CheckConstraint(
            "slug ~ '^[a-z0-9](?:[a-z0-9-]{0,38}[a-z0-9])?$'",
            name="tags_slug_format",
        ),
        sa.CheckConstraint(
            f"color IN ({palette_list})",
            name="tags_color_palette",
        ),
    )

    # ------------------------------------------------------------------
    # 4. feedback_tags (M2M bridge)
    # ------------------------------------------------------------------
    op.create_table(
        "feedback_tags",
        sa.Column(
            "feedback_id",
            sa.BigInteger(),
            sa.ForeignKey("feedback_item.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "tag_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tags.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
    )

    # ------------------------------------------------------------------
    # 5. feedback_notes
    # ------------------------------------------------------------------
    op.create_table(
        "feedback_notes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "feedback_id",
            sa.BigInteger(),
            sa.ForeignKey("feedback_item.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "author_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "length(body) BETWEEN 1 AND 4000",
            name="feedback_notes_body_len",
        ),
    )
    op.create_index(
        "feedback_notes_feedback_idx",
        "feedback_notes",
        ["feedback_id", sa.text("created_at DESC")],
    )
    _create_updated_at_trigger("feedback_notes")

    # ------------------------------------------------------------------
    # 6. feedback_item — workflow columns.
    # ------------------------------------------------------------------
    op.add_column(
        "feedback_item",
        sa.Column(
            "submitter_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("submitters.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "feedback_item",
        sa.Column(
            "type",
            type_enum,
            nullable=False,
            server_default=sa.text("'other'::type_enum"),
        ),
    )
    op.add_column(
        "feedback_item",
        sa.Column("priority", priority_enum, nullable=True),
    )
    op.add_column(
        "feedback_item",
        sa.Column("source_other", sa.Text(), nullable=True),
    )
    op.add_column(
        "feedback_item",
        sa.Column("type_other", sa.Text(), nullable=True),
    )
    op.add_column(
        "feedback_item",
        sa.Column(
            "published_to_roadmap",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "feedback_item",
        sa.Column(
            "published_to_changelog",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "feedback_item",
        sa.Column("release_note", sa.Text(), nullable=True),
    )

    op.create_check_constraint(
        "feedback_item_source_other_max_len",
        "feedback_item",
        "source_other IS NULL OR length(source_other) <= 60",
    )
    op.create_check_constraint(
        "feedback_item_type_other_max_len",
        "feedback_item",
        "type_other IS NULL OR length(type_other) <= 60",
    )
    # One-way invariant: a free-text fallback is only valid when its
    # enum is ``other`` (per the comment in v2/schema.md). The
    # spec's biconditional form would be unsatisfiable for new rows
    # under the ``DEFAULT 'other'`` for ``type`` — type=other +
    # type_other=NULL must be a valid initial state.
    op.create_check_constraint(
        "feedback_item_source_other_chk",
        "feedback_item",
        "source_other IS NULL OR source = 'other'",
    )
    op.create_check_constraint(
        "feedback_item_type_other_chk",
        "feedback_item",
        "type_other IS NULL OR type = 'other'",
    )
    op.create_check_constraint(
        "feedback_item_release_note_max_len",
        "feedback_item",
        "release_note IS NULL OR length(release_note) <= 280",
    )

    op.create_index(
        "feedback_submitter_idx",
        "feedback_item",
        ["submitter_id"],
        postgresql_where=sa.text("submitter_id IS NOT NULL"),
    )


def downgrade() -> None:
    # Reversible (B2 is purely additive — Migration B's data flips
    # are the forward-only step). Useful for rehearsing the migration
    # against a snapshot in CI.
    op.drop_index("feedback_submitter_idx", table_name="feedback_item")

    for name in (
        "feedback_item_release_note_max_len",
        "feedback_item_type_other_chk",
        "feedback_item_source_other_chk",
        "feedback_item_type_other_max_len",
        "feedback_item_source_other_max_len",
    ):
        op.drop_constraint(name, "feedback_item", type_="check")

    for column in (
        "release_note",
        "published_to_changelog",
        "published_to_roadmap",
        "type_other",
        "source_other",
        "priority",
        "type",
        "submitter_id",
    ):
        op.drop_column("feedback_item", column)

    op.execute("DROP TRIGGER IF EXISTS feedback_notes_set_updated_at ON feedback_notes")
    op.drop_index("feedback_notes_feedback_idx", table_name="feedback_notes")
    op.drop_table("feedback_notes")

    op.drop_table("feedback_tags")
    op.drop_table("tags")

    op.execute("DROP TRIGGER IF EXISTS submitters_set_updated_at ON submitters")
    op.drop_index("submitters_workspace_idx", table_name="submitters")
    op.drop_table("submitters")

    bind = op.get_bind()
    postgresql.ENUM(name="priority_enum").drop(bind, checkfirst=False)
    postgresql.ENUM(name="type_enum").drop(bind, checkfirst=False)
