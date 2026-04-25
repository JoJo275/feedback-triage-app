# Tool Decisions

A living reference of tool evaluation notes — what was chosen, what was
skipped, and why. This complements the formal [ADRs](../adr/README.md) with the
lighter-weight reasoning that comes up when comparing specific tools.

<!-- TODO (template users): After forking, review every section below.
     Remove tools you don't use, add tools you adopt, and update rationale
     to reflect YOUR project's constraints. This file is only useful if it
     matches reality. -->

> **When to write here vs. an ADR:**
> An ADR captures a _significant architectural decision_ (e.g. "use pre-commit
> hooks" or "adopt a CI gate pattern"). This file captures the _tool-level
> trade-off notes_ within those decisions (e.g. "typos over codespell because
> it's faster and broader").

---

## Pre-commit Hooks

See [ADR 008](../adr/008-pre-commit-hooks.md) for the architectural decision
to use pre-commit. Notes below cover individual hook tool choices.

### Chosen

| Tool                      | Category           | Why chosen                                                                                                                                                       |
| ------------------------- | ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Ruff**                  | Lint + format      | Single Rust binary that subsumes flake8, isort, pyupgrade, autopep8, and black. Orders of magnitude faster. Configured in one `[tool.ruff]` section.             |
| **typos**                 | Spellcheck         | Rust-based, faster and broader detection than codespell. Auto-fix support. Config in `_typos.toml`.                                                              |
| **pip-audit**             | Vulnerability scan | PyPA-maintained, uses OSV + PyPI advisory DB. Successor to safety.                                                                                               |
| **gitleaks**              | Secret detection   | 150+ curated rules with entropy analysis. Single Go binary. Complements the fast regex `no-secrets-patterns` hook.                                               |
| **deptry**                | Dependency hygiene | No real alternative in Python. Compares `pyproject.toml` against actual imports to find unused, missing, and transitive deps.                                    |
| **actionlint**            | Workflow linting   | Only mature GitHub Actions workflow linter. Catches expression errors, unknown runner labels, missing action inputs.                                             |
| **commitizen**            | Commit messages    | Validates Conventional Commits format. Also provides `cz commit` for interactive authoring.                                                                      |
| **validate-pyproject**    | Config validation  | Validates `pyproject.toml` against PEP 621 / packaging schemas. Catches schema errors before CI.                                                                 |
| **check-jsonschema**      | Config validation  | SchemaStore-backed validation for GitHub workflows, actions, and Dependabot config.                                                                              |
| **no-commit-to-branch**   | Branch safety      | Prevents accidental direct commits to `main`/`master`. Zero config, zero cost.                                                                                   |
| **check-docstring-first** | Code quality       | Catches code placed before the module docstring — easy to miss in review.                                                                                        |
| **prettier**              | Markdown tables    | Manual-stage hook scoped to `*.md`. Fills the one formatting gap Ruff and markdownlint cannot: Markdown table alignment. Also available via `task fmt:markdown`. |

<!-- TODO (template users): If you add domain-specific hooks (e.g. sqlfluff
     for SQL linting, shellcheck for shell scripts), add them to this table
     and update ADR 008's hook inventory. -->

### Skipped

| Tool                              | Category            | Why skipped                                                                                                                                                                             |
| --------------------------------- | ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **pyupgrade**                     | Code moderniser     | Ruff's `UP` rule set includes all pyupgrade checks. Running both is redundant.                                                                                                          |
| **autopep8**                      | Formatter           | Ruff's formatter and linter cover all autopep8 fixes.                                                                                                                                   |
| **black**                         | Formatter           | `ruff-format` is a drop-in replacement, faster, and configured alongside the linter in one tool.                                                                                        |
| **isort**                         | Import sorter       | `ruff check` with isort rules (`I`) handles import sorting. Separate isort adds a dependency for duplicate functionality.                                                               |
| **codespell** (as a hook)         | Spellcheck          | typos is faster and has broader detection. codespell still runs in CI (`spellcheck.yml`) as a complementary safety net — the two overlap ~80% but each catches things the other misses. |
| **safety**                        | Vulnerability scan  | pip-audit is the PyPA-maintained successor. safety's free tier scans an older, smaller database subset.                                                                                 |
| **trufflehog**                    | Secret detection    | More complex setup, heavier runtime. gitleaks covers the same use case with a simpler single-binary approach.                                                                           |
| **Husky**                         | Git hooks framework | Node.js-based. Adds a Node dependency to a Python project. pre-commit is Python-native and has a larger hook ecosystem.                                                                 |
| **markdownlint-cli2** (as active) | Markdown linting    | Available as manual hook. Not active because it requires Node.js — heavier dependency footprint for optional benefit.                                                                   |
| **hadolint** (as active)          | Dockerfile linting  | Available as manual hook. Requires Docker runtime. Also covered in CI by Trivy misconfig scanning.                                                                                      |

### Notes

- **typos + codespell dual strategy:** typos runs locally (fast, Rust-based,
  pre-commit stage). codespell runs in CI (`spellcheck.yml`) with its own
  wordlist. They overlap ~80% but each catches things the other misses.
  Keeping both is intentional — not redundancy.

- **typos exclude for generated files:** `_typos.toml` excludes `CHANGELOG.md`
  (generated by release-please) from spellchecking. The pre-commit hook also
  has a matching `exclude` pattern as a belt-and-suspenders measure — typos may
  still check files passed explicitly by pre-commit even when the config says
  to skip them.

- **deptry requires project venv:** Unlike most hooks that run in pre-commit's
  isolated environment, deptry needs access to your installed packages to
  compare against imports. That's why it runs as a `local`/`system` hook via
  `hatch run deptry .` rather than as a remote-repo hook.

- **pip-audit on pre-push, not pre-commit:** Vulnerability scans hit a network
  API and can take several seconds. Running on every commit would be too slow.
  pre-push is the right trade-off — catches issues before code leaves your
  machine without slowing down every commit.

- **name-tests-test scoped to Python files:** The `name-tests-test` hook
  enforces `test_*.py` naming in `tests/` and `experiments/`. It must be
  restricted to `types: [python]` to avoid false positives on `README.md` and
  other non-Python files in those directories.

---

## GitHub Actions Workflows

See [ADR 003](../adr/003-separate-workflow-files.md) for why workflows are in
separate files, and [ADR 024](../adr/024-ci-gate-pattern.md) for the CI gate
pattern.

### Chosen

| Workflow                      | Purpose                   | Why chosen                                                                                                                                                                         |
| ----------------------------- | ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **ci-gate.yml**               | Fan-in required check     | Single `gate` status in branch protection instead of listing every workflow individually. Adding/removing workflows only requires editing one array in code — no Settings changes. |
| **lint-format.yml**           | Ruff lint + format        | Core quality gate. Ruff is the single linter/formatter (ADR 005).                                                                                                                  |
| **test.yml**                  | pytest matrix             | Runs across Python 3.11–3.13. Core quality gate.                                                                                                                                   |
| **type-check.yml**            | mypy                      | Strict type checking (ADR 007).                                                                                                                                                    |
| **coverage.yml**              | pytest-cov                | Tracks coverage trends via Codecov (80% project target, 70% patch target).                                                                                                         |
| **security-audit.yml**        | pip-audit                 | Vulnerability scanning against OSV/PyPI DB.                                                                                                                                        |
| **bandit.yml**                | Bandit security lint      | Path-filtered to `src/`/`scripts/` — only runs when Python source changes.                                                                                                         |
| **security-codeql.yml**       | GitHub CodeQL             | Deep semantic analysis. Scheduled + PR-triggered.                                                                                                                                  |
| **dependency-review.yml**     | Dependency review         | Flags new dependencies with known vulnerabilities on PRs.                                                                                                                          |
| **container-build.yml**       | OCI image build           | Builds the Containerfile on push/PR.                                                                                                                                               |
| **container-scan.yml**        | Trivy + Grype             | Multi-scanner container vulnerability scanning (ADR 012).                                                                                                                          |
| **spellcheck.yml**            | codespell in CI           | Safety net for typos that the local `typos` hook might miss.                                                                                                                       |
| **link-checker.yml**          | lychee                    | Validates URLs in docs. Path-filtered to `*.md`/`*.html`/`docs/`.                                                                                                                  |
| **commit-lint.yml**           | Commit message validation | Ensures Conventional Commits on PRs (ADR 009).                                                                                                                                     |
| **pr-title.yml**              | PR title validation       | Ensures PR titles follow conventional format.                                                                                                                                      |
| **release-please.yml**        | Automated releases        | Changelog + version bumps (ADR 021).                                                                                                                                               |
| **scorecard.yml**             | OpenSSF Scorecard         | Supply-chain security posture scoring.                                                                                                                                             |
| **sbom.yml**                  | SBOM generation           | Software Bill of Materials (ADR 013).                                                                                                                                              |
| **nightly-security.yml**      | Nightly full scan         | Comprehensive security sweep on schedule.                                                                                                                                          |
| **stale.yml**                 | Issue/PR cleanup          | Auto-labels and closes stale issues/PRs.                                                                                                                                           |
| **labeler.yml**               | Auto-labeling             | Labels PRs based on changed paths.                                                                                                                                                 |
| **pre-commit-update.yml**     | Hook updates              | Weekly PR to update pre-commit hook versions.                                                                                                                                      |
| **spellcheck-autofix.yml**    | Autofix typos             | Weekly PR with codespell auto-corrections.                                                                                                                                         |
| **auto-merge-dependabot.yml** | Auto-merge Dependabot     | Auto-approves and squash-merges minor/patch Dependabot PRs once CI passes.                                                                                                         |
| **docs-build.yml**            | Docs CI gate              | Runs `mkdocs build --strict` on every PR. Part of CI gate.                                                                                                                         |
| **docs-deploy.yml**           | Docs deployment           | Deploys to GitHub Pages on push to main. Path-filtered.                                                                                                                            |
| **smoke-test.yml**            | Script smoke testing      | Runs `--smoke` flag on scripts in a matrix. Catches import/argparse regressions ([ADR 042](../adr/042-script-smoke-testing.md)).                                                   |
| **doctor-all.yml**            | Full health check         | Runs all doctor scripts — warn-only comprehensive diagnostics in CI.                                                                                                               |

<!-- TODO (template users): Remove workflows you don't need (e.g. container-*
     if you don't ship containers, docs-deploy if you don't use GitHub Pages).
     Update docs/workflows.md and ci-gate.yml REQUIRED_CHECKS when you do. -->

### Skipped / Not adopted

| Workflow idea        | Why skipped                                                                                                                                                                                                                                                                  |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Mega CI workflow** | Would consolidate all jobs into one file with `needs:`. Violates ADR 003 (separate files). Loses per-workflow triggers, permissions, path filters, and independent failure isolation. The ci-gate pattern solves the "single required check" problem without this trade-off. |

### Notes

- **Path-filtered workflows and branch protection:** Workflows with `paths:`
  triggers (bandit, link-checker) can't be listed as required status checks in
  branch protection — they don't run on every PR, so GitHub would wait forever
  for a check that never appears. The ci-gate pattern handles this by only
  requiring always-run workflows in the `REQUIRED_CHECKS` list.

- **Scheduled workflows as safety nets:** Most security and scanning workflows
  run on a weekly schedule in addition to PR triggers. This ensures that even
  if a path filter skips a check on a particular PR, the check still runs
  regularly on `main`.

---

## Python Tooling

### Chosen

| Tool           | Purpose                       | Why chosen                                                                                                  |
| -------------- | ----------------------------- | ----------------------------------------------------------------------------------------------------------- |
| **Hatch**      | Project manager + env manager | Manages virtualenvs, runs scripts, builds packages. Single tool replaces tox + pip-tools + build (ADR 016). |
| **Hatchling**  | Build backend                 | PEP 517 build backend. Pairs with Hatch, auto-discovers `src/` layout.                                      |
| **hatch-vcs**  | Version from git tags         | Dynamic versioning from git tags. No manual version bumps. Fallback: `0.0.0+unknown`.                       |
| **pytest**     | Test framework                | De facto standard. Rich plugin ecosystem (ADR 006).                                                         |
| **pytest-cov** | Coverage plugin               | Integrates coverage.py with pytest. Branch coverage enabled, 80% minimum enforced.                          |
| **mypy**       | Type checker                  | Strict mode. Best error messages for gradual typing (ADR 007).                                              |
| **Ruff**       | Linter + formatter            | See pre-commit section above (ADR 005).                                                                     |
| **Bandit**     | Security linter               | AST-based Python security analysis. Skips `B101` (asserts) in config (ADR 018).                             |

### Skipped

| Tool           | Why skipped                                                                                                                                                                                                    |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **tox**        | Hatch environments cover the same use case (matrix testing, isolated envs) with less configuration.                                                                                                            |
| **Poetry**     | Excellent tool but uses a non-standard `[tool.poetry]` config. Hatchling uses standard PEP 621 metadata.                                                                                                       |
| **setuptools** | Works but requires more boilerplate. Hatchling auto-discovers `src/` layout with zero config.                                                                                                                  |
| **Flit**       | Simpler than setuptools, but lacks Hatchling's environment management and plugin ecosystem. No advantage when already using Hatch.                                                                             |
| **PDM**        | Full-featured alternative to Hatch. Less mature ecosystem and smaller community at time of evaluation. Hatch's PEP 621 compliance and env management won out.                                                  |
| **Pyright**    | Valid alternative to mypy. mypy was chosen for broader community adoption and better error messages for gradual typing. Pyright is available via Pylance in VS Code for real-time feedback.                    |
| **pip-tools**  | `pip-compile` is useful for pinning, but Hatch environments + `pyproject.toml` extras handle dependency management for this project's needs. See [ADR 026](../adr/026-no-pip-tools.md) for detailed rationale. |
| **nox**        | Python-native alternative to tox. More flexible than tox but adds a dependency Hatch already covers.                                                                                                           |

---

## Documentation Tooling

See [ADR 020](../adr/020-mkdocs-documentation-stack.md) for the architectural
decision to use MkDocs.

### Chosen

| Tool                       | Purpose                  | Why chosen                                                                                                                           |
| -------------------------- | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| **MkDocs**                 | Static site generator    | Python-native, simple config (`mkdocs.yml`), fast rebuild. Better fit for Python projects than Node-based alternatives.              |
| **mkdocs-material**        | Theme                    | Feature-rich Material Design theme. Built-in search, dark mode toggle, code copy, navigation tabs, content tabs. Active development. |
| **mkdocstrings\[python\]** | API docs from docstrings | Auto-generates API reference from Google-style docstrings. No manual duplication of function signatures.                             |
| **pymdown-extensions**     | Markdown extensions      | Adds tabbed content, details/summary, fenced code blocks with highlighting, inline code highlighting.                                |

<!-- TODO (template users): If you don't need API docs from docstrings, you
     can drop mkdocstrings from the docs dependency group in pyproject.toml. -->

### Skipped

| Tool             | Why skipped                                                                                                                                                                             |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Sphinx**       | More powerful for large API-heavy projects (cross-references, intersphinx). Steeper config, RST-centric (MyST bridges the gap but adds complexity). MkDocs is simpler for this project. |
| **Docusaurus**   | React-based. Adds a full Node.js build pipeline to a Python project. Overkill for project documentation.                                                                                |
| **Jupyter Book** | Sphinx-based, great for notebooks. Not needed here — no notebook-heavy documentation.                                                                                                   |
| **pdoc**         | Zero-config API docs. Too limited for project documentation beyond API reference — no custom pages, navigation, or theming.                                                             |

### Notes

- **Strict mode in CI:** `mkdocs build --strict` runs on every PR via
  `docs-build.yml`. This catches broken links, missing pages, and YAML
  errors before merge.

- **GitHub Pages deployment:** `docs-deploy.yml` deploys on push to `main`,
  path-filtered to `docs/`, `src/`, and `mkdocs.yml` changes.

- **MkDocs hooks have unit tests:** `mkdocs-hooks/repo_links.py` (~360 lines,
  3 link pattern types, protected-region handling) is covered by
  `tests/unit/test_repo_links.py` (86 tests). Tests cover all helper functions,
  all three link patterns, the protect/restore system, and end-to-end
  `on_page_markdown` behaviour.

<!-- TODO (template users): If you add custom MkDocs hooks, add corresponding
     unit tests. Hooks that rewrite content are especially prone to regressions
     when patterns change. See tests/unit/test_repo_links.py for an example. -->

---

## Task Runner

See [ADR 017](../adr/017-task-runner.md) for the architectural decision.

### Chosen

| Tool     | Purpose        | Why chosen                                                                                                                                     |
| -------- | -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| **Task** | Command runner | Go-based, single binary, `Taskfile.yml` config. Wraps `hatch run` commands for convenience. Cross-platform without shell compatibility issues. |

### Skipped

| Tool            | Why skipped                                                                                                                                        |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Make**        | Ubiquitous but tab-sensitive syntax, poor Windows support, file-based targets don't map well to "run this command" tasks.                          |
| **Just**        | Rust-based, simpler than Make. Less adoption than Task, similar feature set. Task's YAML config is more readable for this project's needs.         |
| **nox**         | Python-native session runner. Good for test matrices but overlaps with Hatch's env management. Would add a dependency for duplicate functionality. |
| **Invoke**      | Python-based, `tasks.py` config. Less declarative than Taskfile YAML. Adds a Python dependency when Task is language-agnostic.                     |
| **npm scripts** | Requires `package.json` in a Python project. Wrong ecosystem.                                                                                      |

---

## Container Tooling

See [ADR 019](../adr/019-containerfile.md) and
[ADR 025](../adr/025-container-strategy.md) for architectural decisions.

### Chosen

| Tool / Pattern         | Purpose               | Why chosen                                                                                                                   |
| ---------------------- | --------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| **Containerfile**      | Image definition      | OCI-standard name (not Docker-specific `Dockerfile`). Works with both Podman and Docker (ADR 019).                           |
| **Multi-stage build**  | Image size + security | Builder stage compiles wheel; runtime stage only has the installed package. No build tools, no source code in final image.   |
| **Digest pinning**     | Reproducibility       | Base image pinned to SHA256 digest, not a mutable tag. Ensures identical builds regardless of when the image is pulled.      |
| **Non-root user**      | Runtime security      | Creates `app` user (UID/GID 1000). Container never runs as root.                                                             |
| **docker-compose.yml** | Local orchestration   | Lightweight scaffolding for `docker compose up --build`. Stubs for common services (DB, env, ports) — not production config. |

<!-- TODO (template users): If you don't ship containers, delete Containerfile,
     docker-compose.yml, container-build.yml, and container-scan.yml. Remove
     the container entries from docs/workflows.md and ci-gate.yml. -->

### Skipped

| Tool / Pattern      | Why skipped                                                                                                                      |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **Dockerfile name** | Docker-specific convention. `Containerfile` is the OCI-standard name and works with both Docker and Podman.                      |
| **Distroless base** | Smaller attack surface but harder to debug (no shell). `python:3.12-slim` is a reasonable middle ground for a template project.  |
| **Alpine base**     | Smaller images but musl libc causes issues with some Python packages (numpy, pandas). Slim Debian avoids this class of problems. |
| **Buildpacks**      | Fully managed build. Less control over the image contents. Overkill for a project with a simple `pip install` step.              |

---

## Release & Versioning

See [ADR 021](../adr/021-automated-release-pipeline.md) for the release
pipeline decision.

### Chosen

| Tool               | Purpose               | Why chosen                                                                                                                         |
| ------------------ | --------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| **release-please** | Automated releases    | Google-maintained. Generates changelogs from Conventional Commits with no manual intervention. Creates release PRs automatically.  |
| **hatch-vcs**      | Dynamic versioning    | Version derived from git tags at build time. No manual version bumps. release-please creates the tags, hatch-vcs reads them.       |
| **commitizen**     | Commit message format | Validates Conventional Commits locally (commit-msg hook) and provides `cz commit` for interactive authoring. Feeds release-please. |

### Skipped

| Tool                 | Why skipped                                                                                                                                |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| **semantic-release** | Node.js-based. Adds a Node dependency. release-please is GitHub-native (Action) and doesn't require a Node runtime.                        |
| **bump2version**     | Manual version bumping. Redundant when hatch-vcs derives versions from git tags automatically.                                             |
| **setuptools-scm**   | Similar to hatch-vcs but tied to setuptools. hatch-vcs integrates natively with the Hatch/Hatchling build system already in use.           |
| **CalVer**           | Calendar-based versioning. SemVer is a better fit for a library/template where breaking changes need to be signaled in the version number. |

### Notes

- **release-please `simple` type:** Uses `release-type: "simple"` rather than
  `python` because this is a template project, not a PyPI package. The
  `extra-files` config updates `__init__.py` with the current version.

- **Changelog sections:** Only user-facing changes appear in `CHANGELOG.md`
  (`feat`, `fix`, `perf`, `revert`). Docs, style, chore, refactor, test,
  build, and CI commits are hidden from the changelog but still visible in
  git history.

---

## Coverage & Quality Metrics

### Chosen

| Tool            | Purpose             | Why chosen                                                                                                                        |
| --------------- | ------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **Codecov**     | Coverage tracking   | Free for open source. GitHub integration with PR comments showing coverage diff. Supports branch coverage and per-flag reporting. |
| **coverage.py** | Coverage collection | De facto standard for Python coverage. Branch coverage enabled. Integrated via pytest-cov.                                        |

### Skipped

| Tool           | Why skipped                                                                                                                       |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **Coveralls**  | Similar feature set to Codecov. Codecov has better GitHub Actions integration and more detailed PR comments.                      |
| **SonarCloud** | Full code quality platform (coverage + bugs + smells). Overkill — individual focused tools (Ruff, mypy, Codecov) cover each need. |

### Notes

- **Thresholds:** Project target is 80% overall (1% threshold before failing).
  Patch target is 70% on changed lines in PRs. Configured in `codecov.yml`.

<!-- TODO (template users): Adjust coverage thresholds in codecov.yml and
     pyproject.toml [tool.coverage.report] fail_under to match your project's
     maturity. 80% is a reasonable starting point; raise it as your test suite
     grows. -->

---

## Dependency Automation

See [ADR 010](../adr/010-dependabot-for-dependency-updates.md) for the
Dependabot decision and [ADR 032](../adr/032-dependency-grouping-strategy.md)
for grouping strategy.

### Chosen

| Tool / Pattern            | Purpose                 | Why chosen                                                                                                         |
| ------------------------- | ----------------------- | ------------------------------------------------------------------------------------------------------------------ |
| **Dependabot**            | Dependency updates      | GitHub-native. Monitors 3 ecosystems: `github-actions`, `pip`, `docker`. Weekly PRs with version bumps.            |
| **auto-merge-dependabot** | Auto-merge safe updates | Auto-approves and squash-merges Dependabot PRs for minor/patch bumps once CI passes. Reduces maintenance noise.    |
| **pre-commit autoupdate** | Hook version updates    | `pre-commit-update.yml` runs weekly. Dependabot doesn't support pre-commit hooks natively, so this fills the gap.  |
| **Grouped updates**       | PR noise reduction      | Minor and patch updates are grouped into single PRs per ecosystem. Reduces the number of Dependabot PRs to review. |

### Skipped

| Tool         | Why skipped                                                                                                                                                                                                 |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Renovate** | More configurable than Dependabot (supports pre-commit, regex managers, monorepo grouping). Heavier setup — Dependabot is zero-config for GitHub repos. Revisit if Dependabot's limitations become painful. |

### Notes

- **Three ecosystems:** `github-actions` (weekly, limit 5 PRs),
  `pip` (weekly, limit 10 PRs), `docker` (weekly, Containerfile base images).

- **Pre-commit gap:** Dependabot cannot update pre-commit hook versions.
  The `pre-commit-update.yml` workflow runs `pre-commit autoupdate` weekly
  and opens a PR with the changes.

<!-- TODO (template users): If you use Renovate instead of Dependabot, delete
     .github/dependabot.yml and auto-merge-dependabot.yml. Update this section
     and docs/workflows.md accordingly. -->

---

## Database Strategy

See [ADR 027](../adr/027-database-strategy.md) for the architectural
decision.

### Chosen

| Tool / Pattern | Purpose          | Why chosen                                                                                                          |
| -------------- | ---------------- | ------------------------------------------------------------------------------------------------------------------- |
| **Raw SQL**    | Database access  | No ORM. Plain SQL files in `db/` with numbered migrations, seed data, and documented queries. Maximum transparency. |
| **sqlite3**    | Default database | stdlib module, zero setup. Good enough for templates and small apps. `var/app.example.sqlite3` as example.          |

<!-- TODO (template users): Replace sqlite3 with your production database
     (PostgreSQL, MySQL, etc.). If you adopt an ORM (SQLAlchemy, Django ORM),
     update this section and consider creating an ADR for that decision. -->

### Skipped

| Tool           | Why skipped                                                                                                                            |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| **SQLAlchemy** | Powerful ORM but adds significant complexity. Raw SQL is more transparent for a template project. Easy to add later if needed.         |
| **Django ORM** | Ties the project to Django. This is a standalone Python project, not a Django app.                                                     |
| **Alembic**    | Migration tool for SQLAlchemy. Not needed without an ORM — numbered `.sql` files in `db/migrations/` serve the same purpose with less. |

---

## Label Management

See [ADR 030](../adr/030-label-management-as-code.md) for the architectural
decision.

### Chosen

| Tool / Pattern     | Purpose         | Why chosen                                                                                                        |
| ------------------ | --------------- | ----------------------------------------------------------------------------------------------------------------- |
| **Labels as code** | Issue/PR labels | JSON definitions in `labels/` applied via `scripts/apply_labels.py`. Reproducible, version-controlled, auditable. |

### Notes

- **Two label sets:** `labels/baseline.json` (core workflow labels) and
  `labels/extended.json` (optional detailed labels). Apply with
  `python scripts/apply_labels.py`.

<!-- TODO (template users): Customise label definitions in labels/baseline.json
     and labels/extended.json to match your project's workflow. -->

---

## Environment Dashboard

See [ADR 041](../adr/041-env-inspect-web-dashboard.md) for the web dashboard
decision and [ADR 043](../adr/043-collector-plugin-architecture.md) for the
collector plugin architecture.

### Chosen

| Tool / Pattern              | Purpose            | Why chosen                                                                                                              |
| --------------------------- | ------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| **FastAPI**                 | Web framework      | Async-native, automatic OpenAPI docs, lightweight. Already in the Python ecosystem — no new runtime.                    |
| **Jinja2 + htmx**          | Frontend rendering | Server-side rendering with minimal JavaScript. htmx provides dynamic UI without a full SPA framework.                   |
| **Alpine.js**              | Client-side state  | Lightweight (~15KB) declarative JS for toggles, filters, search. No build step.                                         |
| **Plugin-based collectors** | Data gathering     | Auto-discovered modules in `scripts/_env_collectors/`. Adding a data source requires only creating a new file — no registry edits. |

### Skipped

| Tool / Pattern | Why skipped                                                                                                         |
| -------------- | ------------------------------------------------------------------------------------------------------------------- |
| **Django**     | Full MVC framework — overkill for a single-page diagnostic dashboard. FastAPI is lighter and async-native.          |
| **Flask**      | Viable alternative. FastAPI was chosen for automatic OpenAPI docs and native async support.                          |
| **React/Vue**  | SPA frameworks add a Node.js build pipeline and significant complexity for a developer tool that shows system info. |

---

## Smoke Testing

See [ADR 042](../adr/042-script-smoke-testing.md) for the architectural
decision.

### Chosen

| Tool / Pattern     | Purpose                | Why chosen                                                                                                                         |
| ------------------ | ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| **`--smoke` flag** | Script import/argparse validation | Each script's `--smoke` flag verifies imports resolve and argparse initialises, then exits 0. No real logic executed. |
| **CI matrix**      | Per-script isolation   | GitHub Actions matrix strategy runs each script independently — one failure doesn't mask others.                                   |

### Notes

- The `--smoke` convention is implemented via the shared `_imports.py` module.
- Only scripts that have adopted the `--smoke` flag are included in the matrix.
  New scripts should add `--smoke` support to participate.

---

## Copilot Instructions

See [ADR 044](../adr/044-copilot-skills-and-instructions.md) for the
instruction architecture decision.

### Chosen

| Tool / Pattern                 | Purpose              | Why chosen                                                                                                     |
| ------------------------------ | -------------------- | -------------------------------------------------------------------------------------------------------------- |
| **`applyTo`-scoped files**     | Context targeting    | Copilot only loads instructions matching the current file pattern — no wasted context tokens.                   |
| **Layered architecture**       | Separation of scope  | Global rules in `copilot-instructions.md`, file-specific rules in `.instructions.md`, procedures in `SKILL.md`.|
| **SKILL.md multi-step recipes**| Procedure automation | Encodes sync steps (update index, regenerate docs, update instruction files) that humans forget.               |
