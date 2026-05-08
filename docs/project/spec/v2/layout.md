# SignalNest — Layout & visual composition

> **Scope:** what the SignalNest dashboard and its sibling pages
> *look like* — app shell, hierarchy, page composition, density,
> responsive behaviour, and the visual identity (palette, type,
> shadows, motion) that ride on top of that structure. This is the
> "before-implementation" picture for PR 4.5.
>
> **Audience:** anyone laying out a v2 page, building chrome
> components (`.sn-sidebar`, `.sn-header`, `.sn-hero`, …), or
> reviewing a screenshot against intent.
>
> **Source of truth, in order of authority:**
> [`core-idea.md`](core-idea.md) (locked strings, sidebar order,
> visual non-negotiables) →
> [`pages.md`](pages.md) (per-page composition) →
> [`ui.md`](ui.md) (route map, accessibility) →
> [`css.md`](css.md) + [`theming.md`](theming.md) (CSS plumbing) →
> this file (synthesis + dashboard-specific decisions).
> If anything below contradicts those files, they win and this file
> is wrong — open a PR to fix it.

---

## Reference mockup

![Dashboard mockup, v2 reference](images/Dashboard%20Mockup%201.jpg)

The mockup is the **direction**, not the spec. It looks like a
serious SaaS product and has useful operational density. The job
of this document is to take that direction and reconcile it with
the v2 scope: the locked sidebar, the v2 status enum, the calm
voice, and the "no analytics theater" rule.

---

## TL;DR — what the dashboard says

The dashboard does **not** say *"Here is everything."*
It says *"Here is what needs attention, why it matters, and what to
do next."*

| Slot                 | What lives here                                         | Why it's there                                               |
| -------------------- | ------------------------------------------------------- | ------------------------------------------------------------ |
| App shell            | Sidebar + top header + main content                     | Persistent navigation, workspace identity, current user      |
| Page header          | `<h1>` + one-line description + primary action          | Orient the user, surface the *one* next action               |
| Summary row          | 4 small metric cards                                    | System pulse: what changed, what's piling up                 |
| Main work row        | Triage queue (left, ~65%) + Attention panel (right)     | The operational center; the queue is the product            |
| Insight row          | Top tags + intake sparkline                             | Trends, *secondary* to action                                |
| Lower utility row    | Sources breakdown + recent activity                     | System health, low-density                                   |

The hierarchy goal: **action first, analytics second.** A polished
donut chart that doesn't drive a decision sits on
[`/w/<slug>/insights`](pages.md), not on the dashboard.

---

## Visual identity (locked)

These come from [`core-idea.md`](core-idea.md) — repeated here so a
layout reviewer doesn't have to chase. If a value here drifts from
`core-idea.md`, `core-idea.md` wins.

### Mood

> Calm command center for sorting messy incoming feedback into
> useful product decisions.

Not playful, not corporate-boring, not cyberpunk. **Quiet, focused,
trustworthy, organized.**

### Palette — light (default)

Tokens live in `static/css/tokens.css`; full table in
[`theming.md`](theming.md).

| Token                  | Light value | Use                              |
| ---------------------- | ----------- | -------------------------------- |
| `--color-bg`           | `slate-50`  | App background                   |
| `--color-surface`      | `white`     | Cards, tables, panels            |
| `--color-surface-alt`  | `slate-100` | Secondary panels, hover rows     |
| `--color-text`         | `slate-900` | Primary text                     |
| `--color-text-muted`   | `slate-500` | Metadata, timestamps             |
| `--color-primary`      | `teal-600`  | Active states, primary buttons   |
| `--color-warning`      | `amber-500` | Needs review, warnings           |
| `--color-danger`       | `rose-600`  | Spam, delete, error              |
| `--color-border`       | `slate-200` | Card and table dividers          |
| `--color-focus`        | `teal-500`  | `:focus-visible` ring            |

Dark mode mirrors with `slate-950` background and `teal-400`
primary. The four named theme presets from
[ADR 056](../../../adr/056-style-guide-page.md)
(`production`, `basic`, `unique`, `crazy`) override these tokens on
`/styleguide` only — they are tokens-only swaps, no per-preset
component overrides.

### Backgrounds

- App background is a single flat token (`--color-bg`). **No
  gradients, no patterns, no images** behind the shell in v2.0.
