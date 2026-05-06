# v2.0 — CSS conventions & design system

> Topical detail file. Entry point: [`../spec-v2.md`](../spec-v2.md).
> Visual brief: [`core-idea.md`](core-idea.md).
> Pipeline ADR: [ADR 058 — Tailwind via Standalone CLI](../../../adr/058-tailwind-via-standalone-cli.md).
> Frontend rules: [`../../../notes/frontend-conventions.md`](../../../notes/frontend-conventions.md).

This file is the authoritative answer for *"how does CSS work in
v2.0?"*. It supersedes any earlier guidance for the v2.0 codebase.

---

## The design system at a glance

v2.0 ships a small, **opinionated design system**, not just "some
CSS." The system has four layers; PRs touch one layer at a time:

| Layer            | Lives in                              | What it is                                                                |
| ---------------- | ------------------------------------- | ------------------------------------------------------------------------- |
| 1. Tokens        | `tokens.css`                          | Named primitives (color, radius, shadow, motion, z-layer) as CSS custom properties. The only place raw values exist. |
| 2. Primitives    | `base.css`, `layout.css`              | Element resets + structural layout classes (`sn-page-shell`, `sn-dashboard-grid`, `sn-stack`, `sn-cluster`, `sn-grid-12`, `sn-content-gutter`). |
| 3. Components    | `components.css`                      | The `sn-*` vocabulary — visible UI atoms with documented variants and states. |
| 4. Effects       | `effects.css`                         | Decorative-only: transitions, keyframes, hover polish. Removable for print or low-motion. |

The **styleguide page** (`/styleguide`, [ADR 056](../../../adr/056-style-guide-page.md))
is the system's source of truth: every component renders there in
every state, plus four named theme presets. A component without
a styleguide row is incomplete.

The system rests on three discipline rules that bind every layer:

1. **Tags carry meaning, classes carry style.** Semantic HTML
   first; CSS targets classes only.
2. **Tokens drive everything.** Components reference tokens, not
   raw values; theme switches override token values, never
   selectors.
3. **Three-template promotion.** Patterns are inline utilities
   until they appear in 3+ templates, then they earn a class.

---

## Tooling pipeline

| Step | Input                          | Tool                          | Output                       |
| ---- | ------------------------------ | ----------------------------- | ---------------------------- |
| 1    | `static/css/input.css` (which `@import`s the rest) + `tailwind.config.cjs` | Tailwind Standalone CLI binary | `static/css/app.css`         |
| 2    | `static/css/app.css`           | served by FastAPI `StaticFiles` | browser                      |

- **Standalone CLI only.** No Node.js, no `npm`, no PostCSS plugin
  zoo. The CLI binary is downloaded by `task setup:css` into
  `.tools/tailwindcss` (gitignored) per
  [ADR 058](../../../adr/058-tailwind-via-standalone-cli.md).
- **No preprocessor.** No SCSS, LESS, Stylus.
- **No CSS-in-JS.** No emotion, styled-components, vanilla-extract.
- **No external CSS framework.** No Bootstrap, Bulma, Pico,
  PrimeVue, Materialize. Tailwind is the only framework in v2.0;
  adding a second one needs an ADR.
- **`app.css` is not committed.** Generated at build time, baked
  into the container image; missing locally → run `task build:css`.

---

## File organization

v2.0 ships ~22 distinct pages ([`pages.md`](pages.md)) and a
deliberate visual identity. Putting all CSS source in one file
makes diffs noisy and hides the *kind* of change behind
line-level edits. v2.0 therefore splits CSS source into five
small files with strict charters, all `@import`-ed from
`input.css`:

```text
src/feedback_triage/static/css/
├── input.css       # entry; only @tailwind + @import statements
├── tokens.css      # design tokens (CSS custom properties); no selectors below :root
├── base.css        # element resets + a11y floors; no class selectors
├── layout.css      # layout primitives (page shell, dashboard grid, stack)
├── components.css  # the .sn-* component vocabulary (@apply lives here)
├── effects.css     # transitions, animations, hover/focus polish, gradients
└── app.css         # generated — DO NOT EDIT, NOT COMMITTED
```

