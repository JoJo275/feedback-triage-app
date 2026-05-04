# CSS, Web Page Design, and Custom Frameworks — A Field Guide

> **Audience:** me, learning. Treat this as a textbook chapter,
> not a spec. The repo's enforced rules live in
> [`frontend-conventions.md`](frontend-conventions.md) and
> [`../project/spec/v2/css.md`](../project/spec/v2/css.md);
> this file teaches the *underlying material* so those rules
> make sense and so future architecture decisions are informed.
>
> **Scope:** modern CSS as of 2025–2026, design systems,
> custom frameworks, components, accessibility, performance,
> tooling, and the trade-offs between them. Vendor-neutral
> where useful; project-specific call-outs are clearly labeled.

---

## Quick reference — the CSS facets, what each is, real-world examples

A glossary-style overview of every "kind of thing" the CSS world
contains. Read this first; the rest of the document drills into
each row. The **SignalNest v2.0** column shows what this project
actually picks for that facet — useful when you're trying to
locate "where does X live for us?".

| Facet | What it is | What it does | Real-world examples | SignalNest v2.0 |
| ----- | ---------- | ------------ | ------------------- | --------------- |
| **The language itself** | The CSS spec — selectors, properties, the cascade, inheritance, layout primitives | Tells the browser how to paint and lay out a tree of elements | CSS3, Selectors L4, CSS Color L4, Container Queries, `@layer`, `@scope`, `:has()` | Plain modern CSS, no preprocessor |
| **Selector** | A pattern that picks elements in the DOM | Targets *which* elements a rule applies to | `.sn-button`, `button[type="submit"]`, `:focus-visible`, `:has(> .sn-card-footer)`, `nav a:not(.is-current)` | Class-only, ceiling `0,2,1` (see [`v2/css.md`](../project/spec/v2/css.md)) |
| **Property** | A named CSS rule of the form `name: value` that applies *to* matched elements | Sets one specific aspect of how an element is painted or laid out | `color`, `padding`, `display`, `transform`, `transition`, `aspect-ratio`, `gap`, `z-index` | Used everywhere; we never invent properties — we only set the standard ones |
| **Property / value** | A single declaration: a property paired with a concrete value | The atomic unit of styling — what actually changes how an element looks | `color: #0a7`, `padding: 1rem`, `display: grid`, `transform: translateY(-2px)` | Standard properties + values; tokens used for the *value* side via `var(--…)` |
| **Custom property (CSS variable)** | An author-defined value stored in a `--name` slot, declared on a selector and read with `var(--name, fallback)` | Reuse a value across many rules; theme by overriding the slot in another scope; mutable at runtime via JS | `--color-bg: #fff;` on `:root`, `var(--radius-md)`, dark theme overrides via `[data-theme="dark"] { --color-bg: #111; }` | All design tokens defined in `tokens.css`; `[data-theme="…"]` swaps re-bind the same names |
| **Custom property vs. property** | They are not the same thing | A *property* is a built-in CSS keyword (`color`, `padding`); a *custom property* is a user-defined variable slot (`--color-bg`). The distinction matters because custom properties can be re-bound in nested scopes (`--color-bg` means one thing on `:root`, another on `[data-theme="dark"]`) — built-in properties cannot. | — | The rule of thumb: **components reference custom properties; tokens.css defines them; nothing else hard-codes raw values.** |
| **Design token** | A *named* primitive (color, radius, motion, z-layer) that downstream layers reference instead of raw values | Single source of truth for the design's values; switching themes only changes tokens | Material Tokens, Adobe Spectrum tokens, Tailwind theme keys, GitHub Primer Primitives | `tokens.css` — color, radius, shadow, motion, z-layer |
| **Design system** | Tokens + components + usage rules + docs, treated as a product | Lets a team build consistent UI across many pages | Material 3, Apple HIG, IBM Carbon, GitHub Primer, Atlassian Design System, Shopify Polaris | Custom in-house system, four-layer (tokens → base → layout → components → effects) |
| **Component library** | Pre-built UI atoms a design system ships | Gives you `<Button>`, `<Modal>`, `<Tabs>` ready-made | Radix UI, shadcn/ui, Headless UI, Material UI, Chakra UI, daisyUI | The `sn-*` vocabulary in `components.css` (button, card, pill, modal, etc.) |
| **CSS framework** | A pre-written stylesheet you load to get a baseline look | Saves writing CSS from scratch; opinionated visual identity | Bootstrap, Bulma, Pico, Foundation, Materialize, Spectre | None — explicitly forbidden without ADR |
| **Utility-first framework** | A framework whose "vocabulary" is single-purpose classes you compose in HTML | Skips naming things; lets layout emerge from class strings | Tailwind CSS, UnoCSS, Tachyons, WindiCSS | **Tailwind (Standalone CLI)** — no Node, no PostCSS plugins ([ADR 058](../adr/058-tailwind-via-standalone-cli.md)) |
| **Custom framework** | A framework you write yourself for one app or company | Fits the domain exactly; you own all the trade-offs | The `sn-*` system here; Stripe's internal CSS; any in-house "design language" | This project's `sn-*` layered files |
| **Component (in your codebase)** | One UI atom — a button, card, modal — defined once and reused | Encapsulates look + states + variants behind one name | `sn-button`, `sn-card`, `sn-pill-status`, `sn-modal`, `sn-empty-state` | Defined in `components.css`, demoed on `/styleguide` |
| **Layout primitive** | A reusable structural shape (page shell, grid, stack, cluster) | Owns *where* things go, not *how they look* | "Every Layout" patterns (Stack, Cluster, Sidebar, Switcher); Tailwind's grid utilities | `sn-page-shell`, `sn-dashboard-grid`, `sn-stack`, `sn-cluster`, `sn-grid-12` in `layout.css` |
| **Effect** | Decorative-only styling: transitions, animations, gradient surfaces, hover polish | Adds motion and depth without changing meaning | `transition: opacity .2s`, keyframe `fade-in`, `box-shadow`, gradient backgrounds | `effects.css` — removable for print or low-motion |
| **Reset / base layer** | Element-level rules that normalize browser defaults and set a11y floors | Makes `<button>`, `<input>`, headings start in a known state | `normalize.css`, `reset.css`, modern resets like Andy Bell's, Tailwind `@tailwind base` | `base.css` — `:focus-visible`, `prefers-reduced-motion`, body bg |
| **Architecture / methodology** | Rules for *how to organize* selectors and files | Stops a stylesheet from rotting into one giant mess | BEM, OOCSS, SMACSS, ITCSS, atomic CSS, utility-first, CUBE CSS | Custom four-layer (tokens → base → layout → components → effects) + utility-first composition |
| **Theme / theme preset** | A swap-in set of token values that retargets the look | Light/dark mode, brand variants, accessibility themes | `prefers-color-scheme`, `data-theme="dark"`, Stripe's "elements" appearance API | `[data-theme="dark"]` in `tokens.css`; four named presets planned ([ADR 056](../adr/056-style-guide-page.md)) |
| **CSS-in-JS** | Writing styles inside JavaScript files at build or runtime | Co-locates styles with components; scope by import | styled-components, Emotion, vanilla-extract, Stitches | None — forbidden in v2.0 |
| **Preprocessor** | A language compiled to CSS, with variables / nesting / mixins | Used to add features CSS lacked (now mostly built in) | Sass/SCSS, LESS, Stylus | None — forbidden in v2.0 |
| **Postprocessor** | A pipeline that transforms CSS after authoring | Auto-prefix, purge, minify, future-syntax polyfill | PostCSS, autoprefixer, cssnano, Lightning CSS | None as a separate step — Tailwind Standalone CLI handles it |
| **Build tool / pipeline** | The thing that turns source files into the `app.css` the browser loads | Bundling, tree-shaking, minification, dev watch | webpack, Vite, esbuild, Parcel, Rollup, Tailwind CLI, Hugo Pipes | **Tailwind Standalone CLI binary** → `static/css/app.css` |
| **Methodology for naming** | A convention for what to call your classes | Keeps class names predictable across a team | BEM (`block__element--modifier`), single-class (`.button-primary`), utility (`.flex`) | `sn-<component>-<variant>` (single dash, since `sn-` already namespaces) |
| **State class** | A class that toggles a runtime state on a component | Replaces JS-only style mutation with CSS that follows class changes | `.is-loading`, `.is-active`, `.has-error`, `aria-expanded="true"` | `.is-loading`, `.is-disabled`, `.has-error` on `sn-*` components |
| **Pseudo-class / pseudo-element** | A built-in selector that matches state or a virtual sub-element | Targets `:hover`, `:focus`, `::before`, `::backdrop` without extra markup | `:focus-visible`, `:has()`, `::placeholder`, `::backdrop`, `::marker` | Used freely; `:focus-visible` is mandatory |
| **Media / container query** | A rule wrapper that activates only when a viewport or container condition holds | Responsive design — adapt to screen *or* component context | `@media (min-width: 768px)`, `@container (inline-size > 40ch)` | Mobile-first; Tailwind `sm/md/lg`; `@custom-media` aliases in `tokens.css` |
| **Cascade layer (`@layer`)** | A named bucket that controls source-order independent of file order | Lets a framework's rules sit *below* yours by design, no specificity wars | `@layer reset, base, components, utilities;` | Implicit via Tailwind's `base/components/utilities` stages |
| **Scope (`@scope`)** | A new spec primitive that bounds a selector to a subtree | Like Shadow DOM-lite without web components | `@scope (.card) to (.card-footer) { ... }` | Not used yet; available for component isolation if needed |
| **Accessibility layer** | Rules that exist for assistive-tech users, not visual ones | Focus rings, reduced motion, prefers-contrast, sr-only utilities | `:focus-visible`, `prefers-reduced-motion`, `sr-only`, skip-links, color-contrast | Mandatory floor in `base.css` + skip-link `sn-skip-link` |
| **Tooling around CSS** | Linters, formatters, visual-regression, a11y, perf | Catches mistakes before review and after deploy | Stylelint, Prettier, Percy, Chromatic, axe-core, Lighthouse, BackstopJS | axe-core in CI ([`v2/risks.md`](../project/spec/v2/risks.md), `tests/e2e/`) |
| **Documentation surface** | Where the system is shown and explained | Onboarding, design review, regression catch | Storybook, Histoire, Pattern Lab, Zeroheight, in-house styleguide pages | `/styleguide` page ([ADR 056](../adr/056-style-guide-page.md)) — every component, every state |

