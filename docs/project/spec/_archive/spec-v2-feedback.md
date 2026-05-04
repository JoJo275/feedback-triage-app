# Spec v2.0 — Reviewer Feedback

> **Audience:** the spec-v2.md author. This is direct, unfiltered
> pushback on the v2.0 draft as of May 2026. Read this **before**
> finalizing v2.0; the goal is to surface decisions you have not made
> yet, not to talk you out of v2.0.
>
> **Status of this file:** review notes. Not authoritative. Once you
> decide on each item below, fold the decisions back into `spec-v2.md`
> (or an ADR) and delete or archive this file.

---

## TL;DR

The current v2.0 draft is **a stack proposal, not a spec**. It lists
tools and tables but does not say:

- **Why** v2.0 exists (the Theme section is `TBD`).
- **What user-facing problem** it solves that v1.0 doesn't.
- **What scope** is in vs. out.
- **What the success criteria are** for shipping it.
- **What the API and schema diffs** from v1.0 actually look like.

Without those, the stack list is unanchored: there's no way to argue
"do we really need TanStack Query?" if the spec doesn't say what
features need it.

The biggest concern: **v2.0 as drafted is a from-scratch rewrite of
the frontend** (React/Vite/TS/Tailwind/Router/RHF/Zod) plus a new auth
subsystem plus an email subsystem. That's three big features stacked.
Each is defensible alone; together they delete the v1.0 "small but
sharp" thesis and turn this into a year-long rebuild.

---

## Critical Issues

### 1. v2.0 has no stated theme — fix this first

The `## v2.0 Theme` section is `TBD`. Until it's filled, every other
decision is unanchored. Pick one:

- **A. "Make it usable for a small team"** — auth, email confirmation,
  password reset, multi-user feedback ownership. The current draft is
  closest to this.
- **B. "Improve triage UX"** — labels, bulk actions, full-text search,
  saved filters. No auth, no email.
- **C. "Polish for portfolio review"** — analytics, audit log, export.
  No auth.

A and B+C are mutually exclusive for a single release. Trying to do
all of them is what produces the "8 services" architecture the draft
itself warns against.

**Recommendation:** pick A or B for v2.0; defer the other to v3.0.

### 2. Frontend rewrite is a separate concern from auth

The draft conflates two decisions:

1. **"Should v2.0 add auth?"** (a feature question)
2. **"Should v2.0 replace the frontend with React?"** (an architecture
   question)

These are independent. You can add auth to the v1.0 static-HTML +
vanilla-JS frontend with about a day of work — login form, cookie
session, `/api/auth/me` endpoint, two new pages. You do not need
React, Vite, TypeScript, Tailwind, React Router, TanStack Query, React
Hook Form, Zod, and shadcn/ui to gate routes behind a login.

The v1.0 spec is explicit (lines 487–504): static HTML + vanilla JS,
**no Jinja, no bundler, no SPA framework**. Replacing all of that
needs an ADR with a real "why now" — not a one-liner that React is
"better for a polished product-style dashboard."

**Recommendation:** split the frontend rewrite into its own v3.0 (or
keep it deferred indefinitely). Ship auth on the existing frontend.
If the existing frontend isn't enough, the *spec* should say what's
missing — not "let's switch to React because that's what serious
SaaS uses."

### 3. The "lowest-cost serious setup" still doubles your services

The draft says "1 FastAPI service + 1 Postgres = lowest-cost setup,"
which is true relative to the 5-service nightmare it warns against —
but it's still **double** the v1.0 footprint:

