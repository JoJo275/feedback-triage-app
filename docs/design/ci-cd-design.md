# CI/CD Design

Detailed design of the continuous integration and delivery pipeline,
covering workflow architecture, the repository guard pattern, the CI gate,
and guidance for extending or modifying the pipeline.

<!-- TODO (template users): Update this document to reflect your actual
     CI/CD pipeline after customizing workflows. Remove sections that
     don't apply and add any project-specific pipeline stages. -->

---

## Design Goals

<!-- TODO (template users): Add or remove goals that match your project's
     CI/CD requirements. For example, if you don't use forks you may
     not need the repository guard pattern. -->

| Goal                      | How it's achieved                                                                                       |
| ------------------------- | ------------------------------------------------------------------------------------------------------- |
| **Safe by default**       | Repository guards disable workflows on forks/clones ([ADR 011](../adr/011-repository-guard-pattern.md)) |
| **Single required check** | CI gate aggregates all checks into one `gate` status ([ADR 024](../adr/024-ci-gate-pattern.md))         |
| **Independent failure**   | Each concern has its own workflow file ([ADR 003](../adr/003-separate-workflow-files.md))               |
| **Supply-chain security** | All actions pinned to full commit SHAs ([ADR 004](../adr/004-pin-action-shas.md))                       |
| **Minimal permissions**   | Each workflow declares only the permissions it needs                                                    |
| **Fast feedback**         | Concurrency groups cancel superseded runs; path filters skip irrelevant workflows                       |

---

## Pipeline Architecture

### PR / Push Flow

When a PR is opened or code is pushed to `main`, these workflows run in
parallel — there are no sequential dependencies between them:

```
PR opened / push to main
  │
  ├── Quality ──────────────────────────────────
  │   ├── test.yml          (pytest × 3.11, 3.12, 3.13)
  │   ├── lint-format.yml   (Ruff lint + format)
  │   ├── type-check.yml    (mypy strict)
  │   ├── coverage.yml      (pytest-cov → Codecov)
  │   └── spellcheck.yml    (codespell)
  │
  ├── Security ─────────────────────────────────
  │   ├── security-audit.yml    (pip-audit)
  │   ├── dependency-review.yml (license + vuln scan)
  │   ├── security-codeql.yml   (CodeQL)
  │   ├── bandit.yml            (path-filtered: src/, scripts/)
  │   └── container-scan.yml    (Trivy + Grype)
  │
  ├── PR Hygiene ───────────────────────────────
  │   ├── pr-title.yml      (Conventional Commits title)
  │   ├── commit-lint.yml   (commit message validation)
  │   ├── labeler.yml       (auto-label by path)
  │   └── auto-merge-dependabot.yml (auto-approve minor/patch)
  │
  ├── Build ────────────────────────────────────
  │   ├── container-build.yml (OCI image build)
  │   └── docs-build.yml     (MkDocs --strict)
  │
  └── Gate ─────────────────────────────────────
      └── ci-gate.yml        (polls Checks API → single pass/fail)
```

### Release Flow

Releases are fully automated via release-please:

```
Push to main (conventional commit)
  └── release-please.yml
        ├── Creates/updates Release PR (version bump + changelog)
        └── On merge → creates git tag (v1.2.3)
              └── Tag triggers:
                    ├── release.yml → build sdist + wheel + GitHub Release
                    └── sbom.yml   → generate SPDX + CycloneDX SBOMs
```

### Scheduled Workflows

These run on cron schedules independent of code changes:

| Workflow                 | Schedule | Purpose                                                                |
| ------------------------ | -------- | ---------------------------------------------------------------------- |
| `nightly-security.yml`   | Daily    | Comprehensive security sweep (SBOM rescan, pip-audit, container scans) |
| `security-codeql.yml`    | Weekly   | Deep semantic analysis                                                 |
| `scorecard.yml`          | Weekly   | OpenSSF supply-chain security scoring                                  |
| `security-audit.yml`     | Weekly   | pip-audit against latest vuln databases                                |
| `pre-commit-update.yml`  | Weekly   | Auto-update pre-commit hooks, opens PR                                 |
| `spellcheck-autofix.yml` | Weekly   | Auto-fix typos via codespell, opens PR                                 |
| `stale.yml`              | Daily    | Mark/close inactive issues and PRs                                     |
| `link-checker.yml`       | Weekly   | Validate URLs in documentation                                         |
| `regenerate-files.yml`   | Weekly   | Regenerate requirements.txt files from pyproject.toml                  |

### Event-Driven Workflows

These workflows trigger on specific repository events:

| Workflow                    | Trigger              | Purpose                                                    |
| --------------------------- | -------------------- | ---------------------------------------------------------- |
| `cache-cleanup.yml`         | PR closed            | Clean up GitHub Actions caches for closed PR branches      |
| `auto-merge-dependabot.yml` | Dependabot PR opened | Auto-approve + squash-merge minor/patch dependency updates |
| `docs-deploy.yml`           | Push to main         | Deploy documentation to GitHub Pages (path-filtered)       |

---

## Repository Guard Pattern

Every optional workflow includes a guard condition that prevents execution
unless the repository has explicitly opted in. This is critical for template
repositories — without it, workflows would fail with confusing errors on
fresh forks.

### How It Works

Each job starts with an `if:` condition:

```yaml
jobs:
    my-job:
        if: >-
            ${{
              github.repository == 'YOURNAME/YOURREPO'
              || vars.ENABLE_WORKFLOWS == 'true'
              || vars.ENABLE_MY_WORKFLOW == 'true'
            }}
```

The three opt-in methods (in order of convenience):

1. **Replace the slug** — edit `YOURNAME/YOURREPO` to your actual repo
   slug, or run `scripts/customize.py --enable-workflows OWNER/REPO`.
2. **Global variable** — set `vars.ENABLE_WORKFLOWS = 'true'` to enable
   all guarded workflows at once.
3. **Per-workflow variable** — set `vars.ENABLE_<NAME> = 'true'` for
   granular control (e.g. `ENABLE_STALE`, `ENABLE_TEST`).

### Which Workflows Are Guarded

All 37 workflows use the guard — no workflow runs by default on a
fresh fork or clone.

<!-- TODO (template users): After enabling workflows via customize.py or
     ENABLE_WORKFLOWS variable, verify the guard is working by checking
     the Actions tab. Remove this comment once your workflows are active. -->

Core quality workflows (test, lint, type-check) are guarded for
consistency with the template pattern, even though most users will want
them active immediately. The global `ENABLE_WORKFLOWS` variable
activates everything in one step.

### Guard Evaluation Order

GitHub evaluates the `if:` condition left to right with short-circuit
evaluation. The slug check is first (cheapest), then the global variable,
then the per-workflow variable.

---

## CI Gate Design

The CI gate solves a specific problem: branch protection requires listing
individual check names, which creates maintenance friction as workflows
are added, removed, or renamed.

### How It Works

1. `ci-gate.yml` triggers on the same events as other workflows (PR, push)
2. It uses `actions/github-script` to poll the GitHub Checks API
3. It looks for a configurable list of required check names (job display names)
4. Reports a single `gate` status: pass / fail / pending
5. Branch protection only requires `gate` — one check, not dozens

### Required Checks List

The list of checks the gate monitors is maintained in `ci-gate.yml` as the
`REQUIRED_CHECKS` variable. When adding or removing workflows:

1. Update `REQUIRED_CHECKS` in `ci-gate.yml`
2. Tag required workflow jobs with `# ci-gate: required` in their `name:` line
3. Verify with: `grep -r 'ci-gate: required' .github/workflows/`

### Path-Filtered Workflows and the Gate

Workflows with path filters (bandit, link-checker, docs-deploy) are
**excluded** from the CI gate because they don't run on every PR. If they
were listed as required, the gate would wait forever for a check that never
arrives on unrelated PRs.

These workflows still provide value:

- Report status when they run (visible on the PR)
- Run on `push` to `main` and on schedules — nothing slips through permanently
- Reviewers can see failures and block merge manually

---

## Concurrency and Cancellation

All workflows use concurrency groups to cancel superseded runs:

```yaml
concurrency:
    group: ${{ github.workflow }}-${{ github.ref }}
    cancel-in-progress: true
```

This means: if you push two commits in quick succession, the first run is
cancelled and only the second runs. This saves Actions minutes and provides
faster feedback.

---

## Permissions Model

Each workflow declares the minimum permissions it needs:

```yaml
permissions:
    contents: read # Most workflows only need to read code
```

Workflows that need more (e.g. creating PRs, pushing to registries) declare
additional permissions explicitly. The repository's default Actions
permissions should be set to "Read repository contents" — workflows
escalate only when needed.

---

## Adding a New Workflow

<!-- TODO (template users): After customizing your pipeline, update the
     checklist below to reflect your actual workflow patterns, required
     checks, and documentation locations. -->

When adding a workflow to this project:

1. **Create the file** in `.github/workflows/` following the naming convention
   (`<concern>.yml`)