- Cards sit on `--color-surface` with a 1px `--color-border` and
  `shadow-sm`. Hovered table rows shift to `--color-surface-alt`,
  not a tint of primary.
- Decorative gradients (landing-page hero, empty-state flourishes)
  live in `effects.css` as opt-in `.sn-fx-*` classes — see
  [`theming.md`](theming.md). They must be safe to remove.

### Typography

System font stack only ([`core-idea.md` § Typography](core-idea.md)).
No web font, no `@font-face`.

| Use             | Style                                          |
| --------------- | ---------------------------------------------- |
| Page title      | `text-2xl font-semibold`                       |
| Section header  | `text-lg font-medium`                          |
| Body            | `text-sm text-slate-700`                       |
| Metadata        | `text-xs text-slate-500`                       |
| Status pill     | `text-xs font-medium uppercase tracking-wide`  |

One `<h1>` per page; heading levels are sequential; every page has
a skip-link to `#main`.

### Corners, shadows, motion

| Trait    | Direction                                                      |
| -------- | -------------------------------------------------------------- |
| Corners  | Rounded but not bubbly — `rounded-xl` for cards, `rounded-md` for inputs/buttons |
| Shadows  | Soft, minimal — `shadow-sm` default, `shadow-md` on overlays  |
| Borders  | Subtle — 1px `--color-border`                                  |
| Motion   | Functional only — fade/slide ≤ 200ms, no parallax, respect `prefers-reduced-motion` |

### Logo and favicon (placeholder)

Wordmark is the literal string `SignalNest` in the system font,
semibold, with the dot of the lowercase `i` replaced by a small
filled circle in `var(--color-primary)`. Favicon is a 32×32 SVG of
the letter `S` on a teal rounded square. Both are placeholders —
swappable before public launch, not blocking PR 4.5.

### Iconography

Lucide SVGs exported into `static/img/icons/`. No JS icon library.
Sidebar icon assignments (Radar, Inbox, MessageSquareText, Users,
Map, Sparkles, ChartNoAxesColumn, Settings) are listed in
[`core-idea.md` § Iconography](core-idea.md).

### Pills carry icon + text + color

Status, priority, and tag pills are **never color alone.** Every
pill is `[icon][label]` with the color as a third reinforcement.
Color-blind users and monochrome printouts must remain readable.

---

## App shell

The shell is the same on every authenticated page.

```text
+---------+--------------------------------------------------+
| Sidebar | Top header                                       |
|  240px  +--------------------------------------------------+
|         |                                                  |
|         |  <main id="main">                                |
|         |    Page header                                   |
|         |    Page body                                     |
|         |  </main>                                         |
|         |                                                  |
+---------+--------------------------------------------------+
```

Approximate dimensions:

| Region                | Size                                              |
| --------------------- | ------------------------------------------------- |
| Sidebar (expanded)    | 240px                                             |
| Sidebar (collapsed)   | 72px (icon-only)                                  |
| Top header            | 64px                                              |
| Main content max-width| Fluid; comfortable column ~1200–1440px            |
| Page gutter           | `--space-page-gutter` (24px desktop, 16px mobile) |

These are the targets PR 4.5 implements as `.sn-page-shell`,
`.sn-sidebar`, `.sn-header`, and `.sn-content-gutter` (see
[`css.md`](css.md) for the layout-charter contract).

### Sidebar

Items **and order are locked** by [`core-idea.md`](core-idea.md).
Do not invent new top-level items in this document.

| Order | Item       | Default route                  |
| ----- | ---------- | ------------------------------ |
| 1     | Dashboard  | `/w/<slug>/dashboard`          |
| 2     | Inbox      | `/w/<slug>/inbox`              |
| 3     | Feedback   | `/w/<slug>/feedback`           |
| 4     | Submitters | `/w/<slug>/submitters`         |
| 5     | Roadmap    | `/w/<slug>/roadmap`            |
| 6     | Changelog  | `/w/<slug>/changelog`          |
| 7     | Insights   | `/w/<slug>/insights`           |
| 8     | Settings   | `/w/<slug>/settings`           |

Sidebar conventions:

- Wordmark + workspace name at the top. Workspace name links to
  `/w/<slug>/dashboard`.
