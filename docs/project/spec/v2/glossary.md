# v2.0 — Glossary

> Topical detail file. Entry point: [`../spec-v2.md`](../spec-v2.md).

Short, unambiguous definitions for terms used across v2.0. If a
term is used in two files with two meanings, fix it; this glossary
is the tie-breaker.

---

| Term                  | Meaning                                                                                                  |
| --------------------- | -------------------------------------------------------------------------------------------------------- |
| **SignalNest**        | Brand name for the v2.0 product. The repo slug stays `feedback-triage-app` ([ADR 057](../../../adr/057-brand-vs-repo-naming.md)). |
| **Workspace**         | A tenant. Owns its feedback, tags, submitters, members. URL-prefixed `/w/<slug>/`.                       |
| **Workspace slug**    | URL-safe, globally unique. Lowercase alphanumeric + hyphens. Cannot be changed in v2.0.                  |
| **Membership**        | A row in `workspace_memberships` linking a `user` to a `workspace` with a `workspace_role`.              |
| **Platform role**     | Field on `users.role` (`user_role_enum`) ∈ {`admin`, `team_member`, `demo`}. Cross-cutting; defaults to `team_member`. |
| **Workspace role**    | Field on `workspace_memberships.role` (`workspace_role_enum`) ∈ {`owner`, `team_member`}.                |
| **Owner**             | A workspace member with `workspace_role = 'owner'`. Can manage members and settings.                     |
| **Team member**       | A workspace member with `workspace_role = 'team_member'`. Full feedback CRUD, no settings. UI label: *Team member*. |
| **Admin**             | Platform-wide; the project author. Can switch into any workspace; not a workspace role.                  |
| **Submitter**         | Email-known person who has submitted feedback to a workspace. Row in `submitters`. Does not have a login. |
| **Public submitter**  | Anonymous person who submits via `/w/<slug>/submit` without an email.                                    |
| **Demo user**         | A shared, read-only login pinned to the demo workspace. Resets nightly.                                  |
| **Feedback item**     | One row in `feedback_item`. Always belongs to exactly one workspace.                                     |
| **Status**            | The workflow position of a feedback item ∈ {`new`, `needs_info`, `reviewing`, `accepted`, `planned`, `in_progress`, `shipped`, `closed`, `spam`}. |
| **Priority**          | Team-set urgency ∈ {`low`, `medium`, `high`, `critical`}. Editable by members.                           |
| **Pain level**        | Submitter-set magnitude 1–5. Editable only by the submitter (or in the public form).                     |
| **Tag**               | Workspace-scoped label applied to feedback items. M:N via `feedback_tags` (junction table).             |
| **Internal note**     | Workspace-only comment on a feedback item. Never shown on public surfaces.                               |
| **Publish**           | The act of flipping `published_to_roadmap` or `published_to_changelog`. The only way an item appears on a public page. |
| **Public form**       | The unauthenticated submission page at `/w/<slug>/submit`.                                                |
| **Public roadmap**    | Read-only page at `/w/<slug>/roadmap/public`. Filtered by `published_to_roadmap = true`.                 |
| **Public changelog**  | Read-only page at `/w/<slug>/changelog/public`. Filtered by `status = 'shipped' AND published_to_changelog`. |
| **Mini demo (FU1)**   | The landing page's client-side interactive widget. Vanilla JS, no backend.                               |
| **Five-phase workflow** | Intake → Triage → Prioritize → Act → Close the loop. The product's organizing model.                   |
| **Close the loop**    | Notifying email-known submitters when their feedback ships. Performed via Resend. Fail-soft.             |
| **Fail-soft**         | A side-effect (email send, log emission) is best-effort: if it fails, the user-facing action still succeeds. The failure is recorded. |
| **WorkspaceContext**  | FastAPI dependency that resolves `<slug>` + the current user → `(workspace, membership)` or 404. Every workspace-scoped route depends on it. |
| **Cross-tenant lookup** | A request whose `<slug>` and resource id belong to different workspaces. Always returns 404 — **never** 403, **never** the row. |
| **Canary test**       | A test whose only purpose is to fail loudly when an invariant is broken. Examples: cross-tenant 404, session-per-request reuse. |
| **Tier**              | Tag on a requirement: `Must`, `Should`, `Nice`, `Defer`. Inherited from v1.0.                            |
| **Phase gate**        | The condition that closes a phase. Stated in [`implementation.md`](implementation.md).                   |
| **Locked string**     | A user-facing string that may not be edited without an ADR. Examples: tagline, description, name.        |
| **`sn-*` class**      | Bespoke component class in `static/css/components.css` (or `layout.css` for layout primitives). The only project-defined CSS classes; everything else is a Tailwind utility. |
| **Token**             | Email-borne, single-use string for verify-email / reset-password / accept-invitation. Stored as separate tables (`email_verification_tokens`, `password_reset_tokens`, `workspace_invitations.token_hash`). Distinct from session cookies. |
| **Session**           | The cookie-backed authenticated state. Stored server-side in `sessions`. **Sliding 7-day expiry** — `expires_at` is extended on every authenticated request (see [`auth.md`](auth.md)). |
| **Sliding expiry**    | A TTL that resets to its full window every time the credential is used. Contrast with *absolute* expiry, which is fixed from issue time. |
| **Stale item**        | A feedback item where `created_at < now() - interval '14 days' AND status IN ('new', 'needs_info')`. Surfaced on Inbox and Dashboard summary cards. |
| **Phase**             | A numbered build stage from [`implementation.md`](implementation.md): Phase 0 (Pre-v2), Phase 1 (Alpha), Phase 2 (Beta), Phase 3 (Final), Phase 4 (Polish). The codenames Alpha/Beta/Final and the build-order numbers in [`../spec-v2.md`](../spec-v2.md) are aliases — the canonical numbering is **Phase 0–4**. |

---

## Cross-references

- [`schema.md`](schema.md) — tables behind these terms.
- [`auth.md`](auth.md) — sessions, tokens, roles in motion.
- [`multi-tenancy.md`](multi-tenancy.md) — workspace, membership, context.
- [`core-idea.md`](core-idea.md) — brand-side language ("close the loop", "signal").