### Yes — adding effects, themes, and components is meant to be cheap

The four-layer split is specifically designed so that the four
common asks are **one-file changes**:

| You want to … | Touch this file | Risk |
| ------------- | ---------------- | ---- |
| Add a hover polish, gradient, or animation | `effects.css` only | Low — file is removable |
| Swap or add a theme (e.g. high-contrast, sepia, brand variant) | `tokens.css` only — add a `[data-theme="…"]` block overriding the same custom-property names | Low — components reference tokens, not raw values |
| Add a new component (e.g. `sn-tag-chip`) | `components.css` + a row on `/styleguide` | Low — new vocabulary, no churn to existing components |
| Restyle every button | `components.css`'s `.sn-button-*` block | Medium — visual diff is everywhere |
| Add a new layout primitive | `layout.css` + a `/styleguide` example | Low |
| Add a new design token | `tokens.css` + `tailwind.config.cjs` + `/styleguide` + `core-idea.md` (one PR) | Medium — touches four files by design |
| Replace the entire framework (e.g. Tailwind → vanilla) | All of the above, plus an ADR | High — needs a new ADR |

The contract that makes this cheap is **layer discipline**:
components reference tokens, never raw values; effects are
decorative-only; tokens are the only place values exist. As long
as new code respects layer charters, themes and effects compose
without touching the rest of the system.

> Project rule, not a textbook claim: any new design token
> requires updating `tokens.css`, `tailwind.config.cjs`, the
> styleguide, and `core-idea.md` in one PR. See
> [`v2/css.md`](../project/spec/v2/css.md) §"Authoring rules".

### Custom variants — what each facet lets you customize

A second lens on the same facets, focused on the question "how do
I customize this without breaking everything else?". Each row
names the *customization handle* the facet exposes, and the
typical scope of a change.

| Facet | Customization handle | Typical scope of a change | Risk |
| ----- | -------------------- | -------------------------- | ---- |
| Property | None — properties are standard | n/a | n/a |
| Custom property (variable) | Define a new `--name` or override an existing one in a nested scope | One file (`tokens.css`); one or two-line edit | Low |
| Design token | Add or rename a token, or add a *token preset* (e.g. high-contrast palette) | `tokens.css` + `tailwind.config.cjs` + `/styleguide` row | Medium — touches multiple files by design |
| Design system | Add a new component, a new variant of an existing component, or a new theme | One PR: tokens, components, styleguide row, copy-style-guide entry if user-facing | Medium |
| Component | Add a *modifier* class (`sn-button-ghost`, `sn-pill-status-shipped`) | One block in `components.css` + styleguide example | Low — new vocabulary, no diff to existing |
| Component (variant) | Add an `is-*` / `has-*` state class | Same component file + JS that toggles the class | Low |
| CSS framework | Swap the framework | Touches every page; requires an ADR | High |
| Utility-first framework | Add a custom utility class (one we author) or a new color/spacing scale value | `tailwind.config.cjs` extends the theme; the new utility appears in IntelliSense | Low–Medium |
| Custom framework (this repo's `sn-*`) | Add a new file under `static/css/` (e.g. `print.css`); add a new layer in `app.css`'s import order | `app.css` + the new file; document in `v2/css.md` | Medium |
| Layout primitive | Add a new `sn-<primitive>` class | `layout.css` + styleguide example | Low |
| Effect | Add a new keyframe, transition, or hover polish | `effects.css` only — file is removable, so risk is bounded | Low |
| Reset / base | Add a new element-level rule (e.g. style every `<details>`) | `base.css`; **caution** — this affects every page | Medium |
| Architecture / methodology | Change how files are organized | An ADR — this is a structural change | High |
| Theme / theme preset | Add a `[data-theme="<name>"]` block in `tokens.css` overriding the same custom-property names | `tokens.css` only | Low |
| Build pipeline | Change how `app.css` is built (e.g. add PostCSS plugin) | An ADR (we currently use Tailwind Standalone CLI only) | High |
| Naming methodology | Rename existing classes (e.g. switch from `sn-` to BEM) | Touches every template and every CSS file; needs an ADR | High |
| State class | Add a new `is-*` / `has-*` flag | One component block + the JS that toggles it | Low |
| Pseudo-class / pseudo-element | Use a new pseudo (e.g. `:has()`) in an existing component | One selector edit | Low |
| Media / container query | Add a new breakpoint or container condition | Tailwind config + a comment on why; consistency matters | Medium |
| Cascade layer (`@layer`) | Reorder layers or add a new one | `app.css` (the import / layer order) | Medium — affects specificity globally |
| Scope (`@scope`) | Wrap a component in `@scope` to bound its rules | One component file | Low |
| Accessibility layer | Add a new floor rule (e.g. `prefers-reduced-data`) | `base.css` | Low–Medium |

The pattern: **the lower-risk facets are exactly where most
customization should happen.** "Add a new theme" should not be
risky, and it isn't, because it touches one file. "Replace the
framework" *is* risky, and it requires an ADR. The architecture
makes the cheap things easy and the expensive things explicit.

---

## Glossary — terms used across the web platform

A reference list, alphabetized, of jargon that this document
or any normal CSS / web-platform discussion will throw at you.
Definitions are short on purpose — long enough to ground the
term, short enough to skim.

### A

- **Accessibility tree** — the parallel representation of the
  DOM that assistive technologies (screen readers, switch
  control, voice control) actually consume. Built from semantic
  HTML + ARIA. A `<button>` shows up as a button; a
  `<div onclick>` shows up as a generic group.
- **Accent color** — a CSS property (`accent-color`) that lets
  you tint native form controls (checkboxes, radios, range
  sliders) without restyling them from scratch.
- **ARIA** — *Accessible Rich Internet Applications*. A set of
  HTML attributes (`role`, `aria-*`) that fill gaps where no
  native element conveys the right semantic. Rule: native
  element first, ARIA only when no native option exists.
- **Atomic / utility class** — a class that does one thing
  (`.flex`, `.mt-4`, `.text-center`). Composed in HTML to build
  components.
- **Author / user-agent / user origin** — three "origins"
  whose rules participate in the cascade. Author = your
  stylesheet; user-agent = browser defaults; user = OS-level
  user style overrides.

### B

- **BEM** — *Block, Element, Modifier*. A naming methodology:
  `.card`, `.card__title`, `.card--featured`.
- **BOM** (*Browser Object Model*) — informal name for browser-
  global APIs that aren't part of the DOM: `window`,
  `navigator`, `location`, `history`, `screen`. Where "is this
  Chrome?" lives.
- **Box model** — the rectangular layout model: every box has
  *content*, then *padding*, then *border*, then *margin*.
  `box-sizing: border-box` makes width/height include padding
  and border.
- **Breakpoint** — a viewport (or container) width at which
  layout rules switch. Tailwind defaults: `sm` 640, `md` 768,
  `lg` 1024, `xl` 1280.

### C

- **Cache-busting** — appending a hash or version to an asset
  URL (`app.7f3a2c.css`) so a new deploy gets a fresh URL,
  bypassing the browser cache safely.
- **Cascade** — the algorithm that picks which rule wins when
  multiple rules match the same element. Order: origin & importance
  → cascade layer → specificity → source order.
- **Cascade layer (`@layer`)** — a named bucket whose order is
  controlled by the `@layer name1, name2, …;` declaration,
  independent of source order or specificity within the layer.
- **Container query** — `@container (inline-size > 40ch) { … }`;
  a breakpoint based on a *parent container's* size, not the
  viewport. Makes truly self-contained components possible.
- **Critical CSS** — the small subset of CSS needed to render
  the above-the-fold content. Sometimes inlined in `<head>` for
  faster first paint.
- **CSP (Content Security Policy)** — an HTTP header that
  restricts what a page may load and execute. v2.0 ships with
  `script-src 'self'` only; no inline scripts.
- **Custom element / web component** — a user-defined HTML tag
  registered via `customElements.define('my-thing', …)`. The
  `<my-thing>` tag and its shadow DOM together form a web
  component.

### D

- **Declaration** — a single `property: value` pair inside a
  rule.
- **Design token** — a named primitive value (color, radius,
  spacing, motion). Decouples *what something looks like* from
  *what it's called*.
- **DOM** (*Document Object Model*) — the live, in-memory tree
  the browser builds from parsed HTML. JavaScript reads and
  mutates this tree; CSS selectors match against it.

### E

- **Effect** — decorative-only styling: hover polish,
  transitions, gradients, shadows. Removable without breaking
  function.
- **Event delegation** — attaching one listener on a parent
  element and inspecting `event.target` to handle clicks on
  many children. Saves listener count.

### F

- **Flexbox** — `display: flex`. One-dimensional layout (row
  or column) with growth, shrink, and gap.
- **FOUC** (*Flash of Unstyled Content*) — the brief moment
  before CSS loads where text renders in browser defaults.
  Mitigated by inlining critical CSS or making CSS load early.
- **FOIT / FOFT** (*Flash of Invisible / Fake Text*) — same
  phenomenon for web fonts. v2.0 avoids by using only system
  fonts.
- **Focus ring** — the visible outline that shows which element
  has keyboard focus. Use `:focus-visible` so it only appears
  for keyboard users, not mouse clicks.
- **`@font-face`** — declares a custom font for the page. v2.0
  doesn't use it.

### G

- **GPU compositing** — when the browser hands off a layer to
  the GPU for rendering. Triggered by certain properties
  (`transform`, `opacity`, `filter`). Animating these is cheap;
  animating layout-affecting properties (`width`, `top`) is not.
- **Grid** — `display: grid`. Two-dimensional layout with named
  rows and columns and a `gap`.

### H

- **Hash-suffixed asset** — see *cache-busting*.
- **HTTP cache** — `Cache-Control` + `ETag` headers tell the
  browser when to re-fetch vs. reuse. Aggressive on hashed
  static assets, conservative on HTML.

### I

- **Inheritance** — the rule that some properties (`color`,
  `font-family`) pass from parent to child by default; others
  (`padding`, `border`) do not.
- **Intrinsic sizing** — sizing keywords like `min-content`,
  `max-content`, `fit-content` that size to the content rather
  than to a fixed length.
- **`!important`** — flags a declaration to win the cascade
  step. Used sparingly; v2.0 only allows it inside the
  `prefers-reduced-motion` block.

### L

- **Layout primitive** — a reusable structural shape (Stack,
  Cluster, Sidebar, Switcher) that owns *where* things go.
- **Logical properties** — direction-agnostic versions of
  physical ones: `margin-inline-start` instead of `margin-left`.
  Free win for future RTL support.

### M

- **Media query** — `@media (min-width: 768px) { … }`. The
  oldest responsive primitive.
- **Mode** — a coarse theme switch (`light`, `dark`).
  Separate from finer-grained theme presets.

### N

- **Nesting (CSS)** — native CSS nesting, like preprocessors
  used to provide. `& > .child { … }` inside a parent rule.
  Modern browsers support it; we don't lean on it heavily.
- **Normalize / reset** — element-level CSS that smooths over
  browser default differences. Modern resets are short
  (a few dozen lines).

### P

- **Paint** — the step where the browser fills pixels into
  layers. Fast.
- **Pixel ratio (DPR)** — `window.devicePixelRatio`. 1 on
  typical desktop, 2 on Retina, 3 on some phones. Affects
  whether to ship `@2x` images.
- **Preset** — a named bundle of token values applied as a
  whole (e.g. `data-theme="bumblebee"` flips many tokens at
  once).
- **Pseudo-class** — `:hover`, `:focus`, `:checked`, `:has()`,
  `:not()`. Matches state, not new elements.
- **Pseudo-element** — `::before`, `::after`, `::backdrop`,
  `::placeholder`. Conjures a styleable virtual element.

### R

- **Reflow / layout** — the step where the browser computes
  geometry. Triggered by changes to size, position, content.
  Expensive.
- **Reduced motion** — `prefers-reduced-motion: reduce`. A
  user preference to disable non-essential animation. Honour it.
- **Rem / em** — relative font-size units. `1rem` = root font
  size (typically 16px); `1em` = parent's computed font size.
- **Render-blocking** — a resource (typically `<link rel="stylesheet">`
  in `<head>`) that prevents the browser from rendering until it
  loads. Stylesheets in `<head>` are render-blocking by design.
- **Render tree** — the merged DOM + CSSOM the browser actually
  paints. Hidden elements (`display: none`) are not in it.

### S

- **`@scope`** — bounds a selector to a subtree without web
  components. New, in modern browsers.
- **Selector** — the pattern that picks elements. Class,
  attribute, pseudo, descendant, etc.
- **Semantic HTML** — using the right tag for what an element
  *is* (`<button>` for actions, `<a>` for navigation, `<nav>`
  for nav landmarks). Drives accessibility, SEO, and reader-
  mode behaviour for free.
- **Shadow DOM** — a separate, encapsulated tree attached to a
  custom element. Its styles don't leak in or out. The basis
  of web components.
- **Shadow root** — the root node of a shadow DOM, attached
  to a host element via `host.attachShadow({mode: 'open'})`.
- **Source map** — a sidecar file (`app.css.map`) that maps
  built CSS back to its source. Dev only; not shipped to
  production by v2.0.
- **Specificity** — a 4-tuple `(inline, ID, class+pseudo,
  element)` that decides which selector wins when origin and
  layer are equal. Class-only selectors keep specificity flat.
- **`sr-only`** — a utility class that visually hides content
  while leaving it discoverable to screen readers. Used for
  things like icon-button labels.
- **Stacking context** — a sub-tree whose z-index space is
  isolated from siblings. Triggered by `position` + `z-index`,
  `opacity < 1`, `transform`, etc.

### T

- **Theme** — a coordinated set of token values. v2.0 ships
  `light`, `dark`, plus four ADR 056 presets.
- **Token** — see *design token*.
- **Typography scale** — a sequence of font sizes (e.g.
  12 / 14 / 16 / 20 / 24 / 32) used consistently across the UI.

### U

- **Utility class** — see *atomic class*.
- **Universal selector** — `*`. Matches every element. Useful
  in resets, expensive in deep trees if combined with attribute
  matchers.

### V

- **Variable (CSS)** — see *custom property*. They're the same
  thing under different names; the spec calls them *custom
  properties*, the community calls them *variables*.
- **Viewport** — the visible area of the page in the browser
  window. `100vw` = full viewport width.
- **Viewport unit** — `vw`, `vh`, `vi`, `vb`, `svh`, `lvh`,
  `dvh`. Sized to the viewport. Modern variants (`svh`, `dvh`)
  account for mobile address bars.

### W

- **Web component** — see *custom element*.

---

## Part 0 — How to read this file

Each part is independently useful. Skim for the heading you
need, or read end-to-end. Code snippets are illustrative; copy
into the project only after checking them against the
project's enforced conventions.

| Part | What it teaches |
| ---- | --------------- |
| 1 | What CSS actually does — the cascade, specificity, inheritance |
| 2 | Selectors — the full vocabulary, with what each is for |
| 3 | The box model, layout, and the modern primitives (flexbox, grid, container queries) |
| 4 | Typography, color, and the design-token model |
| 5 | Responsive design — breakpoints, fluid sizing, container queries |
| 6 | States, motion, and accessibility |
| 7 | Architecture — naming systems (BEM, OOCSS, ITCSS, SMACSS, utility-first) |
| 8 | Tools — preprocessors, postprocessors, frameworks, build pipelines |
| 9 | Custom design systems and component libraries |
| 10 | Performance, debugging, and observability |
| 11 | What's new in CSS (2024–2026) and what's coming |
| 12 | Decision frameworks — when to reach for which tool |
| 13 | Project-specific applications — how the above maps to v2.0 |

---

## Part 1 — What CSS actually does

CSS is a **constraint language for styling a tree of elements**.
You don't write "make this red"; you write rules that *match*
elements, and the browser resolves which rule wins for each
property on each element.

### 1.1 The cascade — the algorithm that decides

For every (element, property) pair, the browser picks a value
using this order, from most important to least:

1. **Origin and importance.** Author `!important` beats
   author normal beats user-agent (browser default). User
   styles sit between.
2. **Specificity.** A more specific selector wins.
3. **Source order.** Later rule wins ties.

That's the whole cascade. Everything else (inheritance,
layers, scopes) is layered on top.

