<!-- WORKING COPY — edit freely, this does NOT affect .github/PULL_REQUEST_TEMPLATE.md -->
<!-- Use this file to draft your PR description before pasting it into GitHub. -->
<!-- Branch: wip/2026-05-05-scratch -->
<!--
  Suggested PR title (conventional commit format — type: description):

  refactor(models): split models.py into a package and add v2 enums (PR 1.3a)

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

<!-- Suggested labels: refactor, scaffolding, v2, models, enums, docs, repo-doctor -->

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

Pre-Phase-1 scaffolding for the v2.0 jump, plus a few small tooling
fixes that surfaced while running pre-commit and `task branch`. Lands
PR **1.3a** from
[`docs/project/spec/v2/implementation.md`](../project/spec/v2/implementation.md):
splits the single-file `models.py` into a `models/` package and adds
the four new Python `StrEnum`s that PR 1.3b will wire to native
Postgres enum types.

**No DB changes. No Alembic revisions.** The package split is a pure
import-surface refactor — `from feedback_triage.models import
FeedbackItem` keeps working unchanged. The enums ship now (ahead of
the migration that creates the matching Postgres types) so PR 1.3b
can wire `PgEnum(..., create_type=False)` to them without a circular
dependency.

**What changes you made:**

- **`src/feedback_triage/models/`** — promoted from a single module
  to a package.
  - `__init__.py` re-exports `FeedbackItem`, `SOURCE_ENUM`,
    `STATUS_ENUM` so the historical import path still resolves.
  - `feedback.py` — verbatim move of the old `models.py`
    `FeedbackItem` mapping (only the module docstring changed).
  - `users.py`, `sessions.py`, `tokens.py`, `workspaces.py`,
    `memberships.py`, `invitations.py`, `auth_rate_limits.py`,
    `email_log.py` — empty stubs (module docstring + `from __future__
    import annotations` only). Each docstring points at the ADR / spec
    section that PR 1.3b will implement.
- **`src/feedback_triage/enums.py`** — adds four new `StrEnum`
  classes whose string values match the v2 Postgres enum labels:
  - `UserRole` ∈ `{admin, team_member, demo}`
    (per [`v2/schema.md`](../project/spec/v2/schema.md))
  - `WorkspaceRole` ∈ `{owner, team_member}`
    (per [ADR 060](../adr/060-multi-tenancy-workspace-scoping.md))
  - `EmailStatus` ∈ `{queued, sent, retrying, failed}`
    (per [ADR 061](../adr/061-resend-email-fail-soft.md))
  - `EmailPurpose` ∈ `{verification, password_reset, invitation,
    status_change}` (per ADR 061). `PASSWORD_RESET` carries an inline
    `# nosec B105` — it's an enum label, not a credential.
- **[`docs/project/spec/v2/implementation.md`](../project/spec/v2/implementation.md)**
  — split the original PR 1.3 row into PR 1.3a (this PR — scaffold,
  no migration) and PR 1.3b (Migration A). Bumped totals and ticked
  the four DoD checkboxes for 1.3a.
- **[`scripts/branch_preflight.py`](../../scripts/branch_preflight.py)**
  — fixed vertical alignment of the body line under the first header
  (2-space → 4-space indent). `SCRIPT_VERSION` bumped 1.2.0 → 1.2.1.
- **[`.repo-doctor.toml`](../../.repo-doctor.toml)** and
  **[`repo_doctor.d/python.toml`](../../repo_doctor.d/python.toml)**
  — replaced PowerShell-only `New-Item` fix commands with
  cross-platform `python -c "from pathlib import Path; ..."`
  one-liners so copy-paste works on Windows, macOS, and Linux.

**Why you made them:**

PR 1.3 as originally written touched models, enums, and a 9-table
Alembic migration in one go — too big to review in one pass and
risky to roll back. Splitting it into 1.3a (scaffold) and 1.3b
(migration) means reviewers can verify the import-surface change in
isolation before any DDL lands. The repo-doctor / branch_preflight
tweaks are unrelated polish that surfaced during the same session
and were small enough to fold in.

## Related Issue

N/A — this is planned scaffolding for the v2 milestone tracked in
[`docs/project/spec/v2/implementation.md`](../project/spec/v2/implementation.md).
No external issue.

## Type of Change

- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [ ] ✨ New feature (non-breaking change that adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [x] 📚 Documentation update
- [x] 🔧 Refactor (no functional changes)
- [ ] 🧪 Test update

## How to Test

The whole PR is verifiable against the PR 1.3a DoD: existing tests
still pass, both old and new model import paths resolve, the four
new enums round-trip, and Alembic head is unchanged.

**Steps:**

1. Pull the branch and run `task check` — should be green.
2. Confirm both import paths resolve (see test command below).
3. Confirm `uv run alembic current` still reports `0001 (head)` and
   no new files exist under `alembic/versions/`.
4. Run `task branch` and visually confirm the status line under
   "Branch summary" sits under the title text, not the box border.

**Test command(s):**

```bash
# Full lint + typecheck + tests
task check

# Import-surface smoke
uv run python -c "from feedback_triage.models import FeedbackItem; \
  from feedback_triage.models.feedback import FeedbackItem as F2; \
  from feedback_triage.enums import UserRole, WorkspaceRole, EmailStatus, EmailPurpose; \
  print(UserRole('admin'), WorkspaceRole('team_member'), \
        EmailStatus('retrying'), EmailPurpose('verification'))"

# Alembic head should be unchanged
uv run alembic current

# Repo-doctor cross-platform fix commands (Windows + POSIX both work)
uv run python scripts/repo_doctor.py --smoke
```

**Screenshots / Demo (if applicable):**

N/A.

## Risk / Impact

**Risk level:** Low

**What could break:**

- Anything that imports `feedback_triage.models` as a *module object*
  (not via `from … import …`) and relies on it being a single file
  rather than a package — none in the current tree (`grep` found one
  consumer in `crud.py`, which uses `from feedback_triage.models
  import FeedbackItem` and is unaffected).
- Downstream code that imports the new enum names with different
  spellings — none yet; nothing in `src/` references them outside the
  enum module itself.
- The `branch_preflight.py` indent change is cosmetic; the only
  behavioural risk is the `SCRIPT_VERSION` bump, which is required
  by the `bump-script-version` pre-commit hook.

**Rollback plan:** Revert this PR. The package can be collapsed
back to a single `models.py` by moving `feedback.py` up one level
and deleting the stub modules; no DB state to undo.

## Dependencies (if applicable)

**Depends on:** N/A — no upstream PRs.

**Blocked by:** N/A.

PR **1.3b** (Migration A — auth, tenancy, email_log tables + native
enums) depends on this one. Phase 1 PRs 1.4+ depend on 1.3b, not
directly on this PR.

## Breaking Changes / Migrations (if applicable)

- [ ] Config changes required
- [ ] Data migration needed
- [ ] API changes (document below)
- [ ] Dependency changes

**Details:** None. Pure import-surface refactor + new enum classes
+ docs + tooling polish. The Postgres enum types referenced by the
new Python `StrEnum`s do **not** exist in the database yet — they
are created by PR 1.3b's Migration A.

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

Notes on the checklist:

- "Added tests" — no new tests were added; per the PR 1.3a DoD, the
  existing 66-test suite is the regression check that the package
  split didn't break imports. New tests land alongside the table
  bodies in PR 1.3b.
- "No security concerns" — bandit reports clean. The single `# nosec
  B105` on `EmailPurpose.PASSWORD_RESET` suppresses a known
  false-positive (an enum label, not a credential).

## Reviewer Focus (Optional)

- **Enum string values.** They must match the `CREATE TYPE` labels
  PR 1.3b will ship verbatim. Cross-checked against
  [`v2/schema.md`](../project/spec/v2/schema.md), ADR 060, and
  ADR 061 — but a second pair of eyes is welcome before this lands,
  since renaming a member after 1.3b ships is a breaking change.
- **Stub module docstrings.** Each one points at the ADR / spec it
  will implement. If a reviewer spots a wrong cross-reference, easier
  to fix here than after 1.3b adds the table body.
- **PR ledger split.** The split rationale and totals update in
  [`docs/project/spec/v2/implementation.md`](../project/spec/v2/implementation.md)
  — confirm the "Twenty-five PRs total — ten for Phase 1" sentence
  matches your read of the new structure.

## Additional Notes

Local verification before push:

- `uv run mypy src/feedback_triage` → `Success: no issues found in
  26 source files`.
- `uv run ruff check src/ tests/` + `ruff format --check src/`
  → clean.
- `uv run pytest tests/ -q` → 66 passed.
- `uv run bandit -c pyproject.toml -r src/` → 0 issues.
- `uv run alembic current` → `0001 (head)`, unchanged.
