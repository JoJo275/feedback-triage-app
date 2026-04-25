# Using This Template

This is the source of truth for getting started with this template. It walks
you through customization, explains what every section of the repo does, and
links to deeper docs where they exist.

Implement any of these changes at your discretion — skip or reorder steps to
fit your project.

> **Something not working?**
> See **[Troubleshooting & FAQ](guide/troubleshooting.md)** for solutions
> to common errors with installation, CI/CD, pre-commit hooks, testing, Git,
> and more.

---

## Quick Start

1. **Clone or use as template** on GitHub
2. **Run the customization script** — handles placeholders, package
   renaming, license selection, and optional directory stripping:

    ```bash
    python scripts/customize.py                  # generate customize-config.md (interactive)
    python scripts/customize.py --non-interactive \
        --project-name my-project --author "Jane Doe" \
        --github-user janedoe                    # fully automated
    ```

    **Markdown config workflow** (export → edit → preview → apply):

    ```bash
    python scripts/customize.py                                             # 1. generate customize-config.md
    # 2. edit customize-config.md — fill in your values, toggle checkboxes
    python scripts/customize.py --apply-from customize-config.md --dry-run  # 3. preview (writes customize-report.md)
    python scripts/customize.py --apply-from customize-config.md            # 4. apply for real
    ```

    **Just enable workflows** (without full customization):

    ```bash
    python scripts/customize.py --enable-workflows myorg/myrepo
    python scripts/customize.py --enable-workflows myorg/myrepo --dry-run   # preview first
    ```

    Or do it manually: find-and-replace all placeholders (see
    [Placeholders to Replace](#placeholders-to-replace)), delete what you
    don't need, and customize the remaining files.

    <details>
    <summary><strong>All customize.py flags</strong></summary>

    | Flag | Description |
    | :--- | :---------- |
    | `--non-interactive` | Skip prompts; use CLI flags for all values |
    | `--project-name NAME` | Project name (lowercase-hyphenated) |
    | `--package-name NAME` | Python package name (auto-derived if omitted) |
    | `--author NAME` | Author name |
    | `--github-user NAME` | GitHub username or organization |
    | `--description TEXT` | One-line project description |
    | `--cli-prefix PREFIX` | CLI command prefix (default: initials) |
    | `--license ID` | License (apache-2.0, mit, bsd-3-clause, …) |
    | `--strip DIR [...]` | Remove optional dirs (db, experiments, var, container, …) |
    | `--template-cleanup ITEM [...]` | Clean up template items (adr-files, placeholder-code, …) |
    | `--private-repo` | Strip open-source community files |
    | `--force` | Skip already-customized safety check |
    | `--enable-workflows SLUG` | Replace YOURNAME/YOURREPO in workflows |
    | `--export-config [PATH]` | Export config to Markdown (default: customize-config.md) |
    | `--apply-from PATH` | Apply config from edited Markdown file |
    | `--dry-run` | Preview mode (no file modifications) |
    | `-q`, `--quiet` | Suppress informational output |

    </details>

3. **Bootstrap your environment** — installs Hatch envs, pre-commit hooks,
   and verifies the setup:

    ```bash
    python scripts/bootstrap.py              # full setup
    python scripts/bootstrap.py --dry-run    # preview what would happen
    python scripts/bootstrap.py --strict     # include ruff + mypy quality pass
    python scripts/bootstrap.py --ci-like    # run all checks like CI (quality + docs build)
    ```

    <details>
    <summary><strong>All bootstrap.py flags</strong></summary>

    | Flag | Description |
    | :--- | :---------- |
    | `--dry-run` | Show what would happen without making changes |
    | `--skip-hooks` | Skip pre-commit hook installation |
    | `--skip-test-matrix` | Skip creating test.py3.x environments (faster) |
    | `--strict` | Run optional quality pass (ruff + mypy) after setup |
    | `--fix` | With --strict, auto-fix ruff issues where possible |
    | `--ci-like` | Run all checks including quality + docs build |
    | `--smoke` | Quick import/arg-parse health check; exit 0 immediately |

    </details>

    Bootstrap performs 12 steps: verify Python version, check git, check
    Hatch, create all Hatch environments (default, docs, test matrix),
    install pre-commit hooks (all stages), check Task runner, verify
    editable install, build smoke test, wheel install test, template
    placeholder validation, publishability checks, and CLI entry point check.

> **What's the difference?** [`scripts/customize.py`](../scripts/customize.py)
> rewrites files (renames packages, swaps placeholders, changes the license).
> [`scripts/bootstrap.py`](../scripts/bootstrap.py) sets up your local dev
> environment (creates Hatch envs, installs hooks, verifies the install).
> Run `customize.py` first, then `bootstrap.py`.
>
> Both scripts support `--dry-run` to preview changes and `--help` for the
> full list of flags. See the docstring at the top of each script for details.

> **LLM-assisted setup:** An LLM coding assistant (e.g. Claude, GPT, or
> GitHub Copilot in agent mode) can help you customize this template —
> renaming packages, updating placeholders, adjusting workflows, and
> navigating the repo structure. Point it at this file and ask it to walk
> you through the setup.

> **Install recommended extensions.** Some features — Markdown rendering,
> TOML/YAML highlighting, linting overlays, and inline error display — may
> look broken or unstyled without the VS Code extensions this project
> expects. Install them from
> [`.vscode/extensions.json`](../.vscode/extensions.json) (VS Code will
> prompt you automatically, or run **Extensions: Show Recommended
> Extensions** from the command palette).

---

## Public vs Private Repositories

This template works with both public and private repositories, but some
features behave differently depending on visibility:

| Feature                          | Public repo                                                          | Private repo                                                                                            |
| :------------------------------- | :------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------ |
| **GitHub Actions**               | Free unlimited minutes                                               | Uses your account's included minutes (2,000/mo for Free, more on paid plans). Monitor usage in Settings. |
| **Dependabot alerts**            | Always available                                                     | Always available                                                                                        |
| **Dependabot security updates**  | Always available                                                     | Always available                                                                                        |
| **Code scanning (CodeQL)**       | Free                                                                 | Requires GitHub Advanced Security license (paid) or GHAS trial                                          |
| **Secret scanning**              | Free (push protection included)                                      | Requires GitHub Advanced Security license (paid)                                                        |
| **OpenSSF Scorecard**            | Works (public data accessible)                                       | Will fail — Scorecard requires public repo access. Remove `scorecard.yml` workflow.                     |
| **Pages (docs deployment)**      | Free via GitHub Pages                                                | Requires GitHub Pro/Team/Enterprise, or use an alternative host                                         |
| **Private vulnerability reports** | Available (enable in Settings)                                       | Available (enable in Settings)                                                                          |
| **Container registry (GHCR)**    | Public images free                                                   | Private images count against storage quota                                                              |
| **Codecov**                      | Free for public repos                                                | Free tier available; check Codecov pricing for private repos                                            |

**If your repo is private**, consider:

- Removing `scorecard.yml` workflow (it requires public access)
- Removing `docs-deploy.yml` if you don't have a Pages-capable plan (keep
  `docs-build.yml` for CI validation)
- Removing CodeQL/`codeql.yml` if you don't have Advanced Security (keep
  `bandit.yml` and `security-audit.yml` as alternatives)
- Monitoring your Actions minutes usage, especially if running the full CI
  matrix on every PR

---

## Placeholders to Replace

<!-- TODO (template users): After replacing these, delete this table or mark
     items done. The customize.py script handles most of them automatically. -->

Search your project for these placeholders and replace them with your values:

| Placeholder                 | Replace with                         | Key files                                                                                     |
| :-------------------------- | :----------------------------------- | :-------------------------------------------------------------------------------------------- |
| `simple-python-boilerplate` | Your project name (kebab-case)       | [README.md](../README.md), [pyproject.toml](../pyproject.toml), [SECURITY.md](../SECURITY.md) |
| `simple_python_boilerplate` | Your package name (snake_case)       | [src/](../src/), [pyproject.toml](../pyproject.toml)                                          |
| `JoJo275`                   | Your GitHub username/org             | [SECURITY.md](../SECURITY.md), issue templates                                                |
| `YOURNAME/YOURREPO`         | Your `owner/repo` slug               | [.github/workflows/](../.github/workflows/), [README.md](../README.md)                        |
| `security@example.com`      | Your security contact email          | [SECURITY.md](../SECURITY.md)                                                                 |
| `[INSERT EMAIL ADDRESS]`    | Your contact email                   | Various files                                                                                 |
| `[Your Name]`               | Your name                            | [LICENSE](../LICENSE), [pyproject.toml](../pyproject.toml)                                    |
| `YOUR_TOKEN`                | Your Codecov token (or remove badge) | [README.md](../README.md)                                                                     |

---

## Files to Customize

### Required

| File                                | What to change                                               |
| :---------------------------------- | :----------------------------------------------------------- |
| [README.md](../README.md)           | Project name, description, badges, installation instructions |
| [pyproject.toml](../pyproject.toml) | Package name, author, dependencies, URLs, entry points       |
| [LICENSE](../LICENSE)               | Year, author name (or choose a different license)            |
| [SECURITY.md](../SECURITY.md)       | Repository URL, contact email, PGP key (optional)            |
| [mkdocs.yml](../mkdocs.yml)         | `site_name`, `site_url`, `repo_url`                          |

### Optional

