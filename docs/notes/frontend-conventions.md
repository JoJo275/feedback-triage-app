# Frontend Conventions — Notes (HTML, CSS, Tailwind, design system)

> **Audience:** anyone authoring HTML, CSS, or vanilla JS in this
> project — Copilot included.
> **Companion files:**
> - `.github/copilot-instructions.md` — the **rules** (short, enforced).
> - [`../project/spec/v2/css.md`](../project/spec/v2/css.md) — the
>   **CSS implementation source of truth** for v2.0: pipeline,
>   `input.css`, `tailwind.config.cjs`, the `sn-*` component
>   vocabulary, the build-task wiring.
> - [`../project/spec/v2/core-idea.md`](../project/spec/v2/core-idea.md)
>   — palette, locked strings, voice rules, status / pill colors.
> - [ADR 058 — Tailwind via Standalone CLI](../adr/058-tailwind-via-standalone-cli.md)
>   — the styling-pipeline decision.
> - [ADR 056 — Style guide page](../adr/056-style-guide-page.md)
>   — the four named theme presets (`production`, `basic`,
>   `unique`, `crazy`) used on `/styleguide`.
> - [`custom-css-architecture.md`](custom-css-architecture.md) —
>   the **future-direction sketch** for an expanded multi-file
>   custom CSS system (tokens / base / layout / components /
>   effects). Read that when v2.0's single-`input.css` model
>   starts to strain.
>
> This file is the **rationale** plus the longer-form recommendations.
> Anything stricter or shorter — e.g. *"never style by `id`"* — is
> the rule and lives in `copilot-instructions.md` or `v2/css.md`.

---

## 1. Semantic HTML — yes, hard yes

No pushback on the rule. Every reason to keep it:

- **Accessibility for free.** Screen readers, voice control, and
  keyboard users navigate by landmarks (`<header>`, `<nav>`,
  `<main>`, `<aside>`, `<footer>`) and headings. A page built from
  `<div>`s is invisible to that whole class of users.
- **No JavaScript needed for behavior** that comes built-in.
  `<button>` is keyboard-activatable, focus-styled, and has a role.
  `<dialog>` has modal focus trapping. `<details>`/`<summary>` is a
  free disclosure widget. `<form>` does validation + submission
  without a single line of JS.
- **Better defaults for SEO and link previews.** `<article>`,
  `<time datetime="…">`, `<address>`, and Open Graph meta tags
  carry meaning that crawlers actually use.
- **Cheaper diffs, smaller HTML.** A page with the right tags needs
  fewer Tailwind utility classes. One `<nav>` replaces a
  `<div class="flex …">` plus `role="navigation"` plus `aria-label`.
- **Spec-aligned.** The v2.0 spec and the existing `index.html`
  already use `<header>`, `<main>`, `<section>`, `<form>`,
  `<label>`, `<button>`. Keeping the bar there is cheap.

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

1. Is this a landmark? → `<header>` / `<nav>` / `<main>` /
   `<aside>` / `<footer>`.
2. Is this a self-contained section? → `<section>` (with a heading)
   or `<article>`.
3. Is this a list of similar things? → `<ul>` / `<ol>` / `<dl>`.
4. Is this navigation? → `<nav>` + `<ul>` of `<a>`.
5. Is this a control? → `<button>` / `<a>` / `<input>`.
6. None of the above? → `<div>` is fine. Move on.

If you find yourself adding `role="button"` or `role="navigation"`,
stop: there's a real tag for that. ARIA roles are for cases where
the right tag genuinely doesn't exist (rare in app UIs).

---

## 2. Tags carry meaning, classes carry style

The rule, stated precisely:

- **Tag** = what the element *is*.
- **Class** = how the element *looks* (the Tailwind utilities, plus
  the small bespoke `sn-*` component classes).
- **`id`** = unique anchor for `<label for>`, skip-links, and
  fragment URLs. Never style by `id`.
