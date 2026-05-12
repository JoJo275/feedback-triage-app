# Theming & visual changes — practical guide

> **Scope:** how to change the look-and-feel of the v2 web app —
> colors, spacing, shadows, motion, layout, component styles, and
> decorative effects — **without** breaking the rules in
> [`css.md`](css.md). Read this when you want to touch CSS;
> read [`css.md`](css.md) when you want to know *why* the rules
> exist.

> **Audience:** anyone editing files under
> `src/feedback_triage/static/css/`,
> `src/feedback_triage/templates/`, or `tailwind.config.cjs`.

---

## TL;DR — where do I edit what?

| I want to change…                           | Edit                                                            | Charter from `css.md` |
| ------------------------------------------- | --------------------------------------------------------------- | --------------------- |
| Brand color, surface color, text color      | `static/css/tokens.css` — a `--color-*` custom property         | tokens                |
| Corner radius, shadow strength              | `static/css/tokens.css` — `--radius-*`, `--shadow-*`            | tokens                |
| Animation duration / easing                 | `static/css/tokens.css` — `--motion-*`, `--easing-*`            | tokens                |
| The look of an existing component (card, pill, button) | `static/css/components.css` — the `.sn-<name>` rule    | components            |
| Add a new component                         | `static/css/components.css` — see "promotion rule" below        | components            |
| Page-level structure (grids, gutters, stacks) | `static/css/layout.css` — `.sn-<layout-primitive>`            | layout                |
| Decorative-only flourish (gradient overlays, hover glows, parallax) | `static/css/effects.css` — opt-in `.sn-fx-*` class | effects |
| Base typography, focus ring defaults        | `static/css/base.css`                                           | base                  |
| Add a new theme preset                      | `static/css/tokens.css` — new `:root[data-theme="…"]` block     | tokens                |
| Tailwind tokens / breakpoints / fonts       | `tailwind.config.cjs`                                           | n/a (build config)    |

The single hard rule running through every row above:
**information lives in HTML, presentation lives in CSS.** Never style
by `id` or `data-*`; class is the only styling hook.

---

## The build pipeline

Tailwind Standalone CLI compiles `static/css/input.css` → `app.css`.
`input.css` is a stack of `@import` directives in this order:

```
tokens.css  →  base.css  →  layout.css  →  components.css  →  effects.css
```

The order matters — `tokens` must be first so every later file can
read `var(--color-*)`; `effects` must be last so a flourish can
override a component without specificity tricks.

`app.css` is **generated, not committed**. Don't hand-edit it.

```powershell
task watch:css      # rebuild on save while developing
task build:css      # one-shot build (CI parity)
```

---

## How to change a color

### Existing color

1. Open [`static/css/tokens.css`](../../../../src/feedback_triage/static/css/tokens.css).
2. Find the `--color-*` token. Comments cite the Tailwind shade so
   you can pick its neighbour without guessing hex.
3. Update the value in the `:root` block (light) **and** the
   `:root[data-theme="dark"]` block (dark) — the dark theme is not
   automatic, it's an explicit override.

```diff
 :root {
-    --color-primary: #0d9488; /* teal-600 */
+    --color-primary: #4f46e5; /* indigo-600 */
 }
 :root[data-theme="dark"] {
-    --color-primary: #2dd4bf; /* teal-400 */
+    --color-primary: #818cf8; /* indigo-400 */
 }
```

That's it — every `.sn-button-primary`, `.sn-pill-status--info`, and
focus ring already references the token, so no component file needs
to change.

### Brand-new color

1. Add the token to `tokens.css` (both themes).
2. If you need a Tailwind utility (`bg-accent`, `text-accent`, …),
   add it to `tailwind.config.cjs` under `theme.extend.colors` and
   wire it to the CSS variable so the token stays the source of
   truth:

```js
// tailwind.config.cjs
colors: {
  accent: 'rgb(var(--color-accent-rgb) / <alpha-value>)',
}
```

> **Why the indirection?** It keeps the theme switcher working —
> flipping `data-theme` only flips CSS variables; if you bake a hex
> into the Tailwind config, dark mode silently breaks.

---

## How to add a theme preset

ADR 056 lists four preset slots (`production`, `basic`, `unique`,
`crazy`). Each preset is one `:root[data-theme="<name>"]` block in
`tokens.css`. To add one:

1. Append a new block:

   ```css
   :root[data-theme="crazy"] {
       --color-bg: #18181b;
       --color-primary: #f97316;
       --radius-md: 1.5rem;
       --motion-base: 80ms;
       /* …override every token whose default doesn't fit. */
   }
   ```

2. Wire the picker. The theme switcher (sidebar dropdown, currently
   dormant per PR 1.9) writes the value to
   `document.documentElement.dataset.theme` and persists to
   `localStorage`. Adding a preset is data-only — no JS change.

3. Add a styleguide row in `pages/styleguide.html` so the team can
   eyeball the preset against the canonical components.

> **Theme presets are tokens-only.** A preset must not need a new
> selector or component override to look right. If it does, the
> component itself is wrong — fix the component to consume tokens.

---

## How to change a component's look

Every component lives once in `components.css` under a
`.sn-<component>` class. Edit there.

```diff
 .sn-card {
-    @apply bg-surface border border-line rounded-2xl shadow-sm p-4;
+    @apply bg-surface border border-line rounded-3xl shadow-md p-5;
 }
```

Rules:

- `@apply` is **only** legal in `components.css` and `layout.css`.
- Keep the selector flat. Specificity ceiling is **0,2,1** — one
  class + one state pseudo-class (`:hover`, `:focus-visible`,
  `[aria-expanded="true"]`) is the maximum.
