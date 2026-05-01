# Frontend Conventions — Notes (HTML, CSS, scope)

A companion to the (short) frontend rules in
[`.github/copilot-instructions.md`](../../.github/copilot-instructions.md).
This file expands on **why** semantic HTML matters for this project,
the tags-vs-classes split, and a separate section on whether to grow
this app into a "commercial-product-esque" portfolio piece.

> **For Copilot / new templates:** see the **Semantic HTML and CSS**
> section in `.github/copilot-instructions.md`. The rules there are
> enforced; this file is the rationale and the longer recommendations.

---

## 1. Semantic HTML — yes, hard yes

No pushback on the rule. Every reason to keep it:

- **Accessibility for free.** Screen readers, voice control, and
  keyboard users navigate by landmarks (`<header>`, `<nav>`, `<main>`,
  `<aside>`, `<footer>`) and headings. A page built from `<div>`s is
  invisible to that whole class of users.
- **No JavaScript needed for behavior** that comes built-in. `<button>`
  is keyboard-activatable, focus-styled, and has a role. `<dialog>` has
  modal focus trapping. `<details>`/`<summary>` is a free disclosure
  widget. `<form>` does validation + submission without a single line
  of JS.
- **Better defaults for SEO and link previews.** `<article>`,
  `<time datetime="…">`, `<address>`, and Open Graph meta tags carry
  meaning that crawlers actually use.
- **Cheaper diffs, smaller HTML.** A page with the right tags needs
  fewer classes. One `<nav>` replaces a `<div class="nav">` plus
  `role="navigation"` plus `aria-label`.
- **Spec-aligned with this project.** The spec (and the existing
  `index.html`) already use `<header>`, `<main>`, `<section>`,
  `<form>`, `<label>`, `<button>`. Keeping the bar there is cheap.

### Minimum tag set for this project

| Use case | Right tag |
| --- | --- |
| Page top with logo + primary nav | `<header>` containing `<h1>` and `<nav>` |
| Main page content | `<main id="main">` (one per page; skip-link target) |
| Self-contained chunk with a heading | `<section aria-labelledby="…">` |
| Re-publishable item (one feedback row in detail) | `<article>` |
| List of items | `<ul>` / `<ol>` with `<li>` — never `<div>` rows |
| Tabular data | `<table>` with `<thead>`/`<tbody>`/`<th scope=…>` |
| Action that *does* something | `<button type="button">` (or `type="submit"` inside a form) |
| Action that *navigates* | `<a href="…">` |
| Form input + caption | `<label for="…">` + `<input id="…">` (always paired) |
| Form group | `<fieldset>` + `<legend>` |
| Modal | `<dialog>` (use `.showModal()`, not `.show()`) |
| Disclosure / accordion | `<details>` + `<summary>` |
| Time / date | `<time datetime="2026-04-30T12:00:00Z">` |
| Status / live update region | `<output>` or `<div role="status" aria-live="polite">` |
| Decorative wrapper that needs no semantics | `<div>` — and only then |

### `<div>` and `<span>` — what they actually mean

> `<div>` = generic block container with no semantic meaning. Use it
> when you need a wrapper for layout/styling and **no better tag
> applies**. `<span>` is the same idea inline.

The mental check before reaching for `<div>`:

1. Is this a landmark? → `<header>` / `<nav>` / `<main>` / `<aside>` / `<footer>`.
2. Is this a self-contained section? → `<section>` (with a heading) or `<article>`.
3. Is this a list of similar things? → `<ul>` / `<ol>` / `<dl>`.
4. Is this navigation? → `<nav>` + `<ul>` of `<a>`.
5. Is this a control? → `<button>` / `<a>` / `<input>`.
6. None of the above? → `<div>` is fine. Move on.

If you find yourself adding `role="button"` or `role="navigation"`,
stop: there's a real tag for that. ARIA roles are for cases where the
right tag genuinely doesn't exist (rare in app UIs).

---

## 2. Tags for meaning, classes for styling

The rule, stated precisely:

- **Tag** = what the element *is*.
- **Class** = how the element *looks* (or which variant of the
  component it is).
- **`id`** = unique anchor for `<label for>`, skip-links, and
  fragment URLs. Never style by `id`.
- **`data-*`** = hooks for JavaScript. Never style by `data-*` either,
  unless the styling truly is state-driven (e.g. `data-state="open"`
  on a disclosure).

### Why this matters

