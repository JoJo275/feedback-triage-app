# SignalNest — Core Idea & Theme

> **Status:** **Canonical** brand and visual brief for SignalNest v2.0.
> This file is the single source of truth for what the product is
> called, how it sounds, what it looks like, and which surfaces are
> locked. The v2 spec entry point ([`../spec-v2.md`](../spec-v2.md))
> inherits its Theme statement from this file.
>
> **Predecessor:** an earlier draft lived at
> [`../core-idea.md`](../core-idea.md). That file is now a redirect
> stub; do not edit it. All brand/visual content has been merged
> here.
>
> **Companions:** CSS plumbing in [`css.md`](css.md); per-page
> composition in [`pages.md`](pages.md); product/business posture
> in [`business.md`](business.md). Frontend rationale and
> accessibility checklist in
> [`../../../notes/frontend-conventions.md`](../../../notes/frontend-conventions.md).

---

## One-line product definition

**SignalNest** is a calm, **multi-tenant feedback-triage SaaS** that
helps a small product team turn scattered user feedback into a
five-phase workflow: **Intake → Triage → Prioritize → Act → Close
the loop.**

If a v2.0 feature does not slot into one of those five phases, it
does not ship in v2.0. This is the single sharpest scope rule.

---

## Positioning

The target user is a small product team — indie hackers, an
early-stage startup, a solo founder, an internal product team at a
mid-size company — that is drowning in scattered feedback (email,
Reddit, support tickets, app-store reviews, customer interviews) and
needs a single place to capture, triage, prioritize, and respond to
it.

It is **multi-tenant from v2.0**: every user signs up to a
**workspace**, can invite team members, and sees only their
workspace's data.

It is **free to use** in v2.0 (no billing surface). A paid tier is a
later concern. Full pricing posture in [`business.md`](business.md).

---

## Locked strings

These appear identically across the README, the landing page hero,
the `<title>` tag, the styleguide, the footer, and any external
surface. Edits require an ADR.

| Surface     | Value                                                                                              |
| ----------- | -------------------------------------------------------------------------------------------------- |
| Name        | `SignalNest`                                                                                       |
| Domain      | `signalnest.app`                                                                                   |
| Repo slug   | `feedback-triage-app` ([ADR 057](../../../adr/057-brand-vs-repo-naming.md))                        |
| Tagline     | *Capture the noise. Find the signal.*                                                              |
| Description | *A feedback triage app for turning user requests, bugs, and product ideas into clear next steps.*  |

Forbidden spellings: `Signal Nest`, `Signalnest`, `signalnest` (in
prose).

### App-name usage

**Use:** SignalNest

**Not:** Signal Nest, Signalnest, signalnest.

In UI copy: *Welcome to SignalNest*. In logo / domain:
`signalnest.app`. The repository slug stays `feedback-triage-app`
per [ADR 057](../../../adr/057-brand-vs-repo-naming.md).

---

## Theme statement

> **SignalNest — Calm Signal Intelligence.**
> Turn noisy user feedback into clear product signals.

The app should feel like a **clean command center for sorting messy
incoming feedback into useful product decisions.** Not playful, not
corporate-boring, not cyberpunk. More like: quiet, focused,
trustworthy, organized.

| Element              | Direction                                                                                          |
| -------------------- | -------------------------------------------------------------------------------------------------- |
| Product name         | SignalNest                                                                                         |
| Tagline (locked)     | *Capture the noise. Find the signal.*                                                              |
| Description (locked) | *A feedback triage app for turning user requests, bugs, and product ideas into clear next steps.*  |
| Visual metaphor      | Signals, threads, nests, clusters, clarity, prioritization                                         |
| Mood                 | Calm, sharp, organized, slightly analytical                                                        |
| App personality      | Practical, reliable, modern, not overdesigned                                                      |
| Best fit             | Portfolio SaaS app that feels genuinely usable                                                     |

---

## Brand language

Use language like:

- Collect feedback.
- Triage faster.
- Prioritize what matters.
- Close the loop.