- **`data-*`** = hooks for JavaScript and for state-driven styles
  with **explicit semantics**. Allowed selectors: `data-state`,
  `data-theme`. Never invent ad-hoc `data-*` attributes for
  styling.

Examples of the data-attribute carve-out:

- `data-theme="dark"` on `<html>` — paired with the
  `darkMode: 'selector'` setting in `tailwind.config.cjs`. JS
  toggles the attribute; CSS overrides the `--color-*` tokens.
- `data-state="open"` on `<dialog>` / `<details>` wrappers when JS
  needs to drive open/close styling that the native attribute
  can't reach.

Outside those two cases, push state into a **class**
(`is-loading`, `has-error`) — see §3.

### Why this matters

When meaning lives in the tag, you can restyle the whole site by
swapping the stylesheet without touching HTML. When meaning lives
in the class (`<div class="header">`), the page is locked to that
stylesheet — you've recreated the worst part of "div soup" with
extra steps.

---

## 3. CSS — Tailwind first, custom classes when they earn it

v2.0 uses **Tailwind via the Standalone CLI**
([ADR 058](../adr/058-tailwind-via-standalone-cli.md)) — no Node,
no npm, no PostCSS plugin chain. The full pipeline lives in
[`../project/spec/v2/css.md`](../project/spec/v2/css.md). This
section is the *why* and the conventions; that file is the *what
runs*.

### 3.1 The two-layer mental model

The styling system is **utility-first with a thin component layer**:

| Layer            | Where                                                      | When to use                                                                                   |
| ---------------- | ---------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| Design tokens    | `@layer base` in `static/css/input.css` (CSS custom props) | One source of truth for color, radius, shadow. Theme presets override the same names.        |
| Tailwind utilities | `class="bg-white border border-slate-200 …"` directly in HTML | First reach for *every* visual choice. Most elements only ever need utilities.               |
| `sn-*` components | `@layer components` in `input.css`, defined with `@apply` | Promoted only after the same `class="…"` string appears verbatim in **three or more** templates. |
| `sn-*` utilities  | `@layer utilities` in `input.css`                         | Bespoke utility class only when no Tailwind utility exists (e.g. a custom 12-col grid).      |

There is **no separate "components/cards.css"** file, no SCSS, no
CSS-in-JS. `input.css` is the only CSS source file in v2.0; the
generated `app.css` is the only CSS the browser sees and is **not
committed**.

### 3.2 File organization

```text
src/feedback_triage/static/css/
├── input.css       # source — tokens, @layer base/components/utilities, @apply
└── app.css         # generated by `task build:css`; DO NOT EDIT
```

The structure of `input.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  /* design tokens — CSS custom properties */
  :root { --color-bg: #f8fafc; /* slate-50 */ … }
  :root[data-theme="dark"] { --color-bg: #020617; /* slate-950 */ … }

  /* minimal resets Tailwind preflight does not cover */
  html { color-scheme: light dark; }
  :focus-visible { outline: 2px solid var(--color-focus); outline-offset: 2px; }

  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      animation-duration: 0.01ms !important;
      transition-duration: 0.01ms !important;
    }
  }
}

@layer components {
  .sn-card        { @apply bg-white border border-slate-200 rounded-2xl shadow-sm p-4; }
  .sn-btn-primary { @apply bg-teal-600 hover:bg-teal-700 text-white rounded-xl px-4 py-2 font-medium; }
  /* …rest of the catalog… */
}

@layer utilities {
  .sn-grid-12 { display: grid; grid-template-columns: repeat(12, minmax(0, 1fr)); gap: 1rem; }
}
```

