# SignalNest v2.0 spec — split topical files

This directory holds the detailed v2.0 spec, broken out by topic so
each file stays small enough to read end-to-end. The entry point and
single source of cross-references is [`../spec-v2.md`](../spec-v2.md).

## Brand & product

| File                                       | Topic                                                                |
| ------------------------------------------ | -------------------------------------------------------------------- |
| [`core-idea.md`](core-idea.md)             | v2.0 brand brief — locked strings, voice rules, per-surface checklist |
| [`business.md`](business.md)               | Target user, value prop, pricing, growth, success metrics            |

## Architecture & contract

| File                                       | Topic                                                                |
| ------------------------------------------ | -------------------------------------------------------------------- |
| [`schema.md`](schema.md)                   | Full DDL: enums, auth tables, tenancy tables, workspace data, `feedback_item` changes |
| [`api.md`](api.md)                         | All endpoints: auth, workspaces, feedback, public submission, dashboard, insights |
| [`auth.md`](auth.md)                       | Auth state machine, session cookies, tokens, password hashing        |
| [`multi-tenancy.md`](multi-tenancy.md)     | Workspace context, roles, public route addressing                    |
| [`repo-structure.md`](repo-structure.md)   | Directory layout, module boundaries, naming conventions              |

## Frontend

| File                                       | Topic                                                                |
| ------------------------------------------ | -------------------------------------------------------------------- |
| [`ui.md`](ui.md)                           | Page routes, JS conventions, accessibility, public submission form   |
| [`pages.md`](pages.md)                     | Per-page catalog: sections, components, copy strings, empty states   |
| [`css.md`](css.md)                         | CSS conventions, design tokens, Tailwind config, component vocabulary |

## Cross-cutting

| File                                       | Topic                                                                |
| ------------------------------------------ | -------------------------------------------------------------------- |
| [`email.md`](email.md)                     | Resend integration, fail-soft semantics, templates                   |
| [`security.md`](security.md)               | Rate limits, tenant isolation invariants, content limits, secrets, CSRF posture |
| [`risks.md`](risks.md)                     | Consolidated risk register with severity scores and canaries         |

## Operations

| File                                       | Topic                                                                |
| ------------------------------------------ | -------------------------------------------------------------------- |
| [`tooling.md`](tooling.md)                 | Backend / frontend / build tooling stack                             |
| [`rollout.md`](rollout.md)                 | Phased rollout, v1.0 → v2.0 cut-over, deployment, observability, background cron |
| [`implementation.md`](implementation.md)   | Phase-by-phase build plan with deliverables, DoD, verification steps |
| [`adrs.md`](adrs.md)                       | Accepted ADRs and the TBD list with phase gates                      |

## Reference

| File                                       | Topic                                                                |
| ------------------------------------------ | -------------------------------------------------------------------- |
| [`glossary.md`](glossary.md)               | Term definitions used across all v2 files                            |

The canonical SignalNest brand brief lives in this directory at
[`core-idea.md`](core-idea.md). The v2 entry point is
[`../spec-v2.md`](../spec-v2.md). A short redirect stub lives at
[`core-idea.md`](core-idea.md) for legacy links only.
