# SignalNest — Core Idea, Pushback & Actionables

> **Audience:** the author of [`core-idea.md`](../core-idea.md). This is
> direct, unfiltered review of the brand/visual brief — what's strong,
> what conflicts with v1.0 / v2.0 decisions already made, and what to
> change before the brief drives any code.
>
> **Status:** review notes. Not authoritative. Once each item is
> decided, fold the decision back into `core-idea.md` (or
> [`spec-v2.md`](../spec-v2.md) for cross-cutting calls), then either
> archive this doc or keep it as the brand-decision history.

---

## TL;DR

The brief **does** answer the v2.0 Theme question that was open in
[`spec-v2-feedback.md`](spec-v2-feedback.md#1-v20-has-no-stated-theme--fix-this-first).
The Theme is now:

> **SignalNest is a calm, multi-user feedback-triage tool. v2.0 turns
> v1.0's single-resource CRUD into a workflow: Intake → Triage →
> Prioritize → Act → Close the loop. Visually it ships as a light
> SaaS dashboard.**

That's a real Theme — it picks Theme **A** (multi-user) **and** parts
of Theme **B** (triage UX) from the feedback doc. Good. But that
combination is exactly the "three big features stacked" risk that
feedback doc item #1 warned about. The brief needs an explicit
**phase order** so the workflow ships incrementally instead of as one
big-bang release.

The brief is **strong on visual/brand direction** and **weak on
engineering scope** — it implicitly assumes Tailwind, a SaaS sidebar
layout, and a roadmap/changelog/users surface that the v1.0 spec
doesn't have. None of those are wrong, but they're each ADR-sized
decisions hidden inside a vibe doc.

---

## What the brief does well

1. **One clear product sentence.** "Capture the noise. Find the
   signal." is a real tagline, not a placeholder. Easy to repeat,
   easy to design against.
2. **Calm tone is the right call.** Avoiding cyberpunk / corporate /
   AI-magic is the correct default for a triage tool. Reviewers
   trust calm.
3. **Concrete colors and tokens.** Slate/teal/amber/rose with
   Tailwind-style approximations is a workable token set. Not just
   "use a nice color".
4. **Workflow framing.** _Intake → Triage → Prioritize → Act → Close
   the loop_ is the strongest part of the brief. It turns v1.0's
   single CRUD resource into a story. Anchor v2.0 to this phrase.
5. **Anti-patterns are listed.** "Avoid literal bird nest" / "Avoid
   Awesome!!!" — good guardrails against scope creep and
   AI-generated copy drift.

---

## Critical issues

### 1. Brief assumes Tailwind; v1.0 forbids it without an ADR

The "Tailwind UI style direction" code block uses `bg-slate-50`,
`rounded-2xl`, `shadow-sm`, etc. Those are Tailwind utility classes.
Adopting Tailwind:

- Conflicts with [ADR 051](../../../adr/051-static-html-vanilla-js.md)
  ("static HTML + vanilla JS", no bundler).
- Conflicts with the
  [`docs/notes/frontend-conventions.md`](../../../notes/frontend-conventions.md)
  rule that "Tags carry meaning, classes carry style" — Tailwind is
  the explicit example given of a tool that needs an ADR before
  adoption.
- Doesn't match the v1.0 token model (CSS custom properties in
  `style.css`).

**The brief is using Tailwind names as a *palette shorthand***, not
necessarily mandating Tailwind itself — `slate-50` is a recognizable
hex shortcut. That's fine as a palette, but the doc should say so
explicitly to avoid a future contributor reading "use Tailwind" into
it.

**Actionable:**

- [ ] In `core-idea.md`, change the "Example Tailwind UI style
      direction" heading to **"Palette in Tailwind shorthand"** and
      add a one-line note: _"Tokens, not utility classes. The
      production CSS uses CSS custom properties named after these
      values (e.g. `--color-bg: var(--slate-50)`). See
      [ADR 051](../../../adr/051-static-html-vanilla-js.md)."_
- [ ] If the actual intent **is** to adopt Tailwind, that's an ADR
      paired with the React/Vite ADR (Feature 2 in
      [`spec-v2.md`](../spec-v2.md)). Don't sneak it in.

### 2. Brief implies a SPA-shaped app; the spec hasn't decided yet

The brief describes:

- Left sidebar / top header / main / right drawer.
- Pages: Dashboard, Inbox, Feedback, Roadmap, Changelog, Users,
  Settings.
- "Bulk actions later", "side drawer", "toasts", "empty states with
  icons".
- A landing page at `signalnest.app` with hero + CTA + feature grid.

That layout is plausible as static HTML + vanilla JS — sidebar nav
is just `<nav><a>` — but the **density** and **page count** push
toward a real frontend stack (React or htmx). The spec hasn't
decided yet (Feature 2 in `spec-v2.md` is still "TBD — needs ADR").

