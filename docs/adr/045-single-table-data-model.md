# ADR 045: Single-Table Data Model for v1.0

## Status

Proposed

## Context

The Feedback Triage App models one resource — a feedback item — with a
small fixed set of fields (title, description, source, pain_level, status,
timestamps). Every UI screen, every API endpoint, and every test in v1.0
operates on this single resource.

A common reflex on a "real" app is to introduce satellite tables on day
one — `users`, `tags`, `comments`, `audit_log`, `attachments` — to be
ready for "later." For this project's scope (portfolio-grade v1.0, no
auth, no multi-tenancy) those tables are dead weight.

## Decision

v1.0 uses a single table: `feedback_item`. No `users`, `tags`,
`comments`, or `attachments`.

A second table requires either:

1. A demonstrated need from a feature actually being shipped, **or**
2. An ADR superseding this one with the new entity-relationship sketch
   and migration plan.

## Alternatives Considered

### Multi-table from day one (`users` + `feedback_item` + `tags`)

**Rejected because:** none of the v1.0 features require it. Adds
migration churn, joins on every list query, and decisions about FK
cascade behaviour that this project does not need to make yet.

### Single JSON column for all metadata

**Rejected because:** loses native enum + CHECK enforcement, defeats
typed access in SQLModel, and makes filtering / sorting in SQL awkward.

## Consequences

### Positive

- Migrations are short and review-friendly.
- The list query is a plain `SELECT … ORDER BY created_at DESC LIMIT n`.
- Tests don't need fixture orchestration across tables.

### Negative

- Adding the first satellite table will require an ADR and a clear
  migration. That cost is intentional.

### Neutral

- This decision is local to v1.0 scope; it does not foreclose growth.