### 1.2 Specificity — the count that decides ties

Specificity is a 4-tuple `(a, b, c, d)`, compared
left-to-right:

- `a` — inline `style="…"` attribute (1 if present)
- `b` — `#id` selectors
- `c` — `.class`, `[attr]`, `:pseudo-class` selectors
- `d` — element + `::pseudo-element` selectors

Examples:

| Selector                        | Specificity |
| ------------------------------- | ----------- |
| `*`                             | 0,0,0,0     |
| `button`                        | 0,0,0,1     |
| `.button`                       | 0,0,1,0     |
| `button.button`                 | 0,0,1,1     |
| `.button.is-loading`            | 0,0,2,0     |
| `header .button:hover`          | 0,0,2,1     |
| `#submit`                       | 0,1,0,0     |
| `#submit.button`                | 0,1,1,0     |
| `style="color: red"`            | 1,0,0,0     |
| (any selector with `!important`)| trumps everything except other `!important` |

**Practical rule:** keep selectors at `0,0,1,0` (single class)
or `0,0,2,0` (class + state class). Reaching `0,0,2,1`
(class + pseudo) is fine. Going higher is a smell — you're
fighting the cascade.

### 1.3 Inheritance

Some properties (color, font, line-height, visibility) inherit
to descendants by default; others (margin, padding, border,
display) do not. The keyword `inherit` forces inheritance,
`initial` resets to the spec default, `unset` is "inherit if
the property normally inherits, otherwise initial," `revert`
goes back to the user-agent / user value.

Inheritance is why setting `body { color: var(--color-text); }`
works without per-element rules. It's also why setting
`* { box-sizing: border-box; }` is the standard reset — `box-sizing`
doesn't inherit, so each element needs an explicit rule.

### 1.4 Cascade layers — `@layer`

`@layer` lets you group rules into named layers and order
them explicitly. Within a layer, normal cascade applies;
between layers, the *layer order* wins, regardless of
specificity.

```css
@layer reset, base, components, utilities;

@layer base {
  button { padding: 0.5rem 1rem; }      /* specificity 0,0,0,1 */
}

@layer components {
  .sn-button { padding: 0.75rem 1.5rem; } /* specificity 0,0,1,0 */
}
```

Even though `.sn-button` is more specific, if `components`
came before `base` in `@layer reset, base, components, utilities;`
the order would flip. Tailwind uses this internally
(`@tailwind base; @tailwind components; @tailwind utilities;`)
to guarantee utilities always win over components.

Unlayered styles win over layered styles. `!important` flips
the layer order (highest-priority layer wins for important
declarations). Both rules are weird; learn them once and
move on.

