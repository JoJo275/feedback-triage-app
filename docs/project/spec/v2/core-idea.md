# v2.0 — Core idea (implementation companion)

> Topical detail file. Entry point: [`../spec-v2.md`](../spec-v2.md).
> The full SignalNest brand brief lives at
> [`../core-idea.md`](../core-idea.md); this file is the
> implementation-time distillation: the locked strings, the rules
> implementers must not violate, and the per-surface checklist used
> while building v2.0.

---

## One-line product definition

**SignalNest** is a calm, multi-tenant feedback-triage SaaS that
helps a small product team turn scattered user feedback into a
five-phase workflow: **Intake → Triage → Prioritize → Act → Close
the loop.**

If a v2.0 feature does not slot into one of those five phases, it
does not ship in v2.0. This is the single sharpest scope rule.

---

## Locked strings

These appear identically across the README, the landing page hero,
the `<title>` tag, the styleguide, the footer, and any external
surface. Edits require an ADR.

| Surface     | Value                                                                                                      |
| ----------- | ---------------------------------------------------------------------------------------------------------- |
| Name        | `SignalNest`                                                                                               |
| Domain      | `signalnest.app`                                                                                           |
| Repo slug   | `feedback-triage-app` ([ADR 057](../../../adr/057-brand-vs-repo-naming.md))                                |
| Tagline     | *Capture the noise. Find the signal.*                                                                      |
| Description | *A feedback triage app for turning user requests, bugs, and product ideas into clear next steps.*          |

Forbidden spellings: `Signal Nest`, `Signalnest`, `signalnest` (in
prose).

---

## Theme statement

> SignalNest — Calm Signal Intelligence.
> Turn noisy user feedback into clear product signals.

The app should feel like a **clean command center for sorting messy
incoming feedback into useful product decisions.** Not playful, not
corporate-boring, not cyberpunk. Quiet, focused, trustworthy,
organized.

---

## Voice rules (copy review checklist)

When writing any UI string:

- Prefer **verbs of clarity**: *capture, triage, prioritize, close
  the loop, mark, merge, notify*.
- Prefer **calm acknowledgement**: *New signal received. Status
  updated. Marked as planned.*
- Avoid hype: no `Awesome!!!`, no `Super-powered`, no `magic`, no
  exclamation runs.
- Avoid generic-survey-tool wording: no `Submit your response`,
  no `Thanks for your input`.
- Empty states are factual: *No items match these filters.*
  *No feedback yet — share your public form to get started.*
- Errors are direct: *Email already in use.* *Workspace slug taken.*
  *Token expired.* No `Oops!`.

---

## Visual non-negotiables

These are the rules implementers must not silently break. The full
palette and component shorthand live in
[`../core-idea.md`](../core-idea.md); the CSS plumbing lives in
[`css.md`](css.md).

1. **Tailwind via Standalone CLI** is the styling layer
   ([ADR 058](../../../adr/058-tailwind-via-standalone-cli.md)).
   No CSS-in-JS, no preprocessor, no Bootstrap, no Tailwind via
   npm.
2. **System font stack only** in v2.0. No web font, no
   `@font-face`, no Google Fonts.
3. **Pills carry icon + text + color**, never color alone. The
   color-blind/print path must remain readable.
4. **One `<h1>` per page**, sequential heading levels, skip-link
   to `#main`.
5. **Inline SVG charts.** No Chart.js / D3 / Recharts in v2.0.
6. **Lucide icons as static SVGs**, exported into
   `src/feedback_triage/static/img/icons/`. No JS icon library.
7. **Logo / favicon are placeholders.** A designed mark replaces
   them before public launch but does not block alpha/beta.
8. **Reduced-motion respected** via
   `@media (prefers-reduced-motion: reduce)`.

---

## Roles (implementation-time summary)