Avoid making it sound like a generic survey tool.

**Good copy:**

- New signal received.
- Feedback merged.
- Marked as planned.
- Status updated.
- User notified.
- No matching feedback found.
- This item may be a duplicate.

**Avoid:**

- Awesome!!!
- Your amazing feedback has been processed!
- Super-powered AI magic!

The app should feel **competent, not gimmicky**.

### Voice rules (copy review checklist)

When writing any UI string:

- Prefer **verbs of clarity**: *capture, triage, prioritize, close
  the loop, mark, merge, notify*.
- Prefer **calm acknowledgement**: *New signal received. Status
  updated. Marked as planned.*
- Avoid hype: no `Awesome!!!`, no `Super-powered`, no `magic`, no
  exclamation runs.
- Avoid generic-survey-tool wording: no `Submit your response`,
  no `Thanks for your input`.
- Empty states are factual: *No items match these filters.*
  *No feedback yet — share your public form to get started.*
- Errors are direct: *Email already in use.* *Workspace slug taken.*
  *Token expired.* No `Oops!`.

---

## Visual non-negotiables

Rules implementers must not silently break. Full palette,
components, and CSS plumbing live below and in [`css.md`](css.md).

1. **Tailwind via Standalone CLI** is the styling layer
   ([ADR 058](../../../adr/058-tailwind-via-standalone-cli.md)).
   No CSS-in-JS, no preprocessor, no Bootstrap, no Tailwind via
   npm.
2. **System font stack only** in v2.0. No web font, no
   `@font-face`, no Google Fonts.
3. **Pills carry icon + text + color**, never color alone. The
   color-blind / print path must remain readable.
4. **One `<h1>` per page**, sequential heading levels, skip-link
   to `#main`.
5. **Inline SVG charts.** No Chart.js / D3 / Recharts in v2.0.
6. **Lucide icons as static SVGs**, exported into
   `src/feedback_triage/static/img/icons/`. No JS icon library.
7. **Logo / favicon are placeholders.** A designed mark replaces
   them before public launch but does not block alpha/beta.
8. **Reduced-motion respected** via
   `@media (prefers-reduced-motion: reduce)`.

---

## Roles

The user model SignalNest supports.

| Role                 | Account?     | Scope                  | What they can do                                                                                  |
| -------------------- | ------------ | ---------------------- | ------------------------------------------------------------------------------------------------- |
| Admin                | yes          | Platform-wide          | Project author. Can switch into any workspace, see admin-only routes, run maintenance.            |
| Workspace owner      | yes          | One workspace          | Full CRUD on their workspace's feedback, tags, submitters; invite/remove team members; settings.  |
| Team member          | yes          | One workspace          | Full CRUD on the workspace's feedback, tags, notes; cannot manage members or change settings.     |
| Demo user            | yes (shared) | The demo workspace     | Read-only access to a seeded workspace. One shared login. Resets nightly.                         |
| Submitter / customer | no           | One workspace (linked) | Row in `submitters`. Has email known to the workspace; submitted feedback is grouped by them.     |
| Public submitter     | no           | One workspace (open)   | Anonymous. Submits feedback through a workspace's public form. No persistent identity.            |

Authoritative role mechanics live in
[ADR 059](../../../adr/059-auth-model.md) (platform-level role on
`users`) and
[ADR 060](../../../adr/060-multi-tenancy-workspace-scoping.md)
(workspace-level role on `workspace_memberships`).

---

## App layout

Classic SaaS dashboard layout:

- Left sidebar (collapsible)
- Top header (workspace switcher + user menu)
- Main content area
- Right-side detail drawer (later — out of v2.0 scope)

### Sidebar (logged-in workspace view, v2.0 final)

