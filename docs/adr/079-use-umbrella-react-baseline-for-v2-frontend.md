# ADR 079: Use an umbrella React baseline for v2 frontend architecture

---

## Status

Accepted

## Context

ADR 076 captured a limited React-island pilot and is now superseded.
ADR 077 accepted React + Vite as the v2 page runtime, and ADR 078
added required release/process gates for web build correctness and
widget parity.

Those ADRs are still correct, but they answer different slices of the
same architectural shift. Review and onboarding discussions still
regularly ask whether the project fully transferred to React or only
adopted React for specific components.

The project needs one umbrella ADR that explicitly states the current
frontend baseline, preserves the decision history in 076/077/078, and
defines ownership boundaries after migration.

## Decision

Use this ADR as the umbrella architecture record for the v2 React
transfer.

1. Keep ADR 076 as historical pilot context (already superseded).
2. Keep ADR 077 as the runtime decision and ADR 078 as the release-gate
   decision; neither is replaced or rewritten.
3. Treat React + Vite as the default page runtime for migrated
   workspace/public routes, with `web/` as source of truth and
   `src/feedback_triage/static/app/` as generated output.
4. Keep FastAPI as the server/runtime boundary for auth, tenancy,
   route access control, API contracts, and static asset serving.
5. Allow intentionally server-rendered routes where explicitly scoped
   (for example auth flows or other non-migrated surfaces).
6. Require any proposal to reintroduce mixed-runtime defaults or to
   undo the React runtime baseline to ship as a new ADR.

## Alternatives Considered

### Supersede ADR 077 and ADR 078 with a single replacement ADR

Collapse runtime and release-gate decisions into one new document.

**Rejected because:** This would erase useful decision history and blur
why runtime choice and release gates were split in the first place.

### Keep current ADR set without an umbrella decision

Leave migration context distributed across ADR 076/077/078 and
implementation docs only.

**Rejected because:** It keeps architecture intent fragmented and
continues the recurring ambiguity about whether React adoption is
project-wide or component-scoped.

### Revert to vanilla-first routing as the baseline

Treat React as optional and return to server-rendered HTML + vanilla JS
as the default for v2 page surfaces.

**Rejected because:** This conflicts with accepted ADR 077 and would
reintroduce migration churn and parity risk without product benefit.

## Consequences

### Positive

- One canonical ADR now explains the full React transfer posture.
- Existing ADRs keep their original scope and rationale intact.
- Contributors get clear boundaries for where frontend changes belong.

### Negative

- Another ADR must stay synchronized with spec and migration docs.
- Readers now have one extra document in the React ADR chain.

### Neutral

- Backend architecture (FastAPI, SQLModel, auth/session model,
  tenancy invariants, `/api/v1` contracts) is unchanged.
- Existing acceptance status of ADRs 076/077/078 is unchanged.

### Mitigations

- Cross-link this ADR from spec and migration records.
- Keep implementation links explicit so readers can jump directly from
  decision to code paths.

## Implementation

- [docs/adr/076-use-react-island-for-dashboard-widgets.md](076-use-react-island-for-dashboard-widgets.md) - historical pilot scope retained.
- [docs/adr/077-use-react-vite-as-v2-page-runtime.md](077-use-react-vite-as-v2-page-runtime.md) - runtime decision retained.
- [docs/adr/078-make-web-build-and-widget-parity-required-gates.md](078-make-web-build-and-widget-parity-required-gates.md) - release-gate decision retained.
- [docs/project/spec/spec-v2.md](../project/spec/spec-v2.md) - v2 ADR table includes umbrella reference.
- [docs/project/spec/v2/ui.md](../project/spec/v2/ui.md) - page/runtime contract baseline.
- [docs/project/spec/v2/tooling.md](../project/spec/v2/tooling.md) - React/Vite toolchain baseline.
- [docs/project/spec/v2/implementations/react-full-migration.md](../project/spec/v2/implementations/react-full-migration.md) - migration record and parity gates.
- [web/src/main.tsx](../../web/src/main.tsx) - frontend entrypoint for migrated routes.
- [src/feedback_triage/pages/react_shell.py](../../src/feedback_triage/pages/react_shell.py) - shared React shell rendering.
- [src/feedback_triage/templates/pages/react/workspace_shell.html](../../src/feedback_triage/templates/pages/react/workspace_shell.html) - authenticated shell bootstrap.
- [src/feedback_triage/templates/pages/react/public_shell.html](../../src/feedback_triage/templates/pages/react/public_shell.html) - public shell bootstrap.

## References

- [ADR 076](076-use-react-island-for-dashboard-widgets.md)
- [ADR 077](077-use-react-vite-as-v2-page-runtime.md)
- [ADR 078](078-make-web-build-and-widget-parity-required-gates.md)
- [Spec v2.0](../project/spec/spec-v2.md)
- [React full migration record](../project/spec/v2/implementations/react-full-migration.md)