| Layer            | v1.0                   | v2.0 draft                    |
| ---------------- | ---------------------- | ----------------------------- |
| Backend          | FastAPI (sync)         | FastAPI (async — see #4)      |
| Frontend         | Static HTML in same process | React static build in same process |
| DB               | Postgres               | Postgres                      |
| Email            | (none)                 | Resend (external)             |
| Auth             | (none)                 | Tokens + sessions/JWT         |
| External deps    | 0                      | 1 (Resend)                    |

Resend's free tier is generous, but it's still **a third-party
dependency in the production critical path** for password reset. If
Resend is down, nobody can reset their password. Document the SLA
expectation explicitly in the spec.

**Recommendation:** spec out the Resend failure mode. Specifically:
what happens when Resend is unavailable? Do password-reset requests
queue? Fail fast? Email the admin?

### 4. Async DB driver is buried in the package list

The draft's "Suggested package set" lists `asyncpg`. The v1.0 spec
**explicitly defers** async (see ADR 050, "Sync DB driver in v1.0").
Switching to async is a rewrite of every route, every dependency, and
every test — not a casual line item.

If v2.0 needs async, that's an ADR with measured numbers showing why
sync isn't enough at the expected v2.0 traffic. If it doesn't need
async, drop `asyncpg` from the list and stay on sync.

**Recommendation:** drop `asyncpg`. If a specific feature requires it,
call that feature out and write the ADR.

### 5. Auth choice is hand-waved

The draft says "Cookie-based session or JWT" and "I'd prefer secure
HTTP-only cookies." That's a 30-second answer to a multi-day
decision. Consider:

- **Cookie sessions** require server-side session storage (DB or
  Redis). The draft says "no Redis" — so sessions go in Postgres,
  with all the row-churn that implies.
- **JWT** avoids server-side state but is famously easy to get wrong
  (rotation, revocation, refresh tokens). Most "JWT auth" tutorials
  ship subtly broken implementations.
- **FastAPI Users** is mentioned as optional. If you pick it, that's
  the auth decision — write it down. If you don't, write the auth
  flows out (signup → confirm → login → reset → logout) including
  every endpoint, every redirect, every token TTL.

**Recommendation:** pick one auth model and write the full state
machine into the spec, including:
  - Token TTLs (verification: 24h? reset: 1h?).
  - What happens on token reuse (single-use vs. multi-use).
  - Rate-limit thresholds and what triggers them.
  - Where session/refresh tokens live (cookie attributes, DB schema).
  - Logout semantics (revoke session row vs. blacklist JWT vs. just
    drop the cookie).

### 6. The table list is sketched, not specified

The "Recommended database tables" block lists nine tables with one-line
purposes. That's not a schema. v1.0's spec dedicates ~200 lines to
**one** table; v2.0 needs at least the same rigor for nine. For each
table, spec needs:

- Columns (with types, nullability, defaults).
- Constraints (FKs, CHECK constraints, uniques).
- Enums (at the DB level — v1.0 conventions).
- Indexes.
- Triggers (e.g., `updated_at`).
- Migration strategy from v1.0's single `feedback_item` table to a
  multi-table schema (FK on user_id? backfill? data migration?).

Without this, the schema is one autogenerated migration's worth of
"oh that doesn't fit" pain away from a partial rewrite.

**Recommendation:** before any code, write each table's full DDL into
the spec. v1.0's `feedback_item` section is the model.

### 7. "Build the v1.0 schema into v2.0" is a migration question, not a footnote

v2.0 introduces `users` and presumably wants `feedback.user_id` (so
each item has an owner). The current `feedback_item` rows have no
owner. Migration options:

- **A.** Backfill all existing rows to a "system" or "anonymous" user.
- **B.** Hard cut-over — drop existing rows.
- **C.** Make `user_id` nullable and treat null as "anonymous v1.0
  data."

The spec must pick one and say so. Defaulting to "we'll figure it out"
during implementation is how data loss happens.

**Recommendation:** decide A/B/C in the spec. If A, define the system
user.

### 8. Audit log + email + tags + types + statuses + notes + votes is too many features

The "Recommended database tables" block names nine tables. Even if
each is small, that's nine schema sections, nine sets of CRUD
endpoints, nine UI surfaces, nine sets of tests. The v1.0 spec covers
**one** table and runs ~1700 lines.

**Recommendation:** for v2.0, pick the **minimum** set that delivers
the chosen Theme (#1):
  - Theme A (multi-user): `users`, `email_verification_tokens`,
    `password_reset_tokens`, `feedback` (with `user_id`).
  - Theme B (triage UX): `feedback_tags`, `feedback_statuses` (or
    inline), full-text index. **No** auth, **no** users.

Defer everything else (notes, votes, types, audit log) to a later
release. Each one becomes its own minor version.

### 9. Cost claims are optimistic

The draft says "almost no Railway compute cost" for the auth/email
features. That ignores:

- React static-build asset size (typical Vite + Tailwind + RHF + Zod
  + TanStack Query bundle: 200–400KB gzipped). Egress on Railway is
  metered.
- Postgres row growth from session tokens, verification tokens, and
  reset tokens. Bounded, but non-zero — and you'll need a cleanup job
  (the spec doesn't mention one).
- Background email sends are described as "send directly from
  request" — fine for low volume, but a slow Resend response now
  blocks the user's signup HTTP request. That couples your p95
  latency to Resend's p95 latency.

**Recommendation:** add a "Cost & latency model" section to v2.0 with
explicit numbers. The Railway $5 credit assumption is fragile when
the bundle size and egress aren't disclosed.

---

## Smaller Issues

### 10. Documentation pollution

The pasted block lives below `## Related Docs`, which is supposed to
be the last section of the file. As-is, the spec ends with "tools:"
and a free-form dump. Reformat: stack/tools content moves into the
Proposed Features and ADRs sections. (Done in this pass — see the
reformatted `spec-v2.md`.)

### 11. Mixed pricing claims need dating

"Resend free plan lists 3,000 emails/month" — true today, may not be
true in 12 months. Pricing claims age fast. Mark the date next to the
number and either accept stale data or set a calendar reminder to
refresh.

### 12. shadcn/ui mentioned twice with different recommendations

Once as "Optional UI helpers," once as "I would add shadcn/ui only
after the core app works." Pick one. (If the answer is "later," it
doesn't belong in the v2.0 spec at all.)

### 13. Vitest mentioned but no test coverage target

If v2.0 adds a frontend test framework, the spec needs to say what
"Done" means. v1.0 says "Postgres-backed pytest + Playwright smoke."
v2.0 should say "Vitest + RTL with X% line coverage on the React
components" or explicitly say "no Vitest target until UI stabilizes."

### 14. `@hookform/resolvers + Zod` is an axis the spec doesn't justify

Zod schemas at the frontend duplicate Pydantic schemas at the backend.
You either:
  - Generate frontend types from the OpenAPI schema (one source of
    truth, the backend), or
  - Hand-write Zod schemas (two sources of truth that drift).

The draft picks (b) implicitly. (a) is the better choice for a
type-safe FastAPI app. Document the decision.

### 15. "React deployment: Build static files and serve from FastAPI"

Fine choice, but the spec should say:
- Where the build artifact lives in the container.
- What `StaticFiles` mount serves it.
- How `/api/v1/*` and `/app/*` and `/static/*` paths are partitioned
  (and how the SPA's client-side routing avoids 404s on refresh —
  the classic "SPA fallback to index.html" rule).

### 16. Audit-logs vs. event sourcing

`audit_logs` is listed as "Optional later." If you add it, decide
upfront whether it's append-only (correct) or mutable (wrong). v1.0's
`updated_at` trigger isn't an audit log — it overwrites.

---

## Things the draft gets right

To balance the above:

- **External email provider over self-hosted SMTP.** Right call.
  Self-hosting email in 2026 is masochism.
- **No Redis early.** Good. Postgres can hold sessions and tokens
  fine for the v2.0 traffic profile.
- **No Celery/background worker.** Good. Adds a service and a moving
  part for a feature (transactional email) that doesn't need
  durability beyond "retry on next request."
- **Resend over SES initially.** Right for DX; SES is cheaper but the
  AWS setup tax is real.
- **"Static React served by FastAPI."** Right deployment pattern if
  React is the choice — avoids the second Railway service.
- **Token storage as hashes.** Correct security posture.
- **No WebSockets, no AI summaries.** Right scope discipline (which
  makes the React rewrite stand out as inconsistent).

---

## Recommended Next Steps for the Spec Author

1. **Pick a Theme (#1).** One sentence. Write it at the top of v2.0.
2. **Decide: frontend rewrite yes/no (#2).** If yes, write an ADR
   defending it. If no, drop React/Vite/TS/Tailwind/Router/RHF/Zod
   from the package list.
3. **Decide: sync vs. async (#4).** If async, write an ADR with
   numbers. If not, drop `asyncpg`.
4. **Pick an auth model (#5).** Spec the full state machine.
5. **Spec the schema diff (#6, #7).** Full DDL for every new table;
   migration plan for `feedback_item` → multi-user.
6. **Cut the table list (#8).** Pick the minimum that the Theme
   requires.
7. **Add a Cost & latency section (#9).**
8. **Refold this feedback file's decisions into `spec-v2.md`** and
   delete this file.

Once those eight items are answered, v2.0 stops being a stack list
and becomes a spec.
