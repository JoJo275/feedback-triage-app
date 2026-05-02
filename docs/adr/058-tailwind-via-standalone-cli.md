# ADR 058: Tailwind CSS via Standalone CLI

## Status

Accepted

## Context

[ADR 051](051-static-html-vanilla-js.md) committed v1.0 to hand-rolled
CSS with custom-property tokens and explicitly forbade Tailwind, citing
the Node toolchain that Tailwind has historically required. v2.0
expands the surface significantly (auth pages, multi-page dashboard,
Inbox / Feedback / Submitters / Roadmap / Changelog / Insights /
Settings, plus a public landing page with an interactive demo). Hand-
rolled CSS at that scale produces:

- Larger CSS file with more selector specificity to track.
- More re-implementation of common patterns (button variants, form
  layouts, card/grid utilities).
- Manual upkeep of a token system that Tailwind already provides,
  including dark-mode plumbing.

Tailwind's **Standalone CLI** ships as a single self-contained binary
(per-platform: `tailwindcss-windows-x64.exe`, `tailwindcss-linux-x64`,
etc.) with no Node, no `node_modules`, no JS bundler. It reads a
`tailwind.config.js` (or `.cjs`) plus an input CSS file and emits a
purged, minified CSS file. Adoption cost:

- One binary download per platform (committed to CI cache or
  `tools/tailwindcss/`).
- One config file (`tailwind.config.cjs`).
- One `task build:css` invocation.
- One generated artifact (`src/feedback_triage/static/css/app.css`)
  committed alongside the source `input.css`.

This sidesteps every reason ADR 051 rejected Tailwind: no Node runtime
in CI, no `package.json`, no JS framework dependency, no SPA bundler.

## Decision

Adopt **Tailwind CSS via the Standalone CLI** as the v2.0 styling
layer. Specifically:

- The Standalone CLI binary is downloaded by `task setup:tailwind`
  into `tools/tailwindcss/` (gitignored except for a checksum file).
  The same step runs in the CI job that builds the container image.
- Tailwind config lives in `tailwind.config.cjs` at the repo root.
  Custom properties (CSS variables) defined in `static/css/input.css`
  drive the color palette so the four `data-theme` variants from
  [ADR 056](056-style-guide-page.md) (`production` / `basic` /
  `unique` / `crazy`) work without rebuilding the CSS per theme.
- `task build:css` runs:

  ```text
  ./tools/tailwindcss/tailwindcss \
      -i src/feedback_triage/static/css/input.css \
      -o src/feedback_triage/static/css/app.css \
      --minify
  ```

- `task dev` invokes `task build:css` once at startup and then runs
  `tailwindcss --watch` in the background so edits to HTML or
  `input.css` rebuild `app.css` automatically.
- `app.css` is **committed**. The Containerfile copies it into the
  runtime stage; no Tailwind binary lives in the production image.
- HTML templates use Tailwind utility classes
  (`class="rounded-2xl bg-white p-4 shadow-sm"`). Hand-rolled
  component CSS is permitted only when a utility composition would be
  unreadable (rare).
- The `tags carry meaning, classes carry style` rule from
  [`docs/notes/frontend-conventions.md`](../notes/frontend-conventions.md)
  remains in force. **Tailwind utilities are now the standard style
  layer.** Semantic HTML is unchanged.

The ADR 051 line "no CSS preprocessor, no Tailwind/Bootstrap import —
needs an ADR" is satisfied by **this** ADR.

## Alternatives Considered

### Stay on hand-rolled CSS + custom-property tokens

Continue the v1.0 approach.

**Rejected because:** v2.0's component count (auth, inbox table,
filter chips, status pills, priority pills, submitter cards, roadmap
columns, changelog entries, insights charts, settings forms, modal
dialogs, toasts) makes hand-rolling the variant matrix ~5× more code
than the Tailwind config that produces the same result. Token system
becomes its own maintenance burden.

### Tailwind via npm + Vite (Path C)

Real Node toolchain.

**Rejected because:** reactivates the JS-bundler debate that
[ADR 051](051-static-html-vanilla-js.md) deliberately closed. Adding
Node to CI and to the dev environment for a CSS pipeline alone is
overhead with no benefit; Standalone CLI delivers identical output.

### Tailwind CDN (`<script src="…tailwindcss">`)

Browser-side JIT.

**Rejected because:** ships ~3 MB of JS to every page, no purging,
defeats the whole point of utility-first CSS, and no production app
should rely on it. Tailwind themselves label it "for development
only."

### UnoCSS / Open Props / Pico.css

Tailwind alternatives.

**Rejected because:** UnoCSS still needs a Node runtime for serious
use; Open Props is a token system, not a utility layer (would compose
fine on top of hand-rolled CSS but doesn't solve the variant-matrix
problem); Pico.css is a classless framework (the opposite axis from
the customization needed for SignalNest's brand).

## Consequences

### Positive

- One binary, one config, one generated file. Production image stays
  thin (Tailwind doesn't ship to the runtime).
- Dark mode and the four ADR-056 themes plug into the existing
  custom-property tokens without rebuilding the CSS per variant.
- Component variants (button sizes, status colors, density variants)
  ship as utility compositions instead of CSS classes — fewer
  named-class collisions, smaller diff per UI change.
- Generated `app.css` is small (purged + minified, expected ~15–30 kB)
  and cacheable.

### Negative

- One more build step in `task dev` and `task build`.
- Tailwind binary version pinning is the author's responsibility
  (no `package-lock.json`); recorded as a SHA256 in
  `tools/tailwindcss/.checksum`.
- Tailwind utility class soup in HTML can be hard to read at scale.
  Mitigation: extract long compositions into Jinja-style includes or,
  where unavoidable, a single hand-rolled CSS class.
- A new contributor must run `task setup:tailwind` before
  `task dev` works the first time.

### Neutral

- ADR 051's "static HTML + vanilla JS" stance is **unchanged**. Only
  the CSS authoring layer changed.
- No JS framework added; no SPA reactivated.

### Mitigations

- `task setup:tailwind` is idempotent and is auto-run at the top of
  `task dev` and `task build:css` if the binary is missing.
- The CI job that builds the container verifies `app.css` checksums
  match the source `input.css` + config to catch un-built diffs.
- The Standalone CLI release SHAs are pinned in `Taskfile.yml` and
  refreshed by Dependabot via a custom updater (or hand-bumped quarterly).

## Implementation

- `tailwind.config.cjs` — repo root.
- `src/feedback_triage/static/css/input.css` — `@tailwind base;` /
  `@tailwind components;` / `@tailwind utilities;` plus the
  `:root { --color-…: … }` token block.
- `src/feedback_triage/static/css/app.css` — generated, committed.
- `Taskfile.yml` — `setup:tailwind`, `build:css`, `dev` watch.
- `Containerfile` — copies `app.css` into the runtime stage; does
  **not** install the Tailwind binary into the runtime.
- [`docs/notes/frontend-conventions.md`](../notes/frontend-conventions.md) —
  updated to reflect Tailwind as the style layer.
- `.gitignore` — `tools/tailwindcss/tailwindcss*` (binary), keep
  `tools/tailwindcss/.checksum`.

## References

- [ADR 051: Static HTML + vanilla JS frontend](051-static-html-vanilla-js.md)
- [ADR 056: Style guide page with theme demos](056-style-guide-page.md)
- [Tailwind Standalone CLI release notes](https://github.com/tailwindlabs/tailwindcss/releases)
- [`docs/notes/frontend-conventions.md`](../notes/frontend-conventions.md)
