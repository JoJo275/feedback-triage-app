# ADR 046: Native Postgres Enums + DB CHECK Constraints

## Status

Proposed

## Context

`source` and `status` are closed value sets. `pain_level` is an integer
in [1, 5]. `title` and `description` have length and emptiness rules.

Pydantic enforces all of these at the API boundary. That is necessary
but not sufficient: seed scripts, manual `psql` inserts, future second
clients, and buggy migrations can still write garbage into the table if
the database itself does not refuse.

## Decision

- `source` and `status` are stored as **native Postgres `ENUM` types**
  (`source_enum`, `status_enum`), not as `text` or `varchar`.
- The Python `Source` and `Status` enums in `enums.py` are the single
  source of truth; SQLModel column types map to them; Alembic migrations
  emit the matching `CREATE TYPE` statements.
- All length and range invariants live in DB-level `CHECK` constraints:
  - `feedback_item_pain_level_range` (`pain_level BETWEEN 1 AND 5`)
  - `feedback_item_title_not_blank` (`length(btrim(title)) > 0`)
  - `feedback_item_title_max_len` (`length(title) <= 200`)
  - `feedback_item_description_max_len`
    (`description IS NULL OR length(description) <= 5000`)

### Enum migration policy

Adding a value to an enum requires a dedicated migration with
`ALTER TYPE … ADD VALUE`. Renaming or removing values requires a
two-migration dance (new type, copy column, drop old). Each enum
migration is hand-reviewed.

## Alternatives Considered

### `varchar` + Python validation only

**Rejected because:** Pydantic only protects the JSON entry point.
Defense in depth costs almost nothing here.

### `varchar(N)` instead of `text` + `CHECK length(...)`

**Rejected because:** Postgres stores both identically, but the
community idiom is `text` + `CHECK`. Lowering a `varchar(N)` requires a
full table rewrite; the `CHECK` form makes the constraint explicit in
the schema and easy to relax.

## Consequences

### Positive

- The DB itself rejects invalid rows from any client.
- Enum membership is visible in `\dT+ <enum>` in psql.
- Reviewers can read the migration and see every invariant.

### Negative

- Enum value churn is more painful than `text` columns. This is a
  feature: the friction forces deliberate decisions.