When meaning lives in the tag, you can restyle the whole site by
swapping the stylesheet without touching HTML. When meaning lives in
the class (`<div class="header">`), the page is locked to that
stylesheet — you've recreated the worst part of "div soup" with extra
steps.

### Selector budget

Aim for:

- **0 `!important`** in production CSS. (`!important` is a
  capitulation; reach for it only inside a print stylesheet or to
  override a vendor `style=` you can't remove.)
- **Specificity ≤ 0,2,0** for normal rules. One class, one
  pseudo-class, optionally one element. If a selector reads
  `.foo .bar .baz a:hover`, the structure is wrong, not the CSS.
- **No tag-only style overrides** below the reset/base layer. Once
  you've set `button { … }` in the base, override with `.button-ghost`,
  not `header button`.

### Naming

- BEM-lite is fine and the existing CSS already uses it
  (`button button-primary`, `filter-form`, `field`). Block-Element
  with single dashes (`card__title` is also fine if you prefer the
  full BEM split). **Pick one and stick to it.**
- Utility classes are okay sparingly (`.visually-hidden`, `.sr-only`,
  `.text-right`). Don't grow this into Tailwind unless an ADR says so —
  the spec explicitly forbids a CSS bundler.
- State classes go in their own namespace: `is-open`, `is-loading`,
  `has-error`. Read aloud, they say what they mean.

---

## 3. CSS conventions that pair well with the above

Adopt incrementally; flag in PR review when violated.

### Layering

Use one base layer plus a small number of component files:

```
static/css/
  styles.css        # entry: imports the layers below in order
  base/
    reset.css       # modern reset (Andy Bell or new-css-reset)
    tokens.css      # CSS custom properties (color, spacing, radius)
    typography.css  # element-level type rules
  components/
    button.css
    form.css
    card.css
  layouts/
    container.css
    list-page.css
```

Or — equally fine for this project's size — keep one `styles.css`
internally divided by `/* === Buttons === */` banner comments. The
*structure* matters; the file count doesn't. Don't introduce a CSS
preprocessor; CSS custom properties + nesting (Baseline 2024) cover
everything Sass used to.

### Tokens, not magic numbers

Every color, spacing step, radius, and shadow lives in a CSS custom
property:

```css
:root {
  --color-bg: #0e1116;
  --color-text: #e8edf2;
  --color-accent: #6ea8ff;
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 1rem;
  --radius-1: 0.375rem;
  --radius-2: 0.75rem;
  --shadow-1: 0 1px 2px rgb(0 0 0 / 0.2);
}
```

Components reference tokens, never raw hex. Dark mode becomes a
`:root[data-theme="dark"]` block that overrides the same names. This
is also how a future "themes" feature ships in one PR.

### `prefers-color-scheme` from day one

Two media queries cost nothing now and save a refactor later:

```css
@media (prefers-color-scheme: dark) { :root { /* dark tokens */ } }
@media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }
```

(Yes, that's the one place `!important` is justified — overriding
animation on user request.)

### Sizing in `rem`/`ch`/`%`, not `px`

`px` is fine for `border` and `box-shadow`; everything that scales
with text size (padding, gap, max-width, font-size) uses `rem` or
`ch`. Users with a 24px default font still get a readable layout.

### Layout primitives

- **Flexbox** for one-axis layouts (toolbars, button rows).
- **Grid** for two-axis layouts (forms, dashboards). `grid-template-areas`
  is a great tool for "header / sidebar / main" shells.
- **Container queries** (`@container`) for component responsiveness.
  This app is small enough that a single page-level breakpoint is
  often enough; reach for `@container` when one component genuinely
  reflows independently.
- **Logical properties** (`margin-block-start`, `padding-inline`)
  rather than `margin-top` / `padding-left` once any RTL/i18n is on
  the table.

### Focus styles

Never `outline: none` without a replacement. The default focus ring
is ugly but functional; the cheap fix is:

```css
:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}
```

`focus-visible` (not `:focus`) means mouse clicks don't show the ring,
keyboard tabbing does — which is what users actually want.

### Forms

- Every input has a `<label for>` (already required).
- Group related fields in `<fieldset><legend>…</legend>`.
- Error messages live in a sibling element with
  `aria-describedby="field-id-error"` on the input.
- Use native validation attributes (`required`, `minlength`,
  `pattern`) before adding JS. Style with `:invalid` / `:user-invalid`
  (the latter is what you usually actually want — only flags after
  the user has interacted).

### Accessibility checklist (minimum bar)

- Heading levels are sequential (`<h1>` once per page, then `<h2>`s,
  no skipping to `<h4>`).
- Color contrast ≥ 4.5:1 for body text, 3:1 for large text and UI
  borders. Test in dev tools.
- Every image has `alt=""` (decorative) or meaningful alt text.
- Skip-link to `#main` as the first focusable element.
- Tab order matches visual order. Don't use positive `tabindex`.
- All interactive elements reachable + operable with keyboard alone.

### What to avoid

- **Icon fonts** — they break for screen readers and miss in print.
  Use inline SVG with `<title>` or `aria-label`.
- **`<a href="#">` for buttons** — use `<button type="button">`. An
  empty href clutters history and breaks middle-click.
- **`onclick=` attributes** in HTML when an `addEventListener` in JS
  is just as easy. Keeps logic in one place.
- **Tailwind / Bootstrap import** — the spec forbids it. If a
  utility-first approach is genuinely needed, write an ADR.

---

## 4. Recommended addition to `copilot-instructions.md`

The current Frontend section is short. Suggested replacement (or
expansion) — concrete and rule-shaped, with a pointer back here:

> ### Frontend
>
> - Static HTML files served via `StaticFiles`; **no Jinja, no
>   bundler, no SPA framework**.
> - Vanilla JS + Fetch API for dynamic behavior.
> - **Semantic HTML.** Use the right tag for what an element *is*
>   (`<header>`, `<nav>`, `<main>`, `<section>`, `<article>`,
>   `<button>`, `<a>`, `<form>`, `<label>`). `<div>` is a generic
>   block wrapper with no meaning — use only when no better tag
>   applies. `<span>` is the same rule inline.
> - **Tags carry meaning, classes carry style.** Never use `id` or
>   `data-*` for styling. Never put `role="button"` on a `<div>`;
>   use `<button>`.
> - Every input has a `<label for>`; buttons are `<button>`.
> - Same-origin delivery; CSRF is N/A in v1.0 (no cookie auth).
> - See [`docs/notes/frontend-conventions.md`](../docs/notes/frontend-conventions.md)
>   for the long-form rationale, CSS conventions, and accessibility
>   checklist.

The pointer keeps the instructions file short while letting Copilot
discover the deeper guidance when working in `static/`.

---

## 5. Commercial-product features — should this project grow them?

**Short answer: yes, but stage it.** The framing matters. This is
already two projects sharing one repo:

- *Project A* — the v1.0 spec (the small, finished thing).
- *Project B* — the portfolio piece you actually want to show.

Confusing the two is the trap. The fix is to ship A first, freeze it,
then layer B on top with each feature as its own ADR + spec
addendum. Below is the honest take on each idea.

### Tier 1 — high portfolio ROI, modest scope creep

Each of these has a clean stopping point and shows skill the v1.0
scope can't.

| Feature | Why it's worth it | Realistic effort | New surface |
| --- | --- | --- | --- |
| **Search** (full-text on title + description) | Postgres `tsvector` + GIN index demonstrates real DB chops; visible immediately. | S–M | One column, one index, one query, one input. |
| **Dashboard / summaries page** (`/api/v1/stats`) | Counts by status/source, avg pain, trend chart. Shows API design + viz without a framework. | S | One read-only endpoint, one page. |
| **Saved filters / views** | URL-shareable query params already half-exist; persist as named views in `localStorage` first, DB later. | S | URL convention + small JS. |
| **CSV / JSON export** of filtered list | One `StreamingResponse`, instantly useful, talks to "I think about real users." | S | One endpoint. |
| **Inbox-style triage flow** (J/K to navigate, status hotkeys) | Vanilla JS, no deps. Differentiates the UI immediately. | S | Keyboard handler. |
| **Changelog page** (`/changelog`) reading from `CHANGELOG.md` | Lampshades release-please nicely; "this app dogfoods its own automation." | XS | One route. |
| **Real OpenAPI examples + a Try-It page** | You already have FastAPI's `/docs`; add curated examples. | XS | Pydantic `Config.json_schema_extra`. |
| **Telemetry / structured logs viewable in-app** | `/admin/logs` reading the last 200 structured log lines. Shows ops awareness. | S | One endpoint, one page. |

### Tier 2 — adds depth, but doubles the spec

| Feature | What it actually pulls in |
| --- | --- |
| **Auth / login / users** | Sessions or JWT, password reset, email delivery, CSRF, rate limiting, lockout, audit log, GDPR delete. **At minimum a week of work and three ADRs.** |
| **Multi-tenant (orgs / workspaces)** | Tenant column on every table, row-level security or app-layer scoping, invite flow, billing-shaped surface. Realistically only worth it *with* auth. |
| **Settings page** (per-user prefs) | Trivial visually but presupposes auth + a `user_settings` table. Don't build until users exist. |
| **Deduplication** | Real tsvector-based similarity or trigram (`pg_trgm`) — interesting and visible, but only meaningful once the corpus is big enough to dedupe. Pair with seed data ≥ 200 rows. |
| **Categories / tags** | Many-to-many table, tag CRUD UI, filter chips. Honestly more interesting than a "category" enum because it shows you can model a relationship. |
| **Comments / activity log per item** | Great showcase for a second table + ordering + pagination. |
| **AI summaries** (LLM call to summarize description) | Trendy and visible. Costs money per request; needs a budget cap, an env-var key, an ADR on data egress. |
| **Email / Slack notifications on status change** | Outbox pattern + a worker. Pulls in queueing — cool but a real architectural step. |

### Tier 3 — likely traps for a portfolio piece

| Feature | Why it backfires |
| --- | --- |
| **Realtime / WebSockets** | Adds a long-lived connection that fights serverless deploys. Hard to demo on a sleeping app. |
| **Mobile app** | Out of scope; the README "live demo" is the demo. |
| **Plugin system / extension API** | Looks impressive in a demo, but every reviewer reads it as "this person doesn't know when to stop." |
| **Custom auth provider** (write your own OAuth) | Don't. Use a library or hosted IdP if auth ships. |

### How to stage it without losing the v1.0 ship

1. **Cut the v1.0 release first.** Tag, push, freeze the spec. The
   portfolio piece needs a "1.0" milestone in the README.
2. **Open a `v2-design/` folder under `docs/`.** Write a vision doc
   and a roadmap. Pick the first three Tier-1 features by user
   value, not by what's fun to build.
3. **One ADR per Tier-2 feature** before any code. Auth alone is
   ADRs for password storage, session vs JWT, rate limiting, and
   email delivery. Doing them up front signals seniority more than
   the code does.
4. **Keep each feature its own PR + its own ADR + its own spec
   addendum.** The PR template (under `.github/`) already nudges
   you toward this.
5. **Refresh the README screenshots after every Tier-1 feature.**
   The portfolio piece *is* the screenshots; do not let them rot.

### What "looks like a real product" actually means

Reviewers spend ~90 seconds scanning a portfolio repo. The signal
they pick up isn't usually feature count — it's:

1. **README that gets straight to "what / why / try it."**
2. **A live URL that loads in under 2 seconds.**
3. **Tests that pass on push.** Green CI badges.
4. **A meaningful CHANGELOG.** Real semver, real history.
5. **One thing that makes you go "huh, neat."** Could be the keyboard
   navigation, the search-as-you-type, the inline edit, the dark
   mode toggle that respects `prefers-color-scheme`. **One**.
6. **Code organized like an adult wrote it.** Which you already have.

`simple-python-boilerplate` is a strong portfolio piece because of
those six, not because it has more features than its peers. Apply
the same standard here: ship the small thing well, then add **one**
delightful feature at a time.

---

## 6. Risks worth flagging up front

- **Auth changes the threat model entirely.** The moment you have
  user accounts, you have password hashing, session fixation, CSRF,
  account enumeration, email-link replay, and GDPR. Not building
  auth is a perfectly defensible portfolio choice ("read-only
  triage demo, no PII collected"). Building it badly is worse than
  not building it.
- **Multi-tenant retro-fit is expensive.** If you think auth might
  ship, design every new table with `tenant_id` from day one even
  if it's nullable.
- **AI features need a kill switch.** A budget cap (`MAX_LLM_CALLS_PER_DAY`)
  and a feature flag, both wired before the first call. Otherwise a
  bug in a loop costs real money.
- **Feature creep silently breaks the spec.** Every new feature must
  update [`docs/project/spec/spec-v1.md`](../project/spec/spec-v1.md) or
  it's de-facto undocumented. The spec stays the canonical
  description of the system; v2 doesn't get to skip that rule.

---

## 7. Where this lives

- `.github/copilot-instructions.md` — the **rules** (short, enforced).
- This file — the **rationale**, plus longer-form recommendations
  and the v2 product roadmap thinking.

Update both when frontend conventions change. Update this file alone
when adding ideas to the v2 backlog.
