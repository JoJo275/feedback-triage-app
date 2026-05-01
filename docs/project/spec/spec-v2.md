# Feedback Triage App — Spec v2.0 (Draft)

> **Status:** Draft. Not yet authoritative.
> **Predecessor:** [`spec-v1.md`](spec-v1.md) — shipped v1.0 scope (single
> `feedback_item` resource, no auth, sync DB driver, Railway deploy).
> **Goal of v2.0:** capture the next batch of features layered on top of
> the v1.0 baseline. Until this document lands at "Ratified" below,
> `spec-v1.md` remains the single source of truth.
>
> **Reading order:** read `spec-v1.md` first for the platform contract
> (schema, request envelope, validation rules, deploy model). This file
> only documents *changes* and *additions*. Anything not contradicted
> here inherits from v1.0 unchanged.

---

## Status

| Field            | Value                                                |
| ---------------- | ---------------------------------------------------- |
| Version          | 2.0                                                  |
| State            | Draft (not ratified)                                 |
| Owner            | TBD                                                  |
| Last reviewed    | TBD                                                  |
| Ratification gate | All v1.0 Must items green + this section flipped to "Ratified" |

When this document is ratified, update:

- The **Status** row above to `Ratified`.
- [`docs/index.md`](../../index.md) and [`README.md`](../../../README.md)
  to point at v2.0 as the active spec.
- [`.github/copilot-instructions.md`](../../../.github/copilot-instructions.md)
  to reference v2.0 as the authoritative spec.

---

## Requirement Tiers

Same Must / Should / Nice / Defer system as v1.0. See
[`spec-v1.md` — Requirement Tiers](spec-v1.md#requirement-tiers) for the
definitions.

---

## What Is Inherited from v1.0

Unless explicitly overridden in this document, v2.0 inherits **everything**
from v1.0, including:

- `feedback_item` table, native Postgres enums, CHECK constraints, and
  the `BEFORE UPDATE` trigger maintaining `updated_at`.
- Request/response envelopes (`items`/`total`/`skip`/`limit` for lists),
  ISO 8601 UTC datetimes with `Z` suffix.
- Sync FastAPI routes (`def`, not `async def`).
- Static-HTML + vanilla-JS frontend served from the same FastAPI process.
- Session-per-request DB lifecycle via `get_db`.
- Postgres-backed pytest suite, gated Playwright smoke suite.
- Railway deploy via GitHub source, `alembic upgrade head` as the
  pre-deploy command.
- Container hardening posture (non-root, `HEALTHCHECK`, multi-stage).

If a v2.0 feature requires changing one of these, document the change
explicitly in the relevant section below and add an ADR.

---

## Out of Scope (Inherited from v1.0)

Unless lifted in this document, the v1.0 deferrals continue to apply.
See [`spec-v1.md` — Future Improvements After v1.0](spec-v1.md#future-improvements-after-v10)
for the full list.

---

## v2.0 Theme

> _One-paragraph summary of what v2.0 is **for**. Examples: "Make the
> tool usable for a small team — add accounts, multi-user feedback
> ownership, and basic auditing." Or: "Improve triage UX — add labels,
> bulk actions, and full-text search." Without a stated theme, scope
> creep is guaranteed._

TBD.

---

## Proposed Features

For each feature, capture: **tier**, **why now**, **schema impact**,
**API surface**, **UI surface**, **test impact**, **migration plan**,
and **rollout / rollback notes**. Use the v1.0 spec's section style as
the model.

### Feature 1: TBD

- **Tier:** TBD
- **Why now:** TBD
- **Schema impact:** TBD
- **API surface:** TBD
- **UI surface:** TBD
- **Tests:** TBD
- **Migration plan:** TBD
- **Rollout:** TBD

### Feature 2: TBD

- **Tier:** TBD
- ...

---

## Schema Changes

> Diff from v1.0. Tables added, columns added/changed, new enums, new
> indexes, new triggers. Every change requires a hand-reviewed Alembic
> migration.

TBD.

---

## API Changes

> Diff from v1.0. New endpoints, breaking changes (avoid; if needed,
> introduce `/api/v2/`), modified envelopes.

TBD.

---

## UI Changes

> Diff from v1.0. New pages, new components, behavior changes. Every
> UI change touches the Playwright smoke suite.

TBD.

---

## Migration & Rollout Plan

> How v2.0 ships. Single big-bang release? Phased rollout? Feature
> flags? Backwards compatibility window for the API?

TBD.

---

## ADRs to Write for v2.0

> List ADRs that must accompany v2.0 implementation. Numbered from the
> next free slot in [`docs/adr/`](../../adr/).

TBD.

---

## Future Improvements After v2.0

> Items considered and explicitly punted. Keeps the next reviewer from
> re-litigating the same trade-offs.

TBD.

---

## Related Docs

- [`spec-v1.md`](spec-v1.md) — shipped v1.0 spec (canonical until v2.0 ratifies)
- [`../implementation.md`](../implementation.md) — phase plan; will need a v2.0 phase appendix
- [`../questions.md`](../questions.md) — open questions and decisions
- [`../../adr/`](../../adr/) — ADRs governing the platform