2. **Add the repository guard** — copy the `if:` block from an existing
   workflow and update the `ENABLE_<NAME>` variable name
3. **Pin all actions** to full commit SHAs — never use tags like `@v4`
4. **Add concurrency group** to cancel superseded runs
5. **Set minimal permissions** — start with `contents: read` and add
   only what's needed
6. **Decide if it's required** — if it should block PRs, add the job
   display name to `REQUIRED_CHECKS` in `ci-gate.yml` and tag the
   `name:` line with `# ci-gate: required`
7. **Update documentation:**
    - [workflows.md](../workflows.md) — add to the workflow inventory
    - [architecture.md](architecture.md) — update the CI/CD diagram if
      the new workflow fits a different category
    - [tool-decisions.md](tool-decisions.md) — if the workflow introduces
      a new tool, document the tool choice rationale
    - [copilot-instructions.md](../../.github/copilot-instructions.md) — update
      the workflow categories summary

### SHA-Pinning Actions

Always pin to the full 40-character commit SHA, not a tag:

```yaml
# Good — pinned to exact commit
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2

# Bad — tag can be moved
- uses: actions/checkout@v4
```

Use `task actions:versions` or `scripts/workflow_versions.py` to audit
current SHAs and check for updates.

---

## Extending the Pipeline

<!-- TODO (template users): Replace or extend these subsections with
     deployment, staging, and production pipeline stages specific to
     your project (e.g., deploy to AWS/GCP/Azure, run E2E tests,
     publish to PyPI). -->

### Adding a Test Stage

To add a new test dimension (e.g. integration tests, OS matrix):

1. Create a new workflow or add a matrix dimension to `test.yml`
2. If it should be required, add the job name to `ci-gate.yml`'s
   `REQUIRED_CHECKS`

### Adding a Deploy Stage

For deployment workflows:

1. Create a new workflow triggered by tags or workflow_dispatch
2. Use environment protection rules for production deploys
3. Add required secrets as repository secrets (not variables)
4. Consider requiring manual approval via GitHub Environments

### Adding External Service Integration

For services like Codecov, Snyk, or SonarCloud:

1. Add the workflow with appropriate triggers
2. Store API tokens as repository secrets
3. Add the guard pattern for template compatibility
4. Document the required setup in the workflow's header comment

---

## Troubleshooting

<!-- TODO (template users): Add project-specific troubleshooting entries
     as you encounter CI failures unique to your setup. -->

### Common Issues

| Problem                                  | Cause                               | Fix                                                                      |
| ---------------------------------------- | ----------------------------------- | ------------------------------------------------------------------------ |
| Workflow doesn't run                     | Repository guard blocking           | Set `ENABLE_WORKFLOWS = 'true'` or update repo slug                      |
| CI gate times out                        | Required check name changed         | Update `REQUIRED_CHECKS` in `ci-gate.yml` to match new name              |
| Path-filtered workflow skipped           | PR doesn't touch filtered paths     | Expected behavior — these only run on relevant changes                   |
| "Resource not accessible by integration" | Insufficient permissions            | Add the needed permission to the workflow's `permissions:` block         |
| Duplicate runs on PR                     | Both `push` and `pull_request` fire | Use concurrency groups (already configured) — the duplicate is cancelled |
| Dependabot PR not auto-merged            | CI checks failing or major bump     | Fix CI failures; major version bumps require manual review               |
| Stale workflow closes active issue       | No activity within stale period     | Comment on the issue to reset the timer, or add `pinned` label           |

### Debugging Workflow Failures

1. Check the Actions tab for the specific run's logs
2. Look for the repository guard — if the job shows "skipped", opt in
3. For CI gate issues, check which required checks are missing or pending
4. Use `actionlint` locally to catch YAML/expression errors before pushing:

    ```bash
    actionlint .github/workflows/my-workflow.yml
    ```

---

## Related Documentation

- [Workflows Inventory](../workflows.md) — canonical list of all workflows
- [Architecture](architecture.md) — system overview including CI/CD diagram
- [Tool Decisions](tool-decisions.md) — why specific CI tools were chosen
- [ADR 003](../adr/003-separate-workflow-files.md) — separate workflow files
- [ADR 004](../adr/004-pin-action-shas.md) — SHA-pinned actions
- [ADR 010](../adr/010-dependabot-for-dependency-updates.md) — Dependabot
- [ADR 011](../adr/011-repository-guard-pattern.md) — repository guard pattern
- [ADR 012](../adr/012-multi-layer-security-scanning.md) — multi-layer security scanning
- [ADR 024](../adr/024-ci-gate-pattern.md) — CI gate pattern