Load order is **significant** and corresponds to specificity
intent: tokens → base → layout → components → effects. Don't
reorder.

### File charters

Each file declares its charter at the top in a comment. PRs that
put content in the wrong file are rejected on review.

| File             | May contain                                                                           | Must not contain                              |
| ---------------- | ------------------------------------------------------------------------------------- | --------------------------------------------- |
| `input.css`      | `@tailwind` directives, `@import` of the other files, nothing else                    | rules, tokens, `@apply`                       |
| `tokens.css`     | `:root { --… }`, `[data-theme="…"] :root { --… }`, `@custom-media` declarations       | class selectors, `@apply`, element rules      |
| `base.css`       | element resets (`html`, `body`, `*`), `:focus-visible` ring, reduced-motion           | class selectors                               |
| `layout.css`     | `.sn-page-shell`, `.sn-dashboard-grid`, `.sn-stack`, `.sn-cluster`, container queries | component-level styling, decorative effects  |
| `components.css` | `.sn-<component>` rules with `@apply`; element + state classes                        | tokens, layout primitives, decorative effects |
| `effects.css`    | transitions, keyframes, gradient surfaces, decorative `:hover` polish                 | structural rules; anything required for a11y |

`input.css` is a thin orchestrator:

```css
@tailwind base;
@import "./tokens.css";
@import "./base.css";

@tailwind components;
@import "./layout.css";
@import "./components.css";

@tailwind utilities;
@import "./effects.css";
```

`app.css` is the only file the browser sees. It is generated
by the Tailwind Standalone CLI, baked into the container image,
and **not committed**. Missing locally → run `task build:css`.

### Contents of each file

#### `tokens.css`

```css
/* tokens.css — charter: only :root + [data-theme] custom-property
   declarations and @custom-media. No selectors, no @apply. */

:root {
  --color-bg: #f8fafc;          /* slate-50 */
  --color-surface: #ffffff;
  --color-surface-alt: #f1f5f9; /* slate-100 */
  --color-text: #0f172a;        /* slate-900 */
  --color-text-muted: #64748b;  /* slate-500 */
  --color-primary: #0d9488;     /* teal-600 */
  --color-primary-hover: #0f766e; /* teal-700 */
  --color-warning: #f59e0b;     /* amber-500 */
  --color-danger: #e11d48;      /* rose-600 */
  --color-border: #e2e8f0;      /* slate-200 */
  --color-focus: #14b8a6;       /* teal-500 */
  --radius-sm: 0.375rem;
  --radius-md: 0.75rem;
  --radius-lg: 1rem;
  --shadow-sm: 0 1px 2px rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 12px rgb(0 0 0 / 0.08);
  --motion-fast: 120ms;
  --motion-base: 200ms;
  --motion-slow: 320ms;
  --easing-standard: cubic-bezier(0.2, 0, 0, 1);
  --z-sticky: 10;
  --z-overlay: 50;
}

:root[data-theme="dark"] {
  --color-bg: #020617;          /* slate-950 */
  --color-surface: #0f172a;     /* slate-900 */
  --color-surface-alt: #1e293b; /* slate-800 */
  --color-text: #f1f5f9;        /* slate-100 */
  --color-text-muted: #94a3b8;  /* slate-400 */
  --color-primary: #2dd4bf;     /* teal-400 */
  --color-primary-hover: #5eead4; /* teal-300 */
  --color-warning: #fbbf24;     /* amber-400 */
  --color-danger: #fb7185;      /* rose-400 */
  --color-border: #334155;      /* slate-700 */
  --color-focus: #2dd4bf;
}

@custom-media --md (min-width: 768px);
@custom-media --lg (min-width: 1024px);
```

#### `base.css`

