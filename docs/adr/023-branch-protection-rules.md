# ADR 023: Branch Protection Rules for main

## Status

Accepted

## Context

Multiple architectural decisions in this project rely on pull requests being the only way code reaches `main`:

- **ADR 022 (rebase+merge)** — enforcing a single merge strategy requires disabling direct pushes
- **ADR 021 (release pipeline)** — release-please scans commits on `main` and assumes they arrived via reviewed PRs
- **ADR 009 (conventional commits)** — CI validates commit messages on PRs, but only if PRs are required
- **ADR 008 (pre-commit hooks)** — local hooks can be bypassed with `--no-verify`; CI on PRs is the authoritative gate

Without branch protection, these decisions are advisory — anyone with write access can push directly to `main`, skip CI, and break the release pipeline.

### Options Considered

| Option                            | Approach                                                        | Pros                                       | Cons                                                        |
| --------------------------------- | --------------------------------------------------------------- | ------------------------------------------ | ----------------------------------------------------------- |
| **No protection**                 | Trust contributors to follow conventions                        | Zero friction                              | All other process ADRs are unenforceable                    |
| **CODEOWNERS only**               | Require specific reviewers for certain paths                    | Targeted review coverage                   | Doesn't prevent direct pushes or enforce CI                 |
| **Branch protection rules**       | GitHub-native enforcement of PRs, status checks, linear history | Platform-enforced, auditable, configurable | Adds friction for solo maintainers; admins can bypass       |
| **Rulesets (new GitHub feature)** | More granular than branch protection; supports tag rules        | Finer control, org-level inheritance       | Newer feature, more complex setup, not all plans support it |

### Why Branch Protection (Not Rulesets)

Branch protection rules are well-established, supported on all GitHub plans (including free for public repos), and sufficient for this project's needs. Rulesets offer more granularity but add complexity that isn't needed here. If the project grows to need org-level rule inheritance or tag-specific rules, rulesets can be adopted later.

## Decision

Configure branch protection rules on `main` with the following settings:

### Required Settings

| Setting                                   | Value          | Why                                                   |
| ----------------------------------------- | -------------- | ----------------------------------------------------- |
| **Require a pull request before merging** | Enabled        | Prevents direct pushes; forces code review            |
| **Required approvals**                    | 1 (adjustable) | Ensures at least one reviewer sees every change       |
| **Require status checks to pass**         | Enabled        | CI must pass before merge is allowed                  |
| **Require branches to be up to date**     | Enabled        | Prevents merging stale branches that may conflict     |
| **Require linear history**                | Enabled        | Enforces rebase+merge (ADR 022); blocks merge commits |
| **Require conversation resolution**       | Enabled        | All review comments must be resolved before merge     |

### Required Status Checks

These workflows must pass before a PR can be merged:

| Check           | Workflow      |
| --------------- | ------------- |
| Lint + format   | `lint-format` |
| Tests           | `test`        |
| Type checking   | `type-check`  |
| Commit messages | `commit-lint` |

The exact list should match the CI workflows that run on PRs. Add or remove checks as workflows are added or removed.

### Recommended (Optional) Settings

| Setting                    | Value    | Why                                                                 |
| -------------------------- | -------- | ------------------------------------------------------------------- |
| **Do not allow bypassing** | Enabled  | Even admins go through PRs (disable for solo maintainers if needed) |
| **Restrict who can push**  | Disabled | Not needed when PRs are required                                    |
| **Allow force pushes**     | Disabled | Protects history on `main`                                          |
| **Allow deletions**        | Disabled | Prevents accidental branch deletion                                 |

### Merge Strategy (Companion Settings)

These are configured separately in Settings → General → Pull Requests, but work together with branch protection:

| Setting                       | Value    | Why                                   |
| ----------------------------- | -------- | ------------------------------------- |
| **Allow rebase merging**      | Enabled  | The only permitted strategy (ADR 022) |
| **Allow merge commits**       | Disabled | Would create non-linear history       |
| **Allow squash merging**      | Disabled | Would lose individual commit detail   |
| **Auto-delete head branches** | Enabled  | Cleans up after merge                 |

## Consequences

### Positive

- **Enforces the release pipeline** — commits on `main` always arrive via reviewed PRs, so release-please can trust them
- **CI is authoritative** — even if pre-commit hooks are bypassed locally, CI catches issues before merge
- **Linear history guaranteed** — `Require linear history` prevents merge commits at the platform level
- **Audit trail** — every change on `main` has an associated PR with review history
- **No accidents** — prevents force-push to `main`, accidental direct pushes, and branch deletion

### Negative

- **Friction for solo maintainers** — even the only contributor must open a PR (mitigated: disable "Do not allow bypassing" if working solo)
- **Admin bypass risk** — admins can bypass protection unless "Do not allow bypassing" is enabled
- **Status check maintenance** — adding or renaming CI workflows requires updating the required checks list
- **Stale PRs** — "Require branches to be up to date" means PRs need rebasing when `main` moves ahead (mitigated: GitHub's "Update branch" button)

## References

- [GitHub: About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub: About rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
- [ADR 022 — Rebase and merge strategy](022-rebase-merge-strategy.md)
- [ADR 021 — Automated release pipeline](021-automated-release-pipeline.md)
- [ADR 009 — Conventional commits](009-conventional-commits.md)
- [Releasing guide](../releasing.md)
