# ADR 078: Make web build and widget parity required release gates

## Status

Accepted

## Context

After the React/Vite runtime shift ([ADR 077](077-use-react-vite-as-v2-page-runtime.md)),
the project still carries release-process assumptions from the
vanilla-first phase:

- primary quality gates remain Python-centric,
- generated React assets can drift from source intent,
- dashboard widget parity can regress without a dedicated gate,
- frontend ownership boundaries are not explicit enough for
  high-churn surfaces.

This directly affects confidence in the dashboard surface, where prior
widget behavior has already been lost during route/runtime migration.

## Decision

Promote frontend build correctness and dashboard widget parity to required
release gates.

1. `web/src` is the source of truth for React UI behavior.
2. `src/feedback_triage/static/app/` is generated build output from
   `npm --prefix web run build`; it is never treated as hand-authored code.
3. The default quality gate must include web lint, typecheck, unit tests,
   and web build verification.
4. The production image build path must include a deterministic web asset
   build step (or consume an equivalent CI-produced artifact) so runtime
   assets cannot drift from source.
5. Dashboard widget behavior is a release gate, not an optional visual tweak.
   Any route/runtime swap must pass widget parity checks before rollout.
6. Widget implementation ownership is explicit: dashboard widget code lives in a
   dedicated feature area under `web/src` rather than in monolithic page files.

## Alternatives Considered

### Keep frontend checks in a separate, optional workflow

Leave web checks outside default quality gates and rely on ad hoc frontend validation.

**Rejected because:** Frontend is now a primary runtime path, so optional checks permit regressions on core user journeys.

### Keep generated assets as de facto source of truth

Treat `static/app` outputs as the practical implementation baseline and avoid strict rebuild parity.

**Rejected because:** Generated artifacts hide intent and make regressions harder to detect and review.

## Consequences

### Positive

- Frontend regressions are caught before merge/deploy.
- Dashboard widget behavior gets explicit release protection.
- Build/release reproducibility improves across local, CI, and container flows.

### Negative

- CI/runtime checks become slower and stricter.
- More up-front process overhead on frontend changes.
- Requires follow-through on task/workflow/container wiring.

### Neutral

- Backend API contracts, tenancy model, and DB invariants are unchanged.
- Existing React route contract remains in place.

### Mitigations

- Keep web checks parallelized in CI where possible.
- Scope parity checks to high-risk user paths (dashboard/widget interactions).
- Document ownership boundaries and expiry criteria for transitional flags.

## Implementation

- [Taskfile.yml](../../Taskfile.yml) - include web checks in the default gate.
- [Containerfile](../../Containerfile) - add deterministic web asset build to image pipeline.
- [.github/workflows/web-frontend.yml](../../.github/workflows/web-frontend.yml) - keep dedicated web checks and align path filters with current route/template locations.
- [docs/project/spec/v2/implementations/react-full-migration.md](../project/spec/v2/implementations/react-full-migration.md) - route parity and migration gates.
- [docs/project/spec/v2/implementations/total-signals-widget.md](../project/spec/v2/implementations/total-signals-widget.md) - widget behavior contract baseline.
- [web/src/App.tsx](../../web/src/App.tsx) - temporary monolith to split behind feature ownership.

## References

- [ADR 077](077-use-react-vite-as-v2-page-runtime.md)
- [ADR 076](076-use-react-island-for-dashboard-widgets.md)
- [v2 implementation plan](../project/spec/v2/implementation.md)
- [React full migration plan](../project/spec/v2/implementations/react-full-migration.md)