### 1.5 Scopes — `@scope`

`@scope` (Baseline 2024-ish, still gaining browser support)
lets you scope a block of rules to a subtree:

```css
@scope (.card) to (.card-content) {
  h2 { color: var(--color-primary); }
}
```

Use sparingly. Most projects don't need scopes; they need
better class names.

---

## Part 2 — Selectors, in depth

CSS has a rich selector vocabulary. Knowing the whole set
prevents reaching for JS when CSS already has the answer.

### 2.1 Basic

| Selector             | Matches                              |
| -------------------- | ------------------------------------ |
| `*`                  | every element                        |
| `tag`                | every `<tag>`                        |
| `.class`             | every element with that class        |
| `#id`                | the (one) element with that id       |
| `[attr]`             | every element with that attribute    |
| `[attr="value"]`     | exact-match attribute                |
| `[attr^="prefix"]`   | starts-with                          |
| `[attr$="suffix"]`   | ends-with                            |
| `[attr*="substr"]`   | contains substring                   |
| `[attr~="word"]`     | space-separated word match           |
| `[attr|="lang"]`     | hyphen-prefix match (`en`, `en-US`) |
| `[attr i]`           | case-insensitive (suffix on bracket) |

### 2.2 Combinators

| Combinator | Meaning                                       |
| ---------- | --------------------------------------------- |
| `A B`      | `B` descendant of `A` (any depth)             |
| `A > B`    | `B` direct child of `A`                       |
| `A + B`    | `B` immediately follows `A` (adjacent sibling)|
| `A ~ B`    | `B` follows `A` (general sibling, any gap)    |

### 2.3 Pseudo-classes — *state*

These match elements based on their state, not their content.
Knowing the full list prevents JS-driven style toggles.

| Pseudo-class                    | Matches                                 |
| ------------------------------- | --------------------------------------- |
| `:hover`                        | pointer is over                         |
| `:focus`                        | element has keyboard focus              |
| `:focus-visible`                | element has *keyboard* focus (not mouse)|
| `:focus-within`                 | element or any descendant is focused    |
| `:active`                       | being clicked / tapped                  |
| `:visited`                      | link previously visited                 |
| `:disabled` / `:enabled`        | form element disabled state             |
| `:checked`                      | checkbox / radio is checked             |
| `:indeterminate`                | checkbox in mixed state                 |
| `:required` / `:optional`       | form field requirement                  |
| `:valid` / `:invalid`           | passes / fails validation               |
| `:user-invalid` / `:user-valid` | the above, but only after user interacts (better UX) |
| `:placeholder-shown`            | input is showing placeholder            |
| `:read-only` / `:read-write`    | editable state                          |
| `:default`                      | default option in a `<select>`          |
| `:in-range` / `:out-of-range`   | number input bounds                     |
| `:empty`                        | element has no children                 |
| `:first-child` / `:last-child`  | first / last child of parent            |
| `:nth-child(n)`                 | nth child of parent                     |
| `:nth-of-type(n)`               | nth of same tag among siblings          |
| `:only-child` / `:only-of-type` | sole child / only of its tag            |
| `:not(selector)`                | negation                                |
| `:is(selector-list)`            | matches any in list, low specificity    |
| `:where(selector-list)`         | like `:is`, but **zero specificity**    |
| `:has(selector)`                | parent matching (Baseline 2024)         |
| `:target`                       | element is the URL fragment target      |
| `:lang(en)`                     | language match                          |
| `:dir(ltr)` / `:dir(rtl)`       | direction match                         |
| `:root`                         | document root (`<html>`)                |
| `:defined`                      | custom element is registered            |
| `:fullscreen`                   | element is in fullscreen                |
| `:popover-open`                 | popover element is showing              |
| `:modal`                        | element is acting as a modal            |
| `:has-slotted`                  | a slot is filled                        |

**`:has()` is a game-changer.** Before 2023, you couldn't
style a parent based on its children without JS. Now you can:

```css
.sn-card:has(.sn-button.is-loading) { opacity: 0.7; }
.sn-form-field:has(input:user-invalid) .sn-form-field-help { color: var(--color-danger); }
```

`:where()` is also more important than it looks. It accepts a
selector list but contributes **zero specificity**, which
makes it ideal for resets and base layers — you can target
many elements without raising the bar for everyone overriding
later.

### 2.4 Pseudo-elements — *part of an element*

Pseudo-elements use `::` (double colon). They let you style
parts of an element that aren't in the DOM.

| Pseudo-element         | What it is                              |
| ---------------------- | --------------------------------------- |
| `::before` / `::after` | generated content; needs `content:`     |
| `::first-line`         | first line of text                      |
| `::first-letter`       | first letter of text (drop-cap)         |
| `::placeholder`        | placeholder text in inputs              |
| `::selection`          | user's current selection                |
| `::marker`             | list-item bullet / number               |
| `::backdrop`           | the modal backdrop for `<dialog>` and fullscreen |
| `::file-selector-button` | the button inside `<input type="file">` |
| `::part(name)`         | a `part="name"` element inside a custom element / shadow root |
| `::slotted(selector)`  | nodes assigned to a `<slot>` |
| `::view-transition-*`  | the parts of a view transition (animations between page states) |

`::before` and `::after` are how you style decorative things
without polluting HTML — icons, tooltips, decorative shapes,
loading spinners.

### 2.5 Functional selectors and quantity queries

Combine the above and you can express things that used to
require JS:

```css
/* "if this list has more than 5 items, gray out the rest" */
li:nth-child(n+6) { opacity: 0.5; }

/* "if this form has any invalid field, disable the submit" */
form:has(:user-invalid) button[type="submit"] { @apply opacity-50 cursor-not-allowed; }

/* "if no items match, show the empty state" */
.sn-list:not(:has(.sn-list-item)) .sn-empty-state { display: flex; }
.sn-list:has(.sn-list-item)       .sn-empty-state { display: none; }
```

The lesson: before reaching for JS, ask "is there a selector
for this?"

---

## Part 3 — Box model, layout, and primitives

### 3.1 The box model

Every element is a box: `content` (inner) + `padding` +
`border` + `margin` (outer). `box-sizing: border-box` makes
`width` / `height` include padding and border, which is what
99% of layouts want. Modern reset:

```css
*, *::before, *::after { box-sizing: border-box; }
```

Tailwind's `preflight` does this for you.

### 3.2 Display models

The `display` property picks the *layout algorithm* the
element participates in (and the one its children use):

| `display`     | What it does                                   |
| ------------- | ---------------------------------------------- |
| `block`       | full-width box; stacks vertically              |
| `inline`      | flows in text; ignores width/height            |
| `inline-block`| inline placement, block-style sizing           |
| `flex`        | one-dimensional flexbox layout                 |
| `inline-flex` | flexbox in an inline-sized container           |
| `grid`        | two-dimensional grid layout                    |
| `inline-grid` | grid in an inline-sized container              |
| `contents`    | element disappears from the box tree (layout-wise) — useful for wrappers that should not break the parent's grid/flex |
| `flow-root`   | establishes a new block formatting context     |
| `none`        | element is removed from the layout entirely    |

`display: contents` is underused. It lets you wrap a group of
elements (e.g. for a JS hook) without that wrapper breaking
the parent's grid or flex layout.

### 3.3 Flexbox — one dimension at a time

Flexbox excels at distributing items along a single axis. The
mental model: a parent with `display: flex` aligns children on
the **main axis** (horizontal by default) and the **cross
axis** (perpendicular).

Key properties:

- **Parent:** `display: flex`, `flex-direction`,
  `flex-wrap`, `justify-content` (main axis),
  `align-items` (cross axis), `align-content`, `gap`.
- **Child:** `flex-grow`, `flex-shrink`, `flex-basis`
  (shorthand: `flex: 1 1 auto`), `align-self`, `order`.

Common patterns:

```css
/* Cluster — wrap, aligned, gapped */
.cluster { display: flex; flex-wrap: wrap; align-items: center; gap: 0.5rem; }

/* Stack — vertical, gapped */
.stack { display: flex; flex-direction: column; gap: 1rem; }

/* Sidebar shell that wraps under a width */
.with-sidebar { display: flex; flex-wrap: wrap; gap: 1rem; }
.with-sidebar > .sidebar { flex-basis: 16rem; flex-grow: 1; }
.with-sidebar > .main    { flex-basis: 0;     flex-grow: 999; min-inline-size: 50%; }
```

That last pattern — Heydon Pickering's "sidebar" — is a flex
layout that *flips* under a width threshold without a media
query.

### 3.4 Grid — two dimensions at once

CSS Grid handles real two-dimensional layouts. The mental
model: a parent defines tracks (rows and columns); children
are placed into them.

Key properties:

- **Parent:** `display: grid`, `grid-template-columns`,
  `grid-template-rows`, `grid-template-areas`, `gap`,
  `grid-auto-flow`, `grid-auto-columns`, `grid-auto-rows`,
  `justify-items`, `align-items`, `place-items`.
- **Child:** `grid-column`, `grid-row`, `grid-area`,
  `justify-self`, `align-self`, `place-self`.

The most powerful single line in CSS:

```css
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr)); gap: 1rem; }
```

That's a fully-responsive card grid with no media queries —
each card is at least 16rem wide, columns fill the available
space, items wrap when there isn't room.

`grid-template-areas` lets you sketch layouts in ASCII:

```css
.shell {
  display: grid;
  grid-template-columns: 16rem 1fr;
  grid-template-areas:
    "sidebar header"
    "sidebar main";
  min-height: 100vh;
}
.shell > .sidebar { grid-area: sidebar; }
.shell > .header  { grid-area: header; }
.shell > .main    { grid-area: main; }
```

For a multi-page app, **lean on grid for page shells and
flex for component-level alignment**. Mixing them is normal.

### 3.5 Subgrid