The full block lives in
[`../project/spec/v2/css.md`](../project/spec/v2/css.md#layered-structure-of-inputcss).
Update both files in the same PR.

### 3.3 Naming conventions

This is a custom design system. The naming rules are:

- **Tailwind utilities** stay literal: `bg-teal-600`, `rounded-xl`,
  `text-sm`. Never alias them away with a wrapper class for
  cosmetic reasons.
- **Bespoke component classes** are prefixed `sn-` (SignalNest).
  Block-element shape, single dashes:
  - `sn-card`, `sn-card-header`, `sn-card-footer`.
  - `sn-btn-primary`, `sn-btn-secondary`, `sn-btn-ghost`.
  - `sn-pill-status`, `sn-pill-priority`.
  - `sn-input`, `sn-label`, `sn-toast`, `sn-skip-link`.
- **State classes** use the verb-prefix convention so they read
  aloud:
  - `is-open`, `is-loading`, `is-active`, `is-disabled`.
  - `has-error`, `has-warning`.
- **No BEM `__` or `--`.** The `sn-` prefix plus single dashes
  covers what BEM does without the underscore tax.
- **No utility class with a `sn-` prefix** unless it lives in
  `@layer utilities` and is genuinely a single-purpose CSS
  declaration. The `sn-grid-12` class is the canonical example;
  `sn-card` is *not* a utility (it's a composition).

Names that are **forbidden**:

- Tag-shaped class names — `header`, `nav`, `button` (use the tag).
- Color-baked names — `red-button`, `blue-card`. Use status names
  (`sn-btn-danger`) so a re-skin doesn't lie.
- Layout-baked names on components — `sn-card-left`, `sn-card-grid`.
  Layout is composed with Tailwind utilities at the call site, not
  baked into the component.

### 3.4 The "rule of three" for promoting utilities to a class

The promotion rule, restated:

> First implementation of any visual pattern: inline Tailwind
> utilities. When the same `class="…"` string appears verbatim in
> **three or more** templates, promote it to `sn-<thing>` in
> `input.css` via `@apply`. Don't pre-promote.

Why three:

- Two repeats might be coincidence; three is a pattern.
- Pre-promoted classes make the styleguide lie — they suggest a
  vocabulary that doesn't exist yet.
- Late promotion is cheap (one `@apply` line, search-and-replace);
  early promotion is expensive (every change touches a class file
  *and* every consumer).

When promoting:

1. Pick a name from §3.3.
2. Add the `@apply` line in `input.css` under `@layer components`.
3. Replace the verbatim utility string in every consumer.
4. Run `task build:css` and visually diff.
5. Add a row to the component vocabulary in
   [`../project/spec/v2/css.md`](../project/spec/v2/css.md#component-vocabulary).

### 3.5 Design tokens drive everything

Color, radius, and shadow are CSS custom properties on `:root`
(plus `[data-theme="dark"]`). Tailwind reads them via the
`tailwind.config.cjs` `theme.extend` map, so `bg-bg`, `text-ink`,
`border-line`, `rounded-md` all resolve to `var(--color-…)` or
`var(--radius-…)` at runtime.

Practical consequence: a theme switch (light/dark) or a styleguide
preset (`production` / `basic` / `unique` / `crazy`) is *one
attribute change* on `<html>` or `<main>`. No CSS rebuild, no class
swap, no JS gymnastics.

A **new design token** requires updating four files in one PR:

1. `static/css/input.css` (the `@layer base` block).
2. `tailwind.config.cjs` (the `theme.extend` map).
3. `docs/project/spec/v2/css.md` (the canonical token list).
4. `docs/project/spec/v2/core-idea.md` (the palette tables).

If any of those four lag, the design system has drifted.

### 3.6 Layout primitives

v2.0 layouts are composed from a small Tailwind vocabulary, not
from bespoke layout classes. The catalog:

| Pattern                  | Tailwind composition                              |
| ------------------------ | ------------------------------------------------- |
| Page shell               | `min-h-screen bg-bg text-ink`                     |
| Two-pane (sidebar + main)| `grid grid-cols-[16rem_1fr] min-h-screen`         |
| Content gutter           | `mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-8`     |
| Section heading row      | `flex items-center justify-between gap-4 mb-4`    |
| Table wrapper            | `overflow-x-auto rounded-2xl border border-line` |
| Form row                 | `space-y-1`                                       |
| Stack                    | `space-y-4` / `space-y-6`                         |
| Inline cluster           | `inline-flex items-center gap-2`                  |
| Card grid                | `grid gap-4 md:grid-cols-2 lg:grid-cols-3`        |

Layout composition stays at the **call site**. A page that needs a
two-pane shell writes the Tailwind utility string in its own
template; promoting "two-pane shell" to `.sn-shell-two-pane` would
hide the layout from the reader without saving any keystrokes.

### 3.7 Component vocabulary (v2.0)

The full eight-component list lives in
[`../project/spec/v2/css.md`](../project/spec/v2/css.md#component-vocabulary).
Adding a ninth needs review. Today's list:

`sn-card`, `sn-btn-primary`, `sn-btn-secondary`, `sn-pill-status`,
`sn-pill-priority`, `sn-input`, `sn-label`, `sn-toast`.

Plus the one bespoke utility: `sn-grid-12`.

### 3.8 Theme presets and dark mode

- Dark mode is **opt-in** via `data-theme="dark"` on `<html>`,
  paired with `darkMode: 'selector'` in `tailwind.config.cjs`. We
  do **not** key off `prefers-color-scheme` directly — the user
  toggle wins, OS preference is the *initial* default.
- The four ADR-056 styleguide presets (`production`, `basic`,
  `unique`, `crazy`) override the same `--color-*` token names on
  the `/styleguide` page only. The product UI never sets a preset
  attribute.
- Production app pages: unmarked default tokens (light) **plus**
  the `data-theme="dark"` override.

### 3.9 Selector budget

- **0 `!important`** in production CSS, with one exception: the
  `prefers-reduced-motion` block, which has to override Tailwind's
  own `transition-*` utilities.
- **Specificity ≤ 0,2,0** for normal rules. One class, one
  pseudo-class, optionally one element. If a selector reads
  `.foo .bar .baz a:hover`, the structure is wrong, not the CSS.
- **No tag-only style overrides** below the reset/base layer. Once
  Tailwind preflight has set `button { … }`, override with
  `.sn-btn-ghost`, not `header button`.
- **No inline `style="…"`.** Defeats the cascade and the
  styleguide. Dynamic values (a progress bar width, an inline-SVG
  chart's `stroke-dasharray`) are the only legitimate inline
  styles, and they should be JS-set, not authored.

### 3.10 Z-index discipline

Three values only, all expressed as Tailwind utilities:

| Layer   | Class   | Use                                  |
| ------- | ------- | ------------------------------------ |
| Base    | (none)  | normal flow                          |
| Sticky  | `z-10`  | sticky table headers, top nav        |
| Overlay | `z-50`  | dialogs (`<dialog>`), toasts         |

Anything claiming a fourth layer needs review.

### 3.11 Sizing units

- `rem` for vertical rhythm and font sizes.
- `ch` for max-width on prose blocks (`max-w-prose` = `65ch`).
- `px` only for hairlines (`border-1`) and shadow offsets.
- `%` for fluid widths inside grids and flex containers.

Users with a 24px default font still get a readable layout.

### 3.12 Focus and keyboard

- Every focusable element shows a `:focus-visible` ring tied to
  `var(--color-focus)`. **Never** `outline: none` without a
  replacement.
- Skip-link `.sn-skip-link` is required on every page; it links
  to `#main`.
- Tab order matches visual order. Don't use positive `tabindex`.
- Modal flows use `<dialog>.showModal()` so focus trapping is
  free.

### 3.13 Forms

- Every input has a `<label for>` (already required).
- Group related fields in `<fieldset><legend>…</legend>`.
- Error messages live in a sibling element with
  `aria-describedby="field-id-error"` on the input.
- Use native validation attributes (`required`, `minlength`,
  `pattern`) before adding JS. Style with `:invalid` /
  `:user-invalid` (the latter is what you usually actually want —
  only flags after the user has interacted).

### 3.14 Responsive strategy

- **Mobile-first.** Default styles target ≤ 640px.
- **Three breakpoints**, Tailwind defaults: `sm` 640, `md` 768,
  `lg` 1024. No bespoke breakpoints in v2.0.
- The dashboard sidebar collapses to a top-of-page `<details>`
  disclosure under `md`.
- Tables stay tables; on narrow screens, columns hide via
  `hidden md:table-cell` rather than reflowing into cards.
- Container queries (`@container`) are **not** used in v2.0; reach
  for them only when one component genuinely reflows
  independently of the page.

### 3.15 Motion

- Small, functional transitions only. No decorative animation.
- `prefers-reduced-motion: reduce` zeroes all transitions and
  animations (the one `!important` carve-out).
- No JS-driven animation in v2.0. CSS `transition` covers what we
  need; spring physics is a v3 problem.

### 3.15a Component states — handle all five, every time

Every interactive component (button, input, card-as-link, row,
pill that does anything on click) must declare **all five**
states explicitly, even if some are visually no-ops:

| State        | Selector                                  | What it signals                                      |
| ------------ | ----------------------------------------- | ---------------------------------------------------- |
| Default      | (base class)                              | resting appearance                                   |
| Hover        | `:hover`                                  | pointer is over and the action is available         |
| Focus        | `:focus-visible`                          | keyboard focus, ring tied to `var(--color-focus)`    |
| Disabled     | `:disabled`, `[aria-disabled="true"]`, `.is-disabled` | action unavailable; do not also remove from tab order without reason |
| Error / loading | `.has-error`, `.is-loading`            | server validation failed / async work in flight      |

Rules:

- **Disabled and loading are not the same.** Loading keeps the
  user's intent ("I clicked save, it's working"); disabled denies
  it ("can't click save, fix the form first"). Different visuals,
  different accessibility — `aria-busy="true"` for loading,
  `disabled` (or `aria-disabled`) for disabled.
- **Empty states get the same treatment as components.** A list
  with zero items renders an `<p>` or future `sn-empty-state`
  with copy that tells the user *what to do next*, not just
  "nothing here."
- **Loading states are present from the first render of an async
  surface.** A page that fetches data shows a skeleton or spinner
  *immediately*, not after a 300ms delay — the delay just hides
  the state from users on slow connections, who need it most.
- **Error states echo what the server said**, not a generic
  "something went wrong." The Pydantic validation message or
  the API error envelope's `detail` string is what the user
  sees.
- **Promotion threshold for state classes is one.** Unlike
  components (rule of three), state classes are reused
  immediately — `is-loading` on a button must mean the same
  thing as `is-loading` on a card.

The styleguide page is ship-blocking for state coverage: a
component without a hover, focus, disabled, error, **and**
loading example on `/styleguide` is incomplete.

### 3.16 Accessibility floor

- Heading levels are sequential (`<h1>` once per page, then
  `<h2>`s, no skipping to `<h4>`).
- Color contrast ≥ 4.5:1 for body text, 3:1 for large text and UI
  borders. Test in dev tools.
- Every image has `alt=""` (decorative) or meaningful alt text.
- Skip-link to `#main` as the first focusable element.
- All interactive elements reachable + operable with keyboard alone.
- Pills carry **icon + text + color** — never color alone (the
  color-blind / monochrome-print path must remain readable).

### 3.17 What v2.0 deliberately rejects

| Idea                                | Why                                                       |
| ----------------------------------- | --------------------------------------------------------- |
| Node.js + npm + PostCSS             | Adds a second toolchain ([ADR 058](../adr/058-tailwind-via-standalone-cli.md)). |
| BEM `__` / `--`, ITCSS, OOCSS       | The `sn-` prefix + utilities cover the same ground.       |
| CSS-in-JS                           | No JS framework in v2.0; runtime cost on every render.    |
| Web fonts                           | Zero FOIT, zero licensing surface in v2.0.                |
| `!important` outside reduced-motion | Cascade games are a leak indicator.                       |
| Inline `style="…"`                  | Defeats the cascade and the styleguide.                   |
| `@apply` outside `input.css`        | `@apply` is only legal inside `input.css`'s `@layer components`. |
| Icon fonts                          | Break for screen readers, miss in print. Use inline SVG with `<title>` or `aria-label`. |
| `<a href="#">` for buttons          | Use `<button type="button">`. Empty href clutters history and breaks middle-click. |
| `onclick=` attributes               | Use `addEventListener` in JS so logic stays in one place. |
| Bootstrap, Bulma, Pico, Materialize | One framework is enough; a second one needs an ADR.       |

---

## 4. The frontend section in `copilot-instructions.md`

The current Frontend section is short by design — the rule lives
there, the rationale lives here. If the rule needs to expand, the
shape stays:

> ### Frontend
>
> - Static HTML files served via `StaticFiles`; **no Jinja, no
>   bundler, no SPA framework**.
> - Vanilla JS + Fetch API for dynamic behavior.
> - **Semantic HTML.** Use the right tag for what an element *is*.
>   `<div>` is a generic block wrapper with no meaning — use only
>   when no better tag applies.
> - **Tags carry meaning, classes carry style.** Classes are
>   Tailwind utilities and the bespoke `sn-*` component vocabulary.
>   Never style by `id`. Only `data-state` / `data-theme` are
>   allowed style hooks; never invent ad-hoc `data-*` attributes.
> - Every input has a `<label for>`; buttons are `<button>`.
> - Tailwind via Standalone CLI ([ADR 058](../docs/adr/058-tailwind-via-standalone-cli.md)).
>   `app.css` is generated by `task build:css`; do not edit it.
> - Same-origin delivery; CSRF posture in
>   [`docs/project/spec/v2/security.md`](../docs/project/spec/v2/security.md).
> - See [`docs/notes/frontend-conventions.md`](../docs/notes/frontend-conventions.md)
>   for the long-form rationale, design tokens, the `sn-*`
>   vocabulary, and the accessibility checklist.

---

## 4a. Growth path — when v2.0's single file isn't enough

The v2.0 model deliberately keeps everything in one `input.css`.
That works while the surface is small. When it stops working —
more than ~12 bespoke components, repeated 10-class utility
strings, signature animations or layered effects, a designer
landing with a brand guideline — the next step is a multi-file
split:

```text
static/css/
├── input.css       # entry; @import the rest
├── tokens.css      # design tokens only
├── base.css        # element resets
├── layout.css      # page shells, grids, stacks
├── components.css  # the .sn-* vocabulary
└── effects.css     # transitions, animations, polish
```

That plan — including the proposed component vocabulary
(`sn-button`, `sn-card`, `sn-page-shell`, `sn-dashboard-grid`,
`sn-status-pill`, `sn-feedback-item`, `sn-modal`, `sn-form-field`,
`sn-empty-state`), the hard-parts defenses (naming, dedup,
specificity, organization, responsive consistency, hack
prevention, visual consistency, state handling), and explicit
trigger conditions — lives in
[`custom-css-architecture.md`](custom-css-architecture.md). It
is **not** the v2.0 plan; it's the parking lot for when v2.0
ships and we ask "what comes next?"

Until any two trigger conditions in that file are met, stay
with the v2.0 single-file model. Don't pre-split.

---

## 5. Custom CSS characteristics worth calling out

Things that make this design system *this* design system, beyond
"we use Tailwind":

1. **Single CSS source file.** `input.css` is the only file a
   human edits. No `components/`, no `layouts/`, no `themes/`
   directory. Everything is one file because the project is small
   enough that file-count discipline beats folder discipline.
2. **Tokens are CSS custom properties, not Tailwind palette
   entries.** Tailwind classes resolve through `var(--color-*)` —
   so a theme preset is one attribute swap, not a stylesheet swap.
3. **`sn-` prefix, single dashes.** No BEM noise, no clashes with
   Tailwind's own utility names.
4. **Three-template promotion rule.** The `sn-*` vocabulary stays
   small on purpose; nine components is the upper bound for v2.0.
5. **Theme presets override tokens, never selectors.** ADR 056's
   four presets each redefine the same `--color-*` names on
   `[data-theme="…"]`; nothing else changes. This is what makes
   `/styleguide` cheap.
6. **No CSS preprocessor.** Modern CSS — custom properties,
   nesting (Baseline 2024), logical properties, `:focus-visible`,
   `:user-invalid` — covers what Sass used to.
7. **Generated `app.css` is gitignored.** The container build
   regenerates it; missing locally → run `task build:css`.
8. **`task check` includes `task build:css`.** A missing class
   name in a template → Tailwind doesn't emit the rule → CI
   fails. The CSS pipeline is part of the test gate, not a
   separate concern.

---

## 6. Commercial-product features — the v2.0 plan

The earlier draft of this file outlined a "ship v1.0 first, then
layer v2 on top" plan. v2.0 is now **in flight** — multi-tenancy,
auth, public submission forms, public roadmap and changelog, and
insights are all in scope. The full feature catalog and ADR
backlog live in:

- [`../project/spec/v2/README.md`](../project/spec/v2/README.md)
- [`../project/spec/v2/business.md`](../project/spec/v2/business.md)
- [`../project/spec/v2/adrs.md`](../project/spec/v2/adrs.md)
- [`../project/implementation.md`](../project/implementation.md)

What's deliberately **out** of v2.0 (each one is a recorded
non-goal in [`business.md`](../project/spec/v2/business.md#what-v20-deliberately-does-not-sell)):

- AI / LLM auto-triage.
- Voting / upvotes.
- Real-time updates / WebSockets.
- Bulk actions.
- Slack / Discord webhooks.
- Public API tokens.
- File attachments.
- Mobile app.
- Plugin / extension API.
- Custom auth provider (we use library-grade Argon2id sessions —
  [ADR 059](../adr/059-auth-model.md)).

If a future change request lands one of those, it gets its own
ADR and its own spec addendum before any code.

---

## 7. Risks worth flagging up front

- **Auth changes the threat model entirely.** v2.0 already accepts
  this: see [`v2/auth.md`](../project/spec/v2/auth.md) and
  [`v2/security.md`](../project/spec/v2/security.md). The active
  defenses are Argon2id, SHA-256-hashed session tokens, per-IP and
  per-email rate limits, and identical 202 responses for
  enumeration-prone flows.
- **Multi-tenant retro-fit is expensive.** Every new tenant-scoped
  table carries `workspace_id uuid NOT NULL` from day one;
  [`v2/multi-tenancy.md`](../project/spec/v2/multi-tenancy.md)
  describes the canary test that fails the build on cross-tenant
  reads.
- **AI features need a kill switch.** Not in v2.0. If they ever
  ship, a budget cap and a feature flag must land in the same PR
  as the first call.
- **Feature creep silently breaks the spec.** Every new feature
  must update [`../project/spec/v2/`](../project/spec/v2/) or it's
  de-facto undocumented. The split-file v2 spec stays the
  canonical description of the system.
- **CSS pipeline drift.** `tailwind.config.cjs`, `input.css`,
  `v2/css.md`, and `v2/core-idea.md` must be kept in sync. CI
  catches missing classes via `task build:css`; cross-doc drift
  is caught only by review.

---

## 8. Where this lives

- `.github/copilot-instructions.md` — the **rules** (short,
  enforced).
- [`../project/spec/v2/css.md`](../project/spec/v2/css.md) — the
  **CSS implementation source of truth** (pipeline, `input.css`
  shape, `tailwind.config.cjs`, build tasks, component
  vocabulary).
- [`../project/spec/v2/core-idea.md`](../project/spec/v2/core-idea.md)
  — the **brand brief** (palette, locked strings, voice, status
  colors).
- This file — the **rationale**, naming conventions, the design
  system's custom characteristics, and the longer-form
  recommendations.
- [`custom-css-architecture.md`](custom-css-architecture.md) —
  the **future-direction sketch** for an expanded multi-file
  custom CSS system. Not yet a decision; read when planning
  beyond v2.0.

Update all four when a frontend convention changes. Update this
file alone when adding ideas that aren't yet rules.
