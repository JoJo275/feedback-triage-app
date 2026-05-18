<!-- WORKING COPY — edit freely, this does NOT affect .github/PULL_REQUEST_TEMPLATE.md -->
<!-- Use this file to draft your PR description before pasting it into GitHub. -->
<!-- Branch: wip/2026-05-14-scratch -->
<!--
  Suggested PR title (conventional commit format — type: description):

feat(dashboard): finalize total-signals widget behavior and harden react migration docs

  Alternative:


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

<!-- Suggested labels: area: dashboard, area: frontend, area: docs, type: feature, type: test, status: ready-for-review -->

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

This PR finalizes the v2 Total signals dashboard card behavior and visual treatment,
then updates migration documentation so the React full-migration track is execution-ready
once its ADR gate is approved.

**What changes you made:**

- Implemented and iteratively refined the Total signals card in the dashboard, including:
  sparkline drawing/interaction, marker labeling, delta icon rendering, card spacing,
  focus/hover states, and click-through behavior.
- Added and refined inbox badge SVG assets used by the Total signals title/icon treatment.
- Updated dashboard and summary-card styling for readability, alignment, and interaction parity.
- Updated docs for Total signals implementation and canonical color governance.
- Expanded the full React migration plan with:
  switch recommendation criteria, explicit pros/cons, execution baselines,
  route-level parity gates, feature-flag ownership/expiry, and rollout safeguards.
- Updated targeted dashboard API test coverage to keep parity checks enforceable.

**Why you made them:**

- Lock in shipped Total signals behavior as a stable, testable UI contract.
- Reduce ambiguity and rollout risk for any future full React migration decision.
- Ensure the branch leaves both implementation and documentation in reviewer-ready shape.

## Related Issue

<!-- Use one of: Fixes #123, Closes #123, Resolves #123, Related to #123 -->
<!-- If no issue exists, write "N/A" and briefly explain (e.g., maintenance, small refactor) -->

N/A - branch-scoped UI and documentation hardening work tied to v2 implementation docs.

## Type of Change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [x] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [x] Documentation update
- [x] Refactor (no functional changes)
- [x] Test update

## How to Test

<!-- Help reviewers verify your changes. Don't make them guess! -->

**Steps:**

1. Start local dependencies and app (`task up`, `task migrate`, `task dev`).
2. Log in and open `/w/<slug>/dashboard`; verify Total signals card:
   icon, delta row, sparkline hover interaction, marker wording, card click target,
   keyboard focus visibility, and pointer cursor behavior.
3. Validate targeted dashboard tests and summary aggregation tests.
4. Review updated docs for migration readiness and consistency.

**Test command(s):**

```bash
uv run pytest tests/api/auth/test_dashboard_page.py
uv run pytest tests/api/test_dashboard_summary.py
```

**Executed in this branch snapshot:**

- `tests/api/auth/test_dashboard_page.py` + `tests/api/test_dashboard_summary.py`
- Result: 17 passed, 0 failed

**Screenshots / Demo (if applicable):**

<!-- Add screenshots, GIFs, or video links to help explain your changes -->

- `docs/project/spec/v2/images/total-signals-widget-final.png`

## Risk / Impact

<!-- What's the blast radius? What could go wrong? -->

**Risk level:** Medium

**What could break:**

- Dashboard summary card layout regressions on narrow/medium breakpoints.
- Sparkline hit-testing and marker placement regressions.
- CSS interactions (hover/focus/cursor) diverging from expected behavior.
- Doc/plan drift if migration assumptions are changed without ADR updates.

**Rollback plan:**

- Revert this PR.
- If partial deployment exists, restore previous dashboard template/CSS/JS assets and disable any related frontend flag rollout.

<!-- Or: "Toggle feature flag X" / "Run migration Y" / etc. -->

## Dependencies (if applicable)

<!-- Delete this section if not applicable -->
<!-- List any PRs that must be merged before/after this one -->

**Depends on:** <!-- e.g., #456, or org/other-repo#123 -->

N/A

**Blocked by:** <!-- e.g., waiting for deployment of #456 -->

N/A

## Breaking Changes / Migrations (if applicable)

<!-- Delete this section if not applicable -->

- [ ] Config changes required
- [ ] Data migration needed
- [ ] API changes (document below)
- [ ] Dependency changes

**Details:**

None expected. No database migration included in this branch.

## Checklist

- [x] My code follows the project's style guidelines
- [x] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [x] I have made corresponding changes to the documentation
- [ ] No new warnings (or explained in Additional Notes)
- [x] I have added tests that prove my fix is effective or that my feature works
- [x] Relevant tests pass locally (or explained in Additional Notes)
- [x] No security concerns introduced (or flagged for review)
- [ ] No performance regressions expected (or flagged for review)

## Reviewer Focus (Optional)

<!-- Save reviewer time: "Please pay close attention to X" -->

- Confirm Total signals behavioral parity: click target, icon placement, delta semantics,
  marker wording, hover/cursor behavior, and keyboard focus affordances.
- Check sparkline math/rendering changes for edge cases (small sample sizes, flat trends,
  high variance periods).
- Review migration-doc updates for internal consistency and actionability.
- Spot-check CSS/layout changes on desktop and mobile breakpoints.

## Additional Notes

<!-- Any additional information that reviewers should know -->

- Commit range reviewed for this draft: 64 commits on `wip/2026-05-14-scratch` relative to `origin/main`.
- Highest-churn files in this branch:
  - `src/feedback_triage/templates/pages/dashboard/index.html`
  - `src/feedback_triage/static/css/components.css`
  - `src/feedback_triage/static/js/dashboard.js`
  - `tests/api/auth/test_dashboard_page.py`
  - `docs/project/spec/v2/implementations/total-signals-widget.md`
