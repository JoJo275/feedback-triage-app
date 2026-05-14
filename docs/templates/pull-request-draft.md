<!-- WORKING COPY — edit freely, this does NOT affect .github/PULL_REQUEST_TEMPLATE.md -->
<!-- Use this file to draft your PR description before pasting it into GitHub. -->
<!-- Branch:  -->
<!--
  Suggested PR title (conventional commit format — type: description):



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

This PR is an integration branch that is currently 34 commits ahead of `origin/main`.
It combines v2 UI/UX progress, backend support changes, docs/spec updates, and a React
widget-editor pilot for the dashboard, plus this session's stabilization and planning updates.

**What changes you made:**

- Added dashboard React widget-editor pilot route/page/script and wired classic dashboard edit action to open the React editor.
- Added layout compatibility sync so React editor layout writes are reflected in classic dashboard layout storage.
- Added cache-busted dashboard script URLs and explicit edit-button labeling to reduce stale-asset confusion.
- Updated page-route tests to match current HTML 404 behavior for unknown workspace slugs.
- Added ADR 076 and linked v2 spec/ADR indexes for the React dashboard pilot.
- Added implementation docs for dashboard React path and dashboard vanilla stabilization path.
- Added a new project-wide React migration implementation plan:
  - `docs/project/spec/v2/implementations/react-full-migration.md`
- Included broad branch work already present (auth/theme preferences, Resend webhook ingestion, branding assets, layout/navigation updates, roadmap/changelog/inbox/dashboard iteration, scripts/tooling, docs restructuring, migrations, and tests).

**Why you made them:**

- Deliver v2 final-phase UX and platform improvements already developed on this branch.
- Validate a low-risk React adoption path through a scoped dashboard pilot before any full rewrite decision.
- Fix push-blocking test failures caused by outdated JSON expectations on HTML page-route 404s.
- Document a concrete full React migration path so future work is staged, testable, and reversible.

## Related Issue

N/A - integration branch consolidating ongoing v2 implementation work.

## Type of Change

