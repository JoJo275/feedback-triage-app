<!-- WORKING COPY — edit freely, this does NOT affect .github/PULL_REQUEST_TEMPLATE.md -->
<!-- Use this file to draft your PR description before pasting it into GitHub. -->
<!-- Branch: wip/2026-05-18-scratch -->
<!--
  Suggested PR title (conventional commit format — type: description):

  feat: advance react migration, dashboard APIs, and tooling governance docs


  Alternative:

  docs: consolidate architecture, operations, and tooling guidance for v2 migration


  Available prefixes:
    feat:     — new feature or capability
    fix:      — bug fix
    docs:     — documentation only
    chore:    — maintenance, no production code change
    refactor: — code restructuring, no behavior change
    test:     — adding or updating tests
    ci:       — CI/CD workflow changes
    style:    — formatting, no logic change
    perf:     — performance improvement
    build:    — build system or dependency changes
    revert:   — reverts a previous commit
-->

<!-- Suggested labels:  -->

<!--
  ╔══════════════════════════════════════════════════════════════╗
  ║  This PR description is for HUMAN REVIEWERS.                 ║
  ║                                                              ║
  ║  Release automation (release-please) reads individual        ║
  ║  commit messages on main — not this description.             ║
  ║  Write commits with conventional format (feat:, fix:, etc.)  ║
  ║  and include (#PR) or (#issue) references in each commit.    ║
  ║                                                              ║
  ║  This template captures: WHY you made changes, HOW to test   ║
  ║  them, and WHAT reviewers should focus on.                   ║
  ╚══════════════════════════════════════════════════════════════╝
-->

## Description

This PR advances the v2 migration and delivery framework across frontend runtime, dashboard flows, API integration, CI/quality gates, and architecture documentation.

**What changes you made:**

- Implemented and iterated on React/Vite migration phases, including `AppShell`, public app flows, authenticated route handling, and route context improvements.
- Added/expanded dashboard functionality: total signals behavior, dashboard summary API + widget, and workspace membership-aware app shell behavior.
- Added OpenAPI-to-TypeScript contract generation and frontend structure conventions, including related CI/workflow updates.
- Added and refined tests and test infrastructure updates, including Playwright coverage for authenticated React routes and snapshot/test maintenance.
- Expanded architecture docs and governance docs: ADR 079/080, background-processing boundaries, frontend conventions, production readiness, email framework, development framework, and tooling inventory.
- Added and refined tool-template documentation workflow under `docs/tooling/`.

**Why you made them:**

- Move the project toward the ratified v2 architecture with clearer ownership boundaries and safer incremental rollout.
- Improve developer velocity and reviewability by codifying tool responsibilities, adoption order, and operating constraints.
- Reduce operational and release risk with stronger CI quality gates, documentation rigor, and explicit observability/reliability guidance.

## Related Issue

<!-- Use one of: Fixes #123, Closes #123, Resolves #123, Related to #123 -->
<!-- If no issue exists, write "N/A" and briefly explain (e.g., maintenance, small refactor) -->

N/A — this branch is a stacked migration and documentation stream spanning frontend implementation plus architecture/operations docs hardening.

## Type of Change

- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [x] ✨ New feature (non-breaking change that adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [x] 📚 Documentation update
- [x] 🔧 Refactor (no functional changes)
- [x] 🧪 Test update

## How to Test

<!-- Help reviewers verify your changes. Don't make them guess! -->

**Steps:**

1. Sync and install dependencies.
2. Run backend/frontend checks used across this branch.
3. Run docs strict build and pre-push security hook parity checks.

**Test command(s):**

```bash
uv sync
uv run pytest -m "not e2e"
npm --prefix web run typecheck
npm --prefix web run test
npm --prefix web run build
uv run mkdocs build --strict
pre-commit run pip-audit --hook-stage pre-push --all-files
```

**Screenshots / Demo (if applicable):**

<!-- Add screenshots, GIFs, or video links to help explain your changes -->

N/A for this draft (mixed implementation + docs branch).

## Risk / Impact

<!-- What's the blast radius? What could go wrong? -->

**Risk level:** Medium

**What could break:**

- Frontend route shell assumptions during migration (authenticated/public route behavior).
- API contract drift if generated OpenAPI TS types are not refreshed with API changes.
- Dashboard summary/widget expectations if backend and frontend assumptions diverge.
- Documentation consistency across `tooling.md`, development framework, and architecture docs.

**Rollback plan:** Revert this PR

<!-- Or: "Toggle feature flag X" / "Run migration Y" / etc. -->

## Dependencies (if applicable)

<!-- Delete this section if not applicable -->
<!-- List any PRs that must be merged before/after this one -->

**Depends on:** <!-- e.g., #456, or org/other-repo#123 -->

None.

**Blocked by:** <!-- e.g., waiting for deployment of #456 -->

None.

## Breaking Changes / Migrations (if applicable)

<!-- Delete this section if not applicable -->

- [ ] Config changes required
- [ ] Data migration needed
- [ ] API changes (document below)
- [ ] Dependency changes

**Details:**

No required breaking migration/config steps expected for merge. API additions were made during branch development but are intended to be non-breaking in this stream.

## Checklist

- [x] My code follows the project's style guidelines
- [x] I have performed a self-review of my code
- [x] I have commented my code, particularly in hard-to-understand areas
- [x] I have made corresponding changes to the documentation
- [x] No new warnings (or explained in Additional Notes)
- [x] I have added tests that prove my fix is effective or that my feature works
- [x] Relevant tests pass locally (or explained in Additional Notes)
- [x] No security concerns introduced (or flagged for review)
- [x] No performance regressions expected (or flagged for review)

## Reviewer Focus (Optional)

<!-- Save reviewer time: "Please pay close attention to X" -->

- React migration boundaries between `AppShell`/public app routes and backend APIs.
- Dashboard summary API/widget contract assumptions and test coverage.
- Architecture-document consistency across tooling inventory, development framework, and background-processing/email/operations docs.
- CI workflow changes affecting lock refresh and frontend quality gates.

## Additional Notes

<!-- Any additional information that reviewers should know -->

### Commit coverage (all commits on `main..wip/2026-05-18-scratch`)

1. `2d56435` feat: enhance total signals widget and dashboard interactions
2. `fc49e56` refactor: remove alias for seed:demo in Taskfile
3. `bdd3d54` feat(phase-0): initialize feedback triage web application with React and Vite detailed in react-full-migration.md
4. `c423ce4` feat(phase-1): Implement AppShell component with layout and navigation
5. `44613e5` feat: add commenting expectations to Copilot instructions
6. `bede0cd` feat(phase-2): enhance AppShell with dynamic section labels and update telemetry for API errors
7. `5cafc16` feat(phase-2): update implementation status and add Playwright tests for authenticated React routes
8. `01496b7` feat(phase-3): implement PublicApp component for public feedback submission and roadmap display
9. `b1de650` feat(phase-4): Refactor React frontend tests and components to remove legacy URL handling
10. `f5eaf95` feat: refactor route context handling in App component and update AppShell snapshot
11. `80a0059` chore: update dependencies and improve test snapshots
12. `3d98ae6` feat(dashboard): Implement dashboard summary API and React widget
13. `a2d1683` feat: pinned node base image digest in containerfile, Added OpenAPI-to-TypeScript generation, Add structure convention for React features
14. `0337b46` feat: enhance dashboard and app shell with workspace membership handling and UI updates
15. `626d4f8` feat: add ADR 079 for umbrella React baseline in v2 frontend architecture
16. `e5e2f31` feat: add UV lock drift and refresh workflows for dependency management
17. `3a78c38` feat: update UV Lock Refresh workflow triggers to include push events for path-filtered changes
18. `1cb91bc` feat: enhance documentation with React frontend conventions and update command reference
19. `b1119f0` feat: update React frontend instructions to enhance hook usage guidance and API layering
20. `0cbf711` feat: update CI workflows to enhance frontend quality gates and remove path filtering
21. `fc18da4` feat: add dependency tooling questionnaire and update README for new document
22. `86cc1b7` feat: add critical UI regression paths and test priority matrix for enhanced coverage
23. `22d72e9` feat: enhance documentation structure with conventions and archive sections
24. `de035cb` feat(docs): update command reference and tooling documentation
25. feat(docs): add background processing architecture and tooling guidance
26. `24ad4db` feat(docs): update background processing architecture with current task-to-tool mapping and guidelines
27. `810d1ce` feat(docs): add ADR 080 for staged background-processing boundaries and update related documentation
28. `542ee8a` feat(docs): update ADR 080 with task-to-tool mapping guidelines and rejections for tool selection
29. `30c7c13` feat(docs): expand ADR 080 with decision boundaries for Temporal, Celery, and RabbitMQ usage
30. `55da59f` feat(docs): enhance background processing architecture and add state management boundaries documentation
31. `65302e1` feat(docs): expand frontend frameworks comparison with Laravel, Django, and Ruby on Rails details
32. `17b9a9e` feat(docs): add tooling and conventions mapping to Copilot instructions
33. `b90f571` feat(docs): add recommended tool matrix with usage guidelines and best practices
34. `cc20dac` feat(docs): update tooling inventory with detailed tool descriptions and usage guidelines
35. `537280b` feat(docs): enhance tooling inventory with additional tools and usage guidelines
36. `6e37e2b` feat(docs): added tools status, concrete references, linking, and tightened phrasing in tooling.md
37. `cfc2856` feat(docs): add recommended adoption order for planned tools in tooling.md
38. `8396e9c` feat(docs): expand tooling inventory with reliability and delivery operations section
39. `cc52395` feat(docs): Added scope column to all tooling tables in tooling.md
40. `049173d` feat(docs): add .gitkeep file to operations directory and update tooling.md with Node.js entry
41. `15cea1a` feat(docs): update tooling.md with detailed descriptions for Tailwind CSS, add hadolint and Prettier, and include markdownlint-cli2 for documentation consistency
42. `ee0e104` feat(docs): reorganize tooling.md with separate adoption orders for core architecture and commercial readiness
43. `40dd8ce` feat(docs): add production readiness documentation and update command reference timestamp
44. `66239dc` feat(docs): add email framework documentation and update development framework references
45. `917bb38` feat(docs): enhance email framework documentation with implementation workflows and context conventions
46. `58f09ee` feat(docs): enhance development framework with error telemetry and logging guidelines
47. `eba9fb9` feat(docs): add k6 performance testing scenarios and feature flag governance guidelines
48. `1472693` feat(docs): add tool templates for documenting tools and general usage guidelines
49. `f3573a3` feat(docs): add tool template for documenting tools in the repository
50. `6848dec` feat(docs): update tool template with structured sections and placeholders for better documentation
51. `599a6df` feat(docs): enhance tool template with structured sections and placeholders for improved documentation
52. `1db8ea8` docs: populate PR draft with full branch commit coverage
53. Security follow-up in this branch: upgraded `starlette` in `uv.lock` from `1.0.0` to `1.0.1` to address `PYSEC-2026-161` and unblock pre-push `pip-audit`.

### Pre-push security note

`pip-audit` was re-run via pre-commit pre-push hook and currently passes:

```bash
pre-commit run pip-audit --hook-stage pre-push --all-files
```
