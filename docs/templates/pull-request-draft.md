<!-- WORKING COPY — edit freely, this does NOT affect .github/PULL_REQUEST_TEMPLATE.md -->
<!-- Use this file to draft your PR description before pasting it into GitHub. -->
<!-- Branch: wip/2026-05-06-scratch -->
<!--
  Suggested PR title (conventional commit format — type: description):

    feat(v2): close Phase 2 (Beta) — triage core, public submit, settings, submitters + stale + axe-core

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

<!-- Suggested labels: v2.0, phase-2, triage, public-submit, settings, submitters, a11y, schema-migration -->

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

Lands every Phase 2 (Beta) slice from
[`docs/project/spec/v2/implementation.md`](../../docs/project/spec/v2/implementation.md)
on a single integration branch and closes the phase. After this PR
the v2 triage surface is functionally complete: a workspace owner
can sign up, see an inbox of feedback, drill into a detail page,
manage tags and notes, expose a public submission form, and see
who submitted what — with cross-tenant isolation, stale-item
highlighting, and an automated a11y gate.

**What changes you made:**

- **PR 2.1 — `feat(db)` Migration B** — backfill of
  `feedback_item.workspace_id`, NOT-NULL flip, status rename
  to v2 values, plus the new workflow tables (`tags`,
  `feedback_tag`, `submitters`, `feedback_note`). Hand-reviewed;
  round-trips up/down/up; idempotent backfill.
- **PR 2.2 — `feat(api)`** — v2 API: tags, notes, submitters,
  workspace-scoped feedback CRUD with the new statuses.
  Cross-tenant probes added to `tests/api/test_isolation.py`
  for every new endpoint.
- **PR 2.3 — `feat(ui)` triage core** — `/w/<slug>/inbox`,
  `/w/<slug>/feedback/<id>`, the filter bar, status pills,
  priority pill, tag chips, notes panel, timeline; `_partials/`
  for the Jinja styleguide.
- **PR 2.4 — `feat(api+ui)` public submit** — `/w/<slug>/submit`
  page + `POST /api/v1/public/feedback`, gated by
  `workspace.public_submit_enabled`, anti-spam rate-limits per
  ADR 062, submitter auto-link on email match.
- **PR 2.5 — `feat(ui)` workspace settings** —
  `/w/<slug>/settings` with the public-submission toggle and
  workspace metadata. New canaries in
  `tests/api/test_workspace_settings.py`.
- **PR 2.6 — `feat(triage)` Phase 2 close (this commit)** —
  Should-tier polish:
  - Submitters list & detail pages
    (`/w/<slug>/submitters`, `/w/<slug>/submitters/<id>`).
  - Stale-item highlighting on Inbox: server-side `?stale=true`
    filter via the new `stale_clause()`, JS row badge mirroring
    the same predicate, and a "Stale" summary card.
    Threshold canon-defined as `created_at < now() - interval
    '14 days' AND status IN ('new', 'needs_info')`.
  - axe-core (4.10.2, pinned URL) accessibility scan over
    inbox, feedback detail, settings, submitters list, and
    public submit. Fails on serious/critical WCAG 2.1 A/AA
    violations.

**Why you made them:**

- Phase 2 is the biggest semantic jump in v2: Migration B is
  destructive (status rename) and adds three new tables.
  Shipping it as a chain of small, individually-revertable PRs
  keeps each diff reviewable and lets us run the migration
  round-trip canary on every step.