`grid-template-rows: subgrid` lets a child grid inherit its
parent's tracks. This is how you get aligned cards across
rows where each card has its own header / body / footer
heights but they line up:

```css
.cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }
.cards > .card {
  display: grid;
  grid-template-rows: subgrid;
  grid-row: span 3;  /* card spans 3 rows of the parent */
}
```

Baseline 2023; safe to use.

### 3.6 Container queries

Media queries are about the *viewport*. Container queries are
about the *containing element*. They let a component lay
itself out based on the space *it* has, not the page.

```css
.card-host { container-type: inline-size; container-name: card; }

@container card (min-width: 30rem) {
  .card { display: grid; grid-template-columns: 8rem 1fr; gap: 1rem; }
}
```

When to reach for container queries:

- A component appears in multiple layouts (sidebar vs. main)
  and should reflow independently of viewport width.
- A reusable widget gets dropped into a parent of unknown size.
- You're tempted to write `.in-sidebar .card { … }` — instead,
  use container queries.

When **not** to: page-level layout. The viewport is what the
page lives in; media queries are correct there.

### 3.7 Logical properties

`margin-inline-start` instead of `margin-left`,
`padding-block` instead of `padding-top` + `padding-bottom`.
These respect writing direction and orientation (Arabic, vertical
Japanese, etc.). Defaults you should adopt for new code:

| Old                | New                       |
| ------------------ | ------------------------- |
| `width`            | `inline-size`             |
| `height`           | `block-size`              |
| `min-width`        | `min-inline-size`         |
| `margin-left/right`| `margin-inline-start/end` |
| `padding-top/bot`  | `padding-block-start/end` |
| `text-align: left` | `text-align: start`       |

You don't have to switch all at once. But when adding new
layout code, prefer logical.

### 3.8 Positioning

`position: static` (default), `relative`, `absolute`,
`fixed`, `sticky`. `sticky` is the underused one — it pins
an element when it would scroll past a boundary, then
releases when the parent scrolls past:

```css
thead { position: sticky; top: 0; background: var(--color-bg); }
```

`position: absolute` always positions relative to the nearest
ancestor with `position: relative` (or any other non-static
position). Forgetting that is a top-3 CSS confusion.

### 3.9 Anchor positioning (newer)

`anchor-name` and `position-anchor` let you position one
element relative to another, anywhere in the DOM. Useful for
tooltips, popovers, dropdowns, without JS positioning code.
Browser support is still patchy in early 2026; reach for it
once it's Baseline.

---

## Part 4 — Typography, color, and tokens

### 4.1 Type scale

A **type scale** is a small set of font-sizes used everywhere.
Don't pick sizes ad hoc; pick a scale and stick with it.

A "perfect fourth" scale (×1.333):

| Step | Size       | Use                       |
| ---- | ---------- | ------------------------- |
| -2   | 0.75rem    | tiny labels               |
| -1   | 0.875rem   | meta / captions           |
|  0   | 1rem       | body                      |
|  1   | 1.333rem   | h4                        |
|  2   | 1.777rem   | h3                        |
|  3   | 2.369rem   | h2                        |
|  4   | 3.157rem   | h1                        |

Tailwind's defaults (`text-xs` → `text-9xl`) are a curated
scale; use those rather than inventing your own.

**Line height** scales inversely with font size: 1.5 for body,
1.2 for headings, 1.1 for very large display.

### 4.2 Fluid typography with `clamp()`

`clamp(min, preferred, max)` lets you scale text fluidly with
viewport without media queries:

```css
h1 { font-size: clamp(2rem, 4vw + 1rem, 3.5rem); }
```

That's "at least 2rem, scale with viewport, but never above
3.5rem." One line replaces three breakpoints.

### 4.3 Color spaces and tokens

Modern CSS supports multiple color spaces:

- `rgb()` / `rgba()` — sRGB, classic
- `hsl()` / `hsla()` — easier to manipulate hue/lightness
- `lch()` / `oklch()` — perceptually uniform; equal lightness
  values look equally bright across hues
- `hwb()` — hue, white, black; designer-friendly
- `color()` — explicit color space, e.g.
  `color(display-p3 0.3 0.7 0.5)` for wide-gamut

`oklch()` is the future-leaning choice for design systems
because lightness behaves predictably:

```css
:root {
  --brand-50:  oklch(97% 0.02 180);
  --brand-500: oklch(60% 0.15 180);
  --brand-900: oklch(20% 0.06 180);
}
```

Same hue, lightness as a percentage. Pretty trivial to
generate a 10-step palette.

### 4.4 The design-token model

A **design token** is a named primitive value:
`--color-primary: #0d9488`. The token has *intent*, not
appearance. UI components reference tokens, never raw values:

```css
/* WRONG */
.sn-button-primary { background: #0d9488; }

/* RIGHT */
.sn-button-primary { background: var(--color-primary); }
```

Why: theme switches (light/dark/preset) override the token.
The button doesn't change.

Tokens should describe **purpose**, not value. `--color-bg-card`
beats `--color-white-1`. When the brand changes, the value
changes; the name shouldn't have to.

**Layered tokens** are even better: primitive → semantic → component.

```css
:root {
  /* 1. Primitive — raw color values */
  --gray-100: #f1f5f9;
  --teal-600: #0d9488;

  /* 2. Semantic — what it means in UI */
  --color-bg: var(--gray-100);
  --color-primary: var(--teal-600);

  /* 3. Component — what it's for (often optional for small systems) */
  --button-primary-bg: var(--color-primary);
}
```

Three layers is overkill for v2.0; two (primitive +
semantic) is what most projects need.

### 4.5 Spacing scale

Same idea as type — pick a small set, use everywhere. A
common scale is 4px-based: `0`, `0.25rem`, `0.5rem`,
`0.75rem`, `1rem`, `1.5rem`, `2rem`, `3rem`, `4rem`. Tailwind
provides this via `p-1` / `m-2` / `gap-4` etc.

Adopting a scale eliminates the "is this 14px or 16px?" decision
on every component.

### 4.6 Fonts and font-loading

- **System font stack** (no web font): instant, no FOIT, zero
  licensing. Use this until you have a reason not to.

  ```css
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
    Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif;
  ```

- **Web fonts:** preload and use `font-display: swap` so text
  is readable while fonts load.

  ```css
  @font-face {
    font-family: "Inter";
    src: url("/fonts/inter-var.woff2") format("woff2-variations");
    font-display: swap;
  }
  ```

- **Variable fonts** are one file, every weight/width. Smaller
  total payload than four static weights.

- **Local fonts only** for production: `font-family: Inter, …;`
  with a `@font-face` from your own server. Don't load from
  Google Fonts in production — privacy + extra round trip.

---

## Part 5 — Responsive design

### 5.1 Mobile-first

Default styles target the smallest screen. Add `@media (min-width: …)`
to scale up. The reverse (`max-width`) works but tends to grow
exception-heavy.

```css
.shell { display: block; padding: 1rem; }

@media (min-width: 48rem) {
  .shell { display: grid; grid-template-columns: 16rem 1fr; padding: 2rem; }
}
```

### 5.2 Breakpoints

Pick ≤ 4 named breakpoints; use them everywhere. Tailwind's
defaults are reasonable:

| Token | Min-width    |
| ----- | ------------ |
| `sm`  | 40rem (640px)|
| `md`  | 48rem (768px)|
| `lg`  | 64rem (1024px)|
| `xl`  | 80rem (1280px)|
| `2xl` | 96rem (1536px)|

For a v2.0-shaped app, three (`sm`, `md`, `lg`) is enough.

### 5.3 Fluid sizing

Fluid sizing reduces the number of breakpoints you need.
Instead of "switch from 14px to 16px at 48rem," you write:

```css
font-size: clamp(0.875rem, 0.5vw + 0.75rem, 1rem);
```

Same for spacing:

```css
padding-block: clamp(1rem, 2vw + 0.5rem, 2rem);
```

### 5.4 Container queries vs media queries

| Use case                            | Use                |
| ----------------------------------- | ------------------ |
| "When the viewport is wide enough"  | media query        |
| "When this card has enough room"    | container query    |
| Top-level page shell                | media query        |
| Reusable widget in unknown context  | container query    |

### 5.5 Mobile UX considerations beyond CSS

- Tap targets ≥ 44×44px (iOS) / 48×48px (Android).
- Form inputs should have correct `inputmode` and `autocomplete`.
- `<input type="number">` is often the *wrong* choice; use
  `<input type="text" inputmode="numeric" pattern="[0-9]*">`
  for non-decremented numeric input.
- `viewport` meta: `<meta name="viewport" content="width=device-width, initial-scale=1">`.

---

## Part 6 — States, motion, and accessibility

### 6.1 Component states

Every interactive component has at least these:

| State    | Selector                                  | Notes                            |
| -------- | ----------------------------------------- | -------------------------------- |
| default  | (base)                                    | rest                             |
| hover    | `:hover`                                  | pointer is over                  |
| focus    | `:focus-visible`                          | keyboard focus only              |
| active   | `:active`                                 | being pressed                    |
| disabled | `:disabled` / `.is-disabled`              | cannot be interacted with        |
| loading  | `.is-loading` + `aria-busy="true"`        | async work in flight             |
| error    | `.has-error` / `:user-invalid`            | validation failed                |
| selected | `[aria-selected="true"]` / `.is-active`   | currently chosen                 |
| empty    | `:empty` or container-level `.is-empty`   | nothing to show                  |

**Loading and disabled are different.** Loading keeps intent
("you clicked submit, working on it"); disabled denies it
("can't click submit until you fix the form").

### 6.2 Transitions and animations

Two CSS primitives:

- **Transitions** animate property changes between states.

  ```css
  .sn-button { transition: background-color 120ms cubic-bezier(0.2, 0, 0, 1); }
  ```

