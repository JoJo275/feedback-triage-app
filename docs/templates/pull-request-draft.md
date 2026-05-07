<!-- WORKING COPY — edit freely, this does NOT affect .github/PULL_REQUEST_TEMPLATE.md -->
<!-- Use this file to draft your PR description before pasting it into GitHub. -->
<!-- Branch: chore/v2-ratify -->
<!--
  Suggested PR title (conventional commit format — type: description):

  chore(release): ratify v2.0 — flip docs to v2 + cut v2.0.0

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

<!-- Suggested labels: documentation, release -->

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

PR 3.5 from the v2.0 implementation plan — the ratification PR. Flips
the canonical documentation pointers from v1.0 to v2.0 so that v2.0 is
the authoritative spec for all current work, and instructs
release-please to cut **v2.0.0** as the next release.

**What changed:**

- `docs/index.md` — front page now points at `spec-v2.md` and the v2.0
  implementation plan; v1.0 demoted to historical reference.
- `README.md` — status line, spec link, frontend stack row, and Future
  Improvements section flipped to v2.0; v1.0 spec retained as a
  "historical" link.
- `.github/copilot-instructions.md` — "Repository status" header
  rewritten so v2.0 is authoritative and v1.0 is historical.
- `docs/project/spec/spec-v2.md` — follow-on tasks list checked off
  (docs/index, README, copilot-instructions all flipped in this PR).
- `docs/project/spec/v2/implementation.md` — PR 3.5 ledger row updated
  to "docs done; tag pending"; PR 3.5 deliverable checkbox ticked.

**Why:** Phase 3 of v2.0 is otherwise complete (PRs 3.1–3.4 shipped).
This is the documentation-only flip that closes the spec-ratification
deliverable from the original Phase 3 DoD and is the gate to cutting
the `v2.0.0` tag.

## Related Issue

N/A — tracked directly in
`docs/project/spec/v2/implementation.md` as PR 3.5.

## Type of Change

- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [ ] ✨ New feature (non-breaking change that adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [x] 📚 Documentation update
- [ ] 🔧 Refactor (no functional changes)
- [ ] 🧪 Test update

## How to Test

**Steps:**

1. Read `docs/index.md`, `README.md`, and
   `.github/copilot-instructions.md` — confirm every prominent spec
   link points at `docs/project/spec/spec-v2.md`, with v1.0 surfaced
   only as a historical reference.
2. Build the docs locally and confirm the homepage renders the new
   "Project Spec v2.0" entry.
3. Confirm `docs/project/spec/spec-v2.md` follow-on tasks are checked.
4. Confirm `docs/project/spec/v2/implementation.md` PR 3.5 row is
   updated and the PR-3.5 deliverable checkbox is ticked.

**Test command(s):**

```bash
# Full Phase 3 verification block from implementation.md (run on this branch):
uv run pytest -m "not e2e"
$env:RESEND_DRY_RUN="1"; uv run pytest tests/unit/email/test_client.py
task check

# Optional: docs preview
uv run mkdocs serve
```

**Expected results (already run on this branch, 2026-05-07):**

- `uv run pytest -m "not e2e"` → **284 passed, 5 skipped** in ~93 s.
- `RESEND_DRY_RUN=1 uv run pytest tests/unit/email/test_client.py` →
  **6 passed** in ~0.2 s.
- `task check` → ruff clean, mypy clean, **284 passed / 5 skipped**.
  PowerShell surfaces a non-zero exit due to the Tailwind/Browserslist
  warning being written to stderr (a pre-existing quirk on Windows,
  unrelated to this PR; CI on Linux is unaffected).

> Note on test names: the verification block in `implementation.md`
> references aspirational filenames (`test_inbox_smoke.py`,
> `test_public_submit.py`, `test_email_client.py`). The actual
> equivalents on disk are `tests/e2e/test_feedback_smoke.py`,
> `tests/e2e/test_public_pages_smoke.py`,
> `tests/e2e/test_signup_flow.py`, `tests/e2e/test_a11y.py`, and
> `tests/unit/email/test_client.py`. Consider tidying the
> verification block in a follow-up.

**Screenshots / Demo (if applicable):**

N/A — text-only changes.

## Risk / Impact

**Risk level:** Low

**What could break:** Nothing in the running app. This PR does not
touch any code under `src/`, `alembic/`, `tests/`, `scripts/`, or the
Containerfile. The only behavioural impact is on the next
release-please run (see "Breaking Changes" below): release-please will
open a release PR proposing **v2.0.0** instead of v1.3.0, because of
the `Release-As: 2.0.0` footer on the merge commit.

**Rollback plan:** Revert this PR. If the release-please PR has
already merged, rolling back the `v2.0.0` tag is non-trivial — prefer
forward-fix.

## Dependencies (if applicable)

**Depends on:** PRs 3.1–3.4 (all `done` per the ledger).

**Blocked by:** Nothing.

## Breaking Changes / Migrations (if applicable)

- [ ] Config changes required
- [ ] Data migration needed
- [ ] API changes (document below)
- [ ] Dependency changes
- [x] Release version bump (manual, via `Release-As:` footer)

**Details:**

This PR does not break the API. The "breaking" element is purely the
release-version bump from `1.x` → `2.0.0`, signalling that the
authoritative spec for the codebase is now v2.0.

### Release-please instructions — IMPORTANT

`release-please` reads commit messages on `main` to decide the next
version. To make it propose **v2.0.0** (instead of the next minor
1.3.0), the **squash-merge commit message MUST include the footer**:

```
Release-As: 2.0.0
```

Recommended squash-merge commit body:

```
chore(release): ratify v2.0 — flip docs/index, README, copilot-instructions to v2

Closes PR 3.5 in docs/project/spec/v2/implementation.md.

Release-As: 2.0.0
```

After this merges to `main`, release-please will open a release PR
that:

1. Bumps `.release-please-manifest.json` from `1.2.0` → `2.0.0`.
2. Updates `src/feedback_triage/__init__.py` (extra-files entry).
3. Generates the `2.0.0` section in `CHANGELOG.md`.
4. Cuts the `v2.0.0` git tag once that PR is merged.

No manual `task release` is needed — release-please is the source of
truth for tagging on this repo.

## Checklist

- [x] My code follows the project's style guidelines
- [x] I have performed a self-review of my code
- [x] I have commented my code, particularly in hard-to-understand areas (N/A — docs only)
- [x] I have made corresponding changes to the documentation (this PR *is* the docs change)
- [x] No new warnings (or explained in Additional Notes)
- [x] I have added tests that prove my fix is effective or that my feature works (N/A — docs only; existing suite re-run green)
- [x] Relevant tests pass locally (284 passed, 5 skipped; see "How to Test")
- [x] No security concerns introduced
- [x] No performance regressions expected

## Reviewer Focus (Optional)

1. Confirm the **`Release-As: 2.0.0` footer is preserved** when
   squash-merging — this is the only mechanism that produces a 2.0.0
   release. Without it, release-please will cut 1.3.0 instead.
2. Sanity-check that nothing in `docs/index.md` or `README.md` still
   silently points users at v1.0 as the active spec.
3. Confirm `.github/copilot-instructions.md` no longer says "v1.0
   remains authoritative for the shipped v1.0 implementation until
   Phase 1 code lands" (Phase 1 has long since landed).

## Additional Notes

- The `task release` step described in the PR-3.5 plan is intentionally
  **not** performed in this PR. Tagging is owned by release-please's
  release PR, not by a hand-run `task release`.
- A follow-up cleanup item (low priority): reconcile the verification
  block in `docs/project/spec/v2/implementation.md` with the actual
  on-disk test filenames.