| File                                                                  | When to customize                                                |
| :-------------------------------------------------------------------- | :--------------------------------------------------------------- |
| [.github/ISSUE_TEMPLATE/\*.yml](../.github/ISSUE_TEMPLATE/)           | Adjust fields, labels, or remove templates you don't need        |
| [CONTRIBUTING.md](../CONTRIBUTING.md)                                 | Add project-specific contribution guidelines                     |
| [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md)                           | Usually fine as-is (Contributor Covenant)                        |
| [labels/\*.json](../labels/)                                          | Add custom labels for your workflow — see [labels.md](labels.md) |
| [codecov.yml](../codecov.yml)                                         | Coverage thresholds, flags, path exclusions                      |
| [\*.code-workspace](../simple-python-boilerplate.code-workspace)      | VS Code settings, recommended extensions, default formatters     |
| [.github/copilot-instructions.md](../.github/copilot-instructions.md) | Replace domain/business context for Copilot                      |
| [\_typos.toml](../_typos.toml)                                        | Spellchecker exceptions and ignored words                        |
| [.markdownlint-cli2.jsonc](../.markdownlint-cli2.jsonc)               | Markdown lint rule overrides                                     |
| [Containerfile](../Containerfile)                                     | Entrypoint, OCI labels, base image pin                           |
| [docker-compose.yml](../docker-compose.yml)                           | Service name, image name, ports, volumes, env vars               |
| [container-structure-test.yml](../container-structure-test.yml)        | Package name, entrypoint, user/group assertions                  |
| [.devcontainer/devcontainer.json](../.devcontainer/devcontainer.json) | Project name, Python version, extensions, features               |
| [.github/dependabot.yml](../.github/dependabot.yml)                   | Timezone, reviewers, package ignore rules                        |
| [.editorconfig](../.editorconfig)                                     | Indent sizes per file type if team conventions differ             |
| [.gitattributes](../.gitattributes)                                   | Binary/text overrides for project-specific file types            |
| [.gitmessage.txt](../.gitmessage.txt)                                 | Commit template path if renamed or moved                         |
| [release-please-config.json](../release-please-config.json)           | Package name and extra-files path                                |
| [src/.../scripts\_cli.py](../src/simple_python_boilerplate/scripts_cli.py) | Entry point wrappers — update script list after adding/removing scripts |

---

## Issue Templates

This template includes 3 issue templates plus a config file:

| Template                                                             | Purpose                      | Keep?                  |
| :------------------------------------------------------------------- | :--------------------------- | :--------------------- |
| [bug_report.yml](../.github/ISSUE_TEMPLATE/bug_report.yml)           | Report confirmed bugs        | Always                 |
| [feature_request.yml](../.github/ISSUE_TEMPLATE/feature_request.yml) | Suggest enhancements         | Always                 |
| [documentation.yml](../.github/ISSUE_TEMPLATE/documentation.yml)     | Docs issues/improvements     | If you maintain docs   |
| [config.yml](../.github/ISSUE_TEMPLATE/config.yml)                   | External links & Discussions | Customize link targets |

Additional templates are available in [docs/templates/issue_templates/](templates/issue_templates/README.md)
if you need them (e.g., question, performance).

### Removing templates

Delete the `.yml` files you don't need from [.github/ISSUE_TEMPLATE/](../.github/ISSUE_TEMPLATE/).

### Customizing labels

1. Edit [labels/baseline.json](../labels/baseline.json) or [labels/extended.json](../labels/extended.json)
2. Run `python scripts/apply_labels.py --set baseline --repo OWNER/REPO`
3. Update issue template `labels:` fields to match

For the full label taxonomy, see [labels.md](labels.md).

---

## Security Policy

| Scenario                      | Use                                                                                                 |
| :---------------------------- | :-------------------------------------------------------------------------------------------------- |
| No bug bounty (most projects) | [SECURITY.md](../SECURITY.md) (default) or [SECURITY_no_bounty.md](templates/SECURITY_no_bounty.md) |
| With bug bounty               | [SECURITY_with_bounty.md](templates/SECURITY_with_bounty.md)                                        |
| Standalone bounty policy      | [BUG_BOUNTY.md](templates/BUG_BOUNTY.md)                                                            |

### Enabling Private Vulnerability Reporting

1. Go to your repo → **Settings** → **Security** → **Code security and analysis**
2. Enable **Private vulnerability reporting**

For the security scanning CI setup, see [ADR 012](adr/012-multi-layer-security-scanning.md).

---

## GitHub Features to Enable

After creating your repo, consider enabling:

