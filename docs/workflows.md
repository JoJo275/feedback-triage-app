# GitHub Actions Workflows

<!-- This file is the canonical reference for the project's workflow inventory.
     Keep it in sync whenever workflows are added, removed, or renamed.
     copilot-instructions.md and docs/design/architecture.md reference this file. -->

This project has **37 workflow files** in `.github/workflows/`. All workflows
follow the conventions described at the bottom of this page. Configure these workflows in their respective `.yml` file.

---

## Workflow Inventory

### Quality

| Workflow               | File                                                                  | Triggers         | Job name(s)                            | Purpose                                         |
| ---------------------- | --------------------------------------------------------------------- | ---------------- | -------------------------------------- | ----------------------------------------------- |
| **Test**               | [test.yml](../.github/workflows/test.yml)                             | push, PR, manual | `Test (Python 3.11)` / `3.12` / `3.13` | Runs pytest across Python 3.11–3.13 matrix      |
| **Lint + Format**      | [lint-format.yml](../.github/workflows/lint-format.yml)               | push, PR, manual | `Ruff (lint & format)`                 | Ruff linting and format checks                  |
| **Type Check**         | [type-check.yml](../.github/workflows/type-check.yml)                 | push, PR, manual | `mypy (strict)`                        | mypy strict mode against `src/`                 |
| **Coverage**           | [coverage.yml](../.github/workflows/coverage.yml)                     | push, PR, manual | `Test + upload coverage`               | pytest with coverage, uploads to Codecov        |
| **Spellcheck**         | [spellcheck.yml](../.github/workflows/spellcheck.yml)                 | push, PR, manual | `Spell check (codespell)`              | Fails CI on spelling mistakes                   |
| **Spellcheck Autofix** | [spellcheck-autofix.yml](../.github/workflows/spellcheck-autofix.yml) | weekly, manual   | `Auto-fix typos`                       | Creates a PR to auto-fix spelling mistakes      |
| **TODO Check**         | [todo-check.yml](../.github/workflows/todo-check.yml)                 | push, PR, manual | `Check template TODOs`                 | Reports remaining TODO (template users) markers |
| **Smoke Test**         | [smoke-test.yml](../.github/workflows/smoke-test.yml)                 | push (path-filtered), PR (path-filtered), manual | `Script Smoke Test` | Runs `--smoke` on scripts to validate imports and argparse ([ADR 042](adr/042-script-smoke-testing.md)) |

### Security

| Workflow              | File                                                                | Triggers                                                 | Job name(s)                                                                                              | Purpose                                                  |
| --------------------- | ------------------------------------------------------------------- | -------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| **Security Audit**    | [security-audit.yml](../.github/workflows/security-audit.yml)       | push, PR, weekly, manual                                 | `pip-audit`                                                                                              | Checks Python deps against OSV/PyPI vuln databases       |
| **Bandit**            | [bandit.yml](../.github/workflows/bandit.yml)                       | push (path-filtered), PR (path-filtered), daily, manual  | `Bandit security scan`                                                                                   | Static security analysis for Python source               |
| **Dependency Review** | [dependency-review.yml](../.github/workflows/dependency-review.yml) | PR                                                       | `Scan dependencies`                                                                                      | Scans PRs for vulnerable or risky new dependencies       |
| **CodeQL**            | [security-codeql.yml](../.github/workflows/security-codeql.yml)     | push, PR, weekly                                         | `CodeQL Analysis`                                                                                        | GitHub CodeQL static analysis                            |
| **Container Scan**    | [container-scan.yml](../.github/workflows/container-scan.yml)       | push, PR, weekly, manual                                 | `Build container image`, `Trivy vulnerability scan`, `Grype vulnerability scan`, `Dockerfile / IaC lint` | Multi-scanner container security pipeline                |
| **Nightly Security**  | [nightly-security.yml](../.github/workflows/nightly-security.yml)   | daily, manual                                            | Multiple (SBOM rescan, pip-audit, container scans)                                                       | Consolidated nightly sweep against latest vuln databases |
| **OpenSSF Scorecard** | [scorecard.yml](../.github/workflows/scorecard.yml)                 | push (main), weekly, manual                              | `Scorecard analysis`                                                                                     | Evaluates repo security practices via OpenSSF Scorecard  |
| **License Check**     | [license-check.yml](../.github/workflows/license-check.yml)         | push (path-filtered), PR (path-filtered), weekly, manual | `Verify dependency licenses`                                                                             | Verifies dependency licenses are compatible with project |