| Order | Item       | Default route                 | Purpose                                              |
| ----- | ---------- | ----------------------------- | ---------------------------------------------------- |
| 1     | Dashboard  | `/w/<slug>/dashboard`         | Signal overview cards + intake sparkline             |
| 2     | Inbox      | `/w/<slug>/inbox`             | Triage queue: new + needs-info + reviewing items     |
| 3     | Feedback   | `/w/<slug>/feedback`          | Full filtered/searchable list across all statuses    |
| 4     | Submitters | `/w/<slug>/submitters`        | People who have submitted feedback, with history     |
| 5     | Roadmap    | `/w/<slug>/roadmap`           | Items marked as planned / in-progress; publishable   |
| 6     | Changelog  | `/w/<slug>/changelog`         | Items marked as shipped; publishable                 |
| 7     | Insights   | `/w/<slug>/insights`          | Aggregations: top tags, trends, pain points          |
| 8     | Settings   | `/w/<slug>/settings`          | Workspace info, members, tags CRUD, public form URL  |

### Top header

- **Workspace switcher** (only shown if the user belongs to multiple
  workspaces; v2.0 enforces 1:1, so usually hidden).
- **User menu**: Profile, Sign out.
- **Theme switcher** (light / dark) once dark mode ships.

### Public, unauthenticated routes

| Route                          | Purpose                                                          |
| ------------------------------ | ---------------------------------------------------------------- |
| `/`                            | Marketing landing page + the client-side mini demo (no backend). |
| `/login`                       | Login form.                                                      |
| `/signup`                      | Signup form (creates user + workspace in one step).              |
| `/forgot-password`             | Forgot-password request.                                         |
| `/reset-password?token=…`      | Password reset confirmation.                                     |
| `/verify-email?token=…`        | Email verification confirmation.                                 |
| `/invitations/<token>`         | Workspace-invitation acceptance landing page.                    |
| `/w/<slug>/submit`             | Public feedback submission form for that workspace.              |
| `/w/<slug>/roadmap/public`     | Read-only published roadmap for that workspace.                  |
| `/w/<slug>/changelog/public`   | Read-only published changelog for that workspace.                |
| `/styleguide`                  | Component / theme showcase ([ADR 056](../../../adr/056-style-guide-page.md)). |

Authenticated users hitting `/` are redirected to
`/w/<their-slug>/dashboard`.

---

## Visual style

### Main vibe

| Trait        | Recommendation                       |
| ------------ | ------------------------------------ |
| Overall look | Modern SaaS dashboard                |
| Density      | Medium-dense but readable            |
| Corners      | Rounded, but not bubbly (`rounded-xl`) |
| Shadows      | Soft, minimal (`shadow-sm`)          |
| Borders      | Subtle (`border border-slate-200`)   |
| Background   | Off-white in light, deep slate in dark |
| Accent       | Signal teal                          |
| Motion       | Small, functional transitions only   |

### Color tokens — light (default)

Tokens are CSS custom properties defined in `static/css/input.css`
and consumed by Tailwind utility classes through the
`tailwind.config.cjs` theme map (see
[ADR 058](../../../adr/058-tailwind-via-standalone-cli.md) and
[`css.md`](css.md)).

| Token                  | Light value         | Use                                             |
| ---------------------- | ------------------- | ----------------------------------------------- |
| `--color-bg`           | `slate-50`          | App background                                  |
| `--color-surface`      | `white`             | Cards, tables, panels                           |
| `--color-surface-alt`  | `slate-100`         | Secondary panels, hover rows                    |
| `--color-text`         | `slate-900`         | Primary text                                    |
| `--color-text-muted`   | `slate-500`         | Metadata, timestamps                            |
| `--color-primary`      | `teal-600`          | Active states, primary buttons                  |
| `--color-primary-hover`| `teal-700`          | Primary hover                                   |
| `--color-warning`      | `amber-500`         | Needs review, warnings                          |
| `--color-danger`       | `rose-600`          | Spam, delete, error                             |
| `--color-border`       | `slate-200`         | Card and table dividers                         |
| `--color-focus`        | `teal-500`          | `:focus-visible` ring                           |

### Color tokens — dark (v2.0-final)