- [ ] **Discussions** — For Q&A and community conversations (also enables the
      Discussions link in the [Need Help?](#need-help) section below)
- [ ] **Private vulnerability reporting** — For security issues
- [ ] **Dependabot alerts** — For dependency vulnerabilities
- [ ] **Dependabot security updates** — Auto-create PRs for vulnerable deps
- [ ] **Branch protection** — Require PR reviews, status checks (see [ADR 023](adr/023-branch-protection-rules.md))

---

## Files You Can Delete

This template ships with ~250 files. After customizing, delete anything that
doesn't apply:

| Delete                                                                                   | If you don't need…                                           |
| :--------------------------------------------------------------------------------------- | :----------------------------------------------------------- |
| [docs/templates/](templates/README.md)                                                   | File templates (copy what you need first)                    |
| [docs/adr/template.md](adr/template.md)                                                  | ADR template (keep if you write ADRs)                        |
| [experiments/](../experiments/)                                                          | Example experiment scripts                                   |
| [labels/extended.json](../labels/extended.json)                                          | Extended label set (baseline is enough)                      |
| [Containerfile](../Containerfile), [docker-compose.yml](../docker-compose.yml)           | Container support                                            |
| [.devcontainer/](../.devcontainer/)                                                      | VS Code Dev Container / Codespaces                           |
| [db/](../db/), `scripts/sql/`, [var/](../var/)                                           | Database scaffolding                                         |
| [requirements.txt](../requirements.txt), [requirements-dev.txt](../requirements-dev.txt) | If you only use Hatch (optional mirrors of `pyproject.toml`) |
| `site/`                                                                                  | Built docs output (regenerated by `mkdocs build`)            |
| [mkdocs.yml](../mkdocs.yml), `docs/` (selectively)                                       | If you don't need a documentation site                       |
| [codecov.yml](../codecov.yml)                                                            | If you don't use Codecov for coverage reporting              |

> **Don't forget dependent files**
> Some files depend on others. If you remove container files, also remove
> `container-build.yml` and `container-scan.yml` workflows. If you remove
> issue templates, update the label references. When in doubt, run
> `task check` after deleting.

---

## Checklist

A consolidated checklist for the full setup. Copy this into an issue or
check items off as you go.

### Initial Setup

- [ ] Clone or use "Use this template" on GitHub
- [ ] Run `python scripts/customize.py` (or replace placeholders manually)
- [ ] Run `python scripts/bootstrap.py` to set up the local environment
- [ ] Update remote URL if cloned directly

### Core Files

- [ ] Update [README.md](../README.md) with project description and badges
- [ ] Update [pyproject.toml](../pyproject.toml) — name, author, dependencies, URLs
- [ ] Update [LICENSE](../LICENSE) — year, author (or choose a different license)
- [ ] Update [SECURITY.md](../SECURITY.md) with your contact info
- [ ] Update [mkdocs.yml](../mkdocs.yml) — `site_name`, `site_url`, `repo_url`
- [ ] Update [.github/copilot-instructions.md](../.github/copilot-instructions.md) — replace domain/business context
- [ ] Customize [\*.code-workspace](../simple-python-boilerplate.code-workspace) — rename file, update extensions and settings

### Source Code

- [ ] Rename `src/simple_python_boilerplate/` to your package name
- [ ] Update imports in test files to match new package name
- [ ] Update `[project.scripts]` entry points in [pyproject.toml](../pyproject.toml)
- [ ] Update [scripts\_cli.py](../src/simple_python_boilerplate/scripts_cli.py) — rename module paths and bundled-script references
- [ ] Replace placeholder code in [src/](../src/) and [tests/](../tests/)

### Containers (if keeping)

- [ ] Update [Containerfile](../Containerfile) — entrypoint, OCI labels, base image
- [ ] Update [docker-compose.yml](../docker-compose.yml) — service name, image name, ports
- [ ] Update [container-structure-test.yml](../container-structure-test.yml) — package name, entrypoint
- [ ] Update [.devcontainer/devcontainer.json](../.devcontainer/devcontainer.json) — name, Python version, extensions

### GitHub Configuration

- [ ] Enable Discussions (optional)
- [ ] Enable Private vulnerability reporting
- [ ] Enable Dependabot alerts and security updates
- [ ] Set up branch protection rules — see [ADR 023](adr/023-branch-protection-rules.md)
- [ ] Apply labels: `python scripts/apply_labels.py --set baseline --repo OWNER/REPO`
- [ ] Enable workflows — see [Enabling Workflows](#enabling-workflows)

### Cleanup

- [ ] Delete [docs/templates/](templates/README.md) (after copying what you need)
- [ ] Delete unused issue templates from [.github/ISSUE_TEMPLATE/](../.github/ISSUE_TEMPLATE/)
- [ ] Clear [CHANGELOG.md](../CHANGELOG.md) for your project's history
- [ ] Remove template-specific notes from documentation
- [ ] Add `experiments/` and `var/` to `.gitignore` if keeping those directories
- [ ] Update [.github/dependabot.yml](../.github/dependabot.yml) — reviewers, timezone, ignore rules

### Verification

- [ ] Run `hatch shell` then `pytest` — all tests pass
- [ ] Run `task check` — all quality gates pass
- [ ] Run `task docs:build` — docs build without warnings
- [ ] Verify imports: `python -c "import your_package"`
- [ ] Run `python scripts/check_todos.py` — find remaining template placeholders
- [ ] Run `python scripts/check_python_support.py` — verify Python version consistency

### Pre-1.0 Release Readiness

When you're ready to cut your first stable release, see the
[Pre-1.0 Release Readiness Checklist](releasing.md#pre-10-release-readiness-checklist)
in the releasing guide. It covers code quality, security, documentation,
CI/CD, packaging, and release configuration gates.

---

## CI/CD Workflows Included

This template ships with **37 GitHub Actions workflows** in
[.github/workflows/](../.github/workflows/) covering quality, security, PR
hygiene, releases, docs, containers, and maintenance.

All are SHA-pinned ([ADR 004](adr/004-pin-action-shas.md)) and disabled by
default via repository guards ([ADR 011](adr/011-repository-guard-pattern.md)).
A single **CI Gate** workflow aggregates all required checks into one
branch-protection status ([ADR 024](adr/024-ci-gate-pattern.md)).

For the full inventory, see [workflows.md](workflows.md) or the
[workflows README](../.github/workflows/README.md).

### Enabling Workflows

All optional workflows are disabled by default via a **repository guard** — an
`if:` condition at the top of each job. Until you opt in, workflows silently
skip on forks and clones.

**Three ways to enable:**

| Method                               | How                                                                         | Best for                      |
| :----------------------------------- | :-------------------------------------------------------------------------- | :---------------------------- |
| **Option A — Edit the YAML**         | Replace `YOURNAME/YOURREPO` with your repo slug in each workflow file       | Permanent, no external config |
| **Option B — Global variable**       | Set `vars.ENABLE_WORKFLOWS = 'true'` as a repository variable               | Enable all workflows at once  |
| **Option C — Per-workflow variable** | Set `vars.ENABLE_<WORKFLOW> = 'true'` (e.g., `ENABLE_TEST`, `ENABLE_STALE`) | Granular control              |

> **Fastest approach**
> Run the customization script with the `--enable-workflows` flag:
>
> ```bash
> python scripts/customize.py --enable-workflows myorg/myproject
> python scripts/customize.py --enable-workflows myorg/myproject --dry-run  # preview
> ```

**Setting a repository variable (Options B/C):**

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions** → **Variables** tab
3. Click **New repository variable**
4. Name: `ENABLE_WORKFLOWS` (or `ENABLE_<WORKFLOW>` for individual control)
5. Value: `true`

### Disabling Workflows You Don't Need

Not every project needs all 37 workflows:

| If you don't need…    | Remove these workflows                                        | Notes                                                                                         |
| :-------------------- | :------------------------------------------------------------ | :-------------------------------------------------------------------------------------------- |
| Container support     | `container-build.yml`, `container-scan.yml`                   | Also delete [Containerfile](../Containerfile) and [docker-compose.yml](../docker-compose.yml) |
| Documentation site    | `docs-deploy.yml`                                             | Keep `docs-build.yml` for CI validation of docs                                               |
| Automated releases    | `release-please.yml`, `release.yml`, `sbom.yml`               | Manual releases still work via git tags                                                       |
| Security scanning     | `nightly-security.yml`, `container-scan.yml`, `scorecard.yml` | Keep `security-audit.yml` and `dependency-review.yml` at minimum                              |
| Spell checking        | `spellcheck.yml`, `spellcheck-autofix.yml`                    | Also remove the typos pre-commit hook                                                         |
| Auto-merge Dependabot | `auto-merge-dependabot.yml`                                   | Review Dependabot PRs manually instead                                                        |
| Stale issue cleanup   | `stale.yml`                                                   | Manage stale issues manually                                                                  |

> **Don't remove core quality workflows.**
> These are in the CI gate and should stay unless you're replacing them:
> `test.yml`, `lint-format.yml`, `type-check.yml`, `coverage.yml`,
> `ci-gate.yml`.

**After removing workflows:**

1. Update `REQUIRED_CHECKS` in [ci-gate.yml](../.github/workflows/ci-gate.yml)
2. Update [workflows.md](workflows.md)
3. Update branch protection if affected

### Workflow Categories

| Category          | Workflows                                                                                                                                   | Always run?                                              |
| :---------------- | :------------------------------------------------------------------------------------------------------------------------------------------ | :------------------------------------------------------- |
| **Quality**       | test, lint-format, type-check, coverage, spellcheck, spellcheck-autofix, todo-check                                                         | Yes — in CI gate (except spellcheck-autofix, todo-check) |
| **Security**      | security-audit, bandit, dependency-review, CodeQL, container-scan, nightly, scorecard, license-check                                        | Mixed — some path-filtered                               |
| **PR Hygiene**    | pr-title, commit-lint, labeler                                                                                                              | Yes — in CI gate                                         |
| **Release**       | release-please, release, sbom                                                                                                               | Push to main / tags only                                 |
| **Documentation** | docs-build, docs-deploy                                                                                                                     | docs-build in gate; deploy is path-filtered              |
| **Container**     | container-build, container-scan, devcontainer-build                                                                                         | container-build in gate; devcontainer path-filtered      |
| **Maintenance**   | pre-commit-update, stale, link-checker, auto-merge-dependabot, cache-cleanup, regenerate-files, known-issues-check, repo-doctor, doctor-all | Scheduled / event-triggered                              |
| **Gate**          | ci-gate                                                                                                                                     | Yes — the single required check                          |

---

## Pre-commit Hooks

[Pre-commit hooks](https://pre-commit.com/) catch problems before code leaves
your machine. This template includes **47 hooks** across four Git stages:

| Stage          | When it runs       | Examples                                                             | Count |
| :------------- | :----------------- | :------------------------------------------------------------------- | ----: |
| **pre-commit** | Every `git commit` | Ruff lint/format, mypy, bandit, typos, deptry, YAML/TOML/JSON checks |    37 |
| **commit-msg** | Every `git commit` | Commitizen — validates Conventional Commits format                   |     1 |
| **pre-push**   | Every `git push`   | pytest, pip-audit, gitleaks                                          |     3 |
| **manual**     | On demand          | markdownlint-cli2, hadolint-docker, prettier, forbid-submodules      |     4 |

All hooks are configured in [.pre-commit-config.yaml](../.pre-commit-config.yaml).
See [ADR 008](adr/008-pre-commit-hooks.md) for the full inventory and rationale.

To install all hook stages:

```bash
task pre-commit:install
# or manually:
pre-commit install
pre-commit install --hook-type commit-msg
pre-commit install --hook-type pre-push
```

> **New to pre-commit?** Think of hooks as automated code reviewers. Instead of
> remembering to run the linter, formatter, and tests manually before pushing,
> hooks run them for you. If a check fails, the commit or push is blocked with
> an explanation of what went wrong.

---

## File Templates

[docs/templates/](templates/README.md) contains reusable file templates you can copy
and adapt:

| Template                                                     | Purpose                                  |
| :----------------------------------------------------------- | :--------------------------------------- |
| [SECURITY_no_bounty.md](templates/SECURITY_no_bounty.md)     | Standard security policy (most projects) |
| [SECURITY_with_bounty.md](templates/SECURITY_with_bounty.md) | Security policy with bug bounty program  |
| [BUG_BOUNTY.md](templates/BUG_BOUNTY.md)                     | Standalone bug bounty policy             |
| [pull-request-draft.md](templates/pull-request-draft.md)     | PR description template                  |

Copy what you need, then delete the `docs/templates/` directory.

---

## Command Workflows

This project has **three layers** for running developer commands:
raw Python tools (pytest, ruff, mypy), Hatch (managed environments),
and a Task runner (short aliases). Each layer is optional.

See [command-workflows.md](development/command-workflows.md) for a
detailed breakdown of how `task test` → `hatch run test` → `pytest`
flows through each layer, and guidance on which to use.

---

## Utility Scripts

The [`scripts/`](../scripts/) directory contains standalone tools for
project setup, maintenance, and diagnostics. Each script supports
`--help` for full flag details (also documented in the docstring at
the top of each file).

| Script                                                        | Purpose                                                        | Key flags                                                         |
| :------------------------------------------------------------ | :------------------------------------------------------------- | :---------------------------------------------------------------- |
| [`customize.py`](../scripts/customize.py)                     | Replace boilerplate placeholders, rename package, swap license | `--dry-run`, `--non-interactive`, `--enable-workflows SLUG`       |
| [`bootstrap.py`](../scripts/bootstrap.py)                     | One-command dev environment setup (Hatch envs, hooks, verify)  | `--dry-run`, `--skip-hooks`, `--skip-test-matrix`                 |
| [`clean.py`](../scripts/clean.py)                             | Remove build artifacts and caches                              | `--dry-run`, `--include-venv`                                     |
| [`doctor.py`](../scripts/doctor.py)                           | Diagnostics bundle for bug reports                             | `--markdown`, `--json`, `--output PATH`                           |
| [`env_doctor.py`](../scripts/env_doctor.py)                   | Quick environment health check                                 | `--strict`, `--json`                                              |
| [`repo_doctor.py`](../scripts/repo_doctor.py)                 | Repository structure health checks (configurable rules)        | `--profile NAME`, `--fix`, `--category NAME`                      |
| [`dep_versions.py`](../scripts/dep_versions.py)               | Show/update/upgrade dependency versions                        | `show --offline`, `upgrade --dry-run`                             |
| [`workflow_versions.py`](../scripts/workflow_versions.py)     | Show/update/upgrade SHA-pinned GitHub Actions                  | `show --filter stale`, `upgrade --dry-run`                        |
| [`git_doctor.py`](../scripts/git_doctor.py)                   | Git health dashboard, config management, branch ops            | `--refresh`, `--cleanup`, `--view-commits`, `--apply-recommended` |
| [`check_todos.py`](../scripts/check_todos.py)                 | Scan for remaining TODO (template users) comments              | `--count`, `--json`                                               |
| [`archive_todos.py`](../scripts/archive_todos.py)             | Archive completed TODOs from notes                             | `--dry-run`, `--no-backup`                                        |
| [`changelog_check.py`](../scripts/changelog_check.py)         | Verify CHANGELOG entries match git tags                        | `--verbose`, `--quiet`                                            |
| [`check_known_issues.py`](../scripts/check_known_issues.py)   | Flag stale Resolved entries in known-issues.md                 | `--days N`, `--json`, `--quiet`                                   |
| [`apply_labels.py`](../scripts/apply_labels.py)               | Apply GitHub labels from JSON definitions                      | `--set {baseline,extended}`, `--dry-run`                          |
| [`check_python_support.py`](../scripts/check_python_support.py) | Verify Python version consistency across all config sources    | `--json`, `--quiet`, `--version`                                  |
| [`test_containerfile.py`](../scripts/test_containerfile.py)   | Test the Containerfile image: build, validate, clean up        | `--dry-run`, `--keep`                                             |
| [`test_docker_compose.py`](../scripts/test_docker_compose.py) | Test docker compose stack: build, run, validate, clean up      | `--dry-run`                                                       |

Bash equivalents (`test_containerfile.sh`, `test_docker_compose.sh`) are also
available for shell-based CI pipelines.

Full inventory with additional details: [`scripts/README.md`](../scripts/README.md)

### Health Checks

Four doctor scripts cover different aspects of project health. Run them
individually or all at once:

```bash
task doctor:all                # everything in one report
task doctor:env                # Python, Hatch, tools
task doctor:repo               # repo structure, conventions
task doctor:git                # branches, remotes, git health
task doctor:git:refresh        # fetch, prune, sync tags
task doctor:git:cleanup        # stale branches, git gc
task doctor:git:config:minimal # apply 12 core git configs
```

The `doctor-all.yml` CI workflow runs these same checks on push/PR.
See [workflows.md](workflows.md#local-health-scripts) for the full list.

---

## CLI Entry Points (`spb-*` Commands)

This template ships **21 global CLI commands** defined in
[`pyproject.toml`](../pyproject.toml) under `[project.scripts]`. These are
thin wrappers (in
[`scripts_cli.py`](../src/simple_python_boilerplate/scripts_cli.py)) that
run the bundled scripts via subprocess — so each command inspects whichever
repo your terminal is currently in, not the repo the package was installed from.

### Do I Need to Install Anything?

**If you already cloned the repo and ran `hatch shell`** (or
`pip install -e .`), all `spb-*` commands are already available in that
environment. No extra steps needed.

**If you want the commands available globally** (outside Hatch, in any
terminal, for any project), install with
[pipx](https://pipx.pypa.io/):

```bash
# From a local clone
pipx install /path/to/simple-python-boilerplate

# Or directly from GitHub
pipx install git+https://github.com/JoJo275/simple-python-boilerplate.git
```

After `pipx install`, the `spb-*` commands are on your `PATH` system-wide.

> **Why pipx?** `pipx` installs Python CLI tools in isolated environments so
> they don't pollute your system Python. It's the recommended way to install
> command-line tools. See [pipx docs](https://pipx.pypa.io/) for installation.

### Full Command List

| Command | Purpose | Equivalent script |
| :------ | :------ | :---------------- |
| `spb` | Main CLI command | — |
| `spb-version` | Print version info | — |
| `spb-start` | Start the application | — |
| `spb-doctor` | Diagnose environment issues | — |
| `spb-diag` | Full diagnostics bundle for bug reports | `python scripts/doctor.py` |
| `spb-git-doctor` | Git health dashboard and branch ops | `python scripts/git_doctor.py` |
| `spb-env-doctor` | Environment health check | `python scripts/env_doctor.py` |
| `spb-repo-doctor` | Repository structure health checks | `python scripts/repo_doctor.py` |
| `spb-env-inspect` | Environment, packages, PATH inspection | `python scripts/env_inspect.py` |
| `spb-repo-stats` | Repository statistics dashboard | `python scripts/repo_sauron.py` |
| `spb-clean` | Remove build artifacts and caches | `python scripts/clean.py` |
| `spb-bootstrap` | One-command setup for fresh clones | `python scripts/bootstrap.py` |
| `spb-dep-versions` | Show/update dependency versions | `python scripts/dep_versions.py` |
| `spb-workflow-versions` | Show/update SHA-pinned action versions | `python scripts/workflow_versions.py` |
| `spb-check-todos` | Scan for template TODO comments | `python scripts/check_todos.py` |
| `spb-check-python` | Verify Python version consistency | `python scripts/check_python_support.py` |
| `spb-changelog-check` | Verify CHANGELOG matches git tags | `python scripts/changelog_check.py` |
| `spb-apply-labels` | Apply GitHub labels from JSON definitions | `python scripts/apply_labels.py` |
| `spb-archive-todos` | Archive completed TODOs | `python scripts/archive_todos.py` |
| `spb-customize` | Interactive project customization | `python scripts/customize.py` |
| `spb-check-issues` | Flag stale entries in known-issues.md | `python scripts/check_known_issues.py` |
| `spb-dashboard` | Start the environment inspection dashboard | `hatch run dashboard:serve` |

All arguments are forwarded: `spb-git-doctor --json` works the same as
`python scripts/git_doctor.py --json`.

### How It Works

When you install the package (`pip install .` or `pipx install .`), pip
creates executable wrappers on your `PATH` for each entry in
`[project.scripts]`. Each wrapper:

1. Locates the bundled script inside the installed package
2. Sets `SPB_REPO_ROOT` to your current working directory
3. Runs the script as a subprocess with `cwd` set to your current directory

This means `spb-git-doctor` run from `~/projects/my-app/` inspects
`my-app` — not the template repo where the package was built.

### After Forking: Rename the Prefix

<!-- TODO (template users): After renaming the package, update [project.scripts]
     in pyproject.toml to use your own prefix (e.g., myapp-doctor). -->

After running `scripts/customize.py` to rename the package, update the
`[project.scripts]` section in [`pyproject.toml`](../pyproject.toml) to
replace the `spb-` prefix with your project's prefix (e.g., `myapp-doctor`).
Then update [`scripts_cli.py`](../src/simple_python_boilerplate/scripts_cli.py)
to match.

For the full entry points guide (architecture diagram, adding new commands,
cross-repo usage patterns), see
[docs/guide/entry-points.md](guide/entry-points.md).

---

## Containers

This template includes three container-related files
([ADR 025](adr/025-container-strategy.md)):

| File                                        | Purpose                                                             | Usage                                   |
| :------------------------------------------ | :------------------------------------------------------------------ | :-------------------------------------- |
| [Containerfile](../Containerfile)           | **Production image** — multi-stage build, minimal runtime (~150 MB) | `docker build -f Containerfile .`       |
| [docker-compose.yml](../docker-compose.yml) | **Orchestration** — build + run locally, or multi-service setups    | `docker compose up --build`             |
| [.devcontainer/](../.devcontainer/)         | **Dev environment** — VS Code Dev Container / Codespaces            | Open in VS Code → "Reopen in Container" |

If you don't need containers, delete `Containerfile`, `docker-compose.yml`,
and `.devcontainer/`. If you only want production containers, delete
`.devcontainer/`. If you only want the dev container, delete the other two.

### Containerfile (Production Image)

**What it does:** Builds a minimal, secure production image using a multi-stage
build. Stage 1 ("builder") installs build tools and compiles a wheel. Stage 2
("runtime") copies only the installed package into a slim base image — no
compilers, no source code, no build dependencies.

**What it looks like when built:**

- ~150 MB image (Python 3.12-slim base)
- Non-root user `app` (UID/GID 1000)
- Read-only filesystem compatible
- `PYTHONDONTWRITEBYTECODE=1` and `PYTHONUNBUFFERED=1` set
- OCI metadata labels for tooling compatibility
- Entrypoint is the `spb` CLI command (your package's console_scripts entry point)

**Setup:**

```bash
# Prerequisite: Docker Desktop (or Podman) must be installed and running

# Build the image
docker build -t simple-python-boilerplate -f Containerfile .

# Build with a specific version (for CI — .git isn't in the container)
docker build --build-arg VERSION=1.2.0 -t simple-python-boilerplate:1.2.0 -f Containerfile .

# Run it
docker run --rm simple-python-boilerplate

# Run with arguments
docker run --rm simple-python-boilerplate --help
```

**Why use it:** Deploying to Kubernetes, ECS, Cloud Run, or any container
platform. The multi-stage build keeps the image small and free of build
tooling, reducing the attack surface.

**After customizing:** Update the `ENTRYPOINT`, OCI labels, and base image
pin in the Containerfile. The `TODO (template users)` comments mark what to
change.

### docker-compose.yml (Local Orchestration)

**What it does:** Wraps the Containerfile build into a single command for
local development and testing. Defines security defaults (read-only filesystem,
no-new-privileges) and provides commented templates for ports, volumes,
environment variables, resource limits, and a database service.

**What it looks like running:**

```
$ docker compose up --build
[+] Building 12.3s
[+] Running 1/1
 ✔ Container simple-python-boilerplate  Created
Attaching to simple-python-boilerplate
simple-python-boilerplate  | <your CLI output here>
```

**Setup:**

```bash
# Build and run in foreground (see output)
docker compose up --build

# Build and run in background
docker compose up -d --build

# Check running containers
docker compose ps

# View logs
docker compose logs -f

# Stop and remove containers
docker compose down
```

**Turning it into a web service:** To expose an HTTP endpoint (e.g., FastAPI,
Flask), make these changes:

1. Uncomment `ports: - "8000:8000"` in `docker-compose.yml`
2. Update your app code to start a server on port 8000
3. Uncomment the `HEALTHCHECK` in the Containerfile
4. Optionally uncomment `environment`, `volumes`, and `restart` sections

```bash
# After enabling ports:
docker compose up -d --build
curl http://localhost:8000/health    # health check
curl http://localhost:8000/api/v1    # your API
```

**Adding a database:** The compose file includes a commented Postgres service
template. Uncomment the `db:` service and `volumes:` section, set the
`POSTGRES_PASSWORD` environment variable, and your app container can connect
to `db:5432`.

**Why use it:** Consistent local environment that matches production. One
command to build + run. Easy to add services (databases, caches, queues)
without polluting your host machine.

### VS Code Dev Container

**What it does:** Defines a full development environment that runs inside a
container. VS Code connects to it seamlessly — your terminal, editor, debugger,
and extensions all run inside the container. Also works with GitHub Codespaces.

**Configuration file:** [`.devcontainer/devcontainer.json`](../.devcontainer/devcontainer.json)
— controls the base image, installed features, extensions, environment
variables, and post-create setup commands. See the
[`.devcontainer/README.md`](../.devcontainer/README.md) for full details.

**This is NOT the same as the Containerfile.** The Containerfile builds a
minimal production image. The Dev Container sets up a rich development
environment with all your tools pre-installed. Docker Compose also builds
from the Containerfile — so Compose and the Dev Container use **completely
separate images**. The Dev Container pulls the
`mcr.microsoft.com/devcontainers/python` base image; Compose builds from
`python:3.12-slim` via the Containerfile.

**What carries over into the container:**

- **All project files** — the entire workspace is mounted into the container
  via a volume bind, so every file you see locally (source, tests, configs,
  docs, scripts) is available inside the container.
- **VS Code extensions** — extensions listed in the `customizations.vscode.extensions`
  array in `devcontainer.json` are installed automatically inside the container.
  This is separate from `.vscode/extensions.json` — Dev Containers only read
  the `devcontainer.json` list, so extensions must be listed there explicitly.
  Your locally installed extensions do **not** automatically carry over unless
  they appear in that list.
- **VS Code settings** — `.vscode/settings.json` loads automatically inside the
  container (it's part of the mounted workspace). Container-specific overrides
  (like the Linux terminal profile) go in the `customizations.vscode.settings`
  block in `devcontainer.json`.
- **Git configuration** — your global git config (user.name, user.email, etc.)
  is shared into the container automatically by VS Code.

**What it looks like:**

- Python 3.12 (Debian Bookworm base) with pip, venv, git
- Node.js LTS (for pre-commit hooks like markdownlint, prettier)
- Task runner (go-task) for Taskfile.yml commands
- VS Code extensions auto-installed: Python, Pylance, Ruff, mypy, TOML, YAML,
  Markdown, GitLens, Git Graph, spell checker, EditorConfig, Task
- Hatch environments created and pre-commit hooks installed on first launch
- Runs as non-root `vscode` user

**Setup:**

1. **Install prerequisites:**
    - [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Podman)
    - [VS Code](https://code.visualstudio.com/)
    - [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

2. **Open in container:**
    - Open the project in VS Code
    - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS)
    - Run "Dev Containers: Reopen in Container"
    - Wait for the container to build and `postCreateCommand` to finish

3. **Start working:** Everything is ready — Hatch env, pre-commit hooks,
   extensions, and settings are all configured.

**Exiting the Dev Container:**

- **Command palette** (`Ctrl+Shift+P`) → **Dev Containers: Reopen Folder Locally**
- Or simply **close the VS Code window** — the container stops automatically
- Your files are safe — the container mounts your local project directory, so
  everything you edited persists on your local disk

**For GitHub Codespaces:** No local setup needed. Click "Code → Codespaces →
Create codespace on main" on GitHub. The same `devcontainer.json` configures
the Codespace automatically.

**Why use it:** Eliminates "works on my machine" issues. New contributors get a
fully configured environment in minutes without installing Python, Node, Hatch,
or any tools on their host. Especially useful for teams, onboarding, and when
working across multiple projects with different tool versions.

**Testing the Dev Container:** The
[`devcontainer-build.yml`](../.github/workflows/devcontainer-build.yml)
workflow automatically validates the dev container on PRs that change
`.devcontainer/` files, `pyproject.toml`, or `.pre-commit-config.yaml`. It
uses the [`devcontainers/ci`](https://github.com/devcontainers/ci) GitHub
Action to build the container and run smoke tests (Python, Hatch,
pre-commit, and package import). This catches broken `postCreateCommand`
scripts, missing features, or image pull failures before they affect
contributors. Enable it via the repository guard (same pattern as other
workflows — see [Enabling Workflows](#enabling-workflows)).

**After customizing:** Update `name`, Python version, extensions list, and
`postCreateCommand` in `.devcontainer/devcontainer.json`. Uncomment
`forwardPorts` if your app runs a server.

### Container Structure Tests

[Container structure tests](https://github.com/GoogleContainerTools/container-structure-test)
validate that your built image meets expected properties — installed packages,
user/group configuration, environment variables, metadata, and file layout.
This catches problems like "the package didn't install" or "the image is
running as root" before deployment.

**What gets tested** (defined in `container-structure-test.yml`):

| Category           | Tests                                                                               |
| :----------------- | :---------------------------------------------------------------------------------- |
| **Metadata**       | Entrypoint, user, workdir, env vars (PYTHONDONTWRITEBYTECODE, etc)                  |
| **Commands**       | Python installed, package importable, pip available, no gcc, non-root user, UID/GID |
| **File existence** | /app dir exists, /home/app exists                                                   |
| **File content**   | /etc/passwd and /etc/group contain the app user/group                               |

**Setup:**

```bash
# Install container-structure-test (one-time)
# Option A: Go install
go install github.com/GoogleContainerTools/container-structure-test/cmd/container-structure-test@latest

# Option B: Download binary (Linux/macOS)
curl -LO https://github.com/GoogleContainerTools/container-structure-test/releases/latest/download/container-structure-test-linux-amd64
chmod +x container-structure-test-linux-amd64
sudo mv container-structure-test-linux-amd64 /usr/local/bin/container-structure-test

# Option C: Download binary (Windows) — download from GitHub Releases page
# https://github.com/GoogleContainerTools/container-structure-test/releases
```

**Running the tests:**

```bash
# Build the image first
docker build -t simple-python-boilerplate:test -f Containerfile .

# Run structure tests against the built image
container-structure-test test \
  --image simple-python-boilerplate:test \
  --config container-structure-test.yml
```

**Expected output:**

```
======================================
====== Test file: container-structure-test.yml ======
=== RUN: Command Test: Python is installed
--- PASS
=== RUN: Command Test: Package is installed
--- PASS
=== RUN: Command Test: Non-root user
--- PASS
...
======================================
PASS
```

**After customizing:** Update the package import name, entrypoint, and
Python version in `container-structure-test.yml` to match your project.

### Docker Compose + Test Workflow

A full workflow for building, running, and testing your containerized
application locally:

**Step 1: Build and start**

```bash
docker compose up -d --build
```

**Step 2: Verify the container is running**

```bash
docker compose ps
# NAME                         STATUS
# simple-python-boilerplate    Up 5 seconds
```

**Step 3: Check logs**

```bash
docker compose logs -f
```

**Step 4: Test the running service**

If your app exposes an HTTP endpoint:

```bash
# Health check
curl -f http://localhost:8000/health

# Hit your API
curl http://localhost:8000/api/v1/items

# Run integration tests against the running container
pytest tests/integration/ -v
```

If your app is a CLI tool (default template):

```bash
# Run a command inside the container
docker compose exec app spb --version

# Or run and check exit code
docker compose run --rm app --help
```

**Step 5: Run container structure tests**

```bash
# Test the image itself (not the running container)
container-structure-test test \
  --image simple-python-boilerplate:local \
  --config container-structure-test.yml
```

**Step 6: Tear down**

```bash
docker compose down
```

**Full CI script example:**

```bash
#!/bin/bash
set -euo pipefail

# Build
docker compose up -d --build

# Wait for health (if HTTP service)
# for i in {1..30}; do curl -sf http://localhost:8000/health && break || sleep 1; done

# Test
container-structure-test test \
  --image simple-python-boilerplate:local \
  --config container-structure-test.yml

# Integration tests (if applicable)
# pytest tests/integration/ -v

# Cleanup
docker compose down
echo "All container tests passed."
```

**Automated test scripts:** Two scripts are provided for running docker compose
tests non-interactively (useful in CI or local verification):

- [`scripts/test_docker_compose.py`](../scripts/test_docker_compose.py) — Python
  script that builds, runs, and validates the docker compose stack
- [`scripts/test_docker_compose.sh`](../scripts/test_docker_compose.sh) — Bash
  equivalent for shell-based CI pipelines

Both scripts build the image, start the container, verify it runs correctly,
and clean up. Run either one:

```bash
python scripts/test_docker_compose.py          # Python version
bash scripts/test_docker_compose.sh            # Bash version
python scripts/test_docker_compose.py --dry-run # Preview without executing
```

**Containerfile-only test scripts** (no docker compose, tests the image
directly):

- [`scripts/test_containerfile.py`](../scripts/test_containerfile.py) — Python
  script that builds and validates the Containerfile image
- [`scripts/test_containerfile.sh`](../scripts/test_containerfile.sh) — Bash
  equivalent

```bash
python scripts/test_containerfile.py          # Python version
bash scripts/test_containerfile.sh            # Bash version
python scripts/test_containerfile.py --dry-run # Preview without executing
```

**Troubleshooting:**

| Problem                               | Solution                                                                                                                           |
| :------------------------------------ | :--------------------------------------------------------------------------------------------------------------------------------- |
| `failed to connect to the docker API` | Docker Desktop is not running. Start it from the Start menu / system tray.                                                         |
| `port is already allocated`           | Another process is using the port. Change the host port in `docker-compose.yml` (e.g., `9000:8000`).                               |
| Build fails at `pip install`          | Check that `pyproject.toml` and `src/` are correct. Run `python -m build` locally first to verify.                                 |
| Container exits immediately           | Check `docker compose logs`. For CLI tools, this is normal — the command ran and exited. Use `docker compose run` instead of `up`. |

---

## Documentation Stack

Ready-to-use documentation site powered by MkDocs + Material theme +
mkdocstrings ([ADR 020](adr/020-mkdocs-documentation-stack.md)).

| File / Directory            | Purpose                                           |
| :-------------------------- | :------------------------------------------------ |
| [mkdocs.yml](../mkdocs.yml) | Site configuration (theme, nav, plugins)          |
| `docs/`                     | Markdown source files                             |
| `site/`                     | Built HTML output (regenerated by `mkdocs build`) |

### Idea Development Lifecycle

The `docs/` directory includes a structured lifecycle for moving ideas
from initial thought to shipped code. Use it for non-trivial changes:

```
idea/problem        →  docs/explorations/           Early-stage evaluation
proposed design     →  docs/blueprints/             Structural design shape
decision locked in  →  docs/adr/                    Permanent decision record
build steps         →  docs/implementation-plans/   Step-by-step execution
```

Skip stages that don't apply. Each directory has a README and a template
to copy. See [development/development.md](development/development.md)
for the full workflow.

```bash
task docs:serve    # Live-reload at http://localhost:8000
task docs:build    # Build (strict mode — fails on warnings)
```

### Serving Documentation Locally

**Full project docs (MkDocs Material site with live-reload):**

```bash
task docs:serve          # Serves at http://localhost:8000 with live-reload
# or directly:
hatch run docs:serve     # Same thing, without the Task wrapper
```

**Command reference (auto-generated at build time):**

The command reference page (`docs/reference/commands.md`) is
auto-regenerated by the `generate_commands.py` MkDocs hook every time
you run `mkdocs build` or `mkdocs serve`. No manual step required — it's
always fresh.

```bash
task docs:commands             # Manually regenerate (if needed outside mkdocs)
task docs:commands:check       # Exit 1 if the committed file is stale (CI use)
task docs:commands -- --dry-run # Preview output without writing to disk
```

!!! tip "How auto-generation works"
The `mkdocs-hooks/generate_commands.py` hook runs during `on_pre_build`,
imports the generator from `scripts/generate_command_reference.py`, and
writes the output to `docs/reference/commands.md` only if the content
has changed (avoiding unnecessary live-reload triggers during `mkdocs serve`).

    To disable auto-generation, add to `mkdocs.yml`:

    ```yaml
    extra:
      generate_commands: false
    ```

**Docstring format:** mkdocstrings parses **Google-style** docstrings
(`docstring_style: google` in [mkdocs.yml](../mkdocs.yml)). Ruff enforces the
same convention (`convention = "google"` in [pyproject.toml](../pyproject.toml)).
Update both if you prefer a different style.

**To customize:**

1. Update [mkdocs.yml](../mkdocs.yml) — `site_name`, `site_url`, `repo_url`
2. Edit pages in `docs/` — add your own guides, tutorials, API docs
3. Update the `nav:` section in [mkdocs.yml](../mkdocs.yml)
4. (Optional) Enable GitHub Pages via the `docs-deploy.yml` workflow

Docs have two CI workflows:

- `docs-build.yml` — runs `mkdocs build --strict` on every PR (CI gate check)
- `docs-deploy.yml` — deploys to GitHub Pages on push to `main` (path-filtered)

**Repo-relative link handling:** Documentation files frequently link to
files outside `docs/` (e.g. `../../pyproject.toml`, `../scripts/clean.py`).
These relative links work when browsing on GitHub but would break on the
deployed MkDocs site. The [`repo_links.py`](../mkdocs-hooks/repo_links.py)
build hook automatically rewrites these links to absolute GitHub URLs at
build time, so authors can keep writing natural relative links and they
work in both contexts. See [`mkdocs-hooks/README.md`](../mkdocs-hooks/README.md)
for details.

If you don't need a documentation site, delete [mkdocs.yml](../mkdocs.yml)
and the docs you don't need.

---

## Environment Dashboard

A web-based environment inspection dashboard that runs locally and displays
a comprehensive report of your development environment. Built with FastAPI,
Jinja2, htmx, and Alpine.js.

### What It Shows

20 plugin-based collectors gather data across these categories:

| Section | What it reports |
| :------ | :-------------- |
| System | OS, CPU, architecture, shell, locale |
| Hardware | CPU/GPU specs, RAM, storage, thermals |
| Runtimes | Python version, implementation, all installations |
| Path | PATH entries with dead/duplicate/shadow detection |
| Git | Branch, dirty state, remotes, stash count |
| Venv | Virtual environment type and activation status |
| Packages | Installed packages with versions |
| Project | Repo structure, config files, build tools |
| Project Commands | CLI commands from Taskfile, pyproject.toml |
| Pip Environments | All Python installations with outdated package detection |
| Network | DNS and HTTPS connectivity |
| Filesystem | Disk space, temp dir, write permissions |
| Container | Docker, CI, WSL, dev container detection |
| Security | Secret detection, insecure PATH, SSH keys |
| Pre-commit Hooks | Hook inventory by stage |
| CI/CD Status | Workflow inventory and SHA-pinning status |
| Dependency Health | Outdated and vulnerable packages |
| Disk Workspace | Workspace size breakdown |
| Docs Status | MkDocs config and documentation inventory |
| Insights | Cross-section analysis and warnings |

### Running the Dashboard

```bash
task dashboard:serve          # http://127.0.0.1:8000
# or directly:
hatch run dashboard:serve
```

### Features

- **Dark/light mode** with 7 accent color themes
- **Real-time data freshness** indicator with auto-refresh
- **Redaction levels** (none, partial, full) for sensitive data
- **Copy-to-clipboard** on key values
- **Pip package management** — update outdated packages from the UI
- **Section guides** — expandable help explaining what each section means
- **Static HTML export** at `/export.html`
- **JSON API** at `/api/report` and `/api/summary`
- **Keyboard shortcuts** (`Ctrl+C` to stop)

### Routes

| Route | Purpose |
| :---- | :------ |
| `GET /` | Dashboard page |
| `GET /api/report` | Full JSON report |
| `GET /api/summary` | Summary JSON |
| `GET /export.html` | Static HTML export |
| `GET /section/...` | htmx partials |

See [docs/guide/dashboard-guide.md](guide/dashboard-guide.md) for the full
guide, and the [dashboard instructions](../.github/instructions/dashboard.instructions.md)
for development conventions.

---

## Editor & Git File Handling

Three files work together to ensure consistent formatting and line endings
across editors, operating systems, and git operations:

| File                    | Controls                                                                              | Applies where                                                                           |
| :---------------------- | :------------------------------------------------------------------------------------ | :-------------------------------------------------------------------------------------- |
| `.editorconfig`         | Indentation, charset, trailing whitespace, final newline                              | Any editor that supports EditorConfig (VS Code via extension, JetBrains natively, etc.) |
| `.gitattributes`        | Line ending normalization in git, diff drivers, binary file detection, linguist stats | Git operations (commit, checkout, diff, archive)                                        |
| `.vscode/settings.json` | Formatter choice, format-on-save, rulers, test runner, file exclusions                | VS Code only                                                                            |

### How They Relate

These files target **different layers** of the editing and version control
pipeline:

1. **`.editorconfig`** sets editor behavior _as you type_ — indent size,
   tab vs. spaces, line endings in the editor buffer, trailing whitespace
   trimming. It's editor-agnostic: any IDE that supports the standard reads
   it. In VS Code, the [EditorConfig extension](https://marketplace.visualstudio.com/items?itemName=EditorConfig.EditorConfig)
   applies these rules automatically.

2. **`.gitattributes`** controls what happens when files pass _through git_ —
   normalizing line endings on commit (`* text=auto eol=lf`), forcing LF for
   shell scripts even on Windows, marking binary files so git doesn't try to
   diff them, and setting diff drivers (`*.py diff=python`) for better hunk
   headers. This operates independently of your editor.

3. **`.vscode/settings.json`** configures VS Code-specific tooling — which
   formatter runs on save (Ruff for Python, Prettier for Markdown), test
   discovery settings, file explorer exclusions. These settings only apply
   in VS Code.

**Overlap:** `.editorconfig` and `.vscode/settings.json` both affect
indentation and line endings in VS Code. When the EditorConfig extension is
installed, `.editorconfig` wins for the settings it defines (indent size, EOL
style, trim whitespace). VS Code settings fill in everything else (formatters,
rulers, language-specific overrides). They complement rather than conflict.

**Overlap with `.gitattributes`:** `.editorconfig` sets `end_of_line = lf`
so your editor writes LF. `.gitattributes` sets `* text=auto eol=lf` so git
normalizes to LF on commit regardless. They reinforce each other — if your
editor misses a CRLF, git catches it.

### What to Customize

- **`.editorconfig`** — adjust indent sizes per file type if your team
  prefers different conventions. The defaults match Ruff's formatting.
- **`.gitattributes`** — add entries for file types your project uses
  (e.g., `.proto`, `.parquet`, vendor assets). Mark generated files with
  `linguist-generated=true` to exclude them from GitHub language stats.
- **`.vscode/settings.json`** — add formatters or settings for your stack
  (Django, FastAPI, etc.).

---

## Git Configuration

Unlike VS Code settings (which live in JSON files you edit directly), git
configuration is managed through the **`git config`** command. There are no
config files you edit in the same way as `settings.json` — instead, you
read and write individual settings via the terminal.

### Scopes

Git config has three scopes, each stored in a different file:

| Scope      | File location                                                                    | Applies to               | Set with                                                                |
| :--------- | :------------------------------------------------------------------------------- | :----------------------- | :---------------------------------------------------------------------- |
| **system** | `/etc/gitconfig` (Linux/macOS) or `C:\Program Files\Git\etc\gitconfig` (Windows) | All users on the machine | `git config --system <key> <value>`                                     |
| **global** | `~/.gitconfig` or `~/.config/git/config`                                         | All your repositories    | `git config --global <key> <value>`                                     |
| **local**  | `.git/config` in the repository                                                  | This repository only     | `git config --local <key> <value>` (or just `git config <key> <value>`) |

**Precedence:** local > global > system. A local setting overrides global,
which overrides system.

### Common Operations

```bash
# View a setting (shows effective value across all scopes)
git config <key>                     # e.g. git config user.email

# View where a setting is defined
git config --show-origin <key>       # shows file path and value

# Set at global scope (most common)
git config --global <key> <value>    # e.g. git config --global pull.rebase true

# Set at local scope (project-specific overrides)
git config --local <key> <value>     # e.g. git config --local user.email work@example.com

# Unset a value
git config --global --unset <key>

# List all settings with their scopes
git config --list --show-origin
```

### This Project's Defaults

This template includes git config management via `git_doctor.py`. Use
Taskfile shortcuts or run the script directly:

```bash
task doctor:git:config:minimal             # apply 12 core recommended settings
task doctor:git:config:minimal -- --dry-run # preview first
task doctor:git:config:apply               # apply ALL recommended settings
task doctor:git:config:export              # export full reference to git-config-reference.md
```

For the full reference of all git config options and their recommended values,
see [git-config-reference.md](../git-config-reference.md) (generated by
`python scripts/git_doctor.py --export-config`).

---

## Further Reading

| Topic                          | Document                                                 |
| :----------------------------- | :------------------------------------------------------- |
| Repo layout explained          | [repo-layout.md](repo-layout.md)                         |
| All tools at a glance          | [tooling.md](tooling.md)                                 |
| Why each tool was chosen       | [tool-decisions.md](design/tool-decisions.md)            |
| Architecture overview          | [architecture.md](design/architecture.md)                |
| Templates & examples inventory | [template-inventory.md](reference/template-inventory.md) |
| Known issues & tech debt       | [known-issues.md](known-issues.md)                       |
| Learning resources (links)     | [resources_links.md](notes/resources_links.md)           |
| Learning resources (written)   | [resources_written.md](notes/resources_written.md)       |
| Release policy                 | [releasing.md](releasing.md)                             |
| Contributing guide             | [CONTRIBUTING.md](../CONTRIBUTING.md)                    |
| ADR index                      | [docs/adr/](adr/README.md)                               |

---

## VS Code Configuration

This template uses **two complementary VS Code configuration files** with
different scopes and purposes:

| File                    |  Committed?  | Who it's for     | What it controls                                                               |
| :---------------------- | :----------: | :--------------- | :----------------------------------------------------------------------------- |
| `.vscode/settings.json` | Yes (shared) | All contributors | Project-functional settings: formatters, linters, test config, file exclusions |
| `.code-workspace`       | Yes (shared) | All contributors | Extension recommendations, cosmetic preferences (indentRainbow)                |

### How They Work Together

The **`.vscode/settings.json` file** is the shared project baseline. It's
committed to git and contains the functional toolchain settings (Ruff as
formatter, Pylance type-checking mode, pytest config, file exclusions, etc.)
that ensure every contributor gets the same development experience — regardless
of whether they open the project as a folder or as a workspace.

The **`.code-workspace` file** supplements `.vscode/settings.json` with
extension recommendations and cosmetic preferences. It only loads when a
contributor explicitly opens the `.code-workspace` file (File → Open Workspace
from File).

Because VS Code's "Folder Settings" layer (`.vscode/`) takes priority over the
"Workspace Settings" layer (`.code-workspace`), anything in
`.vscode/settings.json` wins when both are active. This is intentional —
functional settings should be authoritative.

<!-- TODO (template users): If you prefer .vscode/settings.json to be
     personal / git-ignored (so each contributor brings their own editor
     settings), add `.vscode/settings.json` back to .gitignore and move
     shared functional settings into the .code-workspace file instead.
     See .gitignore for the corresponding TODO. -->

**Personal overrides:** If you need to override a shared setting for your
local environment only, use VS Code's _User Settings_ (`Ctrl+,` → User tab)
or a profile. User Settings take lowest priority so they won't affect
other contributors.

### When Does Each File Load?

| Open method                         | `.vscode/settings.json` | `.code-workspace` |
| :---------------------------------- | :---------------------: | :---------------: |
| **File → Open Folder**              |           Yes           |      Ignored      |
| **File → Open Workspace from File** |   Yes (folder-level)    | Yes (supplements) |
| **Codespaces / Dev Containers**     |           Yes           |      Ignored      |

This means `.vscode/settings.json` works regardless of how the project is
opened, making it the right place for functional settings (formatters,
linters, test runners). The `.code-workspace` file only applies when
explicitly opened as a workspace; it provides extension recommendations and
cosmetic preferences on top.

---

## VS Code Workspace File

The [`.code-workspace`](../simple-python-boilerplate.code-workspace) file
provides a shared, version-controlled VS Code configuration for all
contributors. It eliminates "works on my machine" editor config drift by
defining formatter choices, format-on-save behaviour, file exclusions, and
extension recommendations in one place.

### What It Provides

| Section        | What it controls                                                                     |
| :------------- | :----------------------------------------------------------------------------------- |
| **Settings**   | Python formatter (Ruff), format-on-save, Markdown word wrap, file exclusions, rulers |
| **Extensions** | Recommended extensions that VS Code prompts to install on first open                 |

### Opening the Workspace

Open the file directly — **File → Open Workspace from File…** and select
`simple-python-boilerplate.code-workspace`.

VS Code will prompt you to install any recommended extensions you don't
already have.

### Recommended Extensions

All extensions are active by default. The list is split into two tiers —
**project-essential** tools that directly mirror CI/tooling, and
**quality-of-life** tools that improve the editing experience. Template users
should review both and remove or comment out anything that doesn't apply.

**Project-essential** — directly tied to project tooling and CI:

| Extension                                       | Why it's included                                                                              |
| :---------------------------------------------- | :--------------------------------------------------------------------------------------------- |
| `ms-python.python` + `ms-python.vscode-pylance` | Core Python IntelliSense                                                                       |
| `ms-python.mypy-type-checker`                   | Real-time type error feedback (matches CI mypy)                                                |
| `charliermarsh.ruff`                            | In-editor linting + format-on-save (Ruff is the CLI linter, the extension gives live feedback) |
| `DavidAnson.vscode-markdownlint`                | Markdown lint errors inline                                                                    |
| `esbenp.prettier-vscode`                        | Markdown/YAML/JSON formatting                                                                  |
| `bierner.markdown-mermaid`                      | Renders mermaid diagrams in VS Code's Markdown preview (e.g., [releasing.md](releasing.md))    |
| `tamasfe.even-better-toml`                      | TOML syntax for `pyproject.toml`                                                               |
| `redhat.vscode-yaml`                            | YAML validation for workflows and configs                                                      |
| `eamodio.gitlens`                               | Git blame, history, and annotations                                                            |
| `GitHub.vscode-github-actions`                  | Workflow syntax validation and auto-complete (37 workflows in this project)                    |
| `task.vscode-task`                              | Task runner integration for `Taskfile.yml`                                                     |
| `EditorConfig.EditorConfig`                     | Consistent editor settings across editors                                                      |
| `streetsidesoftware.code-spell-checker`         | Spell checking in code and docs                                                                |

**Quality-of-life** — improve the editing experience but not project-critical:

| Extension                            | Why it's included                                                        |
| :----------------------------------- | :----------------------------------------------------------------------- |
| `aaron-bond.better-comments`         | Colourised TODO/FIXME/HACK comments                                      |
| `usernamehw.errorlens`               | Inline error/warning display at end of line                              |
| `github.copilot-chat`                | AI assistant (pairs with `copilot-instructions.md`)                      |
| `oderwat.indent-rainbow`             | Colourised indentation levels (custom high-contrast colours in settings) |
| `ms-python.vscode-python-envs`       | Visual Python environment manager                                        |
| `inferrinizzard.prettier-sql-vscode` | SQL formatting (useful if keeping `db/` scaffolding)                     |
| `mechatroner.rainbow-csv`            | CSV/TSV column highlighting                                              |
| `ms-azuretools.vscode-docker`        | Docker/container integration                                             |

<!-- TODO (template users): Review both tiers. Remove QoL extensions your
     team doesn't need. Add extensions specific to your stack (e.g., database
     clients, REST clients, framework-specific tools). -->

> **Tip:** This file uses JSONC (JSON with Comments). To disable an extension,
> just comment out or delete the line — JSONC handles trailing commas and
> comment gaps gracefully, so you don't need to worry about breaking the array.

### Customizing After Forking

1. **Rename the file** to match your project: `your-project.code-workspace`
2. **Review extensions** — uncomment optional ones your team wants, remove
   ones that don't apply
3. **Add project-specific settings** — e.g., if using Django, add
   `"python.analysis.extraPaths"` or a different test framework
4. **Commit the file** — it belongs in version control so all contributors
   share the same baseline

### Settings Override Hierarchy

VS Code applies settings in layers. Each layer overrides the one above it:

|  Priority   | Source                 | Where It Lives                                | Scope                                    |
| :---------: | :--------------------- | :-------------------------------------------- | :--------------------------------------- |
| 1 (lowest)  | **Default settings**   | Built into VS Code                            | All workspaces                           |
|      2      | **User settings**      | `%APPDATA%/Code/User/settings.json` (Windows) | All workspaces                           |
|      3      | **Workspace settings** | `.code-workspace` file → `"settings"` block   | Everyone who opens this workspace file   |
| 4 (highest) | **Folder settings**    | `.vscode/settings.json` inside a folder       | That folder only (multi-root workspaces) |

Within any layer, **language-specific overrides** (e.g.,
`"[python]": { "editor.formatOnSave": true }`) take precedence over
general settings at that same layer.

**Where Profiles fit:** A VS Code Profile is _not_ a separate layer — it
_replaces_ the User Settings layer entirely. Each profile has its own
`settings.json`, its own set of enabled extensions, and its own keybindings.
Switching profiles swaps which User Settings are active. Workspace settings
(from `.code-workspace`) still override whatever profile is active.

Practical implications:

- Settings in this project’s `.code-workspace` override your personal
  User / Profile settings. This is intentional — it ensures every
  contributor uses the same formatter, ruler positions, and file
  exclusions.
- If you need a personal override that wins over the workspace file,
  create a `.vscode/settings.json` inside the repo root (it’s
  git-ignored by default). This is the Folder Settings layer and
  has the highest priority.
- Profile settings let you control which _extensions_ are active
  per project, which the workspace file cannot enforce.

### Using with VS Code Profiles

`.code-workspace` and [VS Code Profiles](https://code.visualstudio.com/docs/editor/profiles)
complement each other:

- **`.code-workspace`** = team baseline (committed, shared via git, recommends extensions)
- **Profiles** = personal overrides (local to your machine, can enable/disable extensions)

A common pattern: use `code-workspace` for project-agreed settings, and a
VS Code profile to disable extensions from other projects that clutter your
sidebar (e.g., Java extensions when doing Python work).

Note that `.code-workspace` can only _recommend_ extensions — it cannot
force-install or force-disable them. For disabling unwanted extension
suggestions, use the `"unwantedRecommendations"` array in the `extensions`
block.

### Why Some CLI Tools Also Have VS Code Extensions

Tools like Ruff, mypy, and markdownlint exist both as CLI tools (run in CI
and pre-commit hooks) and as VS Code extensions. The CLI tools are the source
of truth — CI enforces them. The VS Code extensions provide **real-time editor
feedback** (red squiggles, format-on-save, quick-fixes) so you catch issues
before committing rather than waiting for the linter to run.

### MkDocs-Specific Markdown Preview

VS Code's built-in Markdown preview does not render MkDocs-specific syntax
like `:::` admonition directives or `mkdocstrings` autodoc blocks. No VS Code
extension currently supports this. For full-fidelity preview of MkDocs
content, use the live-reload server:

```bash
task docs:serve    # http://localhost:8000 with live-reload
```

The `bierner.markdown-mermaid` extension does handle ` ```mermaid ` blocks
in VS Code's Markdown preview.

---

## Copilot Customization

<!-- TODO (template users): After forking, update these files to match YOUR
     project. The boilerplate ships with sensible defaults, but Copilot is
     far more useful when instructions reflect your actual codebase. -->

This template ships with a set of files that configure GitHub Copilot's
behaviour in VS Code. They use three complementary mechanisms:

### How It Works

| Mechanism               | File pattern              | When Copilot reads it                                     | Use for                                                                                |
| :---------------------- | :------------------------ | :-------------------------------------------------------- | :------------------------------------------------------------------------------------- |
| **Instructions**        | `.instructions.md`        | Automatically, when editing files matching `applyTo` glob | File-type-specific rules (e.g., "all workflow YAML files must use SHA-pinned actions") |
| **Global instructions** | `copilot-instructions.md` | Every interaction in the workspace                        | Project-wide context, conventions, review priorities                                   |
| **Skills**              | `SKILL.md`                | When Copilot determines the skill is relevant             | Multi-step procedures (e.g., "add a new ADR")                                          |
| **Agents**              | `AGENTS.md`               | When the named agent is invoked                           | Specialized personas with tool restrictions                                            |

### Files Included

| File                                 | Scope                           |
| ------------------------------------ | ------------------------------- |
| `.github/copilot-instructions.md`    | Project-wide rules and context  |
| `.github/SKILL.md`                   | Multi-step component procedures |
| `.github/workflows/.instructions.md` | Workflow YAML conventions       |
| `scripts/.instructions.md`           | Script conventions              |
| `docs/.instructions.md`              | Documentation conventions       |
| `docs/adr/.instructions.md`          | ADR creation procedure          |
| `tests/.instructions.md`             | Test conventions                |

### Customizing for Your Project

1. **Start with `copilot-instructions.md`.** Replace the "Domain / Business
   Context" section with 2–3 sentences describing what your application does.
   This single change dramatically improves Copilot's suggestions.
2. **Update targeted files.** Edit each `.instructions.md` to reflect your
   conventions. Remove rules that don't apply, add ones specific to your stack.
3. **Add new instruction files** for other file types as needed (e.g.,
   `src/.instructions.md` for application-specific patterns).
4. **Consider adding skills** for repeatable multi-step procedures unique to
   your project.

For details on each mechanism, see the
[VS Code Copilot customization docs](https://code.visualstudio.com/docs/copilot/copilot-customization).

---

## Optional Tools to Consider

Not included in the template, but worth evaluating. Some overlap with
built-in tooling — tools marked “(included)” are already bundled in this
template but listed here so you see how they compare to alternatives.

### Web Frameworks

| Tool                                        | When to use                                                   |
| :------------------------------------------ | :------------------------------------------------------------ |
| [FastAPI](https://fastapi.tiangolo.com/)    | Building an API (async, auto-generated OpenAPI docs)          |
| [Flask](https://flask.palletsprojects.com/) | Lightweight web apps and APIs                                 |
| [Django](https://www.djangoproject.com/)    | Full-featured web framework (ORM, admin, auth built-in)       |
| [Litestar](https://litestar.dev/)           | High-performance async API framework (alternative to FastAPI) |
| [Starlette](https://www.starlette.io/)      | Lightweight ASGI framework (FastAPI builds on this)           |

### Database & ORM

| Tool                                        | When to use                                             |
| :------------------------------------------ | :------------------------------------------------------ |
| [SQLAlchemy](https://www.sqlalchemy.org/)   | Relational DB with Python models (ORM or Core)          |
| [Alembic](https://alembic.sqlalchemy.org/)  | Managing schema migrations (pairs with SQLAlchemy)      |
| [SQLModel](https://sqlmodel.tiangolo.com/)  | Pydantic + SQLAlchemy models in one (good with FastAPI) |
| [Tortoise ORM](https://tortoise.github.io/) | Django-like async ORM                                   |
| [Peewee](https://docs.peewee-orm.com/)      | Minimalist ORM for small projects                       |

### Testing & Quality

| Tool                                                     | When to use                                                              |
| :------------------------------------------------------- | :----------------------------------------------------------------------- |
| [pytest-mock](https://pytest-mock.readthedocs.io/)       | Thin wrapper around `unittest.mock` for pytest fixtures                  |
| [pytest-asyncio](https://pytest-asyncio.readthedocs.io/) | Testing async code with pytest                                           |
| [Hypothesis](https://hypothesis.readthedocs.io/)         | Property-based testing (finds edge cases automatically)                  |
| [Nox](https://nox.thea.codes/)                           | Test automation across Python versions (alternative to tox/Hatch matrix) |
| [tox](https://tox.wiki/)                                 | Test automation (alternative to Hatch matrix)                            |
| [Coverage.py](https://coverage.readthedocs.io/)          | Code coverage (already used via pytest-cov, but can run standalone)      |
| [mutmut](https://mutmut.readthedocs.io/)                 | Mutation testing — verifies test suite quality                           |

### HTTP & Networking

| Tool                                         | When to use                                          |
| :------------------------------------------- | :--------------------------------------------------- |
| [HTTPX](https://www.python-httpx.org/)       | Modern async-capable HTTP client (replaces requests) |
| [requests](https://requests.readthedocs.io/) | Simple synchronous HTTP client                       |
| [aiohttp](https://docs.aiohttp.org/)         | Async HTTP client and server                         |

### CLI & Configuration

| Tool                                                        | When to use                                        |
| :---------------------------------------------------------- | :------------------------------------------------- |
| [Click](https://click.palletsprojects.com/)                 | Building CLI tools (decorator-based, composable)   |
| [Typer](https://typer.tiangolo.com/)                        | Building CLIs with type hints (built on Click)     |
| [Rich](https://rich.readthedocs.io/)                        | Pretty console output, tables, progress bars       |
| [Pydantic](https://docs.pydantic.dev/)                      | Data validation and settings management            |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | Load `.env` files into environment variables       |
| [dynaconf](https://www.dynaconf.com/)                       | Multi-layer config management (env, files, vaults) |

### Task Queues & Background Jobs

| Tool                                               | When to use                                     |
| :------------------------------------------------- | :---------------------------------------------- |
| [Celery](https://docs.celeryq.dev/)                | Distributed task queue (Redis/RabbitMQ backend) |
| [RQ (Redis Queue)](https://python-rq.org/)         | Simple job queue backed by Redis                |
| [Dramatiq](https://dramatiq.io/)                   | Alternative to Celery with saner defaults       |
| [APScheduler](https://apscheduler.readthedocs.io/) | In-process job scheduling (cron-like)           |

### Monitoring & Observability

| Tool                                                             | When to use                                          |
| :--------------------------------------------------------------- | :--------------------------------------------------- |
| [Sentry](https://sentry.io/)                                     | Production error tracking and performance monitoring |
| [structlog](https://www.structlog.org/)                          | Structured logging (JSON output, context binding)    |
| [OpenTelemetry](https://opentelemetry.io/docs/languages/python/) | Distributed tracing, metrics, and logs               |
| [Prometheus client](https://github.com/prometheus/client_python) | Expose metrics for Prometheus scraping               |

### Development & Debugging

| Tool                                               | When to use                                        |
| :------------------------------------------------- | :------------------------------------------------- |
| [IPython](https://ipython.readthedocs.io/)         | Enhanced interactive Python shell                  |
| [icecream](https://github.com/gruns/icecream)      | Better `print()` debugging: `ic(variable)`         |
| [devtools](https://python-devtools.helpmanual.io/) | Debug utilities: `debug(variable)`                 |
| [pdb++](https://github.com/pdbpp/pdbpp)            | Enhanced Python debugger (drop-in pdb replacement) |

### Linting & Formatting (alternatives/additions)

| Tool                                            | When to use                                                                                                |
| :---------------------------------------------- | :--------------------------------------------------------------------------------------------------------- |
| [Prettier](https://prettier.io/)                | Markdown/YAML/JSON formatting **(included** as a manual pre-commit hook and VS Code default formatter**)** |
| [mdformat](https://github.com/hukkin/mdformat)  | Python-native Markdown formatter (no Node.js needed)                                                       |
| [Black](https://black.readthedocs.io/)          | Python code formatter (Ruff's formatter is a drop-in replacement)                                          |
| [isort](https://pycqa.github.io/isort/)         | Import sorting (Ruff includes this via `I` rules)                                                          |
| [Pylint](https://pylint.readthedocs.io/)        | Comprehensive Python linter (overlaps heavily with Ruff)                                                   |
| [pyright](https://microsoft.github.io/pyright/) | Alternative static type checker (faster than mypy, different trade-offs)                                   |

### Packaging & Distribution

| Tool                                    | When to use                                               |
| :-------------------------------------- | :-------------------------------------------------------- |
| [PyInstaller](https://pyinstaller.org/) | Bundle Python app into standalone executables             |
| [Nuitka](https://nuitka.net/)           | Compile Python to C for performance / distribution        |
| [pipx](https://pipx.pypa.io/)           | Install and run Python CLI tools in isolated environments |
| [uv](https://github.com/astral-sh/uv)   | Ultra-fast pip/venv replacement (from the Ruff team)      |

---

## Known Gotchas

Things that aren't obvious and will save you time if you know about them upfront.

### Bot PRs Don't Trigger the CI Gate

PRs created by automated workflows (pre-commit autoupdate, Dependabot) use
`GITHUB_TOKEN`, which **by design** doesn't trigger `pull_request` events
for other workflows. This means the CI gate status check stays stuck at
"Waiting for status to be reported."

**Workarounds:**

1. Close and reopen the PR manually (quickest)
2. Push an empty commit: `git commit --allow-empty -m "ci: trigger gate"`
3. Use a Personal Access Token (PAT) instead of `GITHUB_TOKEN` in the bot
   workflow (most automated, but requires repo secret setup)

See [known-issues.md](known-issues.md) for details.

### Python Version Drift

The minimum Python version is declared in multiple places: `pyproject.toml`
(`requires-python`, classifiers, Hatch test matrix), CI test matrix
(`test.yml`), and `bootstrap.py` (`MIN_PYTHON`). These can drift apart
silently. Run `python scripts/check_python_support.py` periodically to catch
mismatches.

### Hatch Doesn't Auto-Uninstall Removed Dependencies

After removing a dependency from `pyproject.toml`, the old package remains in
the Hatch environment. You must manually clean up:

```bash
hatch env remove default
hatch env create default
```

### Security Scan False Positives

The nightly security scan (`nightly-security.yml`) may flag CVEs in
transitive dependencies that have no fix available yet. Use the `ignore-vulns`
parameter in the pip-audit step to suppress known false positives, and
document each suppression in [known-issues.md](known-issues.md) with a TODO
to remove it when a fix ships.

---

## Need Help?

<!-- TODO (template users): Update the repo URL and Discussions link below
     to point to YOUR repository. Delete the Discussions bullet if you
     haven't enabled GitHub Discussions. -->

- **[Troubleshooting & FAQ](guide/troubleshooting.md)** — covers common errors
  for installation, pre-commit, CI/CD, testing, linting, Git, containers, and more
- **[GitHub Discussions](https://github.com/JoJo275/simple-python-boilerplate/discussions)** — ask questions, share ideas, or get help from the community
- **[Learning resources (links)](notes/resources_links.md)** — curated external links by topic
- **[Learning resources (written)](notes/resources_written.md)** — self-written references and cheat sheets
- Open an issue on the [template repository](https://github.com/JoJo275/simple-python-boilerplate)