- The Should items in PR 2.6 are the bare minimum to make the
  Beta usable for the people who actually triage feedback: a
  list of submitters (so you know who to reply to) and a stale
  badge (so old items don't just disappear into the queue).
- axe-core in the smoke gate is the cheapest possible lock on
  "we won't regress accessibility while iterating." It runs on
  the same Playwright stack already wired up; no new tooling.

## Related Issue

N/A — Phase 2 of the v2 implementation plan
([`spec/v2/implementation.md`](../../docs/project/spec/v2/implementation.md#phase-2--beta)).

## Type of Change

- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [x] ✨ New feature (non-breaking change that adds functionality)
- [x] 💥 Breaking change (Migration B renames feedback statuses;
      auto-applied via Alembic; v1 clients will break — but v2
      is still gated behind Phase 1's `FEATURE_AUTH=false` in
      production until ratification)
- [x] 📚 Documentation update
- [x] 🔧 Refactor (services extracted: `stale_detector`,
      `submitter_link`, `rate_limit`)
- [x] 🧪 Test update

## How to Test

**Steps:**

1. `uv sync` — picks up the `mako 1.3.11 → 1.3.12` bump for
   CVE-2026-44307 (transitive via alembic, no API change).
2. `task up` — Postgres for local + tests.
3. `task migrate` — runs Migration B; verify with
   `uv run alembic downgrade -1 && uv run alembic upgrade head`.
4. `task seed` — populates a workspace with mixed-status
   feedback so the stale predicate is observable.
5. `task dev` — sign up, exercise inbox filters
   (incl. `?stale=true`), open a feedback detail page, flip a
   status, add a note, add a tag, visit
   `/w/<slug>/submitters`, visit `/w/<slug>/settings`, toggle
   public submit, open `/w/<slug>/submit` in a private window
   and submit.
6. (Optional) `task test:e2e` — runs Playwright incl. the new
   axe-core scan. Requires `playwright install chromium` once.

**Test command(s):**

```bash
uv run pytest -m "not e2e"                                       # 248 passed
uv run pytest -m e2e --ignore=tests/e2e/test_feedback_smoke.py   # 6 passed (5 axe + 1 signup)
uv run alembic upgrade head
uv run alembic downgrade -1 && uv run alembic upgrade head       # round-trip
task check                                                       # ruff + mypy + pytest
```

`tests/e2e/test_feedback_smoke.py` (3 v1-era tests) is
**skipped at module level** — it drives the legacy unauthenticated
`/`, `/new`, `/feedback/<id>` routes that PR 1.7 broke when cookie
auth landed. It will be rewritten as `test_inbox_smoke.py` +
`test_public_submit.py` in Phase 3 per
[`implementation.md` Phase 3 verification](../../docs/project/spec/v2/implementation.md#phase-3--verification-post-pr-3-5).

**Screenshots / Demo:** _(attach when posting on GitHub)_

## Risk / Impact

**Risk level:** Medium

**What could break:**

- **Migration B** is the riskiest piece. It rewrites
  `feedback_item.status` enum values and flips
  `feedback_item.workspace_id` to NOT NULL. Mitigations: hand-
  reviewed migration, idempotent backfill, round-trip test in
  CI, gated behind Phase 1's `FEATURE_AUTH=false` so production
  traffic isn't yet using the v2 surface.
- **axe-core fetched at runtime from cdnjs.** The URL is pinned
  to `axe-core/4.10.2/axe.min.js`, so a CDN-side compromise
  would have to swap a specific path. A future hardening could
  vendor `axe.min.js` and SHA-pin it in-repo (parity with ADR 004
  for action SHAs); calling it out now so it doesn't get lost.
- **`stale_clause()` is duplicated in JS.** Both sides hard-code
  the 14-day window and `{new, needs_info}` set. If either
  drifts the badge will lie. The constants are right next to
  each other in the source tree
  (`services/stale_detector.py` and `static/js/inbox.js`);
  a future PR could generate the JS from the Python via a
  build step.

**Rollback plan:** Revert this PR. `alembic downgrade -1`
restores the v1 schema (round-trip is canary'd). `FEATURE_AUTH`
gate from Phase 1 means rolling back doesn't expose v2 to public
traffic.

## Dependencies (if applicable)

**Depends on:** Phase 1 close (PRs 1.3a → 1.9). Already on
`main` as of `v1.1.0`.

**Blocked by:** None.

**Blocks:** Phase 3 (PRs 3.1 → 3.5) — Resend integration for
shipped notifications, public changelog, v2.0 ratification.

## Breaking Changes / Migrations (if applicable)

- [x] Config changes required *(none new in this PR — Phase 1's
      `FEATURE_AUTH` still gates the surface)*
- [x] Data migration needed (Alembic Migration B; up/down
      verified)
- [x] API changes — v2 endpoints under `/api/v1/`: `feedback`
      schema gains `workspace_id`, `submitter_id`, `tags`;
      `status` enum values renamed; new endpoints for `tags`,
      `submitters`, `notes`, `public/feedback`, workspace
      `settings`. v1 clients will break.
- [x] Dependency changes — `mako` bumped `1.3.11 → 1.3.12` in
      `uv.lock` to clear CVE-2026-44307 reported by `pip-audit`
      (no API change; transitive via alembic).

**Details:**

- Status enum: v1 `{new, reviewing, actioned, closed}` →
  v2 `{new, needs_info, planned, in_progress, shipped,
  wont_do, duplicate}` per ADR 064.
- `feedback_item.workspace_id` is now NOT NULL.
- Three new tables: `tags`, `submitters`, `feedback_note`.

## Checklist

- [x] My code follows the project's style guidelines
      (ruff lint + format, mypy strict, bandit clean)
- [x] I have performed a self-review of my code
- [x] I have commented my code, particularly in
      hard-to-understand areas (`stale_clause()`,
      `_signup()` helper, axe-core fetch rationale)
- [x] I have made corresponding changes to the documentation
      (`implementation.md` PR 2.6 row → done; deliverable
      checkboxes ticked)
- [x] No new warnings (`task check` is clean)
- [x] I have added tests that prove my fix is effective or
      that my feature works
- [x] Relevant tests pass locally:
      - Non-e2e: 248 passed
      - e2e (excluding the v1-era smoke skipped above): 6 passed
- [x] No security concerns introduced (bandit clean; pip-audit
      clean after `mako` bump)
- [x] No performance regressions expected (the stale predicate
      is covered by the existing
      `(workspace_id, status, created_at)` composite index)

## Reviewer Focus (Optional)

- Migration B's `op.execute(...)` blocks for the status rename —
  please double-check the WHEN clauses cover every legacy value.
- `tests/e2e/test_a11y.py::_signup` — the helper bypasses email
  verification by flipping `is_verified` directly in SQL. Worth
  a sanity check that this is acceptable for the e2e gate
  (it matches what `test_signup_flow.py` already does for
  workspace setup).
- `services/stale_detector.py` uses `sqlmodel.col(...)` wrappers
  to keep mypy strict happy with the SQLAlchemy 2.x typing.
  Flag if you'd prefer raw `FeedbackItem.created_at < cutoff`
  with a targeted `# type: ignore`.

## Additional Notes

- `pip-audit` blocked the first push attempt on
  `mako 1.3.11` (CVE-2026-44307, sandbox bypass). Resolved by
  `uv lock --upgrade-package mako` → 1.3.12. No source changes,
  lockfile-only delta.
- `tests/e2e/test_feedback_smoke.py` is now `pytest.mark.skip`
  with a reason pointing at the Phase 3 rewrite plan. Surfacing
  this as a known issue rather than silently leaving the e2e
  gate red.
- After this PR, the v2 triage surface is feature-complete for
  Beta. Phase 3 is the email loop and the public changelog —
  neither blocks day-to-day triage.
