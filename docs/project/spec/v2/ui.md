# v2.0 — UI

> Topical detail file. Entry point: [`../spec-v2.md`](../spec-v2.md).
> Brand and visual direction: [`../core-idea.md`](../core-idea.md).

Static HTML + vanilla JS, served by FastAPI's `StaticFiles` and
`HTMLResponse` page routes. Tailwind utility classes are the style
layer ([ADR 058](../../../adr/058-tailwind-via-standalone-cli.md)).

---

## Page routes (HTMLResponse)

| Route                                | Auth         | Notes |
| ------------------------------------ | ------------ | ----- |
| `/`                                  | none / redirect | Marketing landing + mini demo. Logged-in users → `/w/<slug>/dashboard` |
| `/login`, `/signup`                  | none         | |
| `/forgot-password`, `/reset-password`, `/verify-email` | none | |
| `/invitations/<token>`               | maybe-session | accepts after login |
| `/styleguide`                        | none         | [ADR 056](../../../adr/056-style-guide-page.md) |
| `/w/<slug>/dashboard`                | session + member | |
| `/w/<slug>/inbox`                    | session + member | |
| `/w/<slug>/feedback`                 | session + member | |
| `/w/<slug>/feedback/<id>`            | session + member | |
| `/w/<slug>/submitters`               | session + member | |
| `/w/<slug>/submitters/<id>`          | session + member | |
| `/w/<slug>/roadmap`                  | session + member | management view |
| `/w/<slug>/changelog`                | session + member | management view |
| `/w/<slug>/insights`                 | session + member | |
| `/w/<slug>/settings`                 | session + member | members tab is owner-only |
| `/w/<slug>/submit`                   | none         | public submission form |
| `/w/<slug>/roadmap/public`           | none         | |
| `/w/<slug>/changelog/public`         | none         | |

---

## JS conventions

- One small JS file per page (`static/js/<page>.js`), no bundler.
- A shared `static/js/api.js` wraps `fetch` to inject the
  `X-Workspace-Slug` header (read from `<meta name="workspace-slug">`)
  and to handle 401 → redirect to `/login`.
- A shared `static/js/toast.js` for status messaging.
- Mini demo (`static/js/landing-demo.js`) is fully self-contained,
  no shared imports.

---

## Charts

Inline SVG, hand-rolled. No Chart.js, no D3, no Recharts. v2.0's
chart needs (intake sparkline, top-tags bar, status donut) are all
~30-line SVG components. A charting library is its own ADR if the
need ever justifies it.

---

## Iconography

[Lucide](https://lucide.dev/) icons exported as static SVGs into
`src/feedback_triage/static/img/icons/`. No `lucide-react`, no JS
icon library — pure inline SVG.

---

## Public submission form

Per workspace, at `/w/<slug>/submit`. Fields:

| Field         | Type        | Required | Notes |
| ------------- | ----------- | -------- | ----- |
| Description   | textarea    | yes      | 1–4000 chars |
| Type          | select      | yes      | `type_enum` values; `other` reveals `type_other` |
| Source        | hidden      | —        | always `web_form` |
| Pain level    | radio 1–5   | no       | optional |
| Email         | email       | no       | if provided, links/creates a `submitters` row |
| Name          | text        | no       | only used if email provided |
| Honeypot      | hidden text | —        | empty; non-empty submissions are silently dropped (see [`security.md`](security.md)) |

Submission UX: success page thanks the user, optionally offers to
follow this feedback by email if they provided one, links back to
the workspace's public roadmap (if any).

---

## Mini demo (FU1)

A small, self-contained interactive widget on the landing page:

- 8–12 hardcoded JSON feedback items.
- Vanilla JS state (no framework), no backend, no network calls.
- The visitor can drag a status pill, mark a row as planned, type
  in the search box. Refresh resets to the seed.
- Acts as a *"playable screenshot"* that the marketing copy can
  reference: "Try it — no signup required."

---

## Accessibility floor

WCAG 2.2 AA targeted; specific rules:

- Every status / priority pill carries **icon + text + color**, never
  color alone.
- All controls have `:focus-visible` styles using the `--color-focus`
  token.
- Modals use `<dialog>` with `.showModal()`; focus trap is the
  browser's.
- One `<h1>` per page, sequential headings.
- Skip link to `#main` on every page.
- Forms: every `<input>` has a paired `<label for>`; errors are
  announced via `aria-live="polite"`.
- Reduced-motion: `@media (prefers-reduced-motion: reduce)` zeroes
  out animations and transitions.

A Playwright smoke test loads each top-level page and runs
[`axe-core`](https://github.com/dequelabs/axe-core) — failures fail
CI. (Tooling addition tracked in [`tooling.md`](tooling.md).)

---

## Cross-references

- [`../core-idea.md`](../core-idea.md) — visual brief, component shorthand, color tokens.
- [ADR 058 — Tailwind via Standalone CLI](../../../adr/058-tailwind-via-standalone-cli.md)
- [ADR 051 — Static HTML + vanilla JS](../../../adr/051-static-html-vanilla-js.md)
- [`api.md`](api.md) — JSON endpoints the pages call.
- [`security.md`](security.md) — content limits, honeypot, CSP.
- [`../../../notes/frontend-conventions.md`](../../../notes/frontend-conventions.md)