| Token                  | Dark value          |
| ---------------------- | ------------------- |
| `--color-bg`           | `slate-950`         |
| `--color-surface`      | `slate-900`         |
| `--color-surface-alt`  | `slate-800`         |
| `--color-text`         | `slate-100`         |
| `--color-text-muted`   | `slate-400`         |
| `--color-primary`      | `teal-400`          |
| `--color-primary-hover`| `teal-300`          |
| `--color-warning`      | `amber-400`         |
| `--color-danger`       | `rose-400`          |
| `--color-border`       | `slate-700`         |
| `--color-focus`        | `teal-400`          |

> **Tailwind utility classes are real.** When a component spec says
> `bg-white border border-slate-200 rounded-2xl shadow-sm`, those
> are literal Tailwind utility classes that ship via
> [ADR 058](../../../adr/058-tailwind-via-standalone-cli.md).
> Token-shorthand entries above (e.g. `--color-bg: slate-50`) are
> shorthand for the actual hex Tailwind generates from those palette
> entries; the source-of-truth hex values live in [`css.md`](css.md).

The four named theme presets from
[ADR 056](../../../adr/056-style-guide-page.md) (`production`,
`basic`, `unique`, `crazy`) override the same token names on
`/styleguide` only.

### Typography

System font stack for v2.0 — zero web-font cost, zero FOIT, zero
licensing surface, looks correct on every platform.

```text
font-family:
  -apple-system, BlinkMacSystemFont,
  "Segoe UI", Roboto, "Helvetica Neue",
  Arial, "Noto Sans", sans-serif,
  "Apple Color Emoji", "Segoe UI Emoji";
font-family-mono:
  ui-monospace, SFMono-Regular, Menlo, Consolas,
  "Liberation Mono", monospace;
```

A bespoke web font (Inter / Geist / Source Sans 3) is a v3.0 polish
pass, not a v2.0 requirement.

| Use            | Style                                  |
| -------------- | -------------------------------------- |
| Page titles    | `text-2xl font-semibold`               |
| Section headers| `text-lg font-medium`                  |
| Body           | `text-sm text-slate-700`               |
| Metadata       | `text-xs text-slate-500`               |
| Status pills   | `text-xs font-medium uppercase tracking-wide` |

### Logo and favicon (placeholder)

For v2.0 launch:

- **Wordmark**: the literal string `SignalNest` rendered in the
  system font, semibold, with the dot of the lowercase `i` in
  `Signal` replaced by a small filled circle in
  `var(--color-primary)`. Inline SVG, no external asset.
- **Favicon**: a 32×32 SVG containing the letter `S` on a teal
  rounded square. Placeholder; the author intends to replace it
  with a designed mark before public launch.
- **Long-form logo idea (future)**: a small circular nest made of
  2–3 curved lines, with one signal dot in the center.

**Avoid:** literal bird nest, cute mascot, generic chat bubble,
huge radio-wave icon.

### Iconography