- [x] 🐛 Bug fix (non-breaking change that fixes an issue)
- [x] ✨ New feature (non-breaking change that adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [x] 📚 Documentation update
- [ ] 🔧 Refactor (no functional changes)
- [x] 🧪 Test update

## How to Test

<!-- Help reviewers verify your changes. Don't make them guess! -->

**Steps:**

1. Sync dependencies and run migrations.
2. Run tests and verify all suites pass.
3. Start app and verify dashboard edit flow goes to `/w/<slug>/dashboard/react` and saves layout.
4. Verify page-route unknown-slug tests now assert 404 status only.
5. Review docs changes, including ADR 076 and the new full React migration plan.

**Test command(s):**

```bash
uv run pytest -q
uv run pytest tests/api/test_changelog_page.py tests/api/test_public_changelog.py tests/api/test_public_roadmap.py tests/api/test_roadmap_page.py -q
task docs:build
```

Observed in this session:

- Full suite: 333 passed, 0 failed.
- Targeted failing group after fix: 19 passed, 0 failed.

**Screenshots / Demo (if applicable):**

<!-- Add screenshots, GIFs, or video links to help explain your changes -->
N/A in this draft.

## Risk / Impact

<!-- What's the blast radius? What could go wrong? -->

**Risk level:** High

**What could break:**

- Tenant-scoped page routing and auth-gated page access.
- Dashboard widget editing behavior across classic and React flows.
- Migration/order assumptions for Alembic revisions in this branch.
- Frontend parity on roadmap/changelog/inbox/settings surfaces due broad template/CSS/JS churn.

**Rollback plan:** Revert this PR

<!-- Or: "Toggle feature flag X" / "Run migration Y" / etc. -->

## Dependencies (if applicable)

<!-- Delete this section if not applicable -->
<!-- List any PRs that must be merged before/after this one -->

**Depends on:** none (self-contained branch)

**Blocked by:** none

## Breaking Changes / Migrations (if applicable)

<!-- Delete this section if not applicable -->

- [x] Config changes required
- [x] Data migration needed
- [x] API changes (document below)
- [ ] Dependency changes

**Details:**

- Config/env surface updated (for example `.env.example` additions already in branch).
- New Alembic revisions in branch:
  - `0006_users_theme_preference.py`
  - `0007_email_status_webhook_values.py`
  - `0008_feedback_assignee_user.py`
- API additions/changes include user preference endpoint(s) and Resend webhook ingestion route(s).

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

- Confirm dashboard edit flow: classic page -> React editor, and persisted layout compatibility.
- Confirm page-route 404 behavior expectations in tests (HTML page-route behavior vs API JSON envelope).
- Confirm ADR/spec/doc coherence for React pilot vs full-react migration proposal.
- Confirm migration ordering and operational safety for Alembic revisions already in branch.

## Additional Notes

<!-- Any additional information that reviewers should know -->

Current branch info:

- Branch: `wip/2026-05-07-scratch`
- Upstream: `origin/wip/2026-05-07-scratch`
- Ahead of upstream: 34 commits

Commits ahead of `origin/main` (as of draft update):

```text
1c72e80 feat(dashboard): update edit button to link to React widget editor and enhance accessibility
0f45718 feat(dashboard): integrate React island for widget editing and sync layouts
bada2e1 feat: add React widgets pilot to dashboard
feat: update dashboard widget documentation; clarify React implementation and layout configuration
bd9fd7d feat: implement dashboard widget system; establish layout management and responsive behavior
7af89d1 feat: enhance widget layout normalization; improve placement logic and geometry handling
feat: refine widget resizing logic; adjust minimum row sizes and enhance grid metrics calculations
80022e1 feat: improve widget placement logic; enhance active widget identification and snapping behavior
8828f30 feat: enhance dashboard layout customization; improve drag-and-drop activation and widget placement logic
d34434a feat: refine dashboard widget layout logic; improve drag-and-drop handling and spacing
73f3e6c feat: enhance drag-and-drop functionality; improve widget drag shadow and layout responsiveness
f90f549 feat: enhance dashboard layout and widget management; improve drag-and-drop functionality and responsiveness
219e9fd feat: Enhance dashboard layout and interactivity
62f5dc6 feat: update dashboard content gutter styles; adjust width and padding for improved layout
2100187 feat: improve layout spacing and responsiveness; enhance CSS for dashboard components
9a9d315 feat: enhance dashboard layout and functionality
cacfc8f feat: refine dashboard layout and content; enhance clarity on operational metrics and user actions
27d2df4 feat: update dashboard layout and success criteria; enhance clarity on metrics and action priorities
5cf9e8d feat: enhance testing infrastructure with new test database reset script and configuration; update .env.example for test database URL
0d542d8 feat: enhance dashboard with source breakdown, new filters, and improved layout; update tests for new functionality
1938c88 feat: update demo owner email in workspace seeding and documentation; enhance button styles and accessibility in auth pages
3bc3485 feat: update authentication pages with new design and password toggle functionality; enhance workspace seeding with demo owner
3b7a9b0 feat: add accounts.md for centralized account identity management and update references in related spec files
1358aec feat: enhance dashboard and landing page with integrated VS Code workflow and new footer design
8a53779 feat: implement system error pages and enhance dashboard redirection for authenticated users. Improved dev workflow with improved "task dev:all" command
54308cb docs(refactor): refactor documentation references from `pages.md` to `information-architecture.md`
6c2f42a feat: add workspace-scoped feedback creation and enhance landing page
eed2a3a feat: Enhance sidebar and layout for authenticated app shell (PR 4.5)
8fd2cc2 feat(env): add APP_BASE_URL and SECURE_COOKIES variables for configuration
472cc5e feat(docs): add live-preview loop documentation for local development workflow
4bd4dc3 feat(branding): pr 4.4 - add custom favicon and wordmark SVG; update templates for new assets
6cce078 feat(email): pr 4.3 - implement Resend webhook for delivery status ingestion and update email_log status
a200d76 feat(ui): pr 4.2 - implement styleguide theme preset switcher with localStorage persistence
538f59a feat: pr 4.1 - add user theme preference functionality with API endpoint and persistence
```

Files changed vs `origin/main` (name-status):

```text
M       .env.example
M       Containerfile
M       Taskfile.yml
A       alembic/versions/0006_users_theme_preference.py
A       alembic/versions/0007_email_status_webhook_values.py
A       alembic/versions/0008_feedback_assignee_user.py
M       docs/adr/064-pain-vs-priority-dual-fields.md
A       docs/adr/076-use-react-island-for-dashboard-widgets.md
M       docs/adr/README.md
M       docs/guide/dashboard-guide.md
M       docs/notes/css-learning.md
M       docs/notes/custom-css-architecture.md
M       docs/project/spec/spec-v2.md
M       docs/project/spec/v2/README.md
A       docs/project/spec/v2/accounts.md
M       docs/project/spec/v2/adrs.md
M       docs/project/spec/v2/auth.md
M       docs/project/spec/v2/copy-style-guide.md
M       docs/project/spec/v2/core-idea.md
M       docs/project/spec/v2/css.md
A       docs/project/spec/v2/images/Dashboard Mockup 1.jpg
M       docs/project/spec/v2/implementation.md
A       docs/project/spec/v2/implementations/dashboard-vanilla-js.md
A       docs/project/spec/v2/implementations/dashboard.md
R055    docs/project/spec/v2/pages.md   docs/project/spec/v2/information-architecture.md
A       docs/project/spec/v2/layout.md
A       docs/project/spec/v2/layouts/README.md
A       docs/project/spec/v2/layouts/dashboard.md
A       docs/project/spec/v2/live-preview.md
M       docs/project/spec/v2/testing-strategy.md
M       docs/project/spec/v2/theming.md
M       docs/reference/commands.md
M       mkdocs.yml
A       scripts/seed_workspace.py
M       src/feedback_triage/api/v1/_feedback_schemas.py
M       src/feedback_triage/api/v1/feedback.py
A       src/feedback_triage/api/v1/users.py
A       src/feedback_triage/api/v1/webhooks/__init__.py
A       src/feedback_triage/api/v1/webhooks/resend.py
M       src/feedback_triage/auth/schemas.py
M       src/feedback_triage/auth/service.py
M       src/feedback_triage/config.py
M       src/feedback_triage/enums.py
M       src/feedback_triage/errors.py
M       src/feedback_triage/main.py
M       src/feedback_triage/models/feedback.py
M       src/feedback_triage/models/users.py
M       src/feedback_triage/pages/auth.py
M       src/feedback_triage/pages/changelog.py
M       src/feedback_triage/pages/dashboard.py
M       src/feedback_triage/pages/inbox.py
M       src/feedback_triage/pages/insights.py
M       src/feedback_triage/pages/landing.py
M       src/feedback_triage/pages/legal.py
M       src/feedback_triage/pages/public_changelog.py
M       src/feedback_triage/pages/public_roadmap.py
M       src/feedback_triage/pages/roadmap.py
M       src/feedback_triage/pages/settings.py
M       src/feedback_triage/pages/submitters.py
A       src/feedback_triage/pages/system.py
M       src/feedback_triage/services/dashboard_aggregator.py
A       src/feedback_triage/services/email_log_updater.py
M       src/feedback_triage/static/css/components.css
M       src/feedback_triage/static/css/effects.css
M       src/feedback_triage/static/css/input.css
M       src/feedback_triage/static/css/layout.css
M       src/feedback_triage/static/css/tokens.css
A       src/feedback_triage/static/img/apple-touch-icon.png
A       src/feedback_triage/static/img/favicon.ico
A       src/feedback_triage/static/img/favicon.svg
A       src/feedback_triage/static/img/wordmark.svg
M       src/feedback_triage/static/js/auth.js
A       src/feedback_triage/static/js/dashboard.js
A       src/feedback_triage/static/js/dashboard_react_widgets.js
A       src/feedback_triage/static/js/feedback_new.js
A       src/feedback_triage/static/js/styleguide.js
M       src/feedback_triage/static/js/theme.js
M       src/feedback_triage/templates/_base.html
M       src/feedback_triage/templates/_partials/footer.html
A       src/feedback_triage/templates/_partials/header.html
M       src/feedback_triage/templates/_partials/sidebar.html
M       src/feedback_triage/templates/pages/auth/forgot_password.html
M       src/feedback_triage/templates/pages/auth/login.html
M       src/feedback_triage/templates/pages/auth/reset_password.html
M       src/feedback_triage/templates/pages/auth/signup.html
M       src/feedback_triage/templates/pages/auth/verify_email.html
M       src/feedback_triage/templates/pages/changelog.html
M       src/feedback_triage/templates/pages/dashboard/empty.html
M       src/feedback_triage/templates/pages/dashboard/index.html
A       src/feedback_triage/templates/pages/dashboard/react_widgets.html
A       src/feedback_triage/templates/pages/feedback_new.html
M       src/feedback_triage/templates/pages/inbox.html
M       src/feedback_triage/templates/pages/insights.html
M       src/feedback_triage/templates/pages/landing.html
M       src/feedback_triage/templates/pages/roadmap.html
M       src/feedback_triage/templates/pages/settings/index.html
M       src/feedback_triage/templates/pages/submitters/list.html
A       src/feedback_triage/templates/pages/system/error.html
M       src/feedback_triage/templates/styleguide.html
M       tailwind.config.cjs
M       tests/api/auth/test_dashboard_page.py
M       tests/api/test_dashboard_summary.py
M       tests/api/test_feedback_v2.py
A       tests/api/test_resend_webhook.py
A       tests/api/test_users_preferences.py
M       tests/conftest.py
M       tests/e2e/test_a11y.py
M       tests/test_pages.py
A       tools/dev_tools/dev_all_supervisor.py
A       tools/dev_tools/test_db_reset.py
```

Current uncommitted changes in working tree (included in this draft):

```text
M docs/project/spec/spec-v2.md
M docs/project/spec/v2/implementations/dashboard.md
A docs/project/spec/v2/implementations/react-full-migration.md
M docs/templates/pull-request-draft.md
M tests/api/test_changelog_page.py
M tests/api/test_public_changelog.py
M tests/api/test_public_roadmap.py
M tests/api/test_roadmap_page.py
```