```css
/* base.css — charter: element-level rules only. No class selectors. */

html { color-scheme: light dark; }
body { background: var(--color-bg); color: var(--color-text); }

:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: 2px;
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

#### `layout.css`

```css
/* layout.css — charter: structural primitives. No decorative styling. */

.sn-page-shell     { @apply min-h-screen bg-bg text-ink flex flex-col; }
.sn-dashboard-grid { display: grid; grid-template-columns: 16rem 1fr;
                     min-height: 100vh; }
.sn-content-gutter { @apply mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-8; }
.sn-stack          { display: flex; flex-direction: column; gap: 1rem; }
.sn-cluster        { display: flex; flex-wrap: wrap; align-items: center;
                     gap: 0.5rem; }
.sn-grid-12        { display: grid; grid-template-columns: repeat(12, minmax(0, 1fr));
                     gap: 1rem; }
```

#### `components.css`

```css
/* components.css — charter: .sn-<component> rules + their states.
   @apply is only legal here and in layout.css. */

.sn-card        { @apply bg-surface border border-line rounded-2xl shadow-sm p-4; }
.sn-card-header { @apply flex items-center justify-between mb-3; }
.sn-card-body   { @apply space-y-2; }
.sn-card-footer { @apply mt-3 flex items-center justify-end gap-2; }

.sn-button             { @apply inline-flex items-center gap-2 rounded-xl px-4 py-2
                                  font-medium transition-colors; }
.sn-button-primary     { @apply bg-brand text-white hover:bg-brand-hover; }
.sn-button-secondary   { @apply bg-surface border border-line text-ink
                                  hover:bg-surface-alt; }
.sn-button-ghost       { @apply bg-transparent text-ink hover:bg-surface-alt; }
.sn-button-danger      { @apply bg-danger text-white hover:opacity-90; }
.sn-button:disabled,
.sn-button.is-disabled { @apply opacity-50 cursor-not-allowed; }
.sn-button.is-loading  { @apply cursor-progress; }
.sn-button.is-loading::after { /* spinner */ }

.sn-pill-status   { @apply inline-flex items-center gap-1 rounded-full
                            px-2.5 py-1 text-xs font-medium; }
.sn-pill-priority { @apply inline-flex items-center rounded-md
                            px-2 py-0.5 text-xs font-semibold; }

.sn-form-field        { @apply block; }
.sn-form-field-label  { @apply block text-sm font-medium text-ink mb-1; }
.sn-form-field-input  { @apply block w-full rounded-xl border border-line
                                  focus:border-brand focus:ring-2
                                  focus:ring-brand/20; }
.sn-form-field-help   { @apply mt-1 text-xs text-ink-muted; }
.sn-form-field.has-error .sn-form-field-input { @apply border-danger; }
.sn-form-field.has-error .sn-form-field-help  { @apply text-danger; }

.sn-feedback-item { @apply sn-card cursor-pointer hover:shadow-md
                            transition-shadow; }

.sn-modal       { @apply rounded-2xl bg-surface text-ink shadow-md
                          p-6 max-w-lg w-full; }
.sn-modal::backdrop { background: rgb(0 0 0 / 0.4); }

.sn-empty-state { @apply flex flex-col items-center text-center py-12
                          gap-3 text-ink-muted; }

.sn-toast       { @apply fixed bottom-4 right-4 rounded-xl bg-slate-900
                          text-white px-4 py-2 z-50; }

.sn-skip-link   { @apply sr-only focus:not-sr-only focus:absolute
                          focus:top-2 focus:left-2 focus:bg-surface
                          focus:text-ink focus:rounded focus:px-3
                          focus:py-2; }
```

#### `effects.css`

```css
/* effects.css — charter: decorative-only. Removable for print. */

.sn-card   { transition: box-shadow var(--motion-base) var(--easing-standard); }
.sn-button { transition: background-color var(--motion-fast) var(--easing-standard),
                          color            var(--motion-fast) var(--easing-standard); }