[Lucide](https://lucide.dev/) icons, exported as static SVGs into
`src/feedback_triage/static/img/icons/`. No `lucide-react`, no JS
icon library — pure inline SVG.

| Icon                | Use                |
| ------------------- | ------------------ |
| Radar               | Signal detection / brand mark |
| Inbox               | Inbox nav item     |
| MessageSquareText   | Feedback nav item  |
| Tags                | Tags / classification |
| Users               | Submitters nav item|
| Map                 | Roadmap nav item   |
| Sparkles            | Changelog nav item |
| ChartNoAxesColumn   | Insights nav item  |
| Settings            | Settings nav item  |
| GitMerge            | Duplicate merge    |
| CircleDot           | Signal / status indicator |

---

## Status workflow

v2.0 extends the v1.0 `status_enum`. Mapping:

| v1.0 status | v2.0 status     | Notes                                                       |
| ----------- | --------------- | ----------------------------------------------------------- |
| `new`       | `new`           | unchanged                                                   |
| `reviewing` | `reviewing`     | unchanged                                                   |
| `planned`   | `planned`       | unchanged                                                   |
| `rejected`  | `closed`        | renamed; v1.0 rows are migrated `rejected → closed`         |
| —           | `needs_info`    | added; awaiting more info from submitter                    |
| —           | `accepted`      | added; triaged but not yet planned                          |
| —           | `in_progress`   | added; work has started                                     |
| —           | `shipped`       | added; closed-the-loop state; eligible for the changelog    |
| —           | `spam`          | added; explicitly junk                                      |

Visual feel of each status (used as the chip/pill background tone):

| Status      | Visual feel        |
| ----------- | ------------------ |
| New         | Neutral blue-gray  |
| Needs Info  | Amber              |
| Reviewing   | Indigo             |
| Accepted    | Teal               |
| Planned     | Blue               |
| In Progress | Sky                |
| Shipped     | Green              |
| Closed      | Slate              |
| Spam        | Rose               |

Pills are **color + icon + label** — never color alone (accessibility:
color-blind users, monochrome printouts).

---

## Pain level vs. priority

v2.0 keeps both, with distinct UI:

| Field        | Source        | Display                                          | Editable by         |
| ------------ | ------------- | ------------------------------------------------ | ------------------- |
| `pain_level` | The submitter | A 5-dot indicator (●●●○○) — quiet, ungendered    | The submitter only  |
| `priority`   | The team      | A colored pill: Low / Medium / High / Critical    | Workspace members   |

The Inbox and Feedback list show both columns. Filtering / sorting
is supported on each independently.

---

## Inbox design

The inbox is the **triage command center**.

| UI area              | Purpose                                              |
| -------------------- | ---------------------------------------------------- |
| Top summary cards    | New, Needs Info, Reviewing, High Priority, Stale     |
| Filter bar           | Type, status, tag, priority, source, date            |
| Search input         | `WHERE description ILIKE '%q%'` (v2.0); pg_trgm later |
| Feedback table       | Main triage queue, paginated                         |
| Status pills         | Quick workflow state                                 |
| Priority pills       | Low / Medium / High / Critical                       |
| Pain dots            | 1–5                                                  |
| Bulk actions         | Out of v2.0 scope                                    |
| Empty states         | Icon + short explanation + first-action link         |

Example row:

> **\[Feature Request]** Better export options
> *"Would be useful to export filtered feedback to CSV..."*
> Tags: Export, Reporting · Status: Reviewing · Priority: Medium ·
> Pain: ●●●○○ · Source: Web Form · From: alice@example.com · 2h ago

---

## Page-level themes

| Page             | Theme direction                                       |
| ---------------- | ----------------------------------------------------- |
| Dashboard        | "Signal overview" — cards and small inline-SVG charts |
| Inbox            | "Triage queue" — dense actionable rows                |
| Feedback list    | "Searchable archive" — same table, more filters       |
| Feedback detail  | "Case file" — timeline, notes, metadata, related      |
| Submitters       | "Customer roster" — list with submission counts       |
| Roadmap          | "From signals to planned work" — kanban-ish columns   |
| Changelog        | "Closed loop" — reverse-chronological release notes   |
| Insights         | "Trends" — top tags, rising topics, pain heatmap      |
| Settings         | "Clean admin" — workspace, members, tags, public URL  |
| Landing (`/`)    | Marketing + the client-side mini demo                 |
| Privacy / Terms  | Plain, trustworthy, minimal legalese                  |

### Charts

Inline SVG, hand-rolled. No Chart.js, no D3, no Recharts. v2.0's
chart needs (intake sparkline, top-tags bar, status donut) are all
~30-line SVG components. Charting library is its own ADR if the
need ever justifies it.

---

## Visual components (Tailwind shorthand)

| Component        | Tailwind composition                                                                            |
| ---------------- | ----------------------------------------------------------------------------------------------- |
| Card             | `bg-white border border-slate-200 rounded-2xl shadow-sm p-4`                                    |
| Primary button   | `bg-teal-600 hover:bg-teal-700 text-white rounded-xl px-4 py-2 font-medium`                     |
| Secondary button | `bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 rounded-xl px-4 py-2`        |
| Status pill      | `inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium`                   |
| Priority pill    | `inline-flex items-center rounded-md px-2 py-0.5 text-xs font-semibold`                         |
| Pain dots        | `inline-flex gap-0.5 text-slate-400` (filled = `text-teal-600`)                                 |
| Modal            | `<dialog>` with `rounded-2xl shadow-lg max-w-lg`                                                |
| Toast            | `fixed bottom-4 right-4 rounded-xl bg-slate-900 text-white px-4 py-2`                           |
| Input            | `block w-full rounded-xl border border-slate-300 focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20` |
| Form group       | `<label class="block text-sm font-medium text-slate-700 mb-1">`                                 |
| Empty state      | Icon (h-10 w-10 text-slate-400) + `text-base font-medium` + `text-sm text-slate-500` + primary button |

The repeating compositions above are promoted to bespoke
`sn-*` component classes in `input.css` once they appear verbatim
in three or more templates — see [`css.md`](css.md#component-vocabulary)
for the canonical class list and the `@apply` rules.

---

## Landing page

For `signalnest.app`, a clean marketing landing.

### Hero

> **SignalNest**
> *Capture the noise. Find the signal.*
>
> A feedback triage app for turning user requests, bugs, and product
> ideas into clear next steps.

Primary CTA: **Start free** (→ `/signup`)
Secondary CTA: **Try the demo** (→ scrolls to embedded mini demo)

### Sections

| Section            | Purpose                                                                     |
| ------------------ | --------------------------------------------------------------------------- |
| Hero               | Explain the product in one screen                                           |
| Mini demo          | Embedded client-side demo (FU1, see below). Vanilla JS, no backend.         |
| Problem            | Feedback gets scattered and repeated                                        |
| Solution           | Centralize, tag, prioritize, and close the loop                             |
| Feature grid       | Inbox, tags, statuses, notes, submitters, roadmap, changelog, insights      |
| Workflow           | Intake → Triage → Prioritize → Act → Close the loop                         |
| Portfolio note     | "Built as a full-stack portfolio project, usable as a real app."            |
| Footer             | Privacy, Terms, GitHub, Contact                                             |

### Mini demo (FU1) — client-side only

A small, self-contained interactive widget on the landing page:

- 8–12 hardcoded JSON feedback items.
- Vanilla JS state (no framework), no backend, no network calls.
- The visitor can drag a status pill, mark a row as planned, type
  in the search box. Refresh resets to the seed.
- Acts as a "playable screenshot" that the marketing copy can
  reference: "Try it — no signup required."

---

## Workflow alignment

Every v2.0 feature maps to a workflow phase. The full mapping lives
in [`../spec-v2.md`](../spec-v2.md#workflow); the brand-level summary:

| Workflow step     | App surface                                                          |
| ----------------- | -------------------------------------------------------------------- |
| Intake            | Public submission form, signup, mini demo                            |
| Triage            | Inbox, status pills, filter bar, search                              |
| Prioritize        | Tags, priority pills, pain dots, notes                               |
| Act               | Roadmap page (Planned / In Progress columns)                         |
| Close the loop    | Changelog page, status-change emails to submitters with known emails |

---

## Per-surface theme checklist

Use during implementation review of each surface.

### Landing page (`/`)

- [ ] Hero shows the locked tagline + locked description, verbatim.
- [ ] Primary CTA: **Start free** → `/signup`.
- [ ] Secondary CTA: **Try the demo** → scrolls to FU1 mini demo.
- [ ] Mini demo is fully client-side; refresh resets to seed.
- [ ] Footer carries Privacy, Terms, GitHub, Contact.
- [ ] No tracker, no analytics in v2.0.

### Auth pages (`/login`, `/signup`, `/forgot-password`,
`/reset-password`, `/verify-email`)

- [ ] Same shell, no sidebar.
- [ ] One form per page, label + input + helper text.
- [ ] Errors render inline + announced via `aria-live="polite"`.
- [ ] `/signup` creates user **and** workspace in one transaction
      ([`auth.md`](auth.md), [`schema.md`](schema.md)).

### Dashboard shell (`/w/<slug>/...`)

- [ ] Sidebar in the order: Dashboard, Inbox, Feedback, Submitters,
      Roadmap, Changelog, Insights, Settings.
- [ ] Top header carries the workspace name and user menu only —
      workspace switcher is hidden when 1:1 (the v2.0 default).
- [ ] Theme switcher only renders when dark mode ships (FD).
- [ ] Page `<title>`: `<Page> · <Workspace> · SignalNest`.

### Inbox (`/w/<slug>/inbox`)

- [ ] Top summary cards: New, Needs Info, Reviewing, High priority,
      Stale.
- [ ] Filter bar: Type, Status, Tag, Priority, Source, Date.
- [ ] Single search input → `description ILIKE '%q%'` (v2.0;
      pg_trgm deferred).
- [ ] Pain rendered as 5 dots; priority rendered as a pill — never
      collapsed into a single field.
- [ ] No bulk actions (deferred).

### Feedback detail (`/w/<slug>/feedback/<id>`)

- [ ] "Case file" layout: header, status pill, priority pill, pain
      dots, tag chips, submitter chip, timeline of changes,
      internal notes panel.
- [ ] Status change writes a row to the timeline and may trigger a
      Resend email if the status is in the notify-list and the
      submitter has an email ([`email.md`](email.md)).

### Public surfaces

- [ ] `/w/<slug>/submit` — public form, honeypot field, no
      authentication.
- [ ] `/w/<slug>/roadmap/public` — read-only; only items where
      `published_to_roadmap = true`.
- [ ] `/w/<slug>/changelog/public` — read-only; only items where
      `published_to_changelog = true`.
- [ ] No member email or internal note ever leaks onto a public
      surface.

### Styleguide (`/styleguide`)

- [ ] Public route. Renders every component in light, dark (when
      shipped), and the four theme presets from
      [ADR 056](../../../adr/056-style-guide-page.md).
- [ ] Visual regression-friendly: deterministic order, no live data.

---

## Theme checklist (top-of-mind summary)

- [x] Product name: SignalNest
- [x] Domain: `signalnest.app`
- [x] Tagline: *Capture the noise. Find the signal.* (locked)
- [x] Description: *A feedback triage app for turning user requests, bugs, and product ideas into clear next steps.* (locked)
- [x] Primary color: teal
- [x] Secondary accent: amber
- [x] Layout: sidebar SaaS dashboard
- [x] Main workflow: Intake → Triage → Prioritize → Act → Close the loop
- [x] Tone: calm, useful, trustworthy
- [x] Tailwind utility classes (real, via Standalone CLI — ADR 058)
- [x] System font stack (no web font in v2.0)
- [x] Multi-tenant (workspace-scoped — ADR 060)
- [x] Avoid: gimmicky AI branding, loud colors, overcomplicated animations

---

## Cross-references

- [`../spec-v2.md`](../spec-v2.md) — v2.0 spec entry point.
- [`../spec-v1.md`](../spec-v1.md) — shipped v1.0 spec.
- [`css.md`](css.md) — CSS conventions, design tokens, Tailwind config.
- [`pages.md`](pages.md) — per-page UI catalog.
- [`business.md`](business.md) — product positioning and pricing.
- [`../../../notes/frontend-conventions.md`](../../../notes/frontend-conventions.md) — frontend rationale + accessibility checklist.
- [ADR 056 — Style guide page](../../../adr/056-style-guide-page.md)
- [ADR 057 — Brand vs. repo naming](../../../adr/057-brand-vs-repo-naming.md)
- [ADR 058 — Tailwind via Standalone CLI](../../../adr/058-tailwind-via-standalone-cli.md)
- [ADR 059 — Auth model](../../../adr/059-auth-model.md)
- [ADR 060 — Multi-tenancy / workspace scoping](../../../adr/060-multi-tenancy-workspace-scoping.md)
