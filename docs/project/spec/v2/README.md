# SignalNest v2.0 spec — split topical files

This directory holds the detailed v2.0 spec, broken out by topic so
each file stays small enough to read end-to-end. The entry point and
single source of cross-references is [`../spec-v2.md`](../spec-v2.md).

| File                                       | Topic                                                                |
| ------------------------------------------ | -------------------------------------------------------------------- |
| [`schema.md`](schema.md)                   | Full DDL: enums, auth tables, tenancy tables, workspace data, `feedback_item` changes |
| [`api.md`](api.md)                         | All endpoints: auth, workspaces, feedback, public submission, dashboard, insights |
| [`auth.md`](auth.md)                       | Auth state machine, session cookies, tokens, password hashing        |
| [`multi-tenancy.md`](multi-tenancy.md)     | Workspace context, roles, public route addressing                    |
| [`ui.md`](ui.md)                           | Page routes, JS conventions, accessibility, public submission form   |
| [`email.md`](email.md)                     | Resend integration, fail-soft semantics, templates                   |
| [`security.md`](security.md)               | Cross-cutting security: rate limits, tenant isolation invariants, content limits, secrets, CSRF posture |
| [`rollout.md`](rollout.md)                 | Phased rollout, v1.0 → v2.0 cut-over, deployment, observability, background cron |
| [`tooling.md`](tooling.md)                 | Backend / frontend / build tooling stack                             |

Brand and visual direction live one level up in
[`../core-idea.md`](../core-idea.md). Status of v2.0 itself is
tracked in [`../spec-v2.md`](../spec-v2.md).
