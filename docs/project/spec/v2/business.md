# v2.0 — Business / startup characteristics

> Topical detail file. Entry point: [`../spec-v2.md`](../spec-v2.md).
> Brand brief: [`../core-idea.md`](../core-idea.md).

This file captures SignalNest's **product / business posture** at
v2.0 launch. It is not a financial model; it is the single place to
look up the answers to *"who is this for, what does it cost, why
would they switch, what's the moat, and what are we deliberately
not selling?"*

---

## Status

| Field                       | Value                                                |
| --------------------------- | ---------------------------------------------------- |
| Stage                       | Pre-revenue. Portfolio + private alpha.              |
| Pricing                     | Free for all users in v2.0. No billing surface.      |
| Hosting                     | Single Railway service. One Postgres. No CDN.        |
| Legal entity                | None. Operated by the author as a personal project.  |
| Data-processing posture     | Personal-data-minimal; no PII beyond email + name.   |
| Public-launch gate          | v2.0 ratification + a Privacy + Terms page.          |

---

## Target user

The smallest unit of "product team" that has a feedback-triage
problem worth solving.

| Segment                    | Size       | Pain                                                                             |
| -------------------------- | ---------- | -------------------------------------------------------------------------------- |
| Solo founder / indie hacker | 1          | Feedback scattered across DMs, Reddit, email; no system.                         |
| Early-stage startup        | 2–10       | Triage in spreadsheets; no shared status; bugs and feature requests collide.     |
| Internal product team       | 5–20       | Internal tooling teams without a Productboard / Canny budget.                    |
| Power user of v1.0          | 1          | The author. v2.0's first real user.                                              |

**Out of scope for v2.0:** large enterprise, regulated industries
(healthcare, finance), and anyone needing SSO / SAML / SCIM.

---

## Value proposition

> *"Stop losing user feedback in your inbox. Capture it in one
> place, triage it in five steps, and close the loop with the
> people who sent it."*

Three concrete claims SignalNest must back up at v2.0:

1. **One inbox.** Public submission form + authenticated `POST`
   endpoint write to the same `feedback_item` table, scoped to one
   workspace. No CSV exports needed to "consolidate."
2. **Five-phase workflow.** Status enum is opinionated:
   `new → needs_info → reviewing → accepted → planned →
   in_progress → shipped`, plus `closed` and `spam`. The product
   teaches the workflow.
3. **Close the loop.** When a workspace owner marks an item
   `shipped`, the submitter (if email-known) receives a Resend
   email; the item appears on the public changelog. This is the
   feature most competitors charge for.

---

## What v2.0 deliberately does not sell

Saying no is a feature.

- **No AI / LLM "auto-triage."** The market is saturated and the
  trust cost is high. Tags and priority stay human-set in v2.0.
