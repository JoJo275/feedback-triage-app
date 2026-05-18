<!-- WORKING COPY — edit freely, this does NOT affect .github/PULL_REQUEST_TEMPLATE.md -->
<!-- Use this file to draft your PR description before pasting it into GitHub. -->
<!-- Branch: wip/2026-05-07-scratch -->
<!--
  Suggested PR title (conventional commit format — type: description):

  fix: clear CodeQL log-injection alerts and backfill webhook/page/dashboard coverage

  Alternative:
  test: add targeted coverage for resend webhook, dashboard aggregator, and auth/page edge cases


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

<!-- Suggested labels: bug, area: api, area: logging, area: tests, type: security, type: test, status: ready-for-review -->

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

Brief description of the changes in this PR.

**What changes you made:**

**Why you made them:**

## Related Issue

<!-- Use one of: Fixes #123, Closes #123, Resolves #123, Related to #123 -->
<!-- If no issue exists, write "N/A" and briefly explain (e.g., maintenance, small refactor) -->

## Type of Change

- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [ ] ✨ New feature (non-breaking change that adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🔧 Refactor (no functional changes)
- [ ] 🧪 Test update

## How to Test

<!-- Help reviewers verify your changes. Don't make them guess! -->

**Steps:**

1.
2.
3.

**Test command(s):**

```bash
# e.g., pytest tests/test_feature.py -v
```

**Screenshots / Demo (if applicable):**

<!-- Add screenshots, GIFs, or video links to help explain your changes -->

## Risk / Impact

<!-- What's the blast radius? What could go wrong? -->

**Risk level:** Low / Medium / High

**What could break:**

**Rollback plan:** Revert this PR

<!-- Or: "Toggle feature flag X" / "Run migration Y" / etc. -->

## Dependencies (if applicable)

<!-- Delete this section if not applicable -->
<!-- List any PRs that must be merged before/after this one -->

**Depends on:** <!-- e.g., #456, or org/other-repo#123 -->

**Blocked by:** <!-- e.g., waiting for deployment of #456 -->

## Breaking Changes / Migrations (if applicable)

<!-- Delete this section if not applicable -->

- [ ] Config changes required
- [ ] Data migration needed
- [ ] API changes (document below)
- [ ] Dependency changes

**Details:**

## Checklist

- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] No new warnings (or explained in Additional Notes)
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] Relevant tests pass locally (or explained in Additional Notes)
- [ ] No security concerns introduced (or flagged for review)
- [ ] No performance regressions expected (or flagged for review)

## Reviewer Focus (Optional)

<!-- Save reviewer time: "Please pay close attention to X" -->

## Additional Notes

<!-- Any additional information that reviewers should know -->
