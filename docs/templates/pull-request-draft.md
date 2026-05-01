<!-- WORKING COPY — edit freely, this does NOT affect .github/PULL_REQUEST_TEMPLATE.md -->
<!-- Use this file to draft your PR description before pasting it into GitHub. -->
<!-- Branch: wip/2026-04-30-scratch -->
<!--
  Suggested PR title (conventional commit format — type: description):

    feat: v1.0 release candidate — config hardening, seed script, learning notes

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

<!-- Suggested labels: "feature", "documentation", "chore" -->

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

The v1.0 release-candidate sweep: harden production config, finish the
seed script to project script-conventions, document Railway / web-app
tooling for future-me, and reset the version line so the next
release-please PR ships as `v1.0.0` (not `v1.4.0` inherited from the
template).

**What changes you made:**

- **Production safety net** — `Settings` now refuses to boot when
  `APP_ENV=production` and `DATABASE_URL` is unset or points at
  `localhost`. Includes a unit test.
- **`scripts/seed.py`** mirrors the rest of `scripts/` —
  `SCRIPT_VERSION`, `THEME`, `_ui.UI` header/section/kv/footer,
  `_progress.ProgressBar` over the insert loop, `--version`,
  `--smoke` self-check that validates every `Source` and `Status`
  is represented.
- **Version line reset** — removed inherited `v1.3.0` tag and GitHub
  Release; `.release-please-manifest.json` set to `0.0.0`;
  `release-please-config.json` pinned with `"release-as": "1.0.0"`
  for the next release. (This pin must be removed in a follow-up PR
  after `v1.0.0` ships, otherwise every subsequent release tries to
  be 1.0.0 again.)
- **CHANGELOG.md** reset to a fresh template — release-please will
  repopulate from commit history on the next release PR.
- **`copilot-instructions.md`** — Frontend section expanded with
  semantic-HTML, tags-vs-classes, and CSS rules; pointer added to
  the new `frontend-conventions.md` notes file. Targeted-instruction
  table updated to point at the new `script-conventions.md`.
- **`scripts/.instructions.md`** + **`.github/SKILL.md`** — pointers
  to the new script-conventions notes.
- **New notes files** in `docs/notes/`:
  - `script-conventions.md` — rationale for the rules in
    `scripts/.instructions.md` plus 17 recommended additions and a
    half-day-each upgrade table.
  - `frontend-conventions.md` — semantic-HTML rationale, full
    tag-selection table, CSS conventions (tokens, `:focus-visible`,
    no `!important`, accessibility checklist), and a tiered
    "commercial-product features" roadmap (Tier 1 / Tier 2 / Tier 3)
    for v2 work.
  - `webapp-tooling.md` — field guide to web-app tools (Pico,
    Tailwind, htmx, Alpine, React, Svelte, Django, Vite, etc.) with
    when-to-use, pros, cons, and how each would affect this repo.
  - Plus three notes from earlier commits in this branch:
    `railway-learning.md`, `how-deployment-works.md`,
    `post-launch-checklist.md`.

**Why you made them:**

- The localhost-DB-in-production check exists because Railway's
  pre-deploy command silently inherits the default `DATABASE_URL`
  if the Postgres plugin isn't linked, leading to a confusing
  `Connection refused` instead of an actionable error. See
  `docs/project/railway-setup.md` step 2.
- `seed.py` was the only script in `scripts/` not following the
  shared conventions; bringing it in line removes the rough edge
  before v1.0.
- The version reset turns the inherited-template tag history into
  a clean `v1.0.0` for the portfolio piece.
- The notes files capture decisions and trade-offs while context is
  fresh, and pre-write the v2 roadmap so post-1.0 work has a plan.

## Related Issue

N/A — pre-1.0 sweep, not tracking each item as a separate issue.

## Type of Change

- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [x] ✨ New feature (non-breaking change that adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [x] 📚 Documentation update
- [ ] 🔧 Refactor (no functional changes)
- [x] 🧪 Test update

## How to Test

**Steps:**

1. **Production-config guard** — confirm the new validator fails
   loudly when misconfigured and is silent in dev:
   ```powershell
   $env:APP_ENV="production"; $env:DATABASE_URL="postgresql://u:p@localhost/db"
   uv run python -c "from feedback_triage.config import Settings; Settings()"
   # Expect: ValidationError mentioning 'localhost' and railway-setup.md
   Remove-Item Env:\APP_ENV; Remove-Item Env:\DATABASE_URL
   ```
2. **Seed script smoke** — no DB required:
   ```powershell
   uv run python scripts/seed.py --smoke
   # Expect: "seed 1.0.0: smoke ok (20 rows)"
   ```
3. **Seed script end-to-end** — local Postgres up:
   ```powershell
   task up
   task migrate
   uv run python scripts/seed.py --reset
   uv run python scripts/seed.py --version
   ```
4. **Release pipeline dry check** — confirm the manifest + config
   change parses:
   ```powershell
   Get-Content .release-please-manifest.json
   Get-Content release-please-config.json | Select-String release-as
   ```
5. **Lint / format / tests:**
   ```powershell
   uv run ruff check src/ scripts/ tests/
   uv run ruff format --check src/ scripts/ tests/
   uv run pytest tests/test_config.py -v
   task check
   ```

**Test command(s):**

```bash
uv run python scripts/seed.py --smoke
uv run pytest tests/test_config.py -v
task check
```

**Screenshots / Demo (if applicable):**

N/A — no UI changes in this PR.

## Risk / Impact

**Risk level:** Low

**What could break:**

- A production deploy whose `DATABASE_URL` *is* localhost will now
  refuse to start. This is the intended behavior — surfacing the
  misconfiguration early instead of after a confusing `Connection
  refused`. Verify the Railway reference variable resolves to a
  `*.railway.internal` host (which the validator allows).
- Release-please will produce a `v1.0.0` PR on the next run because
  of the `release-as` pin. Reviewers should expect this and merge
  it; the follow-up PR removing the pin must land before the next
  release after that.

**Rollback plan:** Revert this PR. Tag history is already reset on
the remote, but re-tagging `v1.3.0` is possible from any ancestor
commit if needed.

## Dependencies (if applicable)

**Depends on:** N/A

**Blocked by:** N/A

**Follow-up required:** After `v1.0.0` is tagged on `main`, open a
PR removing `"release-as": "1.0.0"` from `release-please-config.json`
so subsequent bumps follow Conventional Commits normally.

## Breaking Changes / Migrations (if applicable)

- [ ] Config changes required
- [ ] Data migration needed
- [ ] API changes (document below)
- [ ] Dependency changes

**Details:** No schema, no API, no dependency changes. The
`release-as` pin is a one-shot release-please instruction, not a
breaking change to consumers.

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

- **`src/feedback_triage/config.py`** — the new
  `_require_remote_db_in_production` validator. Confirm the host
  parsing covers what you'd expect (the `_LOCAL_DB_HOSTS` set
  matches `localhost`, `127.0.0.1`, `::1`, and empty host) and that
  the error message points at the right runbook step.
- **`scripts/seed.py`** — `--smoke` should remain side-effect-free.
  Verify no DB import path runs during smoke.
- **`release-please-config.json`** — the `release-as` line is the
  one-shot pin to `1.0.0`. Track the follow-up issue to remove it
  after the release lands.

## Additional Notes

- Inherited `v1.3.0` tag and GitHub Release have already been
  deleted from the remote (`gh release delete v1.3.0 --yes
  --cleanup-tag`). The `CHANGELOG.md` was reset accordingly so
  release-please regenerates it from commit history.
- The three new `docs/notes/*.md` files are intentionally
  long-form. They are companions to short, rule-shaped instruction
  files (`scripts/.instructions.md`, the Frontend section in
  `copilot-instructions.md`) — instruction files stay terse for
  Copilot's `applyTo` scoping; notes files hold the rationale and
  the v2 roadmap thinking.
- After this PR merges, the planned sequence is: release-please
  opens "release v1.0.0" → merge → tag created → follow-up PR
  removes the `release-as` pin → start v2 work on feature
  branches per `docs/notes/frontend-conventions.md` § 5.
