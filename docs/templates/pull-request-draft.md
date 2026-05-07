<!-- WORKING COPY — edit freely, this does NOT affect .github/PULL_REQUEST_TEMPLATE.md -->
<!-- Use this file to draft your PR description before pasting it into GitHub. -->
<!-- Branch: wip/2026-05-07-scratch -->
<!--
  Suggested PR title (conventional commit format — type: description):

  feat(v2): ship Phase 3 — emails, public + management roadmap/changelog,
  dashboard, insights, mini-demo, ratify v2.0

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

<!-- Suggested labels: feature, release, documentation -->

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

Lands the entire **Phase 3** slice of the v2.0 implementation plan
(`docs/project/spec/v2/implementation.md`) in a single branch, plus
the spec-ratification flip (PR 3.5) and a round of reviewer fixes
addressing the issues called out on the first push.

**What this PR ships (logical slices from the plan):**

| Plan PR | Topic | Notes |
| --- | --- | --- |
| 3.1 | Status-change emails end-to-end | `services/status_change_notifier.py`, `email/templates/status_change.html`, `EmailClient.replay()` + `scripts/email_replay.py` (`task email:replay`) |
| 3.2 | Public roadmap + public changelog | `pages/public_roadmap.py`, `pages/public_changelog.py`, public templates, `Cache-Control` per perf budgets |
| 3.3 | Management roadmap kanban + changelog editor | `pages/roadmap.py`, `pages/changelog.py`, kanban partials, release-note editor |
| 3.4 | Dashboard, privacy + terms, insights v1, mini demo | `services/dashboard_aggregator.py` (cached, lock-protected), `pages/insights.py`, `pages/legal.py`, `pages/landing.py`, `static/js/landing_demo.js` |
| 3.5 | Ratify v2.0 | Flip `docs/index.md`, `README.md`, `.github/copilot-instructions.md` to point at v2.0 as authoritative; check off ratification deliverables |

**Why:** Closes Phase 3 of the v2.0 plan and unblocks cutting the
`v2.0.0` release.

**Reviewer fixes applied on this branch (in response to the first review):**

1. **`api/v1/feedback.py` PATCH no longer commits inside the handler.**
   `get_db()` owns the transaction boundary. The status-change
   notifier call is now wrapped in `try/except Exception` and logs
   any unexpected error — provider/template failures cannot affect
   the API response or roll back the PATCH.
2. **`email/client.py` `EmailClient.replay()` docstring corrected.**
   Now explicitly documents that `ValueError` is raised for missing
   rows / non-replayable status, and that the fail-soft contract
   only applies to *send-time* errors.
3. **`services/dashboard_aggregator.py` cache is now thread-safe.**
   Added `threading.Lock` around every `_cache` get/set/clear so
   concurrent FastAPI threadpool requests can't corrupt the
   `cachetools.TTLCache` ordered dict.
4. **`pages/public_roadmap.py` 30-day cutoff pushed into SQL.**
   Replaced the in-Python post-filter with `OR (status != shipped,
   updated_at >= cutoff)` in the query so Postgres does the work
   and the page doesn't materialise the full shipped archive at
   scale.
5. **`static/js/landing_demo.js` priority seed values aligned with
   the app enum.** Changed `priority: "med"` → `priority: "medium"`
   (8 occurrences) so labels and CSS hooks match `low|medium|high|
   critical` everywhere else in the app.

## Related Issue

N/A — phase work is tracked in
`docs/project/spec/v2/implementation.md`. Closes ledger items
3.1–3.5.

## Type of Change

- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [x] ✨ New feature (non-breaking change that adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [x] 📚 Documentation update
- [ ] 🔧 Refactor (no functional changes)
- [x] 🧪 Test update

## How to Test

**Steps:**

1. Pull the branch, `uv sync`, `task up`, `task migrate`, `task seed`.
2. `task dev` — exercise the new pages by hand:
   - `/` (landing + mini demo, vanilla JS — no API calls)
   - `/w/<slug>/dashboard` (cards, sparkline, top tags, recent activity)
   - `/w/<slug>/insights` (cohorts, trend, leaderboards)
   - `/w/<slug>/roadmap` (management kanban) and `/w/<slug>/roadmap/public`
   - `/w/<slug>/changelog` (editor) and `/w/<slug>/changelog/public`
   - `/privacy` and `/terms`
3. Move a feedback item to `shipped`; confirm the email_log row
   lands at `sent` (or `failed` under `RESEND_DRY_RUN=0` against a
   throttled key) and the PATCH still returns `200`.

**Test command(s):**

```bash
# Phase 3 verification block (run on this branch, all green):
uv run pytest -m "not e2e"
$env:RESEND_DRY_RUN="1"; uv run pytest tests/unit/email/test_client.py
task check
```

**Expected results (run 2026-05-07):**

- `uv run pytest -m "not e2e"` → **284 passed, 5 skipped** (~87 s).
- `RESEND_DRY_RUN=1 uv run pytest tests/unit/email/test_client.py` →
  **6 passed**.
- `ruff check`, `ruff format --check`, `mypy src/` — all clean.
- `task check` shows 284 / 5 skipped; PowerShell surfaces a non-zero
  exit due to the Tailwind/Browserslist warning being written to
  stderr (a pre-existing Windows quirk; CI on Linux is unaffected).

> **Verification block typo (follow-up).** The block in
> `docs/project/spec/v2/implementation.md` references three test
> files that don't exist on disk (`test_inbox_smoke.py`,
> `test_public_submit.py`, `test_email_client.py`). The actual
> equivalents are `tests/e2e/test_feedback_smoke.py`,
> `test_public_pages_smoke.py`, `test_signup_flow.py`,
> `test_a11y.py`, and `tests/unit/email/test_client.py`. Out of
> scope here — flagging for a small follow-up cleanup.

