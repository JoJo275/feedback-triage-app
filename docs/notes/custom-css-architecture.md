# Custom CSS architecture — future direction

> **Status:** exploration / parking lot. **Not** the v2.0 plan.
> v2.0 stays on the Tailwind-first, single-`input.css` model defined
> in [`../project/spec/v2/css.md`](../project/spec/v2/css.md) and
> ratified by [ADR 058](../adr/058-tailwind-via-standalone-cli.md).
> This file exists so the broader design-system idea isn't forgotten
> when v2.0 ships and we start asking *"what comes next?"*.
>
> **Trigger to revisit:** more than ~10 distinct screens, ≥ 3
> bespoke `sn-*` components per screen, or a serious push toward
> a strong visual identity (animation, custom layouts, marketing
> surfaces, public roadmap polish) that Tailwind utilities make
> awkward to express inline.

---

## 1. Why this might exist later

The v2.0 system is intentionally minimal: Tailwind utilities at the
call site, ~8 promoted `sn-*` classes, one `input.css`, no
preprocessor. That works because the v2.0 surface is small (inbox,
detail, settings, public submit, public roadmap, styleguide).

If the product grows in any of these directions, the single-file
model starts to strain:

- **Heavy custom visual identity** — bespoke animations, layered
  effects, signature gradients, illustrative empty states.
- **Many one-off layouts** — landing variants, marketing pages,
  changelog entries with custom typography, embedded widgets.
- **Reusable behavior-bound components** — modals, popovers,
  toasts, command palettes, multi-step forms — where the same
  *combination* of structure + style + state matters everywhere.
- **A visible brand step-up** — when "looks fine" stops being
  good enough and "looks like ours" becomes the goal.

When that happens, the right move is **not** more Tailwind utility
strings on every element. It's a real, organized, multi-file CSS
architecture sitting *alongside* Tailwind (or eventually replacing
the bespoke layer Tailwind currently fills).

---

## 2. Proposed file split

```text
src/feedback_triage/static/css/
├── input.css            # entry — only @import statements + @tailwind
├── tokens.css           # design tokens: colors, spacing, radius, shadow,
│                        # typography scale, motion timings, z-layers
├── base.css             # element resets, root styles, focus ring,
│                        # prefers-reduced-motion, color-scheme
├── layout.css           # page shells, grids, stacks, gutters
├── components.css       # the .sn-* component vocabulary
├── effects.css          # transitions, hover/focus polish, animations,
│                        # gradients, decorative utilities
└── app.css              # generated; DO NOT EDIT
```

`input.css` becomes a thin orchestrator:

```css
@tailwind base;
@import "./tokens.css";
@import "./base.css";

@tailwind components;
@import "./layout.css";
@import "./components.css";

@tailwind utilities;
@import "./effects.css";
```

Why split:

- **`tokens.css`** is the contract every other file reads. Its
  diff is reviewed harder than any other file because a token
  change touches every screen.
- **`base.css`** is small and rarely changes. Splitting it keeps
  the "did anyone touch resets?" question one file away.
- **`layout.css`** and **`components.css`** grow over time;
  isolating them stops `input.css` from becoming a 2000-line wall
  and lets reviewers diff structural vs. visual changes
  separately.
- **`effects.css`** is where the "designed feel" lives — hover
  lifts, focus glows, entrance animations, gradient surfaces.
  Keeping it separate signals that it's *decoration* and tells
  reviewers "this can be deleted in a print stylesheet."

The split is **load-order significant**: tokens before base
before components before effects. Don't reorder without thinking.

---

## 3. Proposed component vocabulary

When promoted to actual components (still `sn-` prefixed, single
dashes), the catalog grows to roughly:

| Class               | What it is                                                |
| ------------------- | --------------------------------------------------------- |
| `sn-button`         | base button; modifiers `--primary`, `--secondary`, `--ghost`, `--danger` |
| `sn-card`           | surface block; modifiers for tone, density, interactivity |
| `sn-page-shell`     | full-page chrome (header / main / footer composition)     |
| `sn-dashboard-grid` | the inbox-style two-pane / sidebar+main grid              |
| `sn-status-pill`    | rounded-full status indicator (icon + text + color)       |
| `sn-feedback-item`  | the canonical row/card for one feedback record            |
| `sn-modal`          | `<dialog>`-based modal styling                            |
| `sn-form-field`     | label + input + help + error composition                  |
| `sn-empty-state`    | illustrated "nothing here yet" block                      |
| `sn-toast`          | transient bottom-right status message (kept from v2.0)    |

Notes on style:

- **Modifiers use single dashes**, not BEM `--`. So
  `sn-button-primary`, not `sn-button--primary`. The `sn-`
  prefix already namespaces; doubling the separator buys
  nothing.
