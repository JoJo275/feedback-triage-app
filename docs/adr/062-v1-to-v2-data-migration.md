# ADR 062: v1.0 → v2.0 data migration — legacy workspace + status rename

## Status

Accepted (2026-05-05). Phase gate: **Beta** — the `NOT NULL
workspace_id` and the status-enum changes both block on this ADR.
The migration ships as **two** Alembic revisions ("Migration A" and
"Migration B") so a deploy that fails between them rolls *forward*
and never down.

## Context

v1.0 ships a single `feedback_item` table with no notion of users
or workspaces. v2.0 introduces multi-tenancy
([ADR 060](060-multi-tenancy-workspace-scoping.md)) and an extended
status workflow ([ADR 063](063-status-enum-extension.md)). Existing
production rows must survive the cut-over without operator
intervention and without a maintenance window long enough to copy
the table.

Two operational realities constrain the migration:

1. **`workspace_id` becomes a non-nullable foreign key on
   `feedback_item`.** Every existing row must be assigned a
   workspace before the `NOT NULL` constraint can be added, or the
   migration fails halfway and rolls back.
2. **Postgres enum changes are non-transactional.**
   `ALTER TYPE … ADD VALUE` cannot run inside a transaction block
   that also performs `UPDATE`s on rows of that enum type. The
   add-value step must be in its own statement *before* any
   `UPDATE` that uses the new value.

Naïvely doing all of this in a single Alembic revision means a
mid-migration failure leaves the schema in a half-applied,
hard-to-recover state — and Alembic's `downgrade()` for a failed
upgrade is rarely exercised in practice. The cleanest answer is to
split the work into two revisions whose only failure mode is
"re-run the second one."

## Decision

The v1 → v2 data migration ships as **two ordered Alembic
revisions**:

### Migration A — schema-only, additive

1. `CREATE TABLE workspaces, memberships, users` (and supporting
   tables / indexes / triggers) per
   [`v2/schema.md`](../project/spec/v2/schema.md).
2. `INSERT INTO users` — one synthetic admin row,
   `email = 'legacy@signalnest.local'`, password hash set to a
   sentinel that no real Argon2id verifier will accept (login
   disabled).
3. `INSERT INTO workspaces` — one row, `slug = 'signalnest-legacy'`,
   `owner_id = <synthetic admin>`, `created_at = NOW()`.
4. `ALTER TABLE feedback_item ADD COLUMN workspace_id uuid NULL
   REFERENCES workspaces(id)` (still nullable).
5. `ALTER TYPE status_enum ADD VALUE` for each new value
   (`needs_info`, `accepted`, `in_progress`, `shipped`, `closed`,
   `spam`). Each `ADD VALUE` is its own statement;
   [Alembic op.execute() with `autocommit_block()`][alembic-autocommit]
   wraps them so they run outside the migration transaction, which
   Postgres requires for new enum values to be visible to
   subsequent statements.

[alembic-autocommit]: https://alembic.sqlalchemy.org/en/latest/api/operations.html#alembic.operations.Operations.execute

After Migration A, the schema accepts both the old and new shape:
existing reads/writes work unchanged, the new enum values are
defined but unused, and `workspace_id` is nullable.

### Migration B — data backfill + tighten

6. `UPDATE feedback_item SET workspace_id = <legacy workspace id>
   WHERE workspace_id IS NULL`.
7. `UPDATE feedback_item SET status = 'closed' WHERE status =
   'rejected'` (status rename from
   [ADR 063](063-status-enum-extension.md)).
8. `ALTER TABLE feedback_item ALTER COLUMN workspace_id SET NOT
   NULL`.
9. `CREATE INDEX … ON feedback_item (workspace_id, …)` per
   [`v2/schema.md`](../project/spec/v2/schema.md) — created here
   rather than in Migration A so the index build runs once on the
   final, populated column.

Migration B is **idempotent**: if it crashes between any two steps,
re-running it from the top is safe — the `UPDATE`s become no-ops on
already-migrated rows, and the `SET NOT NULL` either succeeds (all
rows now have a workspace) or fails with a clear error pointing at
the offending row.

### Rollback policy

Forward-only. Migration A is purely additive and trivially
reversible; Migration B is intentionally **not** reversible —
neither `'rejected'` nor `NULL workspace_id` is a valid v2.0 state,
and writing a `downgrade()` that re-introduces them would be
write-only code. If Migration B has to be backed out, the operator
restores from the snapshot taken immediately before deploy (see
[`v2/rollout.md`](../project/spec/v2/rollout.md)).