### PR Hygiene

| Workflow        | File                                                    | Triggers | Job name(s)                 | Purpose                                              |
| --------------- | ------------------------------------------------------- | -------- | --------------------------- | ---------------------------------------------------- |
| **PR Title**    | [pr-title.yml](../.github/workflows/pr-title.yml)       | PR       | `Conventional commit check` | Enforces conventional commit format on PR titles     |
| **Commit Lint** | [commit-lint.yml](../.github/workflows/commit-lint.yml) | PR       | `Validate commit messages`  | Validates all PR commits follow Conventional Commits |
| **Labeler**     | [labeler.yml](../.github/workflows/labeler.yml)         | PR       | `Auto-label PR`             | Auto-labels PRs based on changed file paths          |

### Release

| Workflow           | File                                                          | Triggers                 | Job name(s)                                                                                | Purpose                                            |
| ------------------ | ------------------------------------------------------------- | ------------------------ | ------------------------------------------------------------------------------------------ | -------------------------------------------------- |
| **Release Please** | [release-please.yml](../.github/workflows/release-please.yml) | push (main)              | `Create or update Release PR`                                                              | Automates version bump, changelog, and git tags    |
| **Release**        | [release.yml](../.github/workflows/release.yml)               | tag push (`v*`), manual  | `Build distribution`, `Publish to PyPI`, `Generate release SBOMs`, `Upload release assets` | Builds sdist + wheel, optionally publishes to PyPI |
| **SBOM**           | [sbom.yml](../.github/workflows/sbom.yml)                     | push, PR, weekly, manual | `Generate SBOMs`                                                                           | Generates SPDX + CycloneDX SBOMs                   |

### Documentation

| Workflow        | File                                                    | Triggers                           | Job name(s)                                       | Purpose                                                         |
| --------------- | ------------------------------------------------------- | ---------------------------------- | ------------------------------------------------- | --------------------------------------------------------------- |
| **Docs Build**  | [docs-build.yml](../.github/workflows/docs-build.yml)   | push, PR, manual                   | `Build docs`                                      | Builds MkDocs site with `--strict` mode (CI gate quality check) |
| **Docs Deploy** | [docs-deploy.yml](../.github/workflows/docs-deploy.yml) | push (main, path-filtered), manual | `Build docs for deploy`, `Deploy to GitHub Pages` | Builds and deploys MkDocs site to GitHub Pages on push to main  |

### Container

| Workflow                | File                                                                  | Triggers                               | Job name(s)             | Purpose                                                    |
| ----------------------- | --------------------------------------------------------------------- | -------------------------------------- | ----------------------- | ---------------------------------------------------------- |
| **Container Build**     | [container-build.yml](../.github/workflows/container-build.yml)       | push (main + tags), PR, manual         | `Build container image` | Builds OCI container image, pushes to ghcr.io on main/tags |
| **Dev Container Build** | [devcontainer-build.yml](../.github/workflows/devcontainer-build.yml) | push (main, path-filtered), PR, manual | `Build dev container`   | Validates dev container config builds and runs correctly   |

### Maintenance

