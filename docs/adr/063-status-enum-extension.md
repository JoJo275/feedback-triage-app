# ADR 063: Status enum extension + `rejected` deprecation

## Status

Accepted (2026-05-05). Phase gate: **Beta** — the inbox UI, the
notification copy, and the workflow rules in
[`v2/api.md`](../project/spec/v2/api.md) all bind to the final
status set defined here. The actual `ALTER TYPE` and data
migration are owned by [ADR 062](062-v1-to-v2-data-migration.md);
this ADR fixes *what* the final set is and *why*.

## Context

v1.0 ships a four-value `status_enum`: `new`, `triaged`, `shipped`,
`rejected`. Two problems surfaced once real teams started using it:

1. **The middle of the workflow is missing.** Teams want to mark a
   piece of feedback as "we asked the customer for more detail" or
   "we accepted it but haven't started" without conflating those
   with `triaged`.
2. **`rejected` is the wrong word.** It implies a value judgement
   on the submitter ("your feedback is bad"), and operators
   reported never wanting to type it. The intent is "this issue is
   resolved without a code change" — better expressed as `closed`.

A separate operational signal — "this came from a bot or
spammer" — was being shoehorned into `rejected`, which made the
existing semantics even muddier.

## Decision

The v2.0 `status_enum` is, in workflow order:

| Value         | Meaning                                                                     | Terminal? |
| ------------- | --------------------------------------------------------------------------- | --------- |
| `new`         | Just submitted; not yet looked at by the team.                              | No        |
| `needs_info`  | Team is waiting on the submitter for clarification.                         | No        |
| `reviewing`   | Team is actively investigating / reproducing.                               | No        |
| `accepted`    | Team agrees this is real and will act on it; no work started yet.           | No        |
| `planned`     | Scheduled for a specific milestone / sprint.                                | No        |
| `in_progress` | Implementation has started.                                                 | No        |
| `shipped`     | Resolved by a code change that has reached production.                      | Yes\*     |
| `closed`      | Resolved without a code change (working as intended, duplicate, withdrawn). | Yes\*    |
| `spam`        | Bot, abuse, or unrelated content. Hidden from default lists.                | Yes       |

\* `shipped` and `closed` are reversible: an operator can move a
row back to `reviewing` if a regression appears or a closed item
turns out to be real after all. `spam` is intentionally **not**
reversible from the UI — un-spamming requires admin SQL or a
workspace-owner-only action — to make spam-marking cheap and
unambiguous.

### `rejected` deprecation path

`rejected` is removed from the v2.0 application surface but
**stays in the Postgres enum type definition** for the lifetime of
v2.0. The reasons:

- Postgres does not support `ALTER TYPE … DROP VALUE` in any
  stable release; the only way to remove a value is to rebuild
  the type, which locks every column using it.
- Leaving the value in the type costs nothing and avoids the
  rebuild lock entirely.

Application-side, `rejected` is forbidden via:

