# Workflows

<!-- TODO (template users): Update this file after removing or adding
     workflows. Keep it in sync with docs/workflows.md. -->

Overview of all GitHub Actions workflows in this repository.

## Quick Reference

### Code Quality (run on every push/PR)

| Workflow          | File                               | Triggers         | What it does                                  |
| ----------------- | ---------------------------------- | ---------------- | --------------------------------------------- |
| **Lint + format** | [lint-format.yml](lint-format.yml) | push, PR, manual | Runs Ruff linter and formatter checks         |
| **Test**          | [test.yml](test.yml)               | push, PR, manual | Runs pytest across Python 3.11, 3.12, 3.13    |
| **Type check**    | [type-check.yml](type-check.yml)   | push, PR, manual | Runs mypy in strict mode against `src/`       |
| **Coverage**      | [coverage.yml](coverage.yml)       | push, PR, manual | Runs pytest with coverage, uploads to Codecov |
| **Spellcheck**    | [spellcheck.yml](spellcheck.yml)   | push, PR, manual | Checks for spelling mistakes with codespell   |

### Security (multi-layered)

| Workflow              | File                                           | Triggers                  | What it does                                                    |
| --------------------- | ---------------------------------------------- | ------------------------- | --------------------------------------------------------------- |
| **Bandit**            | [bandit.yml](bandit.yml)                       | push, PR, nightly, manual | Static security analysis of Python code                         |
| **CodeQL**            | [security-codeql.yml](security-codeql.yml)     | push, PR, weekly          | GitHub's semantic code analysis (security-extended)             |
| **Security audit**    | [security-audit.yml](security-audit.yml)       | push, PR, weekly, manual  | Checks installed packages for known vulnerabilities (pip-audit) |
| **Dependency review** | [dependency-review.yml](dependency-review.yml) | PR                        | Scans new dependencies for vulnerabilities/licenses             |
| **Container scan**    | [container-scan.yml](container-scan.yml)       | push, PR, weekly, manual  | Scans container image for CVEs with Trivy                       |
| **OpenSSF Scorecard** | [scorecard.yml](scorecard.yml)                 | push, weekly, manual      | Evaluates repo security practices, uploads to Security tab      |

### Supply Chain & Compliance

| Workflow    | File                       | Triggers                 | What it does                                                          |
| ----------- | -------------------------- | ------------------------ | --------------------------------------------------------------------- |
| **SBOM**    | [sbom.yml](sbom.yml)       | push, PR, weekly, manual | Generates SPDX + CycloneDX SBOMs                                      |
| **Release** | [release.yml](release.yml) | tag `v*.*.*`, manual     | Builds, attests provenance, publishes to PyPI, creates GitHub Release |

### Container

| Workflow            | File                                       | Triggers              | What it does                                  |
| ------------------- | ------------------------------------------ | --------------------- | --------------------------------------------- |
| **Container build** | [container-build.yml](container-build.yml) | push, PR, tag, manual | Builds OCI image, pushes to GHCR on main/tags |

### Documentation & Links

| Workflow         | File                                 | Triggers                           | What it does                                       |
| ---------------- | ------------------------------------ | ---------------------------------- | -------------------------------------------------- |
| **Docs build**   | [docs-build.yml](docs-build.yml)     | push, PR, manual                   | Builds MkDocs site with `--strict` (CI gate check) |
| **Docs deploy**  | [docs-deploy.yml](docs-deploy.yml)   | push (main, path-filtered), manual | Builds and deploys MkDocs site to GitHub Pages     |
| **Link checker** | [link-checker.yml](link-checker.yml) | push, PR (docs), weekly, manual    | Checks Markdown/HTML for broken links with lychee  |

### PR Hygiene & Maintenance

| Workflow      | File                                                 | Triggers                | What it does                                                 |
| ------------- | ---------------------------------------------------- | ----------------------- | ------------------------------------------------------------ |
| **PR title**  | [pr-title.yml](pr-title.yml)                         | PR (opened/edited/sync) | Enforces conventional commit format on PR titles             |
| **Labeler**   | [labeler.yml](labeler.yml)                           | PR (opened/sync/reopen) | Auto-labels PRs based on changed file paths                  |
| **Stale**     | [stale.yml](stale.yml)                               | daily, manual           | Marks/closes stale issues and PRs                            |
| **Changelog** | [changelog.yml](../workflows-optional/changelog.yml) | push to main, manual    | Generates CHANGELOG.md from conventional commits (git-cliff) |

### Automated Updates

| Workflow               | File                                             | Triggers       | What it does                                |
| ---------------------- | ------------------------------------------------ | -------------- | ------------------------------------------- |
| **Pre-commit update**  | [pre-commit-update.yml](pre-commit-update.yml)   | weekly, manual | Runs `pre-commit autoupdate` and opens a PR |
| **Spellcheck autofix** | [spellcheck-autofix.yml](spellcheck-autofix.yml) | weekly, manual | Fixes typos with codespell and opens a PR   |

## Repository Guards

Most workflows include a **repository guard** that prevents them from running on forks or clones that haven't opted in. Each workflow supports two activation methods:

- **Option A** — Replace `YOURNAME/YOURREPO` in the `if:` condition with your repo slug.
- **Option B** — Set a repository variable (e.g. `vars.ENABLE_TEST = 'true'`) in Settings → Secrets and variables → Actions → Variables.

| Workflow           | Variable                    |
| ------------------ | --------------------------- |
| Lint + format      | `ENABLE_LINT`               |
| Test               | `ENABLE_TEST`               |
| Type check         | `ENABLE_TYPE_CHECK`         |
| Coverage           | `ENABLE_COVERAGE`           |
| Spellcheck         | `ENABLE_SPELLCHECK`         |
| Spellcheck autofix | `ENABLE_SPELLCHECK_AUTOFIX` |
| Bandit             | `ENABLE_BANDIT`             |
| CodeQL             | `ENABLE_CODEQL`             |
| Security audit     | `ENABLE_SECURITY_AUDIT`     |
| Dependency review  | `ENABLE_DEPENDENCY_REVIEW`  |
| Container build    | `ENABLE_CONTAINER_BUILD`    |
| Container scan     | `ENABLE_CONTAINER_SCAN`     |
| Scorecard          | `ENABLE_SCORECARD`          |
| SBOM               | `ENABLE_SBOM`               |
| Release            | `ENABLE_RELEASE`            |
| Link checker       | `ENABLE_LINK_CHECKER`       |
| Labeler            | `ENABLE_LABELER`            |
| Changelog          | `ENABLE_CHANGELOG`          |
| Stale              | `ENABLE_STALE`              |
| Pre-commit update  | `ENABLE_PRE_COMMIT_UPDATE`  |
| Docs build         | `ENABLE_DOCS_BUILD`         |
| Docs deploy        | `ENABLE_DOCS_DEPLOY`        |

## Conventions

All workflows in this repository follow these patterns:

- **SHA-pinned actions** — Every third-party action is pinned to a full commit SHA with a version comment (per [ADR 004](../../docs/adr/004-pin-action-shas.md))
- **`persist-credentials: false`** — On all `actions/checkout` steps
- **Least-privilege permissions** — Each job declares only the permissions it needs
- **Concurrency groups** — With `cancel-in-progress: true` to avoid redundant runs
- **Timeout limits** — Every job has `timeout-minutes` set
- **Consistent naming** — Workflow names match their purpose; job names are descriptive

## See Also

- [workflows-optional/](../workflows-optional/) — Inactive workflow templates you can adopt
- [docs/workflows.md](../../docs/workflows.md) — Detailed workflow documentation