| Workflow                  | File                                                                        | Triggers                                                 | Job name(s)                   | Purpose                                                                                       |
| ------------------------- | --------------------------------------------------------------------------- | -------------------------------------------------------- | ----------------------------- | --------------------------------------------------------------------------------------------- |
| **Pre-commit Update**     | [pre-commit-update.yml](../.github/workflows/pre-commit-update.yml)         | weekly, manual                                           | `Auto-update hooks`           | Runs `pre-commit autoupdate` and opens a PR                                                   |
| **Stale**                 | [stale.yml](../.github/workflows/stale.yml)                                 | daily, manual                                            | `Close stale issues & PRs`    | Marks and closes inactive issues/PRs                                                          |
| **Link Checker**          | [link-checker.yml](../.github/workflows/link-checker.yml)                   | push (path-filtered), PR (path-filtered), weekly, manual | `Check links`                 | Checks Markdown/HTML for broken links using lychee                                            |
| **Auto-merge Dependabot** | [auto-merge-dependabot.yml](../.github/workflows/auto-merge-dependabot.yml) | pull_request_target                                      | `Auto-approve & merge`        | Auto-approves and squash-merges minor/patch Dependabot PRs once CI passes                     |
| **Cache Cleanup**         | [cache-cleanup.yml](../.github/workflows/cache-cleanup.yml)                 | PR closed, manual                                        | `Clean branch caches`         | Deletes GitHub Actions caches for closed/merged PR branches to prevent cache eviction of main |
| **Regenerate Files**      | [regenerate-files.yml](../.github/workflows/regenerate-files.yml)           | weekly, manual                                           | `Regenerate derived files`    | Regenerates requirements.txt and requirements-dev.txt from pyproject.toml and opens a PR      |
| **Known Issues Check**    | [known-issues-check.yml](../.github/workflows/known-issues-check.yml)       | weekly, tag push (v\*), manual                           | `Check stale resolved issues` | Flags stale entries in docs/known-issues.md Resolved table                                    |
| **Repo Doctor**           | [repo-doctor.yml](../.github/workflows/repo-doctor.yml)                     | push, PR, manual                                         | `Repo health check`           | Warn-only repo structure checks (missing files, broken conventions)                           |
| **Doctor All**            | [doctor-all.yml](../.github/workflows/doctor-all.yml)                       | push, PR, weekly, manual                                 | `Full health check`           | Runs all doctor scripts (env, repo, git, TODOs, known issues, diagnostics) — warn-only        |

### Community

| Workflow    | File                                            | Triggers                | Job name(s)                       | Purpose                                                               |
| ----------- | ----------------------------------------------- | ----------------------- | --------------------------------- | --------------------------------------------------------------------- |
| **Welcome** | [welcome.yml](../.github/workflows/welcome.yml) | issue opened, PR opened | `Welcome first-time contributors` | Posts a welcome comment on first-time contributors' first issue or PR |

### Gate

| Workflow    | File                                            | Triggers         | Job name(s) | Purpose                                                                                       |
| ----------- | ----------------------------------------------- | ---------------- | ----------- | --------------------------------------------------------------------------------------------- |
| **CI Gate** | [ci-gate.yml](../.github/workflows/ci-gate.yml) | PR, push, manual | `gate`      | Single fan-in "all-green" check for branch protection ([ADR 024](adr/024-ci-gate-pattern.md)) |

---

## CI Gate: Required Checks

The CI gate ([ADR 024](adr/024-ci-gate-pattern.md)) polls for these job
display names. Branch protection only requires `gate` — not individual checks.

Each required workflow's `name:` line is tagged with `# ci-gate: required`.
Grep for that marker to audit which workflows are coupled to the gate:

```bash
# Unix / Git Bash
grep -r 'ci-gate: required' .github/workflows/

# PowerShell
Select-String -Path ".github\workflows\*.yml" -Pattern "ci-gate: required"
```

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
| `Build docs`                | docs-build.yml        |

**Excluded from gate** (path-filtered, schedule-only, or warn-only — don't run on every PR or don't block):