@keyframes sn-fade-in {
  from { opacity: 0; transform: translateY(4px); }
  to   { opacity: 1; transform: translateY(0); }
}
.sn-toast { animation: sn-fade-in var(--motion-base) var(--easing-standard); }
```

The `[data-theme="dark"]` selector is paired with the `darkMode:
'selector'` setting in `tailwind.config.cjs` (see below) so dark
mode is opt-in and JS-toggled, not OS-driven.

---

## `tailwind.config.cjs`

Lives at the repo root. Minimal and explicit:

```js
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'selector',
  content: [
    './src/feedback_triage/static/pages/**/*.html',
    './src/feedback_triage/static/js/**/*.js',
    './src/feedback_triage/routes/pages/**/*.py',
  ],
  theme: {
    extend: {
      colors: {
        // map tokens to Tailwind palette names so utilities resolve
        // to var(--color-*) at runtime
        bg: 'var(--color-bg)',
        surface: 'var(--color-surface)',
        'surface-alt': 'var(--color-surface-alt)',
        ink: 'var(--color-text)',
        'ink-muted': 'var(--color-text-muted)',
        brand: 'var(--color-primary)',
        'brand-hover': 'var(--color-primary-hover)',
        warn: 'var(--color-warning)',
        danger: 'var(--color-danger)',
        line: 'var(--color-border)',
      },
      borderRadius: {
        sm: 'var(--radius-sm)',
        md: 'var(--radius-md)',
        lg: 'var(--radius-lg)',
      },
      boxShadow: { sm: 'var(--shadow-sm)' },
      fontFamily: {
        sans: [
          '-apple-system','BlinkMacSystemFont','"Segoe UI"','Roboto',
          '"Helvetica Neue"','Arial','"Noto Sans"','sans-serif',
          '"Apple Color Emoji"','"Segoe UI Emoji"',
        ],
        mono: [
          'ui-monospace','SFMono-Regular','Menlo','Consolas',
          '"Liberation Mono"','monospace',
        ],
      },
    },
  },
  plugins: [],
};
```

The `content` glob covers every place a class name can be authored:
HTML page shells, per-page JS, and the small handful of Python files
that emit class names directly (sidebar partial). If a new directory
ever produces classes, it must be added here in the same PR.

---

## Authoring rules

These are tested by code review, not tooling.

### 1. Tags carry meaning, classes carry style

- Use the right HTML tag for what an element *is*: `<header>`,
  `<nav>`, `<main>`, `<section>`, `<article>`, `<aside>`,
  `<footer>`, `<button>`, `<a>`, `<form>`, `<label>`, `<table>`,
  `<dialog>`, `<details>`, `<summary>`, `<figure>`, `<time>`.
  `<div>` and `<span>` are reserved for genuinely semantic-free
  wrappers (layout grouping, animation hooks).
- Actions that *do* something are `<button>`. Things that
  *navigate* are `<a>`. Never `<div onclick>`.
- Every `<input>` has a paired `<label for="…">`. Floating labels
  are still real labels, not placeholders.
- Heading levels are sequential. One `<h1>` per page; no skipping
  levels (`<h2>` then `<h4>` is a bug).
- One `<main>` per page; the skip-link (`sn-skip-link`) targets
  it via `#main`.
- **Never** style by `id` or `data-*`. CSS targets classes only.
  `data-state` / `data-theme` may be *read* by CSS attribute
  selectors only when they represent a state the page mutates at
  runtime (e.g. `[data-theme="dark"]`); never as a styling hook
  for static layout.
- **Never** put `role="button"` on a `<div>`. Use `<button>`.
  ARIA roles are reserved for cases where no native element
  exists; everything else is a sign you picked the wrong tag.
- Decorative icons get `aria-hidden="true"`; meaningful icons
  get an accessible name (`aria-label` on the icon, or visible
  text alongside).

### 2. Compose with utilities first; promote to a class on repeat