- One `<a>` per nav item; current item is `aria-current="page"`,
  styled via `[aria-current="page"]` (the only attribute selector
  the layout charter is allowed to use).
- Lucide icon to the left of the label. Collapsed state shows the
  icon only with the label as a `title` and visible-on-focus
  tooltip.
- Badge counts: a small pill beside Inbox shows the count of `new`
  + `needs_info` items. No other items get badges in v2.0.
- Account area at the bottom: avatar/initial + email, opens the
  user menu (Profile, Sign out, Theme switcher).
- A single `+ New feedback` action sits above the nav list — it
  opens the same form the public page uses, scoped to the active
  workspace.

**Out of v2.0 scope**, do not include in the sidebar: Projects,
Tags-as-top-level, Reports, People (separate from Submitters),
Integrations, Saved Views as a top-level. Tag management lives
inside `Settings`. Insights covers report-style aggregations.

### Top header

| Slot (left → right) | Element                                                    |
| ------------------- | ---------------------------------------------------------- |
| Left                | Page-context breadcrumb (workspace · section · page)        |
| Center              | Global search input (`Search feedback…`)                    |
| Right               | Theme switcher · Workspace switcher (if >1) · User menu     |

The header does **not** carry: notifications bell (no notification
system in v2.0), saved-views dropdown (saved views are an Insights
feature, not a global one), or a second `+ Create` menu (the
sidebar's `+ New feedback` is the global action).

---

## Page-header region

Every authenticated page opens with the same three elements:

```text
<h1>Page title</h1>
<p>One-line description that says what this page is for.</p>
[primary action button — optional, right-aligned on desktop]
```

Examples (canonical copy lives in [`pages.md`](pages.md), repeated
here for layout context):

| Page      | `<h1>`     | Description                                                          | Primary action       |
| --------- | ---------- | -------------------------------------------------------------------- | -------------------- |
| Dashboard | Dashboard  | *Triage feedback, spot trends, and decide what needs attention.*     | `+ New feedback`     |
| Inbox     | Inbox      | *Triage new and pending feedback.*                                   | `+ New feedback`     |
| Feedback  | Feedback   | *Every signal across all statuses.*                                  | `+ New feedback`     |
| Roadmap   | Roadmap    | *Planned and in-progress work.*                                      | *(none)*             |
| Insights  | Insights   | *Trends, top tags, and aggregate pain.*                              | *(none)*             |

Description text uses the calm voice from
[`copy-style-guide.md`](copy-style-guide.md) — verbs of clarity, no
exclamation runs, no "Awesome!" / "magic".

---

## Default dashboard composition

```text
Page header
- <h1>Dashboard</h1>
- Description
- + New feedback

Filter row
- Date range · Status · Tag · More filters

Summary row (4 cards)
- Needs attention · High pain · New this week · Median pain

Main work row
- Triage queue (≈65% width)        - Attention panel (≈35% width)

Insight row
- Top tags                          - Intake sparkline

Lower utility row
- Sources breakdown                 - Recent activity
```

### Filter row

Visible-by-default filters are deliberately few:

- Date range (default: last 7 days)
- Status (multi-select; defaults to `new`, `needs_info`, `reviewing`)
- Tag (multi-select)
- A `More filters` overflow button for: priority, pain, submitter,
  source.

A `Clear filters` link appears only when at least one non-default
filter is active.

> **No saved-views control in the dashboard filter row in v2.0.**
> Saved views are an Insights-page concept. The dashboard's
> defaults are the saved view.

### Summary row — four cards

Each card is small, single-purpose, and scannable. **No card has
more than one delta and one number.** No sparkline inside a summary
card; sparklines live in the insight row.

```text
Needs attention
342
+27% vs previous period
```

Recommended four:

| Card             | What it counts                                              |
| ---------------- | ----------------------------------------------------------- |
| Needs attention  | `new` + `needs_info` + `reviewing` items in date range      |
| High pain        | items where `pain_level >= 4`                               |
| New this week    | items created in the last 7 days                            |
| Median pain      | median `pain_level` across items in range (1–5)             |

### Main work row — triage queue

This is the **operational center of the app.** It gets the most
vertical space on the page and the cleanest typography.

Heading: **Triage queue** (not "Recent feedback" — recency is not
the most important sort key).

Default sort:

1. `needs_info` first (blocked on submitter response)
2. then `new`, by `pain_level` desc, then created desc
3. then `reviewing`, same secondary keys

Default visible columns:

| Column      | Notes                                                  |
| ----------- | ------------------------------------------------------ |
| Type        | feature-request / bug / idea — icon + label            |
| Title       | links to detail drawer                                 |
| Submitter   | name or `Anonymous`                                    |
| Source      | small badge (`public form`, `manual`, `import`)        |
| Pain        | 5-dot indicator (●●●○○)                                |
| Priority    | pill: Low · Medium · High · Critical                   |
| Status      | pill: icon + label + color (v2 enum)                   |
| Tags        | up to 3 chips, then `+N more`                          |
| Time        | relative (`3h`, `2d`); full timestamp on hover         |
| Actions     | open · change status · assign tag                      |

Optional / overflow columns (hidden by default, surfaced via column
chooser): assignee, last seen, duplicate count.

Row interactions:

- Click anywhere outside an action → opens the **detail drawer**
  (right-side slide-in, ~480px wide). v2.0 uses a drawer, not a
  full page, for triage speed.
- Status / priority / tag controls are inline editable.
- **No bulk actions in v2.0.** No "select all" checkbox column.

### Attention panel

Sits to the right of the queue. It exists to make the **next
action obvious**.

```text
Attention required

12  unassigned, high pain
8   waiting on submitter > 7 days
3   reviewing > 14 days

[ Start triage → ]
```

Each row links into the queue with the matching filter pre-applied.
The button focuses the first row of the resulting filtered queue.

### Insight row

| Slot               | Content                                                  |
| ------------------ | -------------------------------------------------------- |
| Top tags           | top 5 tags by signal count, with weekly delta            |
| Intake sparkline   | inline-SVG line chart, 14-day or 30-day toggle           |

Charts are **inline SVG** — no Chart.js / D3 / Recharts in v2.0
([`core-idea.md` § Visual non-negotiables](core-idea.md)).

### Lower utility row

| Slot              | Content                                                          |
| ----------------- | ---------------------------------------------------------------- |
| Sources breakdown | `public form / manual / import` counts, % of total in range      |
| Recent activity   | last ~10 status transitions, who/what/when                       |

A polished "pain distribution donut" is **not** on the dashboard
in v2.0. It belongs on `/w/<slug>/insights` if it earns its space
there.

---

## Component vocabulary used by the dashboard

These are the `.sn-*` components PR 4.5 must define or finish.
Detailed contracts live in [`css.md`](css.md); this is the
shopping list.

| Class                       | Status (May 2026)                                          |
| --------------------------- | ---------------------------------------------------------- |
| `.sn-page-shell`            | exists in `layout.css`                                     |
| `.sn-content-gutter`        | exists                                                     |
| `.sn-stack`, `.sn-cluster`  | exist                                                      |
| `.sn-grid-12`               | exists                                                     |
| `.sn-dashboard-grid`        | exists                                                     |
| `.sn-card`, `.sn-card--*`   | exist                                                      |
| `.sn-button`, `.sn-button-*`| exist                                                      |
| `.sn-pill-priority`         | exists                                                     |
| `.sn-pill-status`           | base exists; **per-status modifiers missing** (PR 4.5)     |
| `.sn-form-*`                | exist                                                      |
| `.sn-modal`, `.sn-toast`    | exist                                                      |
| `.sn-empty-state`           | exists                                                     |
| `.sn-skip-link`             | exists                                                     |
| `.sn-feedback-item`         | exists (table row)                                         |
| `.sn-sidebar`, `.sn-sidebar-item` | **not implemented** — PR 4.5                          |
| `.sn-header`                | **not implemented** — PR 4.5                               |
| `.sn-hero` (landing only)   | **not implemented** — PR 4.5                               |
| `.sn-summary-card`          | **not implemented** — PR 4.5                               |
| `.sn-attention-panel`       | **not implemented** — PR 4.5                               |
| `.sn-drawer`                | **not implemented** — PR 4.5                               |

Anything in the "not implemented" rows is the reason the local
screenshots show unstyled chrome today.

---

## Density modes

| Mode        | Layout behaviour                                                              |
| ----------- | ----------------------------------------------------------------------------- |
| Comfortable | Larger spacing, fewer table rows visible, summary cards stack to 2 across     |
| Compact     | **Default.** Balanced spacing, 4 summary cards across, ~12 table rows         |
| Dense       | Tightened spacing, ~18 table rows, optional secondary columns visible         |

Density is a tokens-only swap (a `[data-density]` attribute on
`<html>` overrides spacing tokens). It is **not** a per-component
override.

Density preference persists per user in `localStorage`; a global
"workspace default" lives in Settings (post-v2.0 polish).

---

## Responsive behaviour

The desktop dashboard is dense. Mobile must not try to render the
same grid.

### Tablet (≥ 768px, < 1280px)

- Sidebar collapses to icon-only (72px).
- Summary row: 2 cards across, two rows.
- Main work row: triage queue full-width, Attention panel slides
  underneath as its own card.
- Insight + utility rows stack to 1-column.

### Mobile (< 768px)

- Sidebar becomes a slide-in drawer triggered from a header
  hamburger. Bottom nav is **not used in v2.0** to keep parity with
  the desktop information architecture.
- Page header collapses: `<h1>` only, description hidden under a
  details/expand control, primary action becomes a floating action
  button (FAB) at bottom-right.
- Summary row: horizontal-scroll lane of cards (snap points), one
  card per viewport.
- Filter row collapses into a single `Filters` button that opens a
  bottom sheet.
- Triage queue table converts to a **card list**:

  ```text
  [icon] Reports page is slow to load
  Pain ●●●●○   Priority High   Status Reviewing
  Source public form · Tags Performance, Reports
  Submitted by James Chen · 2d ago
  [ Open ] [ Change status ]
  ```

- Drawer becomes a full-screen panel.

Mobile-only anti-pattern to avoid: a horizontally-scrolling table.
Always card-ify.

---

## Accessibility constraints that shape layout

These come from [`accessibility.md`](accessibility.md) and
[`core-idea.md`](core-idea.md). Layout decisions must respect them
up-front, not retrofit.

- **Skip link** to `#main` is the first focusable element on every
  page (`.sn-skip-link`, visible on focus only).
- **Heading order** is sequential. The dashboard has exactly one
  `<h1>Dashboard</h1>`; row sections (`Triage queue`, `Attention
  required`, `Top tags`, …) are `<h2>`. No skipped levels.
- **Pills are icon + text + color**, never color alone.
- **Focus ring** uses `:focus-visible` and the `--color-focus`
  token. No `outline: none`.
- **Reduced motion**: any motion the layout introduces (drawer
  slide-in, FAB pop, summary-card delta arrow) is wrapped in
  `@media (prefers-reduced-motion: no-preference)` in
  `effects.css`. The non-motion fallback must still convey the
  state change (e.g. drawer simply appears).

---

## Page composition — non-dashboard surfaces

Per-page detail lives in [`pages.md`](pages.md). The shapes below
are the layout-level summary so this document is self-contained.

### Inbox (`/w/<slug>/inbox`)

```text
Page header — h1 "Inbox" · description · + New feedback
Summary row — New · Needs info · Reviewing · Stale (>7d)
Filter row — same as dashboard, Status default = new + needs_info
Triage queue — full-width (no Attention panel; the page is the panel)
```

### Feedback (`/w/<slug>/feedback`)

Like Inbox but with **all** statuses visible by default and a
saved-views slot in the page header.

### Submitter detail / Submitters list

List page mirrors Feedback's table shape. Submitter detail is a
two-column page: identity + history (left, ~60%) and submitted
items table (right, ~40%).

### Roadmap & Changelog

Card-grid layouts, not tables. Each card is one feedback item with
its target/ship date and tags. Public versions
(`/roadmap/public`, `/changelog/public`) drop the sidebar entirely
and use a centered single-column layout (max-width ~720px) so they
read like a marketing page.

### Insights (`/w/<slug>/insights`)

This is where the analytics that don't earn dashboard space live —
pain distribution donut, source breakdown over time, top-tags
trend lines, segment patterns. Two columns of charts on desktop;
stacked on tablet/mobile.

### Settings

Vertical tab navigation on the left within main content area
(Workspace · Members · Tags · Public form · API keys · Danger
zone). Each tab is a single-column form, max-width ~640px.

### Public landing (`/`)

Sidebar **not** present. Layout:

```text
.sn-header (logo left, [Login] [Sign up] right)
.sn-hero — h1 "Capture the noise. Find the signal." + tagline + CTA + mini-demo
Three-up "How it works" — Capture · Triage · Close the loop
Footer — locked links, signalnest.app, year, repo link
```

### Public submission form (`/w/<slug>/submit`)

Sidebar not present. Single centered card on `--color-bg`, no
chrome. Successful submit replaces the card with the locked
thank-you copy from [`core-idea.md`](core-idea.md).

### Auth pages (`/login`, `/signup`, `/forgot-password`,
`/reset-password`, `/verify-email`, `/invitations/<token>`)

