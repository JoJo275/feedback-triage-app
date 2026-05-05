<!-- WORKING COPY — edit freely, this does NOT affect .github/PULL_REQUEST_TEMPLATE.md -->
<!-- Use this file to draft your PR description before pasting it into GitHub. -->
<!-- Branch: wip/2026-05-05-scratch -->
<!--
  Suggested PR title (conventional commit format — type: description):

    chore: PR 1.2 ADRs + UI box-border fix + release-please depin

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

<!-- Suggested labels: documentation, chore, ui, release -->

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

Three independent fixes, kept as separate commits so each can be cherry-picked or reverted on its own.

**What changes you made:**

1. **`fix(ui)` — `2708be2`** — `scripts/_ui.py` `header()` and `section()` now compute the inner box width from the rendered title (and version, for `header()`), pad the title row, and reuse the same width for the top/bottom borders. Boxes always close cleanly and grow when the title outgrows the requested width.
2. **`chore(release)` — `21825f5`** — Removed `"release-as": "1.0.0"` from `release-please-config.json`. The pin was forcing every release PR to 1.0.0 and blocking SemVer bumps from `feat:` / `fix:` / `BREAKING CHANGE:` commits.
3. **`docs(adr)` — `27e0695`** — PR 1.2 of the v2.0 implementation ledger: ADRs 062, 063, 064 accepted. Updated `docs/adr/README.md`, `mkdocs.yml` nav, `docs/project/spec/spec-v2.md` ADR table, `docs/project/spec/v2/adrs.md` (moved to Accepted), and `docs/project/spec/v2/implementation.md` (PR 1.1 + PR 1.2 marked done with deliverables ticked).

**Why you made them:**

- The task-branch UI helpers were drawing unclosed boxes on long titles — visual rough edge that shows up every time a workflow boots a header.
- Release-please was silently broken; the pin held back v1.0.x patch releases.
- PR 1.2 unblocks Phase 1 implementation work by ratifying the data-migration choreography (ADR 062), the final status workflow (ADR 063), and the pain/priority dual-field decision (ADR 064).

## Related Issue

N/A — maintenance + governance burst rolled up from the in-flight scratch branch.

## Type of Change

- [x] 🐛 Bug fix (non-breaking change that fixes an issue) — UI box borders
- [ ] ✨ New feature (non-breaking change that adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [x] 📚 Documentation update — ADRs 062/063/064 + ledger updates
- [ ] 🔧 Refactor (no functional changes)
- [ ] 🧪 Test update
- [x] Other: release pipeline config (`release-please-config.json`)

## How to Test

**Steps:**

1. UI fix — run any script that calls `_ui.header(...)` / `_ui.section(...)` (e.g., `python scripts/task_branch.py status`) and confirm the right-hand border closes flush with the longest line.
2. Release-please change — inspect the next release PR opened against `main`; it should compute a version bump from commit types since `v1.0.0`, not propose 1.0.0.
3. ADRs — `uv run mkdocs serve`, navigate to ADR 062 / 063 / 064 in the nav, confirm the Accepted ADRs section in `docs/adr/README.md` lists them, and confirm `spec-v2.md` and `v2/adrs.md` show them as Accepted.

**Test command(s):**

```powershell
# UI alignment
uv run python scripts/task_branch.py status

# ADR rendering
uv run mkdocs serve

# Existing test suite (no behavior changes expected)
task check
```

**Screenshots / Demo (if applicable):**

N/A — text-only UI fix; visual diff is "right border now closes".

## Risk / Impact

**Risk level:** Low

**What could break:**

- `_ui.py` change is layout-only; the only callers are dev-time scripts, not the running app.
- Removing the `release-as` pin will let release-please bump versions normally — confirm the next release PR is the expected SemVer step before merging it.
- ADR docs are additive; only `docs/project/spec/v2/adrs.md` had existing rows moved (Proposed → Accepted).

**Rollback plan:** Revert this PR. Each commit can also be reverted independently.

## Dependencies (if applicable)

**Depends on:** PR 1.0 + PR 1.1 of the v2.0 ledger (already merged).

**Blocked by:** Nothing.

## Breaking Changes / Migrations (if applicable)

- [ ] Config changes required
- [ ] Data migration needed
- [ ] API changes (document below)
- [ ] Dependency changes

**Details:** None. ADRs 062/063 describe migrations that will land in **PR 2.x / 3.x**, not in this PR.

## Checklist

- [x] My code follows the project's style guidelines
- [x] I have performed a self-review of my code
- [x] I have commented my code, particularly in hard-to-understand areas
- [x] I have made corresponding changes to the documentation
- [x] No new warnings (or explained in Additional Notes)
- [x] Relevant tests pass locally (or explained in Additional Notes)
- [x] No security concerns introduced (or flagged for review)
- [x] No performance regressions expected (or flagged for review)
- [ ] I have added tests that prove my fix is effective or that my feature works — _N/A: docs + config + cosmetic UI only._

## Reviewer Focus (Optional)

- ADR 062's two-revision Alembic choreography (Migration A schema-only + additive, Migration B data backfill + tighten) — verify the forward-only, idempotent re-run guarantees match what we want for Railway pre-deploy.
- ADR 063's decision to keep `'rejected'` in the enum type definition forever (Postgres has no stable `DROP VALUE`) blocked by `CHECK` and rewritten to `'closed'` by Migration B — confirm the deprecation story holds.
- ADR 064's defaults-sort `priority DESC, pain_level DESC, created_at ASC` — confirm this matches the intended triage UX.

## Additional Notes

Pre-push repo-doctor warnings dropped from 11 → 1 in the follow-up cleanup commit (the remaining finding is "alembic/versions has no .py revisions yet", which is real and tracked under Phase 1 PR 1.0 work).
