"""Round-trip migration test for v2 Migration B (PR 2.1).

Asserts the data-migration choreography from
[ADR 062](../../docs/adr/062-v1-to-v2-data-migration.md) on a snapshot
that contains both legacy ``rejected`` rows and rows with
``workspace_id IS NULL``:

1. Downgrade to revision ``0002`` (post Migration A, pre Migration B).
   Migration B's ``downgrade()`` is schema-only — the data half of B
   stays forward-only per ADR 062 — but the schema downgrade is enough
   to re-create the pre-B shape that the migration is meant to
   transform (NULLABLE ``workspace_id``, no ``status<>'rejected'``
   CHECK, no workspace-scoped indexes).
2. Insert a synthetic legacy snapshot (``rejected`` + ``NULL
   workspace_id`` rows).
3. Upgrade to ``0003`` (Migration B): every legacy row now has
   ``workspace_id`` populated to the synthetic ``signalnest-legacy``
   workspace and ``rejected`` is rewritten to ``closed``.
4. Upgrade to ``0004`` (Migration B2) and round-trip down + up; the
   post-B row state survives unchanged.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from feedback_triage.database import engine

ALEMBIC_INI = "alembic.ini"


@pytest.fixture
def alembic_cfg() -> Config:
    """Alembic config bound to the project's ``alembic.ini``.

    ``config_file_name`` is cleared so ``alembic/env.py`` skips its
    ``logging.config.fileConfig`` call. Without that ``fileConfig``
    runs with ``disable_existing_loggers=True`` and silences every
    pre-existing logger in the test process — which breaks ``caplog``
    for unrelated tests that run after this fixture.
    """
    cfg = Config(ALEMBIC_INI)
    cfg.set_main_option("script_location", "alembic")
    cfg.config_file_name = None
    return cfg


@pytest.fixture
def at_revision_0002(alembic_cfg: Config) -> Iterator[None]:
    """Pin the schema at revision 0002 (post-A, pre-B) for the test.

    ``feedback_item`` is truncated so the test starts clean; the
    synthetic legacy admin + workspace inserted by Migration A are
    re-seeded if a sibling test wiped them. After the test, the
    schema is restored to ``head``.
    """
    command.downgrade(alembic_cfg, "0002")
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE feedback_item RESTART IDENTITY CASCADE"))
        conn.execute(
            text(
                """
                INSERT INTO users (id, email, password_hash, is_verified, role)
                SELECT gen_random_uuid(), 'legacy@signalnest.local',
                       '!disabled-legacy-v1-admin!', false, 'admin'
                 WHERE NOT EXISTS (
                    SELECT 1 FROM users WHERE email = 'legacy@signalnest.local'
                 )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO workspaces (id, slug, name, owner_id, is_demo)
                SELECT gen_random_uuid(), 'signalnest-legacy',
                       'SignalNest (legacy)', u.id, false
                  FROM users u
                 WHERE u.email = 'legacy@signalnest.local'
                   AND NOT EXISTS (
                    SELECT 1 FROM workspaces WHERE slug = 'signalnest-legacy'
                   )
                """
            )
        )
    try:
        yield
    finally:
        command.upgrade(alembic_cfg, "head")


def _seed_legacy_snapshot() -> tuple[int, int]:
    """Insert two rows that simulate v1 production data.

    Returns ``(rejected_id, normal_id)``. Both rows have
    ``workspace_id IS NULL`` because Migration A leaves the column
    nullable; the first row uses the deprecated ``rejected`` status
    so Migration B's ``UPDATE … = 'closed'`` is exercised.
    """
    with engine.begin() as conn:
        rejected_id = conn.execute(
            text(
                "INSERT INTO feedback_item "
                "(title, description, source, pain_level, status) "
                "VALUES ('legacy rejected', 'snapshot row', 'email', 3, "
                "'rejected') RETURNING id"
            )
        ).scalar_one()
        normal_id = conn.execute(
            text(
                "INSERT INTO feedback_item "
                "(title, description, source, pain_level, status) "
                "VALUES ('legacy new', 'snapshot row', 'email', 2, 'new') "
                "RETURNING id"
            )
        ).scalar_one()
    return int(rejected_id), int(normal_id)


def test_migration_b_backfills_workspace_and_renames_rejected(
    alembic_cfg: Config,
    at_revision_0002: None,
) -> None:
    """The full v1 → v2 cut-over choreography on a synthetic snapshot.

    Asserts every leg of ADR 062's contract: backfill, NOT NULL flip,
    status rename, and the new ``CHECK (status <> 'rejected')``
    constraint.
    """
    rejected_id, normal_id = _seed_legacy_snapshot()

    # Pre-condition: both rows have NULL workspace_id; one is rejected.
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, status, workspace_id FROM feedback_item ORDER BY id")
        ).all()
    assert len(rows) == 2
    assert all(r.workspace_id is None for r in rows)
    assert any(r.status == "rejected" for r in rows)

    # ----- Migration B (0003) — backfill + flip + rename -----
    command.upgrade(alembic_cfg, "0003")

    with engine.connect() as conn:
        legacy_ws_id = conn.execute(
            text("SELECT id FROM workspaces WHERE slug = 'signalnest-legacy'")
        ).scalar_one()
        rows = conn.execute(
            text("SELECT id, status, workspace_id FROM feedback_item ORDER BY id")
        ).all()

    assert all(r.workspace_id == legacy_ws_id for r in rows), (
        "every legacy row must point at the legacy workspace post-B"
    )
    assert {r.status for r in rows} == {"new", "closed"}, (
        "rejected must be rewritten to closed"
    )
    assert {int(r.id) for r in rows} == {rejected_id, normal_id}

    # NOT NULL invariant — direct INSERT without workspace_id rejected.
    with engine.begin() as conn, pytest.raises(IntegrityError):
        conn.execute(
            text(
                "INSERT INTO feedback_item "
                "(title, description, source, pain_level, status) "
                "VALUES ('post-B no-ws', 'should fail', 'email', 1, 'new')"
            )
        )

    # CHECK (status <> 'rejected') invariant.
    with engine.begin() as conn, pytest.raises(IntegrityError):
        conn.execute(
            text(
                "INSERT INTO feedback_item "
                "(title, description, source, pain_level, status, "
                "workspace_id) "
                "VALUES ('post-B reject', 'should fail', 'email', 1, "
                "'rejected', :wid)"
            ),
            {"wid": str(legacy_ws_id)},
        )


def test_migration_b2_round_trip_preserves_rows(
    alembic_cfg: Config,
    at_revision_0002: None,
) -> None:
    """B2 is reversible; round-trip preserves the post-B row state."""
    _seed_legacy_snapshot()
    command.upgrade(alembic_cfg, "0003")

    with engine.connect() as conn:
        before = conn.execute(
            text("SELECT id, status, workspace_id FROM feedback_item ORDER BY id")
        ).all()

    command.upgrade(alembic_cfg, "0004")
    with engine.connect() as conn:
        for table in ("submitters", "tags", "feedback_tags", "feedback_notes"):
            count = conn.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()
            assert count == 0, f"{table} must start empty after B2 upgrade"

    command.downgrade(alembic_cfg, "0003")
    command.upgrade(alembic_cfg, "0004")

    with engine.connect() as conn:
        after = conn.execute(
            text("SELECT id, status, workspace_id FROM feedback_item ORDER BY id")
        ).all()
    assert [tuple(r) for r in before] == [tuple(r) for r in after]