The legacy workspace and synthetic admin user persist after the
migration. They are documented in `v2/rollout.md`'s "what's left
behind" section and are not garbage-collected — operators who want
to reassign legacy rows to a real workspace can do so manually,
then delete the legacy workspace once no rows reference it.

## Alternatives Considered

### Single combined migration

Schema + backfill + enum extension in one revision.
**Rejected because:** Postgres prohibits `ALTER TYPE … ADD VALUE`
followed by `UPDATE … = '<new value>'` in the same transaction. A
single revision either uses `autocommit_block()` for the whole
thing (giving up Alembic's transactional safety for *all* steps,
not just the enum) or splits internally — at which point it is
already two migrations in everything but name.

### Maintenance window + offline copy

Lock the table, dump, transform, restore.
**Rejected because:** the data volume in v1 production is small
enough that an online migration is operationally simpler, and the
downtime cost of a maintenance window is higher than the marginal
risk of an online migration that has been rehearsed against a
production snapshot.

### Per-tenant migration on first login

Lazy-create workspaces; migrate rows on demand.
**Rejected because:** v1.0 has no concept of "tenant" — there is
no signal at request time about which workspace a row belongs to.
Every existing row goes to the same legacy workspace; lazy
migration adds complexity without buying anything.

### Drop `rejected` from the enum entirely

Use Postgres 15+ `ALTER TYPE … DROP VALUE` (preview) or rebuild the
type.
**Rejected because:** `DROP VALUE` is not in stable Postgres,
rebuilding the type via `CREATE TYPE … RENAME` is awkward and
locks every column that uses it, and the leftover unused enum
value in the type definition is harmless. The data migration
ensures no row uses `'rejected'`; a `CHECK` constraint added in
Migration B forbids future writes.

## Consequences

### Positive

- **Re-runnable.** A failure during Migration B is recovered by
  re-running B; no manual SQL surgery required.
- **No downtime.** Migration A is additive; Migration B's data
  passes are bounded by a single small table.
- **Auditable.** Two revisions, each with a clear single purpose,
  show up cleanly in `alembic history` and in the
  [v2 implementation ledger](../project/spec/v2/implementation.md).
- **Rehearsable.** Operators can dry-run B against a production
  snapshot before flipping the switch on the live deploy.

### Negative

- **Forward-only.** Migration B has no `downgrade()`; recovery is
  via snapshot restore, which must be in the deploy runbook.
- **Two deploy steps.** The Railway pre-deploy command runs
  `alembic upgrade head`, which executes both A and B
  back-to-back. If A succeeds and B fails, the next deploy will
  retry B — operators must understand that the schema is in an
  intermediate state until B succeeds.
- **Legacy user / workspace pollution.** The synthetic admin and
  `signalnest-legacy` workspace are visible forever in the admin
  surface. Filtered out of default lists; documented in
  `v2/rollout.md`.

### Neutral

- v2.1+ migrations inherit the same A/B split discipline whenever
  they touch enum types or non-nullable foreign keys.

### Mitigations

- The deploy runbook ([`v2/rollout.md`](../project/spec/v2/rollout.md))
  mandates a snapshot taken immediately before
  `alembic upgrade head` and a smoke check (`fta-diag --post-deploy`)
  immediately after, before traffic is restored.
- Both revisions are exercised in CI against a fresh Postgres
  with v1.0 seed data (`scripts/seed.py --legacy-snapshot`).
- The canary test
  `tests/test_migration_v1_to_v2.py::test_legacy_rows_migrated`
  asserts every v1.0 row has `workspace_id IS NOT NULL` and
  `status != 'rejected'` after upgrade.

## Implementation

- `alembic/versions/<a>_v2_schema_only.py` — Migration A.
- `alembic/versions/<b>_v2_backfill_and_tighten.py` — Migration B,
  depends on A.
- [`docs/project/spec/v2/schema.md`](../project/spec/v2/schema.md)
  — full DDL.
- [`docs/project/spec/v2/rollout.md`](../project/spec/v2/rollout.md)
  — operator runbook, snapshot policy, smoke checks.
- `tests/test_migration_v1_to_v2.py` — canary tests (added in
  PR 2.x; see the v2 implementation ledger).

## References

- [ADR 060](060-multi-tenancy-workspace-scoping.md) — why
  `workspace_id` exists.
- [ADR 063](063-status-enum-extension.md) — why `rejected` becomes
  `closed`.
- [Alembic — `autocommit_block`](https://alembic.sqlalchemy.org/en/latest/api/operations.html#alembic.operations.Operations.execute)
- [Postgres docs — `ALTER TYPE`](https://www.postgresql.org/docs/16/sql-altertype.html)