The brief should not pre-commit that decision. Treat the layout as
**target end-state**, with v2.0 shipping the smallest subset that
tells the workflow story.

**Actionable:**

- [ ] Add a "Phasing" section to `core-idea.md` listing which pages
      ship in v2.0-alpha vs. v2.0-beta vs. v2.0-final vs. v3.0.
      Suggested split:
  - **v2.0-alpha (auth backend only):** no UI changes; existing
    `/`, `/new`, `/feedback/{id}` continue to render.
  - **v2.0-beta (auth UI + Inbox):** add `/auth/login`,
    `/auth/signup`, rebrand `/` as **Inbox** with the triage table.
    No sidebar yet — top header only.
  - **v2.0 (final):** add Tags, sidebar nav, status workflow, basic
    Dashboard.
  - **v3.0:** Roadmap, Changelog, Users management, side drawer,
    bulk actions.
- [ ] Until the React/Vite ADR is written, treat the SaaS-dashboard
      sidebar as **aspirational**, not as a Phase-1 commitment.

### 3. Status enum is being expanded silently

v1.0's `status_enum` has a fixed set of values enforced at the DB
level (see [ADR 046](../../../adr/046-postgres-enums-and-check-constraints.md)).
The brief lists **nine** statuses (New, Needs Info, Reviewing,
Accepted, Planned, In Progress, Shipped, Closed, Spam) — that's a
much richer workflow than v1.0 supports.

This is a real schema change disguised as a color palette. Options:

- **A.** Extend the native `status_enum` with the new values
  (Alembic migration, hand-reviewed, irreversible without another
  migration). Simple, fast, locks in the workflow.
- **B.** Move to a `feedback_statuses` lookup table (matches
  `spec-v2.md` Schema sketch). Flexible, but loses DB-level
  enforcement unless paired with a `CHECK (status_id IN (...))`
  trigger. See feedback doc item #6.
- **C.** Keep v1.0's enum and add a separate `workflow_state` column
  for the richer states. Two columns, more migrations, ugly.

**Actionable:**

- [ ] Pick A, B, or C in `spec-v2.md` Schema Changes. Document the
      decision. The brief currently assumes the workflow exists; the
      schema doesn't.
- [ ] Reconcile the status list with v1.0's existing values (which
      are `new`, `triaged`, `closed` per `spec-v1.md`). The brief's
      "New / Reviewing / Accepted / Planned / In Progress / Shipped /
      Closed" is **not** a superset of v1.0 — `triaged` doesn't
      appear. Decide: rename `triaged` → `reviewing`? Drop it?
      Migrate existing rows?

### 4. "Roadmap" and "Changelog" are out-of-scope creep

The brief lists Roadmap and Changelog as sidebar items and as
landing-page sections. Both are:

- Not in v1.0.
- Not in any of the three Theme options in
  [`spec-v2-feedback.md` item #1](spec-v2-feedback.md#1-v20-has-no-stated-theme--fix-this-first).
- Substantial features each (Roadmap = an ordered, dated, public
  view of accepted feedback; Changelog = a public log of what
  shipped).

They're **good ideas** but they belong to v3.0 ("close the loop"
phase of the workflow). Putting them in the v2.0 visual brief makes
them feel committed.

**Actionable:**