- `bandit.yml` — only runs on `src/**`, `scripts/**`, `experiments/**`, `pyproject.toml` changes
- `docs-deploy.yml` — only runs on `docs/**`, `mkdocs.yml`, `src/**/*.py`, `pyproject.toml` changes (deploy only)
- `link-checker.yml` — only runs on `**/*.md`, `**/*.html`, `docs/**` changes
- `license-check.yml` — only runs on `pyproject.toml`, `requirements*.txt` changes
- `known-issues-check.yml` — schedule + tag-push only (no PR trigger)
- `todo-check.yml` — non-blocking (continue-on-error); informational only
- `smoke-test.yml` — only runs on `scripts/**` changes (path-filtered)
- `repo-doctor.yml` — warn-only (always exits 0); informational only
- `doctor-all.yml` — warn-only (all steps continue-on-error); informational only
- `welcome.yml` — community engagement; no quality gate relevance

These still report status when they run and also run on push to main + schedules.

---

## Dependabot

Not a workflow, but automated dependency updates via
[dependabot.yml](../.github/dependabot.yml):

- **GitHub Actions** — Weekly updates, grouped by minor/patch
- **Python (pip)** — Weekly updates for dependencies

---

## Workflow Conventions

All workflows in this project follow these patterns:

| Convention                     | Detail                                                                                                                                                                   |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **SHA-pinned actions**         | Full commit SHAs with human-readable version comments ([ADR 004](adr/004-pin-action-shas.md))                                                                            |
| **Repository guard**           | Workflows are disabled by default via `YOURNAME/YOURREPO` slug check; enable with repo slug or `vars.ENABLE_*` variable ([ADR 011](adr/011-repository-guard-pattern.md)) |
| **Concurrency control**        | `cancel-in-progress: true` per workflow + ref                                                                                                                            |
| **Timeout limits**             | `timeout-minutes` set on every job                                                                                                                                       |
| **Minimal permissions**        | `permissions: contents: read` (least privilege)                                                                                                                          |
| **Persist-credentials: false** | On all checkout steps                                                                                                                                                    |
| **Manual triggers**            | Most workflows include `workflow_dispatch` for manual runs (exceptions: PR-only workflows like `dependency-review`, `labeler`, `pr-title`, `commit-lint`)                |
| **Header comments**            | Each file has a comment block explaining purpose, triggers, and TODO instructions for template users                                                                     |

### File Naming

| Pattern        | Meaning         |
| -------------- | --------------- |
| `workflow.yml` | Active workflow |

### Adding New Workflows