- State variants use modifier classes (`.sn-card--ghost`) or
  state-class attributes (`.is-loading`), never inline styles or
  `style="…"`.
- Never use `!important` outside the `@media (prefers-reduced-motion)`
  block in `effects.css`.

---

## How to add a new component (promotion rule)

A pattern earns a `.sn-<name>` class once it appears in **three or
more templates**. Until then, leave it as ad-hoc Tailwind utilities
on the markup. Premature components rot fast.

1. Confirm the third use site exists (grep templates).
2. Add the class to `components.css`.
3. Replace the utility cluster in all three templates with the new
   class. Remove any one-off Tailwind utilities that the class
   subsumes.
4. Update the styleguide page so the component has a canonical
   reference render.

---

## How to add a decorative-only effect

Flourishes (background gradients, hover glows, sparkle animations)
go in `effects.css` as opt-in `.sn-fx-*` classes. They must:

- Be safe to remove without breaking layout or readability.
- Wrap any motion in `@media (prefers-reduced-motion: no-preference)`.
- Stay below the specificity ceiling (one class).

```css
@media (prefers-reduced-motion: no-preference) {
    .sn-fx-hover-lift {
        transition: transform var(--motion-fast) var(--easing-standard);
    }
    .sn-fx-hover-lift:hover {
        transform: translateY(-2px);
    }
}
```

Add the class to the markup where you want the flourish; never apply
it implicitly via descendant selectors.

---

## How to change layout / spacing

| Need                                    | Edit                                              |
| --------------------------------------- | ------------------------------------------------- |
| Page gutter width                       | `layout.css` — `.sn-content-gutter` `max-w-*`     |
| Vertical rhythm between sections        | `layout.css` — `.sn-stack` `gap`                  |
| Sidebar width                           | `layout.css` — `.sn-dashboard-grid` columns       |
| Form field spacing                      | `components.css` — `.sn-form-row` `gap`           |
| Card inner padding                      | `components.css` — `.sn-card` `p-*`               |

Layout primitives are structural only — **no decoration, no color**.
If you find yourself adding `bg-*` to `layout.css`, the rule belongs
in `components.css` instead.

---

## How to change motion

All transitions reference `--motion-*` and `--easing-standard` from
`tokens.css`. Tune motion globally by editing the tokens; tune one
component by referencing a different token, never by hand-coding a
duration.

```css
.sn-toast {
    transition: opacity var(--motion-fast) var(--easing-standard);
}
```

Reduced-motion is enforced at the `effects.css` level — don't
reinvent the wheel inside individual components.

---

## How to change typography or fonts

1. Font family lives in `tailwind.config.cjs` under
   `theme.extend.fontFamily`. Update the stack and rebuild.
2. Type scale tokens (if/when introduced — currently we lean on
   Tailwind's defaults) belong in `tokens.css` as `--font-*`.
3. Font-weight, letter-spacing, line-height defaults belong in
   `base.css` against element selectors (`body`, `h1`–`h6`).

Don't set `font-family` on individual components — base.css already
inherits to everything.

---

## How to add an icon to a pill / button

Per `css.md`, every pill carries **icon + text + color** so the
information channel doesn't depend on color alone.

1. Pick a glyph that renders reliably across platforms (Unicode
   geometric shapes are safer than emoji — `\u25b2` triangle,
   `\u2605` star).
2. In the partial (`_partials/status_pill.html`,
   `_partials/priority_pill.html`), add the icon to the lookup
   table next to the label and tone.
3. Render it as an inline `<span>` with `aria-hidden="true"` so
   screen readers hear the label only.
4. Style the icon with the existing `.sn-pill-icon` class — it
   handles fixed width and leading. No per-pill CSS needed.

```jinja
<span class="sn-pill-status sn-pill-status--{{ tone }}">
  <span class="sn-pill-icon" aria-hidden="true">{{ icon }}</span>
  {{ label }}
</span>
```

---

## Workflow recap

1. `task watch:css` — Tailwind rebuilds `app.css` on save.
2. Edit the right charter file (table at top of this doc).
3. Reload the styleguide page (or any page using the component) to
   eyeball.
4. Run `task lint:css` (when present) and the visual-regression
   smoke (PR 4.5+) before opening the PR.
5. `task build:css` once for the production-equivalent artifact CI
   will produce.

---

## Common mistakes the linters and reviewers will catch

| Symptom                                            | Likely cause                                                       |
| -------------------------------------------------- | ------------------------------------------------------------------ |
| `!important` review comment                        | Decoration leaking into a component or layout file                 |
| "Specificity > 0,2,1" reviewer flag                | Compound selectors (`.sn-card .sn-button`) — restructure the class |
| Dark mode looks broken after adding a color        | Forgot to override the token in `:root[data-theme="dark"]`         |
| Theme switcher does nothing for your new component | Component hard-codes a hex instead of `var(--color-*)`             |
| New component duplicates an existing one          | Promotion rule not followed — use the existing `.sn-<name>`       |
| `@apply` works in tokens or base                   | It doesn't — those charters forbid `@apply`. Move the rule.        |

---

## Cross-references

- [`css.md`](css.md) — the rules these recipes implement.
- [`information-architecture.md`](information-architecture.md) — page-level layouts and component
  inventory.
- [`copy-style-guide.md`](copy-style-guide.md) — for any visible
  string you add while restyling.
- [`implementation.md`](implementation.md) — PR 4.5 is the visual
  identity pass that will exercise this guide end-to-end.
- [`docs/notes/frontend-conventions.md`](../../../notes/frontend-conventions.md)
  — semantic-HTML rules that pair with the CSS charters.