- [ ] Move "Roadmap" and "Changelog" out of the v2.0 sidebar list in
      `core-idea.md`. Keep them in the **workflow diagram** ("Close
      the loop") so the story stays whole, but mark them v3.0 with a
      footnote.
- [ ] Drop the Changelog section from the landing-page feature grid
      until v3.0.

### 5. "Status emails" pulls Resend deeper into the critical path

The "Close the loop" workflow step says _"changelog, status emails"_.
That implies: when a feedback item moves to "Shipped" or "Planned",
the original submitter gets an email. This is:

- A second use of Resend beyond auth (signup verification + password
  reset), so the Resend dependency case strengthens.
- A new failure mode — silent email-send failures during a status
  change shouldn't break the status change itself.
- Spam risk if status edits are bulk operations.

**Actionable:**

- [ ] Decide whether status-change emails ship in v2.0 or v3.0.
      Recommend **v3.0**. Auth emails alone are enough Resend
      surface for v2.0.
- [ ] If v2.0: spec the failure mode. Status update succeeds even
      if email send fails; failures are logged and retried offline.
      Document in `spec-v2.md` and the Resend ADR.

### 6. Logo direction is fine; logo *delivery* needs a decision

"A small circular nest made of 2–3 curved lines, with one signal dot
in the center" is a clear concept. What's missing:

- Source format (SVG hand-coded? Figma export? AI-generated?)
- Where it lives in the repo (`static/img/logo.svg`?).
- Favicon set (`favicon.ico`, `apple-touch-icon`, `manifest.json`
  with `<link rel="icon">` for various sizes).
- License if any external icon assets are used.

**Actionable:**

- [ ] Add a "Logo assets" subsection to `core-idea.md` listing:
  - Path: `src/feedback_triage/static/img/logo.svg`.
  - Favicon set: 16, 32, 180 (apple), 192, 512 (PWA-ready).
  - Manifest: `static/manifest.webmanifest` with `name: "SignalNest"`.
- [ ] Either commit a placeholder SVG now or note "logo: deferred,
      using text wordmark in v2.0".

### 7. Light-mode-first is correct; locking in dark mode timing

The brief says "build light mode first; add dark mode later only if
the core app is solid." Good. But "later" is vague enough that it
will either ship in v2.0 anyway (creep) or never (the dark-mode
tokens become bit-rot).

**Actionable:**

- [ ] Mark dark mode explicitly **v3.0** in
      [`spec-v2.md`](../spec-v2.md) Future Improvements.
- [ ] Define dark-mode tokens in `themes.css` from the start (see
      [ADR 056](../../../adr/056-style-guide-page.md)) but only as a
      styleguide-page theme — not wired to a real `prefers-color-scheme`
      switch on the live app.

### 8. Brief doesn't mention accessibility

The visual direction is clean and dense. That's at risk for:

- Contrast: slate-500 muted text on slate-50 background needs
  measuring. Teal-600 buttons need WCAG AA contrast against white.
- Focus rings: "subtle" can mean invisible. The
  [`docs/notes/frontend-conventions.md`](../../../notes/frontend-conventions.md)
  rule is `:focus-visible` rings on every interactive element.
- Status colors: relying on color alone for "Spam" / "Shipped"
  fails colorblind users. Pair color with an icon or label.
- Density: "Medium-dense but readable" — measurable as a minimum
  18px line-height and 14px+ body text.

**Actionable:**

- [ ] Add an "Accessibility floor" section to `core-idea.md`:
  - All text ≥ WCAG AA contrast (4.5:1 normal, 3:1 large).
  - All status pills carry both color **and** an icon or initial
    letter.
  - All interactive elements have a visible `:focus-visible` ring
    at ≥ 2px width and ≥ 3:1 contrast against the surrounding
    surface.
  - All form inputs have paired `<label>`.
- [ ] Add a Lighthouse / axe-core check to the Playwright smoke
      suite.

### 9. Tagline appears twice with slightly different wording

- "Capture the noise. Find the signal." (Tagline row, Hero)
- "Turn noisy user feedback into clear product signals." (Core idea)

Both are good. Pick one as the tagline and use the other as the
extended description.

**Actionable:**

- [ ] In `core-idea.md`, label one **Tagline** and the other
      **Description (one-liner)**. Use the same wording everywhere
      that surface is rendered (`<title>`, OG tags, README, mkdocs
      `site_description`).

---

## Decisions still open

| #  | Decision                                                     | Recommended next step                              |
| -- | ------------------------------------------------------------ | -------------------------------------------------- |
| 1  | CSS approach: Tailwind vs. hand-rolled tokens                | Write Feature 2 ADR (paired with React decision)   |
| 2  | Status workflow: enum extend vs. lookup table vs. dual cols  | Pick one in `spec-v2.md` Schema Changes            |
| 3  | Roadmap / Changelog timing                                   | Defer to v3.0; remove from v2.0 sidebar list       |
| 4  | Status-change emails                                         | Defer to v3.0                                      |
| 5  | Logo delivery format and favicon set                         | Add placeholder SVG path; defer real logo to v2.0-final |
| 6  | Dark mode timing                                             | Tokens defined in v2.0; switch shipped in v3.0     |
| 7  | Tagline canonical wording                                    | Pick one; propagate to README, `<title>`, OG tags  |

---

## How this changes spec-v2.md

This brief unblocks the v2.0 Theme. The follow-on edits are:

- [ ] Replace the "Working draft (needs author confirmation)" Theme
      paragraph in `spec-v2.md` with the SignalNest Theme statement
      from this doc's TL;DR.
- [ ] Add a "Workflow" section to `spec-v2.md` after Theme,
      anchored to **Intake → Triage → Prioritize → Act → Close the
      loop**. Map each phase to which v2.0 features deliver it.
- [ ] Reorder the Proposed Features list by **portfolio value ×
      product value** (see new section in `spec-v2.md`).
- [ ] Add Roadmap and Changelog to "Future Improvements After v2.0".
- [ ] Cross-link `core-idea.md` from the v2.0 doc's "Related Docs"
      footer.