Authoritative table: [`../core-idea.md`](../core-idea.md#roles).
Mechanics: [ADR 059](../../../adr/059-auth-model.md) (platform
role) + [ADR 060](../../../adr/060-multi-tenancy-workspace-scoping.md)
(workspace role).

| Role             | Has account? | Scope            | One-line capability             |
| ---------------- | ------------ | ---------------- | ------------------------------- |
| Admin            | yes          | platform         | Cross-workspace; maintenance.   |
| Workspace owner  | yes          | one workspace    | Full CRUD + members + settings. |
| Team member      | yes          | one workspace    | Full CRUD; no members/settings. |
| Demo user        | yes (shared) | demo workspace   | Read-only; resets nightly.      |
| Submitter        | no           | one workspace    | Email-known; rows in `submitters`. |
| Public submitter | no           | one workspace    | Anonymous; via public form.     |

---

## Per-surface theme checklist

Use during implementation review of each surface.

### Landing page (`/`)

- [ ] Hero shows the locked tagline + locked description, verbatim.
- [ ] Primary CTA: **Start free** → `/signup`.
- [ ] Secondary CTA: **Try the demo** → scrolls to FU1 mini demo.
- [ ] Mini demo is fully client-side; refresh resets to seed.
- [ ] Footer carries Privacy, Terms, GitHub, Contact.
- [ ] No tracker, no analytics in v2.0.

### Auth pages (`/login`, `/signup`, `/forgot-password`,
`/reset-password`, `/verify-email`)

- [ ] Same shell, no sidebar.
- [ ] One form per page, label + input + helper text.
- [ ] Errors render inline + announced via `aria-live="polite"`.
- [ ] `/signup` creates user **and** workspace in one transaction
      ([`auth.md`](auth.md), [`schema.md`](schema.md)).

### Dashboard shell (`/w/<slug>/...`)

- [ ] Sidebar in the order: Dashboard, Inbox, Feedback, Submitters,
      Roadmap, Changelog, Insights, Settings.
- [ ] Top header carries the workspace name and user menu only —
      workspace switcher is hidden when 1:1 (the v2.0 default).
- [ ] Theme switcher only renders when dark mode ships (FD).
- [ ] Page `<title>`: `<Page> · <Workspace> · SignalNest`.

### Inbox (`/w/<slug>/inbox`)

- [ ] Top summary cards: New, Needs Info, Reviewing, High priority,
      Stale.
- [ ] Filter bar: Type, Status, Tag, Priority, Source, Date.
- [ ] Single search input → `description ILIKE '%q%'` (v2.0;
      pg_trgm deferred).
- [ ] Pain rendered as 5 dots; priority rendered as a pill — never
      collapsed into a single field.
- [ ] No bulk actions (deferred).

### Feedback detail (`/w/<slug>/feedback/<id>`)

- [ ] "Case file" layout: header, status pill, priority pill, pain
      dots, tag chips, submitter chip, timeline of changes,
      internal notes panel.
- [ ] Status change writes a row to the timeline and may trigger a
      Resend email if the status is in the notify-list and the
      submitter has an email ([`email.md`](email.md)).

### Public surfaces

- [ ] `/w/<slug>/submit` — public form, honeypot field, no
      authentication.
- [ ] `/w/<slug>/roadmap/public` — read-only; only items where
      `published_to_roadmap = true`.
- [ ] `/w/<slug>/changelog/public` — read-only; only items where
      `published_to_changelog = true`.
- [ ] No member email or internal note ever leaks onto a public
      surface.

### Styleguide (`/styleguide`)

- [ ] Public route. Renders every component in light, dark (when
      shipped), and the four theme presets from
      [ADR 056](../../../adr/056-style-guide-page.md).
- [ ] Visual regression-friendly: deterministic order, no live data.

---

## Cross-references

- [`../core-idea.md`](../core-idea.md) — full brand brief.
- [`../spec-v2.md`](../spec-v2.md) — v2.0 spec entry point.
- [`pages.md`](pages.md) — per-page UI catalog.
- [`css.md`](css.md) — CSS conventions and design tokens.
- [`business.md`](business.md) — product positioning and startup
  characteristics.
