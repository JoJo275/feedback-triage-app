<!-- WORKING COPY — edit freely, this does NOT affect .github/PULL_REQUEST_TEMPLATE.md -->
<!-- Use this file to draft your PR description before pasting it into GitHub. -->
<!-- Branch: wip/2026-05-01-scratch -->
<!--
  Suggested PR title (conventional commit format — type: description):

    docs(spec): scaffold and ratify v2.0 spec, ADR 061, Phase 0 close, and 24-PR implementation plan

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

<!-- Suggested labels: documentation, spec, adr -->

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

Scaffolds the entire v2.0 spec ("SignalNest"), ratifies it, ratifies
ADR 061 (Resend + fail-soft email), closes Phase 0, and slices the
remainder of v2.0 work into 24 PR-sized deliverables.
**Documentation only** — no production code, no schema, no
dependencies touched.

**What changes you made:**

- **Project rename:** Feedback Triage → SignalNest (docs surface
  only; package name unchanged).
- **v2.0 spec scaffolded** under `docs/project/spec/v2/`:
  `core-idea.md`, `schema.md`, `api.md`, `pages.md`, `security.md`,
  `multi-tenancy.md`, `rollout.md`, `tooling.md`, `css.md`,
  `copy-style-guide.md`, `observability.md`,
  `performance-budgets.md`, `railway-optimization.md`,
  `pages-catalog.md`, `repo-structure.md`, `risk-register.md`,
  `adrs.md`, `implementation.md`.
- **`spec-v2.md` ratified** (Status: Ratified 2026-05-04).
- **ADR 061 (Resend email, fail-soft)** added and Accepted, with
  full `email_log` DDL, outcome→status table, and `RESEND_DRY_RUN=1`
  test strategy.
- **Phase 0 closed** in `implementation.md` (all pre-flight items
  ticked).
- **CSS architecture** moved to the four-file structure
  (`tokens → base → layout → components → effects`, glued by
  `app.css`); `frontend-conventions.md` and `css-learning.md`
  updated to match, including a new "How CSS is installed in a
  repo" section.
- **`railway-optimization.md`** synced to actual Hobby posture: $5
  credit ceiling, sleep ON, `--workers 2`, 5 GB Postgres volume,
  `pool_size=5` per worker, with cold-start risks documented.
- **`performance-budgets.md`** gained a `cold_start=true` access-log
  carve-out so cold requests do not poison the P95 rollup.
- **`implementation.md`** rewritten with a top-level **PR ledger**
  of 24 conventional-commit-titled PRs (Phase 1: 9, Phase 2: 6,
  Phase 3: 5, Phase 4: 4). Each PR has Touches /
  Deliverables-it-closes / DoD; Migrations A and B are isolated
  PRs; spec-ratification (PR 3.5) lands last in Phase 3.
- **`mkdocs.yml`** + **`docs/adr/README.md`** index updated to
  surface ADRs 045–061.

**Why you made them:**

v2.0 was sitting as scattered drafts with no agreed ratification
path. This PR moves the v2.0 spec from "draft scratch" to "ratified
plan with PR-sized work units" so subsequent code PRs can each cite
a single PR slice from `implementation.md` and a single deliverable
checkbox. It also unblocks the first code PR (PR 1.1 — Tailwind
plumbing + `/styleguide` stub) by locking ADR 061's email contract
and the Railway cost ceiling that Phase 1 budget decisions depend
on.

## Related Issue

N/A — spec scaffolding work; not tracked by an issue. The 24-PR
ledger in `docs/project/spec/v2/implementation.md` replaces the
need for a tracker issue per phase.

## Type of Change

- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [ ] ✨ New feature (non-breaking change that adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [x] 📚 Documentation update
- [ ] 🔧 Refactor (no functional changes)
- [ ] 🧪 Test update

## How to Test

This PR contains no executable code changes. Reviewers verify by
reading and by building the docs site.

**Steps:**

1. Skim `docs/project/spec/spec-v2.md` — confirm Status row reads
   `Ratified (2026-05-04)`.
2. Open `docs/project/spec/v2/implementation.md` — confirm the
   **PR ledger** lists 24 rows (1.1–4.4) and Phase 0 is fully
   checked off.
3. Open `docs/adr/061-resend-email-fail-soft.md` — confirm Status
   is **Accepted (2026-05-04)** and the `email_log` DDL block is
   present.
4. Build the docs site and confirm no broken links and that ADRs
   045–061 appear in the nav.

**Test command(s):**

```bash
# Docs build (must be clean — no broken links, no missing nav entries)
uv run mkdocs build --strict

# Markdown / typo check (best-effort; not the CI gate)
uv run pre-commit run typos --all-files

# No code changes, but confirm the existing test suite still parses
uv run pytest --collect-only -q
```

**Screenshots / Demo (if applicable):**

N/A — pure documentation diff. Reviewers can preview rendered
output locally with `uv run mkdocs serve`.

## Risk / Impact

**Risk level:** Low

**What could break:**

- **Broken cross-references** if a moved/renamed file is linked
  from outside `docs/project/spec/v2/`. Mitigated by
  `mkdocs build --strict` and lychee in CI.
- **Stale guidance** if `.github/copilot-instructions.md` still
  points reviewers at v1.0 in places where v2.0 is now
  authoritative. Note: this PR does **not** flip
  copilot-instructions to v2.0-authoritative — that flip is
  deliberately deferred to PR 3.5 alongside the `v2.0.0` git tag,
  per the ratification policy now codified in
  `implementation.md`.
- **PR-ledger drift** if Phase 1 code work starts before this
  lands — later PRs would have nothing to cite.

**Rollback plan:** Revert this PR. No schema, no dependency, no
runtime change to undo. The pre-fork `wip/...` drafts remain in
git history.

## Dependencies (if applicable)

**Depends on:** N/A

**Blocked by:** N/A

This PR is the unblocker for **PR 1.1** (`feat(css): tailwind
plumbing + four-file architecture + /styleguide stub`). Phase 1
cannot legitimately start until this PR-ledger and ADR 061 are
merged.

## Breaking Changes / Migrations (if applicable)

- [ ] Config changes required
- [ ] Data migration needed
- [ ] API changes (document below)
- [ ] Dependency changes

**Details:** None. Documentation only.

## Checklist

- [x] My code follows the project's style guidelines
- [x] I have performed a self-review of my code
- [x] I have commented my code, particularly in hard-to-understand areas
- [x] I have made corresponding changes to the documentation
- [x] No new warnings (or explained in Additional Notes)
- [ ] I have added tests that prove my fix is effective or that my feature works <!-- N/A — docs only -->
- [x] Relevant tests pass locally (or explained in Additional Notes)
- [x] No security concerns introduced (or flagged for review)
- [x] No performance regressions expected (or flagged for review)

## Reviewer Focus (Optional)

Please pay close attention to:

1. **`implementation.md` — the PR ledger.** Are any deliverables
   from the original Phase 1–4 Must / Should / Nice tables missing
   a checkbox under one of the 24 PRs? Are any PRs too fat to
   land as a single review?
2. **ADR 061's outcome→status mapping.** Does the fail-soft
   contract (network error → status change still commits;
   `email_log` row lands at `failed`) match what we want
   operationally?
3. **`railway-optimization.md`** — the actual Hobby posture
   (sleep ON, 2 workers, 5 GB volume, $5 ceiling). Anyone
   disagree before this gets baked into Phase 1 sizing?
4. **PR-slicing of Migration B (PR 2.1).** Two Alembic revisions
   in one PR is a deliberate exception to "one logical change per
   commit" — confirm this is acceptable per ADR 062's
   roll-forward rule.

## Additional Notes

- Phase numbering: **0–4 are canonical**. The codenames Alpha /
  Beta / Final / Polish are aliases for Phases 1–4 and are used
  interchangeably in the spec.
- The v1.0 spec (`docs/project/spec/spec-v1.md`) remains in the
  tree for historical reference. It is **not** removed by this PR;
  removal happens after v2.0.0 ships.
- ADRs 062, 063, and 064 are still **TBD** in the spec table on
  purpose — they are drafted in PR 1.2 (the doc-only PR at the
  start of Phase 1), not here. Reviewers should not ask for them
  in this PR.
