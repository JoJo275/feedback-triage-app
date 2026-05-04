# v2.0 — CSS conventions & design system

> Topical detail file. Entry point: [`../spec-v2.md`](../spec-v2.md).
> Visual brief: [`core-idea.md`](core-idea.md).
> Pipeline ADR: [ADR 058 — Tailwind via Standalone CLI](../../../adr/058-tailwind-via-standalone-cli.md).
> Frontend rules: [`../../../notes/frontend-conventions.md`](../../../notes/frontend-conventions.md).

This file is the authoritative answer for *"how does CSS work in
v2.0?"*. It supersedes any earlier guidance for the v2.0 codebase.

---

## Tooling pipeline

| Step | Input                          | Tool                          | Output                       |
| ---- | ------------------------------ | ----------------------------- | ---------------------------- |
| 1    | `static/css/input.css` + `tailwind.config.cjs` | Tailwind Standalone CLI binary | `static/css/app.css`         |
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

```text
src/feedback_triage/static/css/
├── input.css       # source — tokens, @layer base/components/utilities, @apply
└── app.css         # generated — DO NOT EDIT
```

`input.css` is the **only** CSS source file in v2.0. It is short by
design: every screen is built from Tailwind utilities, and the
file's job is to define the design tokens, the resets that Tailwind's
`preflight` does not cover, and a tiny set of bespoke component
classes for things that would otherwise repeat 30+ times.

### Layered structure of `input.css`

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  /* design tokens — CSS custom properties */
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
  }

  [data-theme="dark"] :root,
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

  /* minimal resets Tailwind preflight does not cover */
  html { color-scheme: light dark; }
  :focus-visible { outline: 2px solid var(--color-focus); outline-offset: 2px; }

  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
      scroll-behavior: auto !important;
    }
  }
}

@layer components {
  /* bespoke classes — sn- prefix; only when @apply repeats > 30x */
  .sn-card        { @apply bg-white border border-slate-200 rounded-2xl shadow-sm p-4; }
  .sn-btn-primary { @apply bg-teal-600 hover:bg-teal-700 text-white rounded-xl px-4 py-2 font-medium; }
  .sn-btn-secondary { @apply bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 rounded-xl px-4 py-2; }
  .sn-pill-status { @apply inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium; }
  .sn-pill-priority { @apply inline-flex items-center rounded-md px-2 py-0.5 text-xs font-semibold; }
  .sn-input       { @apply block w-full rounded-xl border border-slate-300 focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20; }
  .sn-label       { @apply block text-sm font-medium text-slate-700 mb-1; }
  .sn-toast       { @apply fixed bottom-4 right-4 rounded-xl bg-slate-900 text-white px-4 py-2; }
  .sn-skip-link   { @apply sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:bg-white focus:text-slate-900 focus:rounded focus:px-3 focus:py-2; }
}

@layer utilities {
  /* bespoke utilities — only when no Tailwind utility exists */
  .sn-grid-12 { display: grid; grid-template-columns: repeat(12, minmax(0, 1fr)); gap: 1rem; }
}
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
  `<nav>`, `<main>`, `<section>`, `<article>`, `<button>`, `<a>`,
  `<form>`, `<label>`, `<table>`, `<dialog>`, `<details>`. `<div>`
  / `<span>` are reserved for genuinely semantic-free wrappers.
- **Never** style by `id` or `data-*`. CSS targets classes only.
- **Never** put `role="button"` on a `<div>`. Use `<button>`.
  ARIA roles are reserved for cases where no native element exists.

### 2. Compose with utilities first; promote to a class only on repeat

- First implementation of any pattern: inline Tailwind utilities.
- When the same `class="..."` string appears verbatim in **three
  or more** templates, promote to `sn-<thing>` in `input.css` via
  `@apply`.
- Don't pre-promote. Don't keep two parallel ways to render a card.

### 3. Tokens drive everything

- Color, radius, shadow values come from CSS custom properties
  defined in the `@layer base` block above.
- Tailwind's palette (`teal-600`, `slate-200`) is allowed in
  templates because the config maps it through CSS variables, but
  the **theme presets** (light, dark, plus the four
  [ADR 056](../../../adr/056-style-guide-page.md) presets) all
  override the same custom-property names and nothing else.
- A new design token requires updating `input.css`,
  `tailwind.config.cjs`, the styleguide, and `core-idea.md` in
  one PR.

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

Every screen is built from this list. Adding a ninth component
needs review.

| Class             | What it is                                            |
| ----------------- | ----------------------------------------------------- |
| `sn-card`         | white surface block, the most-used container         |
| `sn-btn-primary`  | filled teal call-to-action                            |
| `sn-btn-secondary`| outlined neutral action                               |
| `sn-pill-status`  | rounded-full status indicator (color + icon + label)  |
| `sn-pill-priority`| rounded-md priority indicator                         |
| `sn-input`        | text / email / password / textarea wrapper            |
| `sn-label`        | label paired with `sn-input`                          |
| `sn-toast`        | transient bottom-right status message                 |

Layout primitives — provided by Tailwind utilities directly, not
promoted to classes:

| Pattern              | Tailwind composition                              |
| -------------------- | ------------------------------------------------- |
| Page shell           | `min-h-screen bg-bg text-ink`                     |
| Two-pane (sidebar+main) | `grid grid-cols-[16rem_1fr] min-h-screen`     |
| Content gutter       | `mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-8`     |
| Section heading row  | `flex items-center justify-between gap-4 mb-4`    |
| Table wrapper        | `overflow-x-auto rounded-2xl border border-line`  |
| Form row             | `space-y-1`                                       |
| Stack                | `space-y-4` / `space-y-6`                         |
| Inline cluster       | `inline-flex items-center gap-2`                  |

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
| `task build:css`    | One-shot build: `input.css` → `app.css`, minified.                  |
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
| `@apply` in HTML / page shells      | `@apply` is only legal inside `input.css`'s `@layer components`. |

---

## Cross-references

- [`core-idea.md`](core-idea.md) — palette, components shorthand.
- [`pages.md`](pages.md) — per-page composition using these classes.
- [`tooling.md`](tooling.md) — `task build:css` wiring.
- [`../../../notes/frontend-conventions.md`](../../../notes/frontend-conventions.md)
- [ADR 056 — Style guide page](../../../adr/056-style-guide-page.md)
- [ADR 058 — Tailwind via Standalone CLI](../../../adr/058-tailwind-via-standalone-cli.md)