Sidebar not present. Centered single-column card, max-width
~420px. Wordmark above the card, locked footer below.

### Styleguide (`/styleguide`)

Sidebar not present. Top bar with the four-way preset switcher
(`production` / `basic` / `unique` / `crazy`). Sectioned, one
section per component family. See
[ADR 056](../../../adr/056-style-guide-page.md).

---

## Layout anti-patterns to avoid

- Treating every widget as equally important.
- Putting more than four filters in the default visible row.
- Making decorative charts larger than the triage queue.
- Sorting work items by recency only (the queue's sort is
  status-then-pain, not created-desc).
- Inventing a new sidebar item not in the locked table.
- Adding a "saved views" or "notifications" control to the global
  header — both are out of v2.0 scope.
- Implementing bulk actions in the triage table — out of v2.0
  scope.
- Building drag-and-drop dashboard customization — not a v2.0
  goal.
- Force-shrinking the desktop table onto mobile instead of
  card-ifying.
- Hiding the primary action below the fold.
- Using color alone for status (color must always travel with icon
  + text).
- Using a web font, gradient app background, or background image
  in v2.0.

---

## What PR 4.5 must deliver, layout-wise

In rough order of "biggest visible win first":

1. `.sn-sidebar` + `.sn-sidebar-item` (incl. `[aria-current="page"]`
   styling, collapsed state, badge slot).
