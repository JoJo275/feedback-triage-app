# ADR 064: Pain vs. Priority — dual-field rationale

## Status

Accepted (2026-05-05). Phase gate: **Beta** — the feedback-detail
UI, the inbox sort/filter controls, and the notification copy all
depend on these two fields being separate. Locked before any v2.0
UI ships.

## Context

v1.0 has a single `pain_level SMALLINT` (1–5) field on
`feedback_item`. In practice, the team uses it for two
incompatible things:

1. **How much this hurts the customer.** A signal *from* the
   submitter, captured at intake. "I can't ship a build because of
   this" is a 5; "the spinner is the wrong shade of blue" is a 1.
2. **How much this matters to the team this sprint.** A decision
   *by* the team, made during triage. "Drop everything" is
   different from "we'll get to it eventually."

Collapsing both into one number forces a choice with no good
answers:

- If the team can edit `pain_level`, the field is no longer a
  customer signal — it becomes a tug-of-war between submitters
  saying "this is a 5" and operators saying "no, it's a 2." The
  data stops being a faithful record of what customers said.
- If the team cannot edit `pain_level`, sorting the inbox by
  pain produces a popularity contest: the loudest customer wins,
  no matter how strategic the issue is.

Real product teams handle this with two fields — one immutable
report, one mutable decision — and v2.0's narrow scope is the
right place to formalise that.

## Decision

v2.0 splits the single `pain_level` into two distinct columns,
both nullable, with different write rules and different UI
treatments.

### `pain_level` — submitter signal, integer 1–5

- **Who writes it:** the submitter, at intake. Collected via the
  feedback form.
- **Who edits it:** an admin can correct an obvious mistake
  (e.g. "10 out of 5 stars" cases), but the standard team
  workflow does **not** offer an edit affordance for this field.
- **Range:** integer `1..5` enforced by both Pydantic and a
  Postgres `CHECK (pain_level BETWEEN 1 AND 5)`. Same as v1.0.
- **Why integer not slider:** five buckets is the largest set
  that submitters can self-rank consistently; slider widgets
  collapse to "min, mid, max" in practice and add no signal.
- **Why not freeform numeric:** an open-ended scale (like a
  10-or-100-point Likert) loses the discriminator function — every
  submitter has a different idea of what "70" means.
- **Why nullable:** v1.0 rows that pre-date the form's pain field
  exist; backfilling them with a synthetic value would be a lie.

### `priority` — team decision, four-level enum

- **Who writes it:** the team during triage.
- **Who edits it:** any workspace member with the appropriate
  role (see [ADR 060](060-multi-tenancy-workspace-scoping.md)).
- **Values:** `low`, `medium`, `high`, `critical` (Postgres
  `priority_enum`).
- **Why enum not numeric:** the values are policy categories
  with operational consequences (`critical` triggers a
  notification escalation; `low` doesn't appear in the default
  inbox). Numbers invite "is this a 6 or a 7?" discussions; the
  four-level scale forces a real choice.
- **Why four levels:** three (`low`/`med`/`high`) collapses
  under load — everything urgent becomes `high`. Five-plus
  levels reproduce the granularity problem the enum was meant to
  fix. Four with a sharp `critical` gives an out-of-band lane
  for genuine emergencies without overloading `high`.
- **Why nullable:** a feedback item that has not yet been
  triaged has no priority. The inbox UI surfaces "needs
  prioritising" as a first-class state rather than treating
  `medium` as a secret default.

### Combined display

The feedback-detail page renders these as two separate widgets
side-by-side, never merged:

- **Pain meter** — five filled/empty pips with a tooltip
  ("Reported by submitter — not editable from triage").
- **Priority chip** — a coloured pill (`critical` red, `high`
  orange, `medium` blue, `low` slate) with an inline editor
  visible to triagers.