- First implementation of any pattern: inline Tailwind utilities.
- When the same `class="..."` string appears verbatim in **three
  or more** templates, promote to `sn-<thing>` in
  `components.css` (or `layout.css` if it's structural) via
  `@apply`.
- Don't pre-promote. Don't keep two parallel ways to render a
  card.
- `@apply` is **only** legal inside `components.css` and
  `layout.css`. Never in HTML, never in `tokens.css` or
  `base.css`.

#### Utility classes vs. component classes — which goes where

| Pattern                                                          | Goes in           |
| ---------------------------------------------------------------- | ----------------- |
| One element, one page (`flex items-center gap-2`)                | inline utilities  |
| Same 4–6 utility string, two templates                            | inline utilities  |
| Same string in 3+ templates                                      | promote to `sn-*` |
| Structural / layout shape (page shell, dashboard grid, stack)    | `layout.css`      |
| Visible UI atom with variants + states (button, card, modal)     | `components.css`  |
| Token (color, radius, shadow, motion, z-layer)                   | `tokens.css`      |
| Element-level reset / a11y floor                                 | `base.css`        |
| Decorative-only hover polish, keyframes, gradients               | `effects.css`     |

Authored utility strings should rarely exceed **6 utilities** on
one element. If they do, you're either missing a layout primitive
or you've found a candidate for promotion.

### 3. Tokens drive everything

- Color, radius, shadow, motion, and z-layer values come from CSS
  custom properties defined in `tokens.css`.
- Tailwind's palette (`teal-600`, `slate-200`) is allowed in
  templates because the config maps it through CSS variables, but
  the **theme presets** (light, dark, plus the four
  [ADR 056](../../../adr/056-style-guide-page.md) presets) all
  override the same custom-property names and nothing else.
- A new design token requires updating `tokens.css`,
  `tailwind.config.cjs`, the styleguide, and `core-idea.md` in
  one PR.

### 3a. Specificity budget

Class-only selectors. Hard ceiling **0,2,1**:

- `0,1,0` — single class. The default.
- `0,2,0` — class + state class (`.sn-button.is-loading`).
- `0,2,1` — class + pseudo (`:hover`, `:focus-visible`,
  `::before`, `::backdrop`).
- Anything higher is a smell. Reach for a modifier class before a
  deeper selector.
- No `#id` selectors. No tag-only style overrides below `base.css`.
- Element-tag rules below `base.css` are forbidden — if you need
  to style every `<button>` inside a card, give the card's
  buttons a class.

### 4. No `!important`

- Forbidden, with one exception: the `prefers-reduced-motion`
  block above, where it's necessary to override Tailwind's own
  `transition-*` utilities.

### 5. Sizing units

- Use `rem` for vertical rhythm and font sizes.
- Use `ch` for max-width on prose blocks (e.g. `max-w-prose` =
  `65ch`).
- Avoid `px` except for hairlines (`border-1` / `1px`) and shadow
  offsets.

### 6. Focus is non-negotiable

- Every focusable element shows a `:focus-visible` ring tied to
  `var(--color-focus)`.
- Do **not** zero out `outline` without replacing it.
- Skip-link `.sn-skip-link` is required on every page; it links
  to `#main`.

### 7. Z-index discipline

Three values only, declared as utilities:

| Layer       | Tailwind class | Use                                  |
| ----------- | -------------- | ------------------------------------ |
| Base        | (none)         | normal flow                          |
| Sticky      | `z-10`         | sticky table headers, top nav        |
| Overlay     | `z-50`         | dialogs (`<dialog>`), toasts         |

Anything claiming a fourth layer needs review.

### 8. Responsive strategy

- **Mobile-first.** Default styles target ≤ 640px.
- **Three breakpoints**, Tailwind defaults: `sm` 640, `md` 768,
  `lg` 1024.
- The dashboard sidebar collapses to a top-of-page `<details>`
  disclosure under `md`.
- Tables stay tables; on narrow screens, columns hide via
  `hidden md:table-cell` rather than reflowing into cards.

---

## Component vocabulary

Every screen is built from this list. Adding a new component
needs a row on `/styleguide` and a brief mention in this table
in the same PR. Modifiers (`-primary`, `-secondary`, etc.) use
single dashes — not BEM `--` — because the `sn-` prefix already
namespaces.

| Class                              | Used on                                          |
| ---------------------------------- | ------------------------------------------------ |
| `sn-card` / `sn-card-header` / `sn-card-body` / `sn-card-footer` | dashboard cards, settings panels |
| `sn-button` + `-primary` / `-secondary` / `-ghost` / `-danger`   | every action surface                  |
| `sn-pill-status`                   | status pills (one per `status_enum` value)       |
| `sn-pill-priority`                 | priority pills (low / medium / high / critical)  |
| `sn-pill-type`                     | feedback-type pill (bug / feature_request / etc.) — icon + text + color |
| `sn-tag-chip`                      | tag chips on inbox rows + detail page (workspace-tag color, removable on detail) |
| `sn-submitter-chip`                | inline submitter avatar + name on inbox / detail / submitters list |
| `sn-pain-dots`                     | 5-dot pain-level indicator (filled = `var(--color-primary)`) |
| `sn-form-field` / `-label` / `-input` / `-help` + `.has-error`   | every form input                |
| `sn-feedback-item`                 | clickable inbox / list row container             |
| `sn-modal`                         | `<dialog>` styling                               |
| `sn-empty-state`                   | empty-state blocks across pages                  |
| `sn-toast`                         | bottom-right transient notification              |
| `sn-skip-link`                     | accessibility skip-link, every page              |
| `sn-page-shell` / `sn-dashboard-grid` / `sn-stack` / `sn-cluster` / `sn-grid-12` / `sn-content-gutter` | layout primitives ([`layout.css`](#contents-of-each-file)) |

Pills (`sn-pill-*`) all carry **icon + text + color** \u2014 never
color alone. Color is decorative; icon and text are the
information channel ([`accessibility.md`](accessibility.md)).

| Class                | Modifiers                                          | What it is                                                 |
| -------------------- | -------------------------------------------------- | ---------------------------------------------------------- |
| `sn-card`            | (`-header`, `-body`, `-footer` parts)              | the most-used surface block                                |
| `sn-button`          | `-primary`, `-secondary`, `-ghost`, `-danger`      | base button; states `is-loading`, `is-disabled`, `has-error` |
| `sn-pill-status`     | (color via state class: `is-open`, `is-resolved`…) | rounded-full status indicator (icon + text + color)        |
| `sn-pill-priority`   | (`-low`, `-med`, `-high`)                          | rounded-md priority indicator                              |
| `sn-form-field`      | (`-label`, `-input`, `-help` parts)                | label + input + help + error composition                   |
| `sn-feedback-item`   | —                                                  | the canonical row/card for one feedback record             |
| `sn-modal`           | (`-header`, `-body`, `-footer` parts)              | `<dialog>`-based modal; `::backdrop` styled                |
| `sn-empty-state`     | —                                                  | illustrated "nothing here yet" block                       |
| `sn-toast`           | `-info`, `-success`, `-warn`, `-danger`            | transient bottom-right status message                      |
| `sn-skip-link`       | —                                                  | a11y skip-to-main link                                     |

Layout primitives live in `layout.css`, not in templates as
utility strings:

| Class                | What it is                                              |
| -------------------- | ------------------------------------------------------- |
| `sn-page-shell`      | full-page chrome (header / main / footer)               |
| `sn-dashboard-grid`  | sidebar + main two-pane (collapses on mobile)           |
| `sn-content-gutter`  | `mx-auto max-w-6xl px-4 … py-8` wrapper                 |
| `sn-stack`           | vertical flex with gap                                  |
| `sn-cluster`         | inline-flex with wrap + gap                             |
| `sn-grid-12`         | 12-column CSS grid                                      |

Why these are promoted now: the v2.0 page surface is ~22
distinct screens ([`pages.md`](pages.md)). Composing each from
raw utility strings at the call site duplicates the same
six-utility shells dozens of times. Layout primitives in
`layout.css` make page templates read as structure
(`<div class="sn-dashboard-grid">…`) rather than as decoration.

### State classes (cross-component vocabulary)

State classes are reused across components and mean the same
thing everywhere. Defined in `components.css` next to their
first owner; reused without redefinition.

| Class           | Means                                                  |
| --------------- | ------------------------------------------------------ |
| `is-open`       | disclosure-style component is expanded                 |
| `is-active`     | currently-selected nav item, tab, or filter            |
| `is-loading`    | async work in flight; pair with `aria-busy="true"`     |
| `is-disabled`   | action unavailable; pair with `aria-disabled="true"`   |
| `has-error`     | server validation failed                               |
| `has-warning`   | non-fatal advisory                                     |

Loading and disabled are **not** the same: loading keeps the
user's intent ("working on it"), disabled denies it ("can't
click this yet"). Different visuals, different ARIA, different
recovery paths.

### Required state coverage

Every interactive component declares **all five** of: default,
hover, focus-visible, disabled, loading. Error is required
where the component participates in form validation. The
styleguide page is ship-blocking: a component without all
required states rendered on `/styleguide` is incomplete.

---

## Theme presets (styleguide only)

[ADR 056](../../../adr/056-style-guide-page.md) defines four named
presets — `production`, `basic`, `unique`, `crazy` — used **only**
on `/styleguide`. They override the same `--color-*` tokens via a
`data-theme` attribute on the styleguide's `<main>` wrapper.

Production app pages always use the unmarked default tokens (light
mode) plus the dark-mode override; theme presets never reach the
real product.

---

## Build & dev workflow

| Task                | What it does                                                        |
| ------------------- | ------------------------------------------------------------------- |
| `task setup:css`    | Downloads the Tailwind Standalone CLI binary into `.tools/`.        |
| `task build:css`    | One-shot build: `input.css` (with its `@import`s) → `app.css`, minified. |
| `task watch:css`    | Watcher: re-builds on save while `task dev` is running.             |
| `task dev`          | FastAPI auto-reload + (optional) parallel `watch:css`.              |
| `task check`        | CI gate; includes `task build:css` so missing classes fail the build. |

In the container image, `task build:css` runs in the build stage
and `app.css` is copied into the runtime stage. The runtime image
does not contain the CLI binary.

---

## What v2.0 deliberately rejects

| Idea                                | Why it's rejected for v2.0                              |
| ----------------------------------- | ------------------------------------------------------- |
| Node.js + npm + PostCSS             | Adds a second toolchain ([ADR 058](../../../adr/058-tailwind-via-standalone-cli.md)). |
| BEM, ITCSS, OOCSS                   | Tailwind covers the same ground without taxonomy churn. |
| CSS-in-JS                           | No JS framework in v2.0; runtime cost on every render.  |
| A web font                          | Zero FOIT, zero licensing surface in v2.0.              |
| `!important` outside reduced-motion | Cascade games are a leak indicator.                     |
| Inline `style="..."`                | Defeats the cascade and the styleguide.                 |
| `@apply` in HTML / page shells      | `@apply` is only legal inside `components.css` and `layout.css`. |
| `@apply` in `tokens.css` or `base.css` | Tokens are declarations only; base is element-level only.      |
| Page-scoped CSS files               | A pattern needed by one page is composed inline; a pattern needed by many is promoted to `components.css`. |

---

## Cross-references

- [`core-idea.md`](core-idea.md) — palette, components shorthand.
- [`pages.md`](pages.md) — per-page composition using these classes.
- [`theming.md`](theming.md) — practical recipes for changing
  colors, components, layout, motion, and adding theme presets
  without breaking these rules.
- [`tooling.md`](tooling.md) — `task build:css` wiring.
- [`../../../notes/frontend-conventions.md`](../../../notes/frontend-conventions.md)
- [ADR 056 — Style guide page](../../../adr/056-style-guide-page.md)
- [ADR 058 — Tailwind via Standalone CLI](../../../adr/058-tailwind-via-standalone-cli.md)
