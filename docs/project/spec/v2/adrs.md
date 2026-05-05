# v2.0 — ADRs to write

> Topical detail file. Entry point: [`../spec-v2.md`](../spec-v2.md).
> Filing conventions: [`../../../adr/.instructions.md`](../../../adr/.instructions.md).

This file is the *to-do list of architectural decisions for v2.0*.
It tracks which ADRs are accepted, which are still TBD, and what
each TBD must answer before its corresponding phase can close.

When an ADR ships, **delete its row from the TBD section here** and
move it to the Accepted section. Don't leave stale entries.

> **Phase codenames.** *Alpha / Beta / Final / Polish* are aliases
> for **Phases 1 / 2 / 3 / 4** in [`implementation.md`](implementation.md).
> Phase 0 (foundation, no code yet) is not aliased.
> See [`glossary.md`](glossary.md).

---

## Accepted (already merged)

| #   | Title                                       | Phase enabled    |
| --- | ------------------------------------------- | ---------------- |
| 056 | Style guide page (`/styleguide`)            | Alpha            |
| 057 | Brand vs. repo naming (SignalNest / `feedback-triage-app`) | Alpha |
| 058 | Tailwind via Standalone CLI                 | Alpha            |
| 059 | Auth model — cookie sessions + Argon2id     | Alpha            |
| 060 | Multi-tenancy / workspace scoping           | Alpha            |
| 061 | Email provider (Resend) + fail-soft semantics | Alpha          |
| 062 | v1.0 → v2.0 data migration ([file](../../../adr/062-v1-to-v2-data-migration.md)) | Beta |
| 063 | Status enum extension + `rejected` deprecation ([file](../../../adr/063-status-enum-extension.md)) | Beta |
| 064 | Pain vs. Priority dual-field rationale ([file](../../../adr/064-pain-vs-priority-dual-fields.md)) | Beta |

---

## TBD (must land alongside or before their phase)

Order is intentional: each ADR below depends only on the ones
above it.

*(All Beta-phase ADRs are now accepted — see the table above.
This section is preserved for the next round of TBD ADRs.)*

---

## Recommended ADRs (file when relevant)

These are not v2.0 ratification gates, but each one is a real
decision that someone will eventually rediscover the hard way if
not written down.

| #   | Title (proposed)                                              | When                                    |
| --- | ------------------------------------------------------------- | --------------------------------------- |
| 065 | Rate-limit posture — public submission form                   | Before the public form ships (Beta).    |
| 066 | Content limits — feedback description / note length, image upload posture | Before the public form ships.   |
| 067 | CSP / security headers configuration                          | Before public launch.                   |
| 068 | Cookie + session lifetime tuning + rolling renewal policy     | After Resend (Final), before launch.    |
| 069 | Inline-SVG charting — when (if ever) to swap for a library    | Before any v3 chart ask.                |
| 070 | Background-job posture (cron vs. queue) for stale-item / cleanup | Before scheduled work lands.         |
| 071 | Audit log surface — what writes to log, what reads it         | Before paid tier.                       |
| 072 | Public-roadmap caching strategy                                | Before any "real" external traffic.    |
| 073 | Domain handling — workspace-on-subpath vs. custom domains     | Before paid tier.                       |
| 074 | Privacy & data-retention policy                                | Before public launch.                   |
| 075 | Demo-workspace reset job                                      | Before demo user goes live (Final).     |

---

## Authoring rules (reminder)

- One ADR per decision. If a single PR introduces two unrelated
  decisions, file two ADRs.
- ADRs are immutable once Accepted. Supersession is a new ADR that
  links back.
- Prefer **decided** over **comprehensive**. An ADR is the
  smallest writeup that lets a future reader avoid re-relitigating.
- Cross-link the relevant spec file ([`schema.md`](schema.md),
  [`api.md`](api.md), [`auth.md`](auth.md), …) so the ADR doesn't
  re-state what the spec already says.

---

## Cross-references

- [`../../../adr/.instructions.md`](../../../adr/.instructions.md) — ADR creation procedure.
- [`implementation.md`](implementation.md) — phase plan referencing these IDs.
- [`../spec-v2.md`](../spec-v2.md) — ADRs table (the canonical
  short version).
