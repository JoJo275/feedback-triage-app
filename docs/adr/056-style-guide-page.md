# ADR 056: Style guide page with theme demos

## Status

Proposed

## Context

The v1.0 frontend is hand-written static HTML + vanilla JS + a single
hand-rolled CSS file with custom-property tokens
([ADR 051](051-static-html-vanilla-js.md)). As the surface grows (new
auth pages, the v2.0 triage extensions, dashboard polish), three needs
converge:

1. **Regression visibility.** When tokens or component CSS change,
   there's no single page that shows every component. Reviewing each
   real page individually is slow, and easy to miss a state (focus,
   disabled, error).
2. **Portfolio surface.** This is a portfolio project. A reviewer
   landing on the repo benefits from a single page that shows the
   author can build a coherent design system, not just a working CRUD.
3. **Theming experimentation.** The author wants to keep the production
   UI conservative ("basic") but also demonstrate range — a "unique"
   variation and a deliberately playful "crazy" one — without those
   variants leaking into the live app.

A separate Storybook would solve (1) and partly (2) but adds a JS
build pipeline and Node toolchain that
[ADR 051](051-static-html-vanilla-js.md) explicitly rejects. A static,
hand-built page using the same tokens and the same `style.css` keeps
the no-bundler rule intact and doubles as a living regression check.

The user-facing app must continue to render in exactly one theme — the
production theme. The style guide page is the **only** surface where
the alternate themes are reachable.

## Decision

Add a single static page at `GET /styleguide` that exhibits every
component used by the app, with a four-way theme selector that flips a
`data-theme` attribute on the document root.

**Themes:**

| Token             | Purpose                                                                           |
| ----------------- | --------------------------------------------------------------------------------- |
| `production`      | The exact theme rendered everywhere else in the app. The default. Locked.         |
| `basic`           | A pared-down baseline — neutral palette, system fonts, minimal accents.           |
| `unique`          | A confident, distinctive variation — refined palette, deliberate type contrast.   |
| `crazy`           | A deliberately playful, high-contrast variation. Demonstrates token range.         |

**Page contents (every state of every component):**

- Typography scale (`h1`–`h6`, body, small, code, blockquote).
- Links (default, hover, visited, focus-visible).
- Buttons (default, primary, destructive, disabled, loading).
- Form controls (`input`, `textarea`, `select`, `checkbox`, `radio`,
  date) with paired `<label>`, valid/invalid/disabled states, and
  helper text.
- Tables (default, with sticky header, with empty state).
- Alerts / banners (info, success, warning, error).
- Cards.
- `<dialog>` (modal trigger).
- `<details>` / `<summary>`.
- Skeleton / loading placeholders.
- Empty state and 404 placeholder fragments.
- Token swatches: every CSS custom property rendered as a labeled
  swatch (so token edits are visible at a glance).

**Theme mechanics:**

- Themes are scoped via `html[data-theme="<name>"] body.styleguide-page`
  selectors so they cannot affect any other route. The `body` class
  gate is non-negotiable.
- Theme tokens live in `static/css/themes.css`, loaded **only** on
  `/styleguide`. The production theme remains in the existing
  `style.css` and is unaffected.
- The selector is a `<fieldset>` with four radio inputs (semantic HTML,
  see [`docs/notes/frontend-conventions.md`](../notes/frontend-conventions.md)),
  not a custom toggle. Selection persists to `localStorage` under the
  key `styleguide-theme`; the default on first visit is `production`.
- Reduced-motion preference is respected; theme transitions are
  instant under `prefers-reduced-motion: reduce`.

**Route and visibility:**

- Page route: `GET /styleguide` (HTML), unversioned (matches the
  existing `/`, `/new`, `/feedback/{id}` page routes).
- Linked from the footer in production builds. Always available — no
  feature flag — because it's a portfolio surface, not a debug tool.
- Excluded from `sitemap.xml` (low SEO value).
- Excluded from the Playwright smoke suite by default; a single
  `tests/e2e/test_styleguide.py` smoke that loads the page and cycles
  the four themes is added under `@pytest.mark.e2e` (gated, opt-in,
  matches the rest of the e2e suite).

## Alternatives Considered

### Storybook (or Histoire / Ladle)

Run a separate component-explorer service.

**Rejected because:** introduces a JS build pipeline (Vite + Node),
which contradicts [ADR 051](051-static-html-vanilla-js.md). Solves a
problem we don't have yet (component isolation in a framework app)
and adds a maintenance surface bigger than the app's own frontend.

### Multiple per-theme pages (`/styleguide/basic`, `/styleguide/crazy`, …)

One page per theme, no toggle.

**Rejected because:** four pages to keep in sync defeats the
"one regression surface" goal. The toggle is part of the value: a
reviewer flipping themes sees the token system working in real time.

### Embed the demos directly inside `/` or another live page

Show the theme variants in the actual app.

**Rejected because:** the production app must render in exactly one
theme. Mixing demo theming into live pages makes UX testing
ambiguous and risks the alternate themes leaking into production
builds.

### Skip the page; rely on visual diff CI

Use Playwright + visual snapshots against `/`, `/new`, `/feedback/{id}`.

**Rejected because:** doesn't solve the portfolio-showcase need, and
visual diff infrastructure is its own project. Can be added later
*on top of* the styleguide page (snapshot the styleguide, not three
ad-hoc pages).

## Consequences

### Positive

- One page exhibits every component in every state — token edits and
  CSS regressions become a single visual scan.
- The theme toggle is a portfolio asset that demonstrates token-driven
  theming without bringing in a framework.
- The "production" theme remains the single source of truth for the
  rest of the app; alternate themes cannot leak.
- New components must be added to the styleguide as part of their PR,
  which keeps the design surface documented.

### Negative

- The styleguide page must be kept in sync as components evolve. Out
  of date is worse than absent.
- Three additional themes × every component = real CSS volume in
  `themes.css`. Bounded by the token-swap-only rule, but still a file
  to maintain.
- One more route to test, lint, and serve from `StaticFiles`.

### Neutral

- No build tool added; page is static HTML + the same vanilla CSS/JS
  conventions the rest of the app uses.
- No new dependencies.

### Mitigations

- Add a section to the PR template / `tests/.instructions.md`: "If you
  added or changed a component, update `/styleguide`."
- Wire a single Playwright e2e smoke that cycles the four themes; if
  any theme fails to render, the smoke fails.
- Keep `themes.css` strictly token-overrides — no new selectors. If a
  theme needs a structural change, the design system has out-grown a
  token theme and a new page (or a new ADR) is the right answer.

## Implementation

- `src/feedback_triage/static/styleguide.html` — the page itself.
- `src/feedback_triage/static/css/themes.css` — `[data-theme="basic"]`,
  `[data-theme="unique"]`, `[data-theme="crazy"]` overrides scoped to
  `body.styleguide-page`.
- `src/feedback_triage/static/js/styleguide.js` — theme selector +
  `localStorage` persistence.
- `src/feedback_triage/routes/pages.py` — register `GET /styleguide`.
- `tests/e2e/test_styleguide.py` — gated Playwright smoke cycling all
  four themes.
- Footer link in `src/feedback_triage/static/_partials/footer.html`
  (or wherever the app's footer lives).

## References

- [ADR 051: Static HTML + vanilla JS frontend](051-static-html-vanilla-js.md)
- [`docs/notes/frontend-conventions.md`](../notes/frontend-conventions.md)
- [`docs/project/spec/spec-v2.md`](../project/spec/spec-v2.md) —
  v2.0 spec, Style Guide Page section.
