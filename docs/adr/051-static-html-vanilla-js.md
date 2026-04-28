# ADR 051: Static HTML + Vanilla JS Frontend (No Jinja, No SPA)

## Status

Accepted

## Context

The frontend has three pages (list, new, detail) with simple forms and
list rendering. The candidates:

- **Static HTML + vanilla JS + Fetch API** served via `StaticFiles`.
- **Server-side templating** (Jinja2) rendering each page.
- **SPA framework** (React, Svelte, etc.) with a build pipeline.

## Decision

Ship plain static HTML files via `StaticFiles`. JavaScript talks to the
JSON API via `fetch()` from the same origin and does all dynamic
rendering client-side. **No Jinja templates, no Node toolchain, no
bundler, no SPA framework.**

Page routes (`/`, `/new`, `/feedback/{id}`) are thin route handlers in
`routes/pages.py` that return the correct HTML file. They are
unversioned (HTML is UI surface, not API contract).

Same-origin delivery means CSRF is N/A in v1.0 — no cookie auth, all
writes are JSON via `fetch()` with `Content-Type: application/json`.
Browsers do not auto-attach credentials cross-origin without explicit
`credentials: 'include'`.

## Alternatives Considered

### Jinja2 server-side templates

**Rejected because:** with three pages and a JS-driven UI, the templates
would render `{}` placeholders into otherwise-static HTML — pure
overhead. One fewer dependency, one fewer language in the repo.

### React / Svelte / SPA

**Rejected because:** scope creep. A bundler, a package manifest, a JS
ecosystem, and a build pipeline is days of churn for three pages.

### Progressive enhancement (Jinja first paint + JS hydration)

**Deferred** — listed as a Future Improvement. Cheap to add later by
swapping `StaticFiles` for Jinja templates.

## Consequences

### Positive

- The "vanilla HTML/CSS/JS" claim in the README is literally true.
- Zero JS toolchain to maintain.
- Same-origin delivery sidesteps CSRF for v1.0.

### Negative

- No first-paint without JS. Acceptable for a portfolio app.
- No component reuse beyond plain `import` of helper modules.