The inbox supports independent sort/filter on both fields. The
default sort is `priority DESC, pain_level DESC, created_at
ASC` — team decision first, customer signal as tiebreaker, age
as final tiebreaker. Workspaces can override via saved filters
(spec'd in [`v2/information-architecture.md`](../project/spec/v2/information-architecture.md)).

### Composite metrics live elsewhere

A team that wants a single "score" — for example, `priority *
pain_level` — gets it via a derived view or a saved filter, not
a stored column. The base table records facts; rankings are
queries.

## Alternatives Considered

### Keep one field, rename to `score`

Stick with one integer; remove ambiguity by calling it a score.
**Rejected because:** renaming doesn't fix the conflicted-write
problem. Either the submitter owns the score (popularity
contest) or the team does (no customer signal). The name is
not the disease.

### Three fields — pain, priority, business value

Add a third axis ("how much money is on the line").
**Rejected because:** v2.0 deliberately stays narrow. Business
value is real but is a downstream concern that needs CRM
context the app doesn't have. A field that gets filled with
"medium" by every operator is worse than no field.

### Single mutable field, with audit log

One column; track who set it to what via the audit table.
**Rejected because:** the UI still has to surface "this is the
submitter's number" vs "this is the team's number" somewhere,
and reconstructing that from an audit log on every render is
both expensive and fragile. Two columns is the storage that
matches the semantics.

### Computed priority from `pain_level`

`priority` is a generated column based on
`pain_level`.
**Rejected because:** that's the same field with a different
name. The whole point is that the team's decision diverges from
the submitter's report — that divergence is the data we want.

## Consequences

### Positive

- The submitter's signal is preserved verbatim, forever. The
  data faithfully answers "what did customers report?" months
  later, even after team priorities have shifted.
- The team's decision is editable, auditable, and named in the
  UI in language operators recognise (`critical`, not "5").
- Inbox views can be tuned to either signal independently —
  "show me everything customers said is a 5 that we have not
  triaged" is one filter; "show me everything `critical` regardless
  of customer pain" is another.
- The `null priority` state lets the inbox surface "untriaged"
  as a first-class lane.

### Negative

- Two fields cost two form fields (intake form for pain, triage
  edit for priority) and two columns of UI real estate on the
  detail page.
- Operators who *do* want a single number for sorting need to
  pick which one or write a saved filter that combines them.
  This is a documentation problem, not a model problem.
- Migrating v1.0 rows: `pain_level` carries over unchanged;
  `priority` is `NULL` for every existing row. Inbox reads must
  handle the `NULL` case from day one.

### Neutral

- The `priority_enum` joins the
  [ADR 063](063-status-enum-extension.md) status enum as a
  Postgres native type with its own
  `ALTER TYPE … ADD VALUE` upgrade path.

### Mitigations

- The intake form copy explicitly tells submitters their pain
  rating is not a "request priority" — it's a record of impact
  on them. Reduces the natural drift toward "everyone clicks 5
  to get attention."
- The triage UI shows the submitter's pain rating prominently
  next to the priority editor; operators triaging a `pain=5,
  priority=low` divergence see it immediately and can adjust if
  it's a mistake.
- `tests/test_inbox_sort.py` exhaustively asserts the default
  sort order over a fixture covering all
  (`priority`, `pain_level`, `created_at`) combinations,
  including the all-NULL-priority case.

## Implementation

- [`docs/project/spec/v2/schema.md`](../project/spec/v2/schema.md)
  — `priority_enum`, the `priority` column DDL,
  `pain_level` `CHECK` (unchanged from v1.0).
- [`docs/project/spec/v2/information-architecture.md`](../project/spec/v2/information-architecture.md)
  — feedback-detail layout (pain meter + priority chip).
- [`docs/project/spec/v2/api.md`](../project/spec/v2/api.md) —
  request/response shapes for `pain_level` and `priority`.
- [`docs/project/spec/v2/core-idea.md`](../project/spec/v2/core-idea.md)
  `#pain-level-vs-priority` — narrative for the team.
- `src/feedback_triage/enums.py` — `Priority` Python enum.

## References

- [ADR 060](060-multi-tenancy-workspace-scoping.md) — defines
  the role that gates priority editing.
- [ADR 062](062-v1-to-v2-data-migration.md) — the migration
  that adds the `priority` column nullable on existing rows.
- [ADR 063](063-status-enum-extension.md) — sibling enum
  (`status_enum`) that follows the same Postgres-native-enum
  pattern.
