# v2.0 — Accessibility

> Topical detail file. Entry point: [`../spec-v2.md`](../spec-v2.md).
> See also: [`ui.md`](ui.md), [`css.md`](css.md),
> [`testing-strategy.md`](testing-strategy.md).

This file is the **a11y floor** — the minimum every page must
meet — plus the automated tooling and CI gates that enforce it.

---

## Standard

Target: **WCAG 2.2 AA**. We do not chase AAA. We do not ship
a page that fails AA on a primary user task.

---

## Color & contrast

- All text meets **4.5:1 contrast** against its background;
  large text (≥ 24px or ≥ 19px bold) meets 3:1.
- All non-text UI affordances (focus rings, form-field borders,
  pill outlines) meet **3:1** against the surface they sit on.
- Tokens in [`css.md`](css.md) are pre-checked at design time;
  custom Tailwind utilities that mix tokens (`bg-primary/10`,
  etc.) must be re-verified.
- Both `light` and `dark` themes meet the same contrast targets.
  Each of the four ADR 056 presets is verified before merge.

### Color is never the only channel

Pills (`sn-pill-status`, `sn-pill-priority`, `sn-pill-type`)
**always carry icon + text + color**. Status colors alone are
decorative. This is a hard rule — see [`css.md`](css.md)
"Component vocabulary".

---

## Keyboard

- Every interactive control is reachable via `Tab` and operable
  with `Enter` / `Space`.
- Tab order matches visual order.
- Focus styles are **visible** (`:focus-visible` ring tied to
  `--color-focus`); never `outline: 0` without a replacement.
- A skip-link (`.sn-skip-link`) is the first focusable element
  on every page; it links to `#main`.
- Modal `<dialog>` elements:
  - Open with `showModal()` (so backdrop + focus trap come for free).
  - Restore focus to the trigger element on close.
  - `Escape` closes.
- Toasts (`sn-toast`) are non-modal, non-focus-stealing, and use
  `role="status"` (`aria-live="polite"`).

### Keyboard shortcuts

| Key      | Action                                                              |
| -------- | ------------------------------------------------------------------- |
| `/`      | Focus the inbox/feedback search input (when on those pages)         |
| `Escape` | Close modals, popovers, and the mobile sidebar `<details>`          |
| `g i`    | (deferred to v2.1) Go to Inbox                                      |
| `g d`    | (deferred to v2.1) Go to Dashboard                                  |

Two-key shortcuts ship in v2.1; v2.0 only has `/` and `Escape`.

---

## Forms

- Every `<input>` / `<select>` / `<textarea>` has a paired
  `<label for="…">`. No floating labels, no placeholder-as-label.
- Validation errors render in `.sn-form-help.has-error` and the
  field gets `aria-invalid="true"` + `aria-describedby`.
- Required fields are marked with text (`*` is decorative; the
  word "required" is in the help text or the label).
- Server errors mirror client error styling so users see one
  consistent error UI ([`error-catalog.md`](error-catalog.md)).

---

## Headings, landmarks, and structure

- One `<h1>` per page.
- Heading levels are sequential (no skipping `<h2>` to `<h4>`).
- Page shell uses landmarks: `<header>`, `<nav>`, `<main id="main">`,
  `<aside>` (sidebar), `<footer>`.
- Lists use `<ul>`/`<ol>`/`<li>`; never `<div>` rows pretending
  to be a list.
- Tables that present data use `<table><thead><tbody>` with
  `<th scope="col">`; never `<div>`-grids ([`ui.md`](ui.md)).

---

## Motion & reduced motion

- Animations honour `prefers-reduced-motion: reduce`. The
  reduced-motion block in [`css.md`](css.md) is the only place
  `!important` is allowed.
- No autoplay. No looping animations longer than 5s on idle UI.
- Toasts dismiss in ≤ 4s by default; sticky errors require a click.

---

## Color scheme

- The shell respects `prefers-color-scheme` on first visit; the
  user's explicit choice in Settings overrides via a `data-theme`
  attribute on `<html>` ([`css.md`](css.md)).
- The `<meta name="color-scheme" content="light dark">` tag is
  set on every page so form controls render correctly.

---

## Axe-core ruleset (CI)

Playwright e2e tests inject **axe-core** and assert zero
violations of the rules listed below on every page in the
e2e suite. These rules are the enforced floor; a violation
fails CI ([`testing-strategy.md`](testing-strategy.md)).

| Rule ID                          | Why it's in the floor                            |
| -------------------------------- | ------------------------------------------------ |
| `color-contrast`                 | 4.5:1 / 3:1 contrast                             |
| `label`                          | every input has a label                          |
| `button-name`                    | every `<button>` has an accessible name          |
| `link-name`                      | every `<a>` has an accessible name               |
| `image-alt`                      | every `<img>` has `alt` (decorative = `alt=""`)  |
| `aria-valid-attr`                | only valid ARIA attributes                       |
| `aria-valid-attr-value`          | values are valid                                 |
| `aria-required-attr`             | required ARIA attributes are present             |
| `duplicate-id-aria`              | no duplicate `id` referenced by ARIA             |
| `landmark-one-main`              | exactly one `<main>` per page                    |
| `page-has-heading-one`           | exactly one `<h1>` per page                      |
| `region`                         | content is in a landmark                         |
| `tabindex`                       | no positive `tabindex`                           |
| `frame-title`                    | iframes have titles (we have none, but it's free) |
| `meta-viewport`                  | viewport meta is present and not zoom-locked     |

We **do not** assert the full WCAG ruleset because some axe rules
are best-effort heuristics that produce noisy false positives in
fast-moving UI. Adding a rule to the floor needs a one-line note
here in the PR that adds it.

---

## Manual checks (per PR touching UI)

Reviewer checklist — fast, mostly visual:

- [ ] Tab through the new page; focus is visible and ordered.
- [ ] `Escape` dismisses modals and reopened popovers.
- [ ] Zoom to 200% in the browser; no content lost behind
      sidebars or modals.
- [ ] Toggle dark mode; text is still readable.
- [ ] Toggle `prefers-reduced-motion` (DevTools → Rendering);
      animations either freeze or play instantly.
- [ ] Screen-reader spot-check on the new control with VoiceOver
      (macOS) or NVDA (Windows). Not required to be perfect — the
      label, role, and state must be announced.

---

## Out of scope (v2.0)

- Full WCAG AAA conformance.
- Internationalization (RTL, locale-specific date/number formats)
  — English only in v2.0; logical CSS properties used where free
  ([`css.md`](css.md)).
- Live-region transcription of toasts beyond `aria-live="polite"`.
- Custom keyboard-shortcut binding.