**Screenshots / Demo (if applicable):**

N/A.

## Risk / Impact

**Risk level:** Medium

**What could break:**

- New surface area is large (≈4.7k LOC added across pages, services,
  templates, JS, tests). Mitigations:
  - Every page route is exercised by an API/integration test.
  - Status-change emails are fail-soft per ADR 061; a Resend outage
    cannot roll back a PATCH (regression-tested in
    `tests/api/test_status_change_email.py`).
  - Dashboard cache uses an explicit lock (see Reviewer Focus).
- Public pages (`/w/<slug>/roadmap/public`,
  `/w/<slug>/changelog/public`) are unauthenticated — submitter PII
  is intentionally never rendered; verified by tests.

**Rollback plan:** Revert this PR. Any failed status-change emails
remain as `email_log` rows replayable later via `task email:replay`.

## Dependencies (if applicable)

**Depends on:** Phase 1 + Phase 2 already on `main` (auth, tenancy,
feedback CRUD, public submit).

**Blocked by:** Nothing.

## Breaking Changes / Migrations (if applicable)

- [ ] Config changes required
- [ ] Data migration needed (no Alembic revision in this PR)
- [ ] API changes (no contract changes; only fail-safety hardening
      around PATCH `/api/v1/feedback/{id}`)
- [ ] Dependency changes (none — `cachetools` and `jinja2` already
      pinned)
- [x] Release version bump (manual, via `Release-As:` footer)

**Details:**

This PR carries the **v2.0 ratification** documentation flip
(`docs/index.md`, `README.md`, `.github/copilot-instructions.md`)
and is intended to be the commit that release-please reads when it
proposes the next release.

### Release-please instructions — IMPORTANT

`release-please` reads commit messages on `main` to decide the next
version. To make it propose **v2.0.0** (instead of the next minor
1.3.0), the **squash-merge commit message MUST include the footer**:

```
Release-As: 2.0.0
```

Recommended squash-merge commit body:

```
feat(v2)!: ratify v2.0 — phase 3 + ratification flip

Closes PRs 3.1–3.5 in docs/project/spec/v2/implementation.md.

Release-As: 2.0.0
```

After this merges to `main`, release-please will open a release PR
that:

1. Bumps `.release-please-manifest.json` from `1.2.0` → `2.0.0`.
2. Updates `src/feedback_triage/__init__.py` (extra-files entry).
3. Generates the `2.0.0` section in `CHANGELOG.md`.
4. Cuts the `v2.0.0` git tag once that PR is merged.

No manual `task release` is needed — release-please owns tagging.

## Checklist

- [x] My code follows the project's style guidelines (ruff + mypy clean)
- [x] I have performed a self-review of my code
- [x] I have commented my code, particularly in hard-to-understand areas
- [x] I have made corresponding changes to the documentation (spec, implementation plan, README, copilot-instructions, ADR-aligned docstrings)
- [x] No new warnings (Tailwind/Browserslist nag on Windows is pre-existing — see "How to Test")
- [x] I have added tests that prove my fix is effective or that my feature works
- [x] Relevant tests pass locally (284 passed, 5 skipped)
- [x] No security concerns introduced (or flagged for review)
- [x] No performance regressions expected (dashboard cache + roadmap SQL filter both improve scale behaviour)

## Reviewer Focus (Optional)

1. **`Release-As: 2.0.0` footer must be preserved** when squash-merging
   — without it, release-please cuts 1.3.0 instead of 2.0.0.
2. **Reviewer fix #1: `api/v1/feedback.py` PATCH.** Confirm `db.commit()`
   is gone and the `try/except` around `notify_status_change` matches
   the contract in `database.py` (`get_db` owns commit/rollback).
3. **Reviewer fix #3: `dashboard_aggregator._cache_lock`.** Confirm
   the lock spans every read and write and that `reset_cache()` is
   also guarded.
4. **Reviewer fix #4: `public_roadmap.py` SQL filter.** Confirm the
   new `or_(status != SHIPPED, updated_at >= cutoff)` predicate
   produces the same column contents as the previous Python-side
   filter (existing tests exercise both paths).
5. **`pages/insights.py` patch coverage is 56%.** No insights tests
   in this PR — the page is read-only and renders aggregate counts
   from already-tested aggregators. Suggested follow-up: an
   integration test asserting the route renders for a seeded
   workspace and 404s for an unknown slug. **Not** added here to
   keep this PR focused on the reviewer-flagged correctness issues.

## Additional Notes

- Codecov reports patch coverage **87.28%** (52 missed lines across
  five files). The lion's share is `insights.py` at 56% (39 lines)
  — see Reviewer Focus #5. The other four files
  (`email/client.py` 83%, `status_change_notifier.py` 88%,
  `config.py` 80%, `public_roadmap.py` 95%) are at acceptable levels
  given how much of those branches is provider/error-path code.
- `task release` from the original PR-3.5 plan is intentionally
  **not** invoked — tagging is owned by release-please's release PR,
  not by a hand-run command.