2. `.sn-header` (breadcrumb, search input, right-side menu cluster).
3. `.sn-page-shell` finalised so sidebar + header + main snap
   together without gap or overflow at all three breakpoints.
4. `.sn-pill-status--<status>` modifiers for all nine v2 statuses.
5. `.sn-summary-card` (number + label + delta).
6. `.sn-attention-panel` (heading + linked metric rows + CTA).
7. `.sn-drawer` (right-side slide-in for feedback detail).
8. `.sn-hero` and landing-page chrome.
9. `effects.css` polish pass — focus-ring refinement, hover-lift
   `.sn-fx-*` opt-ins, motion respecting reduced-motion.
10. Styleguide additions so every new component above has a
    canonical render under all four presets.

Each item ships as flat-class CSS at specificity ≤ 0,2,1 per the
charter rules in [`css.md`](css.md), reads only tokens from
`tokens.css`, and is added to the styleguide before being used in a
page template.

---

## Cross-references

- [`core-idea.md`](core-idea.md) — locked strings, sidebar order,
  visual non-negotiables, role model.
- [`pages.md`](pages.md) — per-page composition and copy.
- [`ui.md`](ui.md) — full route map, JS conventions, accessibility
  hooks.
- [`css.md`](css.md) — four-charter rules, specificity ceiling,
  what each charter owns.
- [`theming.md`](theming.md) — token recipes, theme presets, how
  to add a component or effect without breaking the cascade.
- [`live-preview.md`](live-preview.md) — how to see a layout edit
  in the browser without a PR.
- [`accessibility.md`](accessibility.md) — keyboard, ARIA, contrast
  budget.
- [`copy-style-guide.md`](copy-style-guide.md) — voice and tone
  rules for every string the layout puts on screen.
- [`implementation.md`](implementation.md) — phase plan; PR 4.5 is
  the slot that ships the chrome listed above.
- [ADR 056](../../../adr/056-style-guide-page.md) — styleguide page
  + four-way preset system.
- [ADR 058](../../../adr/058-tailwind-via-standalone-cli.md) —
  styling toolchain.