1. A `CHECK (status <> 'rejected')` constraint added in
   [Migration B](062-v1-to-v2-data-migration.md#migration-b--data-backfill--tighten).
2. The Pydantic `Status` enum / OpenAPI schema does not list
   `rejected` as a valid input or output value.
3. The data migration in
   [ADR 062](062-v1-to-v2-data-migration.md) rewrites every
   existing `rejected` row to `closed`.

If a future v2.x revision wants to formally retire the unused
enum value, it can do so by rebuilding the type (acceptable cost
once usage has stabilised). Until then it is a dead identifier
that the application never produces and the database refuses to
accept.

### Allowed transitions

The v2.0 transition graph (enforced at the service layer, not in
the database — see "Alternatives Considered"):

```
new ──► needs_info ──► reviewing ──► accepted ──► planned ──► in_progress ──► shipped
 │                          ▲                                                    │
 │                          │                                                    │
 ├──────────────────────────┴────────► closed ◄──────────────────────────────────┘
 │
 └──► spam   (terminal; one-way; admin-reversible only)
```

- Any non-terminal state can move forward to any later
  non-terminal state, or directly to `closed`.
- `shipped` and `closed` can be moved back to `reviewing` (the
  "this came back" path).
- `spam` has no outgoing edges in the UI.

The exact matrix lives in
[`v2/api.md`](../project/spec/v2/api.md) and is the source of
truth for both the inbox UI and the API's
`PATCH /feedback/{id}` validator.

### UI mapping

| Status        | Color token (Tailwind) | Icon (Lucide)      |
| ------------- | ---------------------- | ------------------ |
| `new`         | `slate-500`            | `inbox`            |
| `needs_info`  | `amber-500`            | `help-circle`      |
| `reviewing`   | `blue-500`             | `search`           |
| `accepted`    | `emerald-500`          | `check-circle`     |
| `planned`     | `indigo-500`           | `calendar-clock`   |
| `in_progress` | `violet-500`           | `play-circle`      |
| `shipped`     | `green-600`            | `package-check`    |
| `closed`      | `zinc-500`             | `circle-slash`     |
| `spam`        | `red-700`              | `shield-x`         |

Mirrored in
[`v2/core-idea.md#status-workflow`](../project/spec/v2/core-idea.md);
this table is the canonical pairing.

## Alternatives Considered

### Keep `rejected`, add the new values

Less migration work; backwards-compatible at the API level.
**Rejected because:** the original objection was naming, not
shape. Keeping `rejected` means every operator still has the
"don't type this" rule to remember, and the new `closed` would
fight `rejected` for the same use case.

### Database-enforced transition graph

Use a `CHECK` or trigger that validates `OLD.status →
NEW.status` is in the allowed set.
**Rejected because:** the transition rules are workflow policy,
not data integrity, and they will evolve faster than the schema.
Service-layer enforcement keeps the graph editable without a
migration and lets us return a structured 409 error to the API
client. The database keeps the easy invariants
(`status <> 'rejected'`, no NULL).

### Two enums (one "open", one "closed")

Split the type into open / terminal halves.
**Rejected because:** the inbox query (`WHERE status IN
(open_states)`) is identical to the single-enum case in cost, and
the join overhead of two columns is not worth the marginal
type-safety win.

### Numeric workflow position

Replace the enum with a `position SMALLINT` and a side table of
labels.
**Rejected because:** the workflow is fixed in v2.0; the
flexibility of free-form labels is exactly the kind of "every
team makes their own taxonomy" surface that v2.0's narrow scope
deliberately avoids.

## Consequences

### Positive

- The middle of the workflow is now expressible without abuse of
  `triaged`. Teams stop inventing their own conventions.
- `closed` reads well in notifications and in the changelog the
  inbox emits ("Issue X was closed by Y").
- `spam` is a dedicated lane, so spam handling can be tuned
  (auto-hide, no notifications, no metrics) without leaking into
  the rest of the workflow.

### Negative

- v1.0 clients that hard-coded the four-value enum break on
  upgrade. v1.0 has no advertised public API, but any internal
  scripts or saved searches need updating —
  [`v2/rollout.md`](../project/spec/v2/rollout.md) lists the
  surfaces.
- `rejected` lingers as a vestigial enum value forever. Cost is
  one line of documentation per release, not a real maintenance
  burden, but it is permanent.

### Neutral

- The v1.0 `triaged` value is renamed to `reviewing` in the same
  migration. `triaged` was rarely used in production; the rename
  is captured in [ADR 062](062-v1-to-v2-data-migration.md)'s
  Migration B alongside the `rejected → closed` rewrite.

### Mitigations

- The Pydantic `Status` enum is the single source of truth for
  the API; OpenAPI schema generation derives from it, so the
  docs and the validator can never disagree.
- `tests/test_status_workflow.py` exhaustively asserts the
  allowed-transition matrix from `v2/api.md`.
- Notification templates (ADR 061's `email_log` consumers) gain
  unit tests that render every (`old_status` → `new_status`)
  pair so a typo in a template can't ship silently.

## Implementation

- [`docs/project/spec/v2/schema.md`](../project/spec/v2/schema.md)
  — `ALTER TYPE` statements + `CHECK (status <> 'rejected')`.
- [`docs/project/spec/v2/api.md`](../project/spec/v2/api.md) —
  the canonical transition matrix.
- [`docs/project/spec/v2/core-idea.md`](../project/spec/v2/core-idea.md)
  — UI semantics and status copy.
- `src/feedback_triage/enums.py` — the Python `Status` enum
  (extended in v2.0).

## References

- [ADR 062](062-v1-to-v2-data-migration.md) — owns the actual
  `ALTER TYPE` and the `rejected → closed` data rewrite.
- [Postgres — `ALTER TYPE`](https://www.postgresql.org/docs/16/sql-altertype.html)
- [Postgres mailing list — DROP VALUE rationale](https://www.postgresql.org/message-id/CAH2-WzkSDB1Z6gZxKqEh1nPnLdC8WpO%2BrR-VQ7%3DHqf6PsCY1Pw%40mail.gmail.com)