- **No voting / upvotes.** Pain level (submitter's number) and
  priority (team's pill) cover the same need without a public
  popularity contest.
- **No real-time updates.** A page refresh is fine for v2.0 traffic.
- **No bulk actions.** One item at a time keeps the UX honest.
- **No Slack / Discord webhooks.** Email is the only egress in
  v2.0 ([`email.md`](email.md)).
- **No public API tokens.** The public submission form is the
  only programmatic surface.
- **No file attachments.** Object storage adds a vendor and a
  vulnerability surface.

Every item above is logged as a future improvement in
[`../spec-v2.md`](../spec-v2.md#future-improvements-after-v20).

---

## Competitive landscape

Not a market analysis — a positioning statement.

| Tool         | What they do well        | Why a small team picks SignalNest                          |
| ------------ | ------------------------ | ---------------------------------------------------------- |
| Canny        | Public voting + roadmap  | We don't sell voting; we sell triage.                      |
| Productboard | Heavy product strategy   | We're 1/100th the surface area, free, and self-hostable.   |
| Linear       | Engineering issue tracker| We're upstream of Linear — the *signal* before the issue.  |
| Trello board | Anyone can use it        | We give the workflow that a Trello board imitates poorly.  |
| Spreadsheet  | Free, flexible           | We're free and we close the loop automatically.            |

**One-line wedge:** *"The triage step before your issue tracker."*

---

## Pricing posture

v2.0 ships **free.** No billing code, no Stripe, no plan-gating
logic. Future paid tiers (deferred, not designed):

| Tier           | Likely shape                                 |
| -------------- | -------------------------------------------- |
| Free           | 1 workspace, ≤ 3 members, ≤ 500 feedback items. |
| Pro (later)    | Unlimited members, unlimited items, custom domain on public roadmap. |
| Team (later)   | Multiple workspaces per user, audit log, export. |

When a paid tier is real, it gets its own ADR and its own table in
the schema. Until then there is no `plan` column on `workspaces` —
adding one prematurely is the [YAGNI](https://en.wikipedia.org/wiki/You_aren%27t_gonna_need_it)
trap to avoid.

---

## Distribution & growth

v2.0 is intentionally low-effort on growth.

- **Portfolio first.** The author's GitHub README, personal site,
  and a single `Show HN`-style post are the only launch surfaces.
- **The product as the demo.** The landing page mini demo (FU1)
  is the marketing asset; no separate gallery, no video.
- **Public roadmap / changelog as growth loop.** A workspace's
  public roadmap and changelog include a small *"Powered by
  SignalNest"* footer link. This is the only viral surface.

No paid acquisition, no SEO investment, no email capture funnel in
v2.0.

---

## Retention model (informational)

What the product does to keep a logged-in user coming back:

- **Closed-loop email.** If the workspace marks an item shipped,
  every email-known submitter is notified. This pulls them back to
  the public changelog.
- **Stale-item surfacing.** The Inbox highlights items that have
  sat in `new` or `needs_info` for > 14 days.
- **Insights weekly digest** (deferred, FE follow-on). Not in v2.0.

Out of scope: gamification, streaks, "you're on fire" UI.

---

## Risk register (business-shaped)

Engineering-shaped risks live in [`security.md`](security.md) and
[`rollout.md`](rollout.md).

| Risk                                              | Likelihood | Impact | Mitigation                                                                  |
| ------------------------------------------------- | ---------- | ------ | --------------------------------------------------------------------------- |
| Resend email deliverability tanks                 | Low        | Med    | Fail-soft send ([`email.md`](email.md)); status changes still succeed.      |
| Spam abuse of public form                         | Med        | Med    | Honeypot + rate limit + workspace owner can disable form.                   |
| Cross-tenant data leak                            | Low        | High   | `WorkspaceContext` + e2e isolation tests; RLS deferred but reserved.        |
| Postgres outage on Railway                        | Low        | High   | Read-only public pages already lean on aggressive caching; v2.0 accepts.    |
| Author burnout / project pause                    | Med        | Med    | Free tier; no SLA published; codebase remains usable as a personal install. |
| Trademark conflict on "SignalNest"                | Low        | Low    | Domain reserved; pre-launch trademark check is a release-gate task.         |
| GDPR data-subject request before legal entity exists | Low     | High   | Privacy page commits to a single contact email; deletion is a manual SQL. |

---

## Success metrics (informational)

v2.0 does not embed analytics. These are read out of Postgres on
request.

| Metric                                | Source                                | Goal at "v2.0 done"   |
| ------------------------------------- | ------------------------------------- | --------------------- |
| Live workspaces                       | `SELECT count(*) FROM workspaces`     | ≥ 5                   |
| Feedback items captured               | `SELECT count(*) FROM feedback_item`  | ≥ 200                 |
| Items reaching `shipped`              | `WHERE status = 'shipped'`            | ≥ 10                  |
| Closed-loop emails sent               | `email_log` table count               | ≥ 10                  |
| Public roadmap views                  | Railway access logs                   | informational only    |

If none of these move, v2.0 is a portfolio piece, not a product —
which is an acceptable outcome.

---

## Cross-references

- [`../spec-v2.md`](../spec-v2.md) — v2.0 spec entry point.
- [`../core-idea.md`](../core-idea.md) — brand brief.
- [`rollout.md`](rollout.md) — phased technical launch.
- [`email.md`](email.md) — Resend integration & fail-soft model.
- [`security.md`](security.md) — engineering-shaped risks.
