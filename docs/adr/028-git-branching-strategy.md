# ADR 028: Git Branching Strategy

## Status

Accepted

## Context

A defined branching strategy ensures contributors know where to work, how
to propose changes, and what the release flow looks like. This complements
[ADR 022 (rebase merge strategy)](022-rebase-merge-strategy.md) and
[ADR 023 (branch protection)](023-branch-protection-rules.md), which cover
_how_ code lands on `main` and _what gates_ it must pass.

This ADR addresses a higher-level question: what branches exist, what are
they for, and when are they created?

### Forces

- This is a **template repository** — the branching model should be simple
  enough for solo developers yet scale to small teams
- CI workflows trigger on specific branch/event combinations (push to `main`,
  PRs, tags)
- release-please automates releases from `main` via a Release PR
- Branch protection rules require PR review and CI status checks on `main`

## Decision

Use a **trunk-based development** model with short-lived feature branches.
`main` is the single integration branch.

### Branch categories

| Branch     | Lifetime    | Purpose                               | Convention                                                                   |
| :--------- | :---------- | :------------------------------------ | :--------------------------------------------------------------------------- |
| `main`     | Permanent   | Integration branch; always deployable | Protected, requires PR                                                       |
| Feature    | Short-lived | New features, bug fixes, chores       | `feat/short-description`, `fix/short-description`, `chore/short-description` |
| Release PR | Automated   | Created by release-please             | `release-please--branches--main`                                             |

### Rules

1. **All changes go through PRs into `main`** — no direct pushes (enforced
   by [branch protection](023-branch-protection-rules.md))
2. **Feature branches are short-lived** — ideally merged within a few days.
   Long-lived branches invite merge conflicts and integration pain.
3. **No `develop` branch** — trunk-based development uses `main` directly.
   A separate `develop` branch adds ceremony without benefit for this
   project's size.
4. **No release branches** — release-please handles releases from `main`
   via tags. If a hotfix is needed for an older release, create a branch
   from the tag (rare, and documented in [releasing.md](../releasing.md)).
5. **Branch naming follows the conventional commit type** — the prefix
   (`feat/`, `fix/`, `docs/`, `chore/`, `ci/`, `refactor/`, `test/`)
   matches the commit type, making the intent obvious in PR lists.

### Workflow

```
main ────●────●────●────●────●────●──── (always deployable)
          \       /      \         /
           feat/x        fix/y
```

1. Create a branch from `main` (`feat/add-auth`, `fix/null-check`)
2. Commit with conventional messages ([ADR 009](009-conventional-commits.md))
3. Open a PR — CI gate ([ADR 024](024-ci-gate-pattern.md)) must pass
4. Rebase and merge ([ADR 022](022-rebase-merge-strategy.md))
5. Branch auto-deleted after merge

## Alternatives Considered

### Git Flow

Long-lived `develop` and `main` branches, with `release/`, `hotfix/`, and
`feature/` branches.

**Rejected because:** Designed for projects with multiple supported releases
and scheduled release cycles. Overkill for a template that ships continuously
from `main`. Adds merge ceremony and branch management overhead with no
benefit at this scale.

### GitHub Flow (with `main` only, no naming convention)

Simple model where all branches merge into `main` but without naming
conventions.

**Rejected because:** The model itself is essentially what we use, but
adding a naming convention (type prefix) improves discoverability and aligns
with the conventional commit strategy already in place.

### Release branches

Maintain a `release/x.y` branch for each release series.

**Rejected because:** release-please handles releases via tags from `main`.
Creating release branches adds maintenance burden for a workflow that already
works without them.

## Consequences

### Positive

- Simple mental model — `main` plus short-lived branches
- Aligns with existing ADRs (rebase merge, branch protection, conventional
  commits, CI gate)
- Branches are self-documenting via naming convention
- release-please integrates seamlessly with trunk-based development
- Auto-delete keeps the remote branch list clean

### Negative

- No support for parallel release tracks out of the box (hotfixing v1 while
  developing v2 requires ad-hoc branching)
- Short-lived branch expectation doesn't prevent long-lived branches in
  practice — it's a convention, not a technical enforcement

### Mitigations

- Stale branch cleanup can be automated (the template includes
  `cache-cleanup.yml` which handles cache expiry; branch staleness can be
  checked manually via `gh` CLI)
- For the rare hotfix-on-old-version scenario, the process is documented
  in [releasing.md](../releasing.md)

## Implementation

- [.github/workflows/](../../.github/workflows/) — Workflows trigger on
  `push: branches: [main]` and `pull_request: branches: [main]`
- [ADR 022](022-rebase-merge-strategy.md) — Merge strategy
- [ADR 023](023-branch-protection-rules.md) — Branch protection rules
- [ADR 024](024-ci-gate-pattern.md) — CI gate pattern
- [release-please-config.json](../../release-please-config.json) — Release
  automation

## References

- [Trunk-based development](https://trunkbaseddevelopment.com/)
- [GitHub Flow](https://docs.github.com/en/get-started/using-github/github-flow)
- [ADR 009](009-conventional-commits.md) — Conventional commits
- [ADR 021](021-automated-release-pipeline.md) — Automated release pipeline