1. Create a new `.yml` file in `.github/workflows/`
2. Follow the conventions above — copy an existing workflow as a starting point
3. Pin actions to full SHAs (not tags) — use `scripts/workflow_versions.py` to manage
   (see [Managing Action Versions](#managing-action-versions) below)
4. Add the repository guard pattern
5. Add minimal required permissions
6. Include concurrency and timeout settings
7. If the workflow should block PRs, add its job `name:` to `REQUIRED_CHECKS` in `ci-gate.yml`
   and tag the `name:` line with `# ci-gate: required`
8. Update this file and `copilot-instructions.md`

---

## Managing Action Versions

All GitHub Actions are pinned to full commit SHAs ([ADR 004](adr/004-pin-action-shas.md)).
`scripts/workflow_versions.py` manages the version comments and upgrades.

### Commands

| Task                  | Command                                           | What it does                                            |
| --------------------- | ------------------------------------------------- | ------------------------------------------------------- |
| **Show versions**     | `task actions:versions`                           | List all pinned actions with current and latest tags    |
| **Show (offline)**    | `task actions:versions -- --offline`              | Skip GitHub API calls                                   |
| **Show (JSON)**       | `task actions:versions -- --json`                 | Machine-readable output                                 |
| **Filter stale**      | `task actions:versions -- --filter stale`         | Show only stale/missing comment actions                 |
| **Filter upgradable** | `task actions:versions -- --filter upgradable`    | Show only upgradable actions                            |
| **CI check**          | `task actions:check`                              | Exit non-zero if stale or upgradable (CI gate shortcut) |
| **Update comments**   | `task actions:update-comments`                    | Sync `# vX.Y.Z` comments and add action descriptions    |
| **Upgrade all**       | `task actions:upgrade`                            | Upgrade all actions to latest release                   |
| **Upgrade (preview)** | `task actions:upgrade:dry-run`                    | Preview upgrades without modifying files                |
| **Upgrade one**       | `task actions:upgrade -- actions/checkout`        | Upgrade a specific action                               |
| **Pin version**       | `task actions:upgrade -- actions/checkout v6.1.0` | Pin to a specific version                               |

### Typical workflow after Dependabot updates

Dependabot updates SHAs but not the version comments. After merging a
Dependabot PR:

```bash
task actions:update-comments   # sync comments to match new SHAs
```

### Color output

Color is auto-detected. Use `--color` to force it or `--no-color` to disable.
Respects `NO_COLOR` and `FORCE_COLOR` environment variables.

> **Tip:** Set `GITHUB_TOKEN` for higher API rate limits (5,000/hr vs 60/hr unauthenticated).
> The remaining rate limit is displayed at the end of each run.

### Quiet / CI mode

Use `--quiet` (or `-q`) to suppress all table and summary output.
The exit code indicates status: **0** = all OK, **1** = stale or upgradable actions found.
Status and progress messages are sent to stderr.
This is useful for CI gates:

```bash
python scripts/workflow_versions.py show --quiet || echo "Actions need attention"
```

---

## Local Health Scripts

These scripts complement the CI workflows above by providing instant
local diagnostics. The `doctor-all.yml` workflow runs all of them in CI.

| Script                   | Task shortcut      | Purpose                                         |
| ------------------------ | ------------------ | ----------------------------------------------- |
| `scripts/env_doctor.py`  | `task doctor:env`  | Check Python, Hatch, tools, editable install    |
| `scripts/repo_doctor.py` | `task doctor:repo` | Verify repo structure and conventions           |
| `scripts/git_doctor.py`  | `task doctor:git`  | Git health dashboard, branch stats, remote sync |
| `scripts/doctor.py`      | `task doctor`      | Diagnostics bundle (for bug reports)            |

### git_doctor.py Commands

`git_doctor.py` is the most feature-rich local script. Key Taskfile shortcuts:

| Task                             | What it does                                  |
| -------------------------------- | --------------------------------------------- |
| `task doctor:git`                | Dashboard: branches, remotes, health checks   |
| `task doctor:git:watch`          | Auto-refresh dashboard every N seconds        |
| `task doctor:git:refresh`        | Fetch remotes, prune refs, sync tags          |
| `task doctor:git:cleanup`        | Delete stale branches, run `git gc`           |
| `task doctor:git:commits`        | Detailed commit report (SHAs, stats)          |
| `task doctor:git:commits:md`     | Write commit report to `commit-report.md`     |
| `task doctor:git:config:export`  | Export git config reference to Markdown       |
| `task doctor:git:config:apply`   | Apply recommended git config                  |
| `task doctor:git:config:minimal` | Apply core subset (12 keys)                   |
| `task branch:create`             | Interactive branch creation off `origin/main` |

All commands support `--dry-run` where applicable. Pass extra flags with
`task doctor:git -- --json` or `task doctor:git:cleanup -- --dry-run`.

---

## See Also

- [Architecture — CI/CD section](design/architecture.md) — CI/CD architecture diagram
- [Releasing](releasing.md) — Release workflow details
- [SBOM Strategy](sbom.md) — SBOM formats, channels, and authoritative source
- [tooling.md](tooling.md) — All tools at a glance (many run via these workflows)
- [USING_THIS_TEMPLATE.md](USING_THIS_TEMPLATE.md) — Workflow enablement, disabling, and categories
- [ADR 003](adr/003-separate-workflow-files.md) — Why separate workflow files
- [ADR 004](adr/004-pin-action-shas.md) — Why pin to SHAs
- [ADR 011](adr/011-repository-guard-pattern.md) — Repository guard pattern
- [ADR 013](adr/013-sbom-bill-of-materials.md) — SBOM strategy (SPDX + CycloneDX)
- [ADR 024](adr/024-ci-gate-pattern.md) — CI gate pattern