- **Animations** play a `@keyframes` rule, optionally on loop.

  ```css
  @keyframes spin { to { transform: rotate(360deg); } }
  .sn-spinner { animation: spin 1s linear infinite; }
  ```

Rules:

- Animate **transform** and **opacity** for performance.
  These are GPU-composited; everything else can trigger
  layout/paint.
- Keep durations small for UI: 100–300ms. Anything longer
  feels slow.
- Use **easing**: `cubic-bezier(0.2, 0, 0, 1)` (Material
  "standard") is a safe default. `linear` only for spinners
  and progress bars.

### 6.3 `prefers-reduced-motion`

Respect users who've turned off motion at the OS level:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

This is the one place `!important` is correct — you're
overriding everything else for accessibility.

### 6.4 Focus management

- **Always** show a visible focus indicator. `outline: none`
  without a replacement is a WCAG failure.
- Use `:focus-visible` so mouse clicks don't show the ring,
  but keyboard navigation does.
- Focus order = tab order = visual order. Don't fight this
  with positive `tabindex` values.
- Modals trap focus. `<dialog>.showModal()` does this for
  free.

### 6.5 ARIA — what to use, what to avoid

The first rule of ARIA: **don't use ARIA**. Use the right
HTML element. `<button>`, not `<div role="button">`.

When ARIA *is* needed:

- `aria-label` / `aria-labelledby` — accessible name when
  visible text isn't enough.
- `aria-describedby` — additional descriptive text (form
  field hints, error messages).
- `aria-busy="true"` / `aria-live="polite"` — async loading,
  status updates.
- `aria-expanded`, `aria-controls`, `aria-haspopup` —
  disclosure widgets and menus.
- `aria-hidden="true"` — purely decorative content (icons
  with redundant labels next to them).

Things to avoid:

- `role="button"` on a `<div>`. Use `<button>`.
- `aria-label` on something that has a visible label that
  also describes it. They have to match, and they will drift.
- `tabindex="0"` to make a `<div>` focusable. Use a real
  control.

### 6.6 Color contrast

WCAG AA requires:

- **4.5:1** for body text.
- **3:1** for large text (≥ 18pt or ≥ 14pt bold) and UI
  components / graphical elements.

Test with browser dev tools; every modern browser has a
contrast checker. A pretty palette that fails contrast is
not acceptable.

### 6.7 Keyboard, screen reader, voice

The accessibility floor is **everything works without a
mouse**. Tab through the page; you should be able to do every
action. Read the page with VoiceOver / NVDA; landmarks
should make sense, the heading outline should be coherent.

---

## Part 7 — CSS architecture systems

This is where projects pick a **methodology**. None is
correct in the absolute; each addresses a different scaling
problem.

### 7.1 BEM — Block, Element, Modifier

```css
.card { … }                      /* block */
.card__title { … }               /* element of card */
.card__title--large { … }        /* modifier of element */
.card--featured { … }            /* modifier of block */
.card--featured .card__title { … } /* descendant inside modifier */
```

**Strengths:** flat specificity, no leakage, names tell you
relationships.
**Weaknesses:** verbose, ugly, double-underscore noise.
Awkward for utility composition.

### 7.2 OOCSS — Object-Oriented CSS

Separate **structure** from **skin**. A `.card` defines layout
(padding, border, radius); a `.theme-light` or `.theme-warning`
defines color. Compose by stacking classes:
`<div class="card theme-light">`. Sometimes called
"single-purpose classes."

**Strengths:** reusable. Predates utility-first by a decade.
**Weaknesses:** name explosion. Without discipline, you end
up with `.card`, `.card-large`, `.card-padded`, `.card-blue`,
all subtly different.

### 7.3 SMACSS — Scalable, Modular Architecture for CSS

Categorizes rules into Base, Layout, Module, State, Theme.
File structure mirrors the categories.

**Strengths:** good mental model for medium projects.
**Weaknesses:** prescriptive folder structure; the categories
overlap.

### 7.4 ITCSS — Inverted Triangle CSS

Orders CSS by reach, from broad to narrow:

1. Settings — variables, tokens
2. Tools — mixins, functions
3. Generic — resets, normalize
4. Elements — bare HTML elements
5. Objects — layout primitives (cosmetic-free)
6. Components — UI components
7. Utilities — single-purpose classes

Each layer's specificity is higher than the previous. With
`@layer`, you can enforce this with one declaration:
`@layer settings, tools, generic, elements, objects, components, utilities;`.

**Strengths:** predictable specificity. Maps cleanly to
modern `@layer`.
**Weaknesses:** more files than small projects need.

### 7.5 OOCSS + BEM (the hybrid)

What most teams actually do. Block-Element-Modifier names
plus a few "object" classes for layout. Pragmatic, common.

### 7.6 Atomic / utility-first (Tailwind, Tachyons)

Single-purpose classes; build UI by composition at the call
site. `<div class="flex items-center gap-4 p-4 rounded-2xl bg-white shadow-sm">`.

**Strengths:** no naming, small CSS bundle (only used classes
are emitted), instant composability, consistent design via
token-mapped scales.
**Weaknesses:** verbose markup, learning curve, hard to read
at first, need a build step.

The "rule of three" promotion pattern (utility-first until
something repeats, then promote to a class) is what makes
utility-first scalable for medium-sized projects. Without
that promotion discipline, templates become unreadable.

### 7.7 CSS Modules / scoped styles

A build-time tool gives every class a unique hash:
`.card__abc123`. Imports return a class-name map. Used
heavily in React / Vue / Svelte.

**Strengths:** zero leakage, component-scoped.
**Weaknesses:** requires a JS build step; not relevant for
this project.

### 7.8 CSS-in-JS (emotion, styled-components, vanilla-extract)

Styles colocated in JS files, often as tagged template
literals or object syntax. Shipped as runtime CSS or compiled
to static CSS at build time.

**Strengths:** strong colocation, theming primitives.
**Weaknesses:** runtime cost (for runtime variants),
toolchain weight, redundant if you have utility-first or CSS
modules.

### 7.9 Design tokens (Style Dictionary, Theo)

A toolchain that emits the *same* token set as CSS,
JavaScript, iOS, Android, etc. Useful when the design system
spans platforms. Overkill for a web-only project.

---

## Part 8 — Tools

### 8.1 Preprocessors — Sass, Less, Stylus

Adds variables (predates CSS custom properties), nesting
(now native CSS), mixins, functions, partials, math.

```scss
$brand: #0d9488;

.button {
  background: $brand;
  &:hover { background: darken($brand, 10%); }
}
```

**Used to be essential.** Now native CSS covers almost all of
it. Reach for Sass only when you need build-time logic that
CSS can't do (e.g. generating dozens of color stops from a
loop).

### 8.2 Postprocessors — PostCSS

A build step that transforms CSS via plugins: autoprefixer,
nesting (before native), `@import` inlining, custom syntax,
minification.

Tailwind itself is a PostCSS plugin (via the standard CLI) or
a standalone Go-based tool (the Standalone CLI). The
Standalone CLI is what this project uses, per ADR 058 — it
removes the Node toolchain entirely.

### 8.3 Frameworks — what each is for

| Framework      | Style                | Strengths                                | Weaknesses                              |
| -------------- | -------------------- | ---------------------------------------- | --------------------------------------- |
| Bootstrap      | component-first      | "free" UI, big team familiarity          | dated look; class soup; jQuery legacy  |
| Bulma          | component-first      | Sass-friendly; clean API                 | smaller ecosystem                       |
| Foundation     | component-first      | accessibility-conscious                  | dated; less momentum                    |
| Tailwind CSS   | utility-first        | composable; small bundle; great defaults | initial verbosity; learning curve       |
| Pico CSS       | classless / minimal  | drop-in beautiful HTML                   | not for custom designs                  |
| Open Props     | tokens only          | ready-made design tokens                 | no components                           |
| Skeleton       | minimal              | lightweight                              | dated                                   |
| Materialize    | Material Design      | known design language                    | opinionated; heavy                      |
| Tachyons       | utility-first        | predates Tailwind; tiny                  | smaller ecosystem                       |
| UnoCSS         | utility-first        | fast; preset-based                       | fewer integrations                      |
| Shoelace       | web components       | framework-agnostic UI components         | requires JS                             |
| daisyUI        | Tailwind components  | adds component classes on Tailwind       | adds another vocabulary                 |

### 8.4 Linters and formatters

- **stylelint** — CSS linter; catches unknown properties,
  duplicate selectors, BEM violations, etc.
- **Prettier** — formats CSS / SCSS. Opinionated, fast.
- **ruff** — formats Python only; doesn't touch CSS.
- **CSStree validator** — strict CSS validation.

For the v2.0 stack: not using Prettier/stylelint yet; relies
on Tailwind and Tailwind's own warnings. Adding stylelint to
catch dedup / specificity violations is on the table once
the bespoke layer grows.

### 8.5 Build pipelines

- **Tailwind Standalone CLI** — single Go binary; reads
  `input.css` + config, emits `app.css`. No Node. The
  v2.0 choice.
- **Tailwind via npm / PostCSS** — Node toolchain, more
  flexibility (other PostCSS plugins).
- **Vite / esbuild / Rollup** — bundlers that include CSS
  pipelines. Useful for SPA codebases.
- **Hand-rolled** — concatenate `.css` files, minify with
  `cssnano`, ship. Works for small projects.

### 8.6 Browser dev tools

The Chrome / Firefox dev tools are the most important CSS
tool. Practice with:

- **Computed pane** — what value won, and why.
- **Layout inspector** — flex / grid / multicol overlays.
- **Animations panel** — pause, slow down, edit keyframes.
- **Accessibility tree** — what screen readers see.
- **Coverage** — which CSS rules are unused on this page.
- **Color picker** — built-in contrast checker.

---

## Part 9 — Custom design systems and component libraries

