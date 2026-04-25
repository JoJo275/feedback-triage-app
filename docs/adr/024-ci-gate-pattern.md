# ADR 024: CI gate pattern for branch protection

## Status

Accepted

## Context

Branch protection (ADR 023) requires listing every CI workflow that must pass before a PR can merge. As the project grows, this creates maintenance friction:

- **Adding a workflow** requires a trip to Settings → Branches → Edit protection → add the new check name.
- **Renaming a workflow job** silently breaks protection — the old name is "pending" forever, the new name isn't required.
- **Path-filtered workflows** (bandit, link-checker) don't run on every PR, so they can't be listed as required without blocking unrelated changes.

We evaluated three approaches:

| Approach                          | How it works                                                             | Trade-off                                                                                     |
| --------------------------------- | ------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------- |
| **List every check individually** | Add each job name to branch protection                                   | Must update Settings whenever a workflow changes; path-filtered workflows block unrelated PRs |
| **Mega-workflow**                 | One `ci.yml` with `needs:` between all jobs                              | Loses per-workflow triggers, permissions, and independent failure isolation (ADR 003)         |
| **Fan-in gate**                   | A thin polling job watches the Checks API and reports a single pass/fail | One required check in branch protection; workflow list maintained in code, not Settings       |

## Decision

Add a **ci-gate workflow** (`ci-gate.yml`) that:

1. Triggers on `pull_request` and `push` to `main` (same as most check workflows).
2. Uses `actions/github-script` to poll the GitHub Checks API for a configurable list of required check names.
3. Reports a single `gate` status: pass if all required checks pass, fail if any fail, wait if any are pending.

In branch protection, only **`gate`** is set as the required status check.

### What goes in the required list

Workflows that **always run on every PR** are listed as required:

| Check name                  | Workflow              |
| --------------------------- | --------------------- |
| `Ruff (lint & format)`      | lint-format.yml       |
| `mypy (strict)`             | type-check.yml        |
| `Spell check (codespell)`   | spellcheck.yml        |
| `Test + upload coverage`    | coverage.yml          |
| `Test (Python 3.11)`        | test.yml              |
| `Test (Python 3.12)`        | test.yml              |
| `Test (Python 3.13)`        | test.yml              |
| `pip-audit`                 | security-audit.yml    |
| `Scan dependencies`         | dependency-review.yml |
| `Build container image`     | container-build.yml   |
| `Conventional commit check` | pr-title.yml          |
| `Validate commit messages`  | commit-lint.yml       |

### What stays outside the gate

**Path-filtered workflows** are excluded because they don't run on every PR. If they ran, the gate would wait forever for a check that will never appear:

| Workflow         | Path filter                                                | Why excluded                            |
| ---------------- | ---------------------------------------------------------- | --------------------------------------- |
| bandit.yml       | `src/**`, `scripts/**`, `experiments/**`, `pyproject.toml` | Doesn't run on docs-only or CI-only PRs |
| link-checker.yml | `**/*.md`, `**/*.html`, `docs/**`                          | Doesn't run on code-only PRs            |

These workflows still provide value:

- They report status when they _do_ run (visible red ✗ on the PR).
- They run on `push` to `main` and on a weekly schedule, so nothing slips through permanently.
- Reviewers can see the red check and block merge manually.

### Why not a mega-workflow

A single file with `needs:` between all jobs would:

- Violate ADR 003 (separate workflow files per concern)
- Force all jobs onto the same trigger — losing path filters, independent schedules, and per-workflow permissions
- Make diffs noisier and debugging harder
- Require a full CI re-run when any single job is re-triggered

The fan-in gate preserves full independence of every workflow file while centralising the "is everything green?" question.

## Consequences

### Positive

- **One required check** — Branch protection only references `gate`; no Settings changes when workflows are added, removed, or renamed
- **Workflow list in code** — The `REQUIRED_CHECKS` array is version-controlled, reviewable, and self-documenting
- **Preserves ADR 003** — Every workflow keeps its own file, triggers, and permissions
- **Graceful with path filters** — Path-filtered workflows are simply omitted from the list
- **Self-healing** — If a check is re-run, the gate picks up the latest result automatically

### Negative

- **Polling delay** — The gate polls every 15 seconds; adds ~15 s of latency after the last check finishes
- **API rate limits** — Each poll is one Checks API call; 120 polls × 15 s = 30 min ceiling. Well within GitHub's 1,000 requests/hour limit for `GITHUB_TOKEN`.
- **Name coupling** — `REQUIRED_CHECKS` references job _display names_, which can drift if someone renames a job's `name:` field without updating the gate. Mitigated by code review and the fact that the gate will fail loudly (timeout) if a name is wrong.
- **Doesn't enforce path-filtered checks** — bandit and link-checker failures are advisory, not blocking. Acceptable because they also run on push to `main` and on schedules.

## Implementation

- [.github/workflows/ci-gate.yml](../../.github/workflows/ci-gate.yml) — Fan-in gate workflow
- [ADR 023](023-branch-protection-rules.md) — Branch protection rules (update required checks to reference `gate` only)

## References

- [GitHub Checks API](https://docs.github.com/en/rest/checks/runs)
- [actions/github-script](https://github.com/actions/github-script)
- [ADR 003 — Separate workflow files](003-separate-workflow-files.md)
- [ADR 023 — Branch protection rules](023-branch-protection-rules.md)
