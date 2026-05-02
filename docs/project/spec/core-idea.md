# SignalNest — Core Idea & Theme

> **Status:** Author's brand and visual brief for SignalNest v2.0.
> Lives alongside [`spec-v2.md`](spec-v2.md); the spec inherits the
> Theme statement from this file. This is the *what it looks and
> feels like* document; `spec-v2.md` is the *what it does and how
> it's built* document.

---

## Positioning

SignalNest is a **B2B SaaS feedback-triage tool for product teams.**

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
later concern.

---

## Theme

**SignalNest — Calm Signal Intelligence.**

Turn noisy user feedback into clear product signals.

The app should feel like a **clean command center for sorting messy
incoming feedback into useful product decisions.** Not playful, not
corporate-boring, not cyberpunk. More like: quiet, focused,
trustworthy, organized.

| Element            | Direction                                                 |
| ------------------ | --------------------------------------------------------- |
| Product name       | SignalNest                                                |
| Tagline (locked)   | *Capture the noise. Find the signal.*                     |
| Description (locked) | A feedback triage app for turning user requests, bugs, and product ideas into clear next steps. |
| Visual metaphor    | Signals, threads, nests, clusters, clarity, prioritization |
| Mood               | Calm, sharp, organized, slightly analytical               |
| App personality    | Practical, reliable, modern, not overdesigned             |
| Best fit           | Portfolio SaaS app that feels genuinely usable            |

The tagline and description are **locked** — they appear identically
in the README, the landing page hero, the `<title>` tag, and every
external surface. Edits to either need an ADR.

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

### App-name usage

**Use:** SignalNest

**Not:** Signal Nest, Signalnest, signalnest.

In UI copy: *Welcome to SignalNest*. In logo / domain:
`signalnest.app`. The repository slug stays `feedback-triage-app`
per [ADR 057](../../adr/057-brand-vs-repo-naming.md).

---

## Roles

The user model SignalNest supports.

| Role                 | Account? | Scope                  | What they can do                                                                                  |
| -------------------- | -------- | ---------------------- | ------------------------------------------------------------------------------------------------- |
| Admin                | Yes      | Platform-wide          | Project author. Can switch into any workspace, see admin-only routes, run maintenance.            |
| Workspace owner      | Yes      | One workspace          | Full CRUD on their workspace's feedback, tags, submitters; invite/remove team members; settings.  |
| Team member          | Yes      | One workspace          | Full CRUD on the workspace's feedback, tags, notes; cannot manage members or change settings.     |
| Demo user            | Yes      | The demo workspace     | Read-only access to a seeded workspace. One shared login. Resets nightly.                         |
| Submitter / customer | No       | One workspace (linked) | Row in `submitters`. Has email known to the workspace; submitted feedback is grouped by them.     |
| Public submitter     | No       | One workspace (open)   | Anonymous. Submits feedback through a workspace's public form. No persistent identity.            |

Authoritative role mechanics live in
[ADR 059](../../adr/059-auth-model.md) (platform-level role on
`users`) and
[ADR 060](../../adr/060-multi-tenancy-workspace-scoping.md)
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
| `/styleguide`                  | Component / theme showcase ([ADR 056](../../adr/056-style-guide-page.md)). |

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
[ADR 058](../../adr/058-tailwind-via-standalone-cli.md)).

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
> [ADR 058](../../adr/058-tailwind-via-standalone-cli.md).
> Token-shorthand entries above (e.g. `--color-bg: slate-50`) are
> shorthand for the actual hex Tailwind generates from those palette
> entries.

The four named theme presets from
[ADR 056](../../adr/056-style-guide-page.md) (`production`,
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

| Component        | Tailwind composition                                                    |
| ---------------- | ----------------------------------------------------------------------- |
| Card             | `bg-white border border-slate-200 rounded-2xl shadow-sm p-4`            |
| Primary button   | `bg-teal-600 hover:bg-teal-700 text-white rounded-xl px-4 py-2 font-medium` |
| Secondary button | `bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 rounded-xl px-4 py-2` |
| Status pill      | `inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium` |
| Priority pill    | `inline-flex items-center rounded-md px-2 py-0.5 text-xs font-semibold` |
| Pain dots        | `inline-flex gap-0.5 text-slate-400` (filled = `text-teal-600`)         |
| Modal            | `<dialog>` with `rounded-2xl shadow-lg max-w-lg`                        |
| Toast            | `fixed bottom-4 right-4 rounded-xl bg-slate-900 text-white px-4 py-2`   |
| Input            | `block w-full rounded-xl border border-slate-300 focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20` |
| Form group       | `<label class="block text-sm font-medium text-slate-700 mb-1">`         |
| Empty state      | Icon (h-10 w-10 text-slate-400) + `text-base font-medium` + `text-sm text-slate-500` + primary button |

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
in [`spec-v2.md`](spec-v2.md#workflow); the brand-level summary:

| Workflow step     | App surface                                                          |
| ----------------- | -------------------------------------------------------------------- |
| Intake            | Public submission form, signup, mini demo                            |
| Triage            | Inbox, status pills, filter bar, search                              |
| Prioritize        | Tags, priority pills, pain dots, notes                               |
| Act               | Roadmap page (Planned / In Progress columns)                         |
| Close the loop    | Changelog page, status-change emails to submitters with known emails |

---

## Theme checklist

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

## Related docs

- [`spec-v2.md`](spec-v2.md) — technical spec; Theme is sourced from this file
- [`spec-v1.md`](spec-v1.md) — shipped v1.0 spec
- [ADR 056 — Style guide page](../../adr/056-style-guide-page.md)
- [ADR 057 — Brand vs. repo naming](../../adr/057-brand-vs-repo-naming.md)
- [ADR 058 — Tailwind via Standalone CLI](../../adr/058-tailwind-via-standalone-cli.md)
- [ADR 059 — Auth model](../../adr/059-auth-model.md)
- [ADR 060 — Multi-tenancy / workspace scoping](../../adr/060-multi-tenancy-workspace-scoping.md)