### 9.1 What a design system is

Three layers:

1. **Tokens** — primitives (color, spacing, type).
2. **Components** — reusable UI elements with documented
   states, variants, and a11y guarantees.
3. **Patterns** — combinations of components for common
   tasks (forms, dashboards, landing pages).

Add **content guidelines** (voice, microcopy) and you have
the full picture.

### 9.2 Building one yourself

A minimum viable design system:

1. Pick a **type scale** (e.g. Tailwind's defaults).
2. Pick a **spacing scale** (e.g. 4px-based).
3. Pick a **color palette** with semantic names (`bg`,
   `surface`, `ink`, `brand`, `warn`, `danger`, `line`,
   `focus`).
4. Define a **radius scale** (small / medium / large).
5. Define a **shadow scale** (small / medium).
6. Define a **motion scale** (fast / base / slow + easing).
7. Build a **components.css** with the canonical class list.
8. Build a **styleguide page** rendering every component in
   every state.

Steps 1–6 are tokens; steps 7–8 are the system. v2.0 has all
eight in flight.

### 9.3 Component libraries — buy vs. build

**Buy** when:

- The app is primarily forms + tables + dashboards.
- Your team has no designer.
- Time-to-market dominates over visual identity.

**Build** when:

- Visual identity is a differentiator.
- You have at least one designer or strong opinion-holder.
- The app has marketing surfaces, public roadmap, or
  customer-facing pages where polish matters.

**Hybrid** is common: buy the boring parts (date pickers,
combo boxes), build the brand-driven parts (cards, buttons,
empty states, page shells).

### 9.4 Reusable component anatomy

A reusable component, in any system, declares:

- **Public API** — what props / slots / classes does it
  accept?
- **Variants** — primary / secondary / etc.
- **States** — default, hover, focus, disabled, loading, error.
- **Sizes** — small / medium / large (if applicable).
- **Slots / parts** — header, body, footer (named places to
  put content).
- **A11y guarantees** — focus management, ARIA, keyboard
  shortcuts.
- **Documentation** — what it's for, what it's not for, when
  *not* to use it.

For pure-CSS components (no JS framework), the "API" is the
class names. For web components, it's slots + attributes +
custom events.

### 9.5 Composition over configuration

A component with 30 props is a sign you should split it. Two
patterns to lean on:

- **Compound components** — `Card`, `CardHeader`, `CardBody`,
  `CardFooter`. The parent wires accessibility; the children
  are slots.
- **Slots** — name the holes, let consumers fill them.
  Native: `<slot>` in web components, `<template>` in web
  components, named slots in Vue / Svelte.

For pure-CSS-class components: parts are named via
`<class>-<part>`. `sn-card`, `sn-card-header`, `sn-card-body`,
`sn-card-footer`. Consumers compose:

```html
<article class="sn-card">
  <header class="sn-card-header">…</header>
  <div class="sn-card-body">…</div>
  <footer class="sn-card-footer">…</footer>
</article>
```

### 9.6 Documenting components — the styleguide

Every component appears on `/styleguide` with:

- Default rendering.
- Each variant.
- Each state (hover via `:hover` simulator; focus, disabled,
  loading, error, empty).
- Code snippet showing the markup.
- Notes on when to use / not use.

The styleguide is **load-bearing**. Without it, components
drift; with it, the truth is testable.

---

## Part 10 — Performance, debugging, observability

### 10.1 What's expensive

The browser pipeline: **parse → style → layout → paint →
composite**. Properties that affect later steps are more
expensive:

- **Composite-only** (cheap): `transform`, `opacity`,
  `filter`, `backdrop-filter`. GPU-accelerated.
- **Paint** (medium): `color`, `background`, `border-color`,
  `box-shadow`. Re-rasterize affected pixels.
- **Layout** (expensive): `width`, `height`, `top`, `left`,
  `padding`, `margin`, `font-size`. Re-flow the page.

Animate transform + opacity. Avoid animating width/height/top.

### 10.2 Bundle size

CSS is tiny compared to JS, but Tailwind + Bootstrap full
builds are 200kB+. Build tools strip unused classes:

- Tailwind: `content` glob; only emits used classes.
- PurgeCSS: same, for hand-rolled CSS.
- Coverage tab in dev tools: which rules are unused on this
  page.

A 50kB CSS bundle is comfortable. 100kB is a smell. 500kB is
broken.

### 10.3 Critical CSS

Inline the CSS needed to render the above-the-fold content;
load the rest asynchronously. Reduces first-paint time on
slow networks.

For a v2.0-shaped app on Railway with a fast origin,
critical CSS is overkill — one CSS file, one round trip,
done.

### 10.4 Debugging the cascade

When a rule "isn't working," in order:

1. **Inspect element → Computed.** What value won? What
   selector won?
2. Specificity issue? Check the Styles pane; struck-through
   declarations show the rules that lost.
3. Cascade-layer issue? Check `@layer` rules in dev tools.
4. Inheritance issue? Some properties don't inherit
   (`background`, `border`). Some do (`color`, `font`).
5. `display: none` / `visibility: hidden` / `opacity: 0` —
   element is in the tree but invisible.

The most common bug: inline styles overriding everything
because something set `style="…"` from JS. Search the
codebase for `.style.` and `setAttribute('style'`.

### 10.5 Visual regression

A real test for design systems: render every component on
`/styleguide`, take a screenshot, diff against a stored
golden image. Playwright + `expect(page).toHaveScreenshot()`
is enough for a small project.

---

## Part 11 — What's new in CSS (2024–2026)

A non-exhaustive list of things that recently became Baseline
or are about to:

| Feature                     | Status                | What it does                                      |
| --------------------------- | --------------------- | ------------------------------------------------- |
| `:has()`                    | Baseline 2024         | parent / sibling selection                        |
| `@container`                | Baseline 2023         | container queries                                 |
| `@layer`                    | Baseline 2022         | named cascade layers                              |
| `:where()` / `:is()`        | Baseline 2022         | low-specificity grouping                          |
| `subgrid`                   | Baseline 2023         | child grid inherits parent's tracks               |
| Logical properties          | Baseline 2022         | `inline-size`, `block-size`, etc.                 |
| `aspect-ratio`              | Baseline 2022         | enforce a width:height ratio                      |
| `accent-color`              | Baseline 2022         | recolor checkboxes / radios / range with one prop |
| `color-mix()`               | Baseline 2024         | mix two colors at a percentage                    |
| `oklch()` / `oklab()`       | Baseline 2023         | perceptually uniform color spaces                 |
| Native CSS nesting          | Baseline 2023         | nest selectors without preprocessor               |
| `@scope`                    | mixed (2024–)         | scope rules to a subtree                          |
| View transitions            | partial               | smooth animations between page states             |
| Anchor positioning          | partial               | position elements relative to others              |
| `text-wrap: balance`        | Baseline 2024         | balanced line wrapping for headings               |
| `text-wrap: pretty`         | mixed                 | improved orphan handling                          |
| Container-style queries     | partial               | `@container style(--theme: dark)` and similar     |
| `@starting-style`           | Baseline 2024         | initial-state styles for transitions on insert    |
| `field-sizing: content`     | partial               | inputs auto-size to content                       |
| `interpolate-size`          | partial               | `height: auto` transitions                        |
| Popover API + `[popover]`   | Baseline 2024         | native lightweight overlays                       |

Adopt new features when they're Baseline; experimental ones
are fine for prototypes but risky for production.

### 11.1 `@starting-style` and `interpolate-size`

These two together solve the long-standing "can't transition
to `height: auto`" problem:

```css
.card {
  height: auto;
  transition: height 200ms;
  interpolate-size: allow-keywords;
}

.card.is-collapsed {
  height: 0;
  overflow: hidden;
}
```

### 11.2 View transitions

Animate between page states with one declaration:

```css
::view-transition-old(root),
::view-transition-new(root) {
  animation-duration: 200ms;
}
```

```js
document.startViewTransition(() => updateDOM());
```

Useful for SPA-feeling transitions on traditional MPA apps.

### 11.3 `color-mix()`

```css
.sn-button-primary { background: var(--color-primary); }
.sn-button-primary:hover { background: color-mix(in oklch, var(--color-primary), black 10%); }
```

No preprocessor needed; the browser computes it at runtime.

---

## Part 12 — Decision frameworks

When a CSS question lands, walk these questions in order.

### 12.1 "Is there a selector for this?"

Before writing JS, check:

- `:has()` — parent matching
- `:is()` / `:where()` — selector grouping
- `:not()` — negation
- `:nth-child` / `:nth-of-type` — index-based
- `:user-invalid` — interaction-aware validation
- Container queries — context-aware sizing
- `@starting-style` — entry transitions

### 12.2 "Should this be a utility, a component, or a token?"

| Use case                                            | Reach for      |
| --------------------------------------------------- | -------------- |
| One element, this page only                         | inline utility |
| Three+ elements with the same string                | component      |
| A value used in many components                     | token          |
| A value used in one component as a one-off          | hard-coded in component, with a comment |

### 12.3 "Should I add a CSS framework?"

| Situation                                       | Pick                  |
| ----------------------------------------------- | --------------------- |
| Internal admin UI, no design                    | Pico CSS or Bootstrap |
| Customer-facing app with brand intent           | Tailwind + custom     |
| Heavy form / data-grid app                      | Tailwind + a UI lib   |
| Marketing site only                             | Tailwind or hand-roll |
| You already have one — add a second?            | almost never          |

### 12.4 "Should I switch from utility-first to component-first?"

Stay utility-first while:

- ≤ ~10 promoted components.
- Per-element class strings rarely exceed 6 utilities.
- No designer or guideline.

Switch when:

- ≥ ~12 promoted components.
- Repeated 10-class strings appear in three places.
- A designer / brand guideline lands.
- ≥ 10 distinct pages.

### 12.5 "Should I split CSS into multiple files?"

A single file works up to ~600 lines or so. After that:

- Split by **layer** (tokens, base, layout, components,
  effects). Same as ITCSS.
- Don't split by component (`button.css`, `card.css`) unless
  files are big enough to matter; the cost of jumping
  between files exceeds the benefit until each file is
  ~100 lines.

---

## Part 13 — How this all maps to v2.0 (project-specific)

### 13.1 What v2.0 chose

- **Utility-first via Tailwind** with a thin bespoke
  component layer (`sn-*`).
- **Tailwind Standalone CLI** (no Node), per
  [ADR 058](../adr/058-tailwind-via-standalone-cli.md).
- **Five-file CSS source split** (`tokens.css`, `base.css`,
  `layout.css`, `components.css`, `effects.css`) imported
  from a thin `input.css` orchestrator, per
  [`../project/spec/v2/css.md`](../project/spec/v2/css.md).
- **CSS custom properties for tokens**; Tailwind config maps
  utility names to `var(--color-*)` etc.
- **`data-theme="dark"` for dark mode** + four named
  styleguide presets, per
  [ADR 056](../adr/056-style-guide-page.md).
- **Class-only selectors, ≤ 0,2,1 specificity**, no
  `!important` outside `prefers-reduced-motion`.
- **Three-template promotion rule** for `sn-*` components.
- **State classes shared across components** (`is-loading`,
  `is-disabled`, `has-error`).
- **Styleguide page** as the source of truth for visual
  vocabulary.

### 13.2 What v2.0 rejected (and why)

| Rejected                              | Why                                                  |
| ------------------------------------- | ---------------------------------------------------- |
| Node + npm + PostCSS                  | Standalone CLI removes the second toolchain          |
| Sass / Less / Stylus                  | Native CSS covers what they did                      |
| CSS-in-JS                             | No JS framework in v2.0; runtime cost                |
| BEM / OOCSS / SMACSS / ITCSS by name  | The `sn-` prefix + `@apply` + layered files cover the same ground |
| Bootstrap / Bulma / Pico              | Tailwind is enough; second framework needs an ADR    |
| Web fonts                             | Zero FOIT, zero licensing surface                    |
| `!important`                          | Cascade games are a leak indicator                   |
| Inline `style="…"` for static values  | Defeats the cascade and the styleguide               |
| Classes on `id` selectors             | Specificity creep                                    |
| `data-*` selectors for styling        | Use classes; reserve `data-state` / `data-theme`     |

### 13.3 What might come later

- **Page-scoped CSS** (e.g. a marketing landing page) —
  needs an ADR; gates on whether the pattern is genuinely
  page-scoped vs. promotable.
- **Pattern B** (no inline utilities anywhere) — gates on
  styleguide stability + designer involvement.
- **Visual regression tests** against `/styleguide` —
  Playwright screenshot diffs.
- **Dropping Tailwind entirely** — only with overwhelming
  evidence that hand-rolled is cheaper. Unlikely.

### 13.4 Why splitting was worth it (vs. staying single-file)

The original v2.0 plan kept everything in `input.css`. With
~22 pages catalogued in
[`../project/spec/v2/pages.md`](../project/spec/v2/pages.md)
and a deliberate visual identity, the single-file model
would have grown to ~1000+ lines mixing tokens, components,
layout, and effects. Splitting up front:

- Keeps each diff's *intent* visible (a token change vs. a
  component change vs. an effect change).