- **Element classes** — when a component has internal parts —
  follow the same pattern: `sn-card-header`, `sn-card-body`,
  `sn-card-footer`. Read aloud they sound like what they are.
- **No layout in components.** `sn-card` doesn't `flex` itself
  into a grid; the *parent* (`sn-dashboard-grid`,
  `sn-page-shell`) does layout. Component classes only style
  the element they're on.

---

## 4. The hard parts — and the answer to each

This is the section that matters. Custom CSS systems fail in
predictable ways. The plan below names each failure mode and
commits to a defense.

### 4.1 Naming classes consistently

**Defense:** one rule, written down: `sn-<component>` for the
block, `sn-<component>-<part>` for sub-parts, `sn-<component>-<modifier>`
for variants. Single dashes only. No BEM, no camelCase, no
abbreviations.

If the name needs more than three segments
(`sn-card-header-icon-warning`), the structure is wrong — split
into a separate component.

State classes use the verb-prefix convention from
[`frontend-conventions.md`](frontend-conventions.md#33-naming-conventions):
`is-open`, `is-loading`, `has-error`, `has-warning`. Never
encode state in the component name itself.

### 4.2 Avoiding duplicated styles

**Defense:** a CI check that greps for repeated declaration
clusters. Cheap version: a script that flags any `@apply` line
appearing more than twice in `components.css`. Better version:
`stylelint` with `declaration-block-no-redundant-longhand-properties`
and a custom rule for repeated property bundles.

Manual rule: before adding a new class, search the existing
catalog for the same visual outcome. If it's there, use it; if
it's *almost* there, add a modifier rather than a sibling class.

### 4.3 Keeping specificity low

**Defense:** one specificity budget, enforced by code review:

- **0,1,0** — single class. The default.
- **0,2,0** — class + state class (`.sn-button.is-loading`).
  Allowed.
- **0,2,1** — class + pseudo (`:hover`, `:focus-visible`,
  `::before`). Allowed.
- **Anything higher** is a smell. Reach for a modifier class
  before a deeper selector.

No `#id` selectors. No tag-only style overrides below `base.css`.
No `!important` outside `prefers-reduced-motion`.

### 4.4 Organizing files

**Defense:** the load-order in §2 is the rule. Each file has a
**charter** stated at the top in a comment, and contributions
that don't fit a file's charter go in a different file or a new
file. Example charters:

- `tokens.css` — *only* `:root { --… }` and `[data-theme="…"]`
  blocks. No selectors, no `@apply`, no `@media`.
- `base.css` — element-level rules (`html`, `body`, `:focus-visible`,
  `*`). No class selectors.
- `components.css` — only `.sn-<component>` rules.
- `effects.css` — only transitions, animations, gradients,
  hover/focus polish that isn't intrinsic to the component.

If a PR adds a `:root { --… }` line to `components.css`, it's
rejected. The charter is the file's contract.

### 4.5 Making responsive layouts consistent

**Defense:** breakpoints come from `tokens.css` as custom media
queries (or named tokens consumed by Tailwind config), not from
ad-hoc `@media (min-width: 763px)` calls.

```css
/* tokens.css */
@custom-media --md (min-width: 768px);
@custom-media --lg (min-width: 1024px);
```

Three breakpoints, named, used everywhere. Adding a fourth
needs review.

Layout primitives (`sn-page-shell`, `sn-dashboard-grid`) own
their responsive behavior. Pages don't re-implement
"sidebar collapses to disclosure" — they use the layout class
and trust it.

### 4.6 Preventing one-off hacks

**Defense:** three rules, in order of severity:

1. **No inline `style="…"`** outside JS-set dynamic values.
2. **No `!important`** outside the reduced-motion block.
3. **No utility-strings longer than ~6 classes** on a single
   element in HTML once the bespoke system exists. If a span
   needs eight Tailwind classes, it's a component.

When a one-off is genuinely needed (a marketing page with a
custom hero), it lives in a *page-scoped* file
(`pages/marketing-hero.css`) with a charter saying "this file
is the one-off; nothing else imports from it." That keeps the
hack visible.

### 4.7 Maintaining visual consistency

**Defense:** the styleguide page (`/styleguide`,
[ADR 056](../adr/056-style-guide-page.md)) renders every
component, every modifier, every state. Ship-blocking rule: a
new component is not "done" until it appears on the styleguide.

Visual regression: a Playwright screenshot test against the
styleguide page, run on PRs that touch `static/css/`. One
golden image per breakpoint per theme preset; diffs require
review.

### 4.8 Handling hover / focus / disabled / error / loading states

**Defense:** every interactive component declares **all five**
states, even if some are no-ops. The component file looks like:

```css
.sn-button { /* default */ }
.sn-button:hover { /* hover */ }
.sn-button:focus-visible { /* focus */ }
.sn-button:disabled,
.sn-button.is-disabled { /* disabled */ }
.sn-button.has-error { /* error */ }
.sn-button.is-loading { /* loading — spinner via ::after */ }
```

Missing-state rule: the styleguide page renders **every state
of every component**. A component without a `:disabled` example
on the styleguide is incomplete.

State classes are documented once in `tokens.css`-adjacent
comments, and reused everywhere — `is-loading` means the same
thing on a button, a card, a form, a feedback item.

---

## 5. Coexistence with Tailwind

This isn't a "rip out Tailwind" plan. The split system can sit
alongside Tailwind utilities indefinitely. Two coexistence
patterns:

**Pattern A — Tailwind for layout-at-the-call-site, custom CSS
for components.** Pages compose layout with utility strings
(`grid grid-cols-[16rem_1fr]`); elements inside use bespoke
component classes (`<button class="sn-button sn-button-primary">`).
This is the v2.0 model, just with a richer component layer.

**Pattern B — Custom CSS owns everything.** `sn-page-shell`,
`sn-dashboard-grid`, `sn-stack`, `sn-cluster` replace the
utility strings entirely. Tailwind's `preflight` and design
tokens still anchor the system, but no utility classes appear
in templates. Higher up-front cost, lower per-page cost long
term.

Pick one and commit. Mixing the two patterns inconsistently is
worse than either alone.

---

## 6. When to make the jump — decision criteria

Stay with v2.0's single-`input.css` model while **all** of these
hold:

- Total bespoke `sn-*` classes ≤ 10.
- Per-screen utility strings rarely exceed 6 classes per element.
- No screen has a custom animation longer than a 200ms transition.
- Designers (when we have any) say "Tailwind utilities are fine."

Promote to the multi-file architecture in §2 when **any two** of
these hold:

- More than 12 bespoke components, or `components.css` exceeds
  ~400 lines.
- We add a styling concern Tailwind doesn't cover well —
  multi-step gradients, layered shadows, custom keyframes,
  scroll-driven effects.
- Two components keep duplicating the same 10-class utility
  string.
- A designer or a visual identity guideline lands and the
  Tailwind palette stops being the source of truth.
- The styleguide page exceeds ~500 lines and is hard to skim.

Promote to **Pattern B (no inline utilities)** only with an ADR.
That's a one-way door.

---

## 7. Risks of going custom

Recording these honestly so future-me doesn't romanticize the
move:

- **Bigger surface to maintain.** Every component is now a thing
  the team owns end-to-end, including hover/focus/disabled.
- **Dead-class drift.** Utilities self-prune (Tailwind only
  emits used classes). Custom classes don't — `purgecss` or a
  manual audit becomes mandatory.
- **Onboarding cost.** New contributors learn the bespoke
  vocabulary before they can ship. Tailwind is recognized;
  `sn-feedback-item` is not.
- **Cross-doc drift.** `tokens.css`, `core-idea.md`, `css.md`,
  `tailwind.config.cjs`, and the styleguide must stay in
  lockstep. v2.0 already has four files in this sync; the split
  adds five more.
- **Specificity creep.** Without strict review, `sn-card .sn-button`
  selectors appear, and the specificity budget breaks. Once it
  breaks, it doesn't come back without a refactor.

The mitigation for every one of these is **the styleguide page +
the charter rules + visual regression tests**. Without those,
don't make the jump.

---

## 8. Cross-references

- [`../project/spec/v2/css.md`](../project/spec/v2/css.md) — the
  current (v2.0) CSS source of truth.
- [`frontend-conventions.md`](frontend-conventions.md) — long-form
  rationale for the v2.0 model; §3 covers naming, tokens, layout
  primitives.
- [`../project/spec/v2/core-idea.md`](../project/spec/v2/core-idea.md)
  — palette and brand brief.
- [ADR 056 — Style guide page](../adr/056-style-guide-page.md)
- [ADR 058 — Tailwind via Standalone CLI](../adr/058-tailwind-via-standalone-cli.md)

---

## 9. Why this lives in `notes/`

This is **direction**, not **decision**. Decisions belong in
ADRs; specs belong in `docs/project/spec/`. A future-direction
sketch with trade-offs and trigger conditions lives here, in
`notes/`, where it can evolve without dragging the v2.0 spec
through churn every time the idea is refined.

When (if) we commit to this architecture, the path is:

1. Write an ADR proposing the split (supersedes or complements
   ADR 058).
2. Promote this file's content into a new
   `docs/project/spec/v3/css.md` (or a v2.x addendum).
3. Demote *this* file to a historical-rationale note linking to
   the new spec.
4. Update [`frontend-conventions.md`](frontend-conventions.md)
   §8 cross-references and the rules in
   `.github/copilot-instructions.md`.

Until then: this is the parking lot.
