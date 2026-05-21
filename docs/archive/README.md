# Documentation Archive

This directory stores documentation kept for historical context that is no longer authoritative for active development.

## Use This Directory For

- Out-of-date docs that describe removed or superseded behavior
- Historical migration notes kept for traceability
- Prior design writeups that no longer match the active architecture

## Do Not Use This Directory For

- Active specifications (keep in `docs/project/spec/`)
- Active design docs (keep in `docs/design/`)
- Superseded ADRs (keep in `docs/adr/archive/`)

## Archiving Rules

1. Add a short archive note at the top of each file:
   - Archived on: `YYYY-MM-DD`
   - Superseded by: link to active doc
   - Reason: one sentence
2. Keep the original document content intact except for the archive note and link fixes.
3. Never treat archived docs as source of truth for implementation decisions.

## Source Of Truth

Current implementation guidance should come from:

- [`docs/project/spec/spec-v2.md`](../project/spec/spec-v2.md)
- [`docs/project/spec/spec-v1.md`](../project/spec/spec-v1.md) where historical v1 context is still needed
- [`docs/design/`](../design/)
- [`docs/adr/`](../adr/)