- Lets `tokens.css` be reviewed harder than the rest.
- Isolates `effects.css` so it can be deleted for print or
  for a low-motion fallback.
- Matches the ITCSS/SMACSS reasoning without the taxonomy
  baggage.
- Maps cleanly to `@layer` if/when we need it.

### 13.5 What to keep learning

- **`:has()` patterns.** Most useful selector of the last
  decade; we'll find more places to use it as the app grows.
- **Container queries.** Currently unused; will become
  relevant when the same component appears in two different
  parents.
- **View transitions.** Could replace some "manual" page
  transition work for free.
- **`oklch()` palettes.** Once the brand brief evolves, the
  palette generation problem is much easier in `oklch`.
- **`@scope`.** Keep an eye on browser support; could replace
  some discipline-based rules with mechanical enforcement.

---

## Appendix A — A glossary of CSS jargon

| Term                | Means                                                                |
| ------------------- | -------------------------------------------------------------------- |
| Cascade             | The algorithm that resolves which rule wins for each property        |
| Specificity         | The 4-tuple count used to break cascade ties                         |
| Inheritance         | A property's value flowing from parent to child                      |
| FOUC                | Flash Of Unstyled Content (CSS not loaded yet)                       |
| FOIT                | Flash Of Invisible Text (web font hasn't loaded; text hidden)        |
| FOFT                | Flash Of Faux Text (using a fallback before web font loads)          |
| Reflow / Layout     | Browser recalculating positions / sizes                              |
| Repaint             | Browser re-rasterizing pixels without recomputing layout             |
| Composite           | GPU combining painted layers — cheapest                              |
| BFC / IFC           | Block / Inline Formatting Context — layout containers                |
| Stacking context    | Sub-tree where z-index is locally meaningful                         |
| Critical CSS        | The minimum CSS for first paint, often inlined                       |
| Above-the-fold      | The part of the page visible without scrolling                       |
| Reset / Normalize   | Stylesheets that flatten browser default differences                 |
| Preflight           | Tailwind's reset                                                     |
| Atomic CSS          | Each class does one thing — Tailwind / Tachyons / Atomizer           |
| Container query unit| `cqw`, `cqi`, `cqh` — sizing relative to the container               |
| Logical property    | Direction-aware: `inline-start` vs. `left`                           |
| Cascade layer       | A named bucket of rules with explicit ordering (`@layer`)            |
| Design token        | Named primitive value, often a CSS custom property                   |

---

## Appendix B — Recommended reading

- **MDN Web Docs** — the reference. Always check there first.
- **CSS-Tricks** — practical articles, deep dives, "almanac."
- **web.dev** — Google's CSS / Web Platform site. Strong
  performance and a11y coverage.
- **Smashing Magazine** — long-form essays, often by spec
  authors.
- **A List Apart** — older, but the foundational essays
  (Ethan Marcotte's "Responsive Web Design," Jeffrey
  Zeldman) still teach.
- **Heydon Pickering — *Inclusive Components*** — the best
  book on accessible-by-default UI components.
- **Adam Wathan — *Refactoring UI*** — the manual that made
  Tailwind make sense.
- **Lea Verou — *CSS Secrets*** — single-file tricks,
  pre-modern but still gold.
- **Una Kravets / Jhey Tompkins — Chrome / web.dev posts**
  — strong on the new (post-2022) features.
- **Josh Comeau's CSS for JS Developers** — paid course;
  the best "fundamentals → advanced" path I know.

---

## Appendix C — A short list of patterns worth memorizing

```css
/* Box-sizing reset */
*, *::before, *::after { box-sizing: border-box; }

/* Visually hidden but accessible (sr-only) */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* Auto-fit responsive grid */
.cards { display: grid; gap: 1rem;
         grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr)); }

/* Fluid type */
h1 { font-size: clamp(2rem, 4vw + 1rem, 3.5rem); }

/* Aspect ratio */
.media { aspect-ratio: 16 / 9; }

/* Truncate single line */
.truncate { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* Truncate multi-line (line-clamp) */
.clamp-2 { display: -webkit-box; -webkit-line-clamp: 2;
           -webkit-box-orient: vertical; overflow: hidden; }

/* Sticky header */
header { position: sticky; top: 0; z-index: 10; background: var(--color-bg); }

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}

/* Focus ring with offset */
:focus-visible { outline: 2px solid var(--color-focus); outline-offset: 2px; }

/* Has-based states */
form:has(:user-invalid) button[type="submit"] { opacity: 0.5; pointer-events: none; }
.list:not(:has(.list-item)) .empty-state { display: flex; }
```

---

## Appendix D — Cross-references

- [`frontend-conventions.md`](frontend-conventions.md) — the
  enforced rules for v2.0 plus rationale.
- [`custom-css-architecture.md`](custom-css-architecture.md)
  — the long-form rationale for the v2.0 multi-file split.
- [`../project/spec/v2/css.md`](../project/spec/v2/css.md) —
  the authoritative v2.0 CSS plan: file charters, component
  vocabulary, build pipeline.
- [`../project/spec/v2/core-idea.md`](../project/spec/v2/core-idea.md)
  — palette, brand brief, voice.
- [`webapp-tooling.md`](webapp-tooling.md) — when to use
  which web-app tool (React / htmx / Pico / Tailwind /
  Django / etc.).
- [ADR 056 — Style guide page](../adr/056-style-guide-page.md)
- [ADR 058 — Tailwind via Standalone CLI](../adr/058-tailwind-via-standalone-cli.md)

---

## Appendix E — Self-check questions

After reading this file, you should be able to answer:

1. What are the three things the cascade considers, in order?
2. What's the difference between `:focus` and `:focus-visible`?
3. When do you reach for `:where()` vs. `:is()`?
4. What does `:has()` enable that JS used to be required for?
5. What's the difference between flexbox and grid? When to
   reach for which?
6. What does a container query do that a media query can't?
7. What are logical properties, and why do they matter for i18n?
8. What is a design token, and why does it have *intent* not
   *appearance* in its name?
9. What's the ITCSS specificity ordering, and how does
   `@layer` enforce it?
10. When would you switch from utility-first to component-first?
11. What's the canonical loading-vs-disabled distinction?
12. What's the one place `!important` is correct?
13. Why is the styleguide page load-bearing in this project?
14. Why did v2.0 split CSS source into five files instead of one?
15. What two CSS features (post-2023) will become more
    important to learn as the app grows?

If any of these is fuzzy, re-read the relevant part.
