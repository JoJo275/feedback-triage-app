# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records for this project.

ADRs are short documents that capture important architectural decisions made during development, along with their context and consequences.

## What is an ADR?

An ADR records a significant decision that affects the structure, non-functional characteristics, dependencies, interfaces, or construction techniques of a project.

## Format

Each ADR follows the structure defined in [template.md](template.md):

1. **Title** — Short descriptive name
2. **Status** — Proposed, Accepted, Deprecated, Superseded
3. **Context** — What is the issue or situation?
4. **Decision** — What did we decide?
5. **Alternatives Considered** — What else was evaluated and why was it rejected?
6. **Consequences** — What are the results (positive, negative, mitigations)?
7. **Implementation** — Links to the files that implement this decision
8. **References** — External docs, specs, or related ADRs

To create a new ADR, copy `template.md` to `NNN-short-title.md` and fill it in.

## Lifecycle

```
idea/problem → explorations/
proposed design → blueprints/
decision locked in → adr/              (this directory)
build steps → implementation-plans/
```

## When to Write an ADR

Write an ADR when a decision:

- Is **hard to reverse** (choosing a framework, database, or deployment strategy)
- **Affects multiple parts** of the project (new convention, pattern, or tooling)
- Would be **useful context** for future contributors ("why did we do it this way?")

Don't write an ADR for routine choices (dependency patch updates, style tweaks).
For lightweight tool comparisons, use [docs/design/tool-decisions.md](../design/tool-decisions.md) instead.

## Index

| ADR                                                   | Title                                                              | Status   |
| ----------------------------------------------------- | ------------------------------------------------------------------ | -------- |
| [001](001-src-layout.md)                              | Use src/ layout for package structure                              | Accepted |
| [002](002-pyproject-toml.md)                          | Use pyproject.toml for all configuration                           | Accepted |
| [003](003-separate-workflow-files.md)                 | Separate GitHub Actions workflow files                             | Accepted |
| [004](004-pin-action-shas.md)                         | Pin GitHub Actions to commit SHAs                                  | Accepted |
| [005](005-ruff-for-linting-formatting.md)             | Use Ruff for linting and formatting                                | Accepted |
| [006](006-pytest-for-testing.md)                      | Use pytest for testing                                             | Accepted |
| [007](007-mypy-for-type-checking.md)                  | Use mypy for static type checking                                  | Accepted |
| [008](008-pre-commit-hooks.md)                        | Use pre-commit hooks for automated checks                          | Accepted |
| [009](009-conventional-commits.md)                    | Use Conventional Commits for commit messages                       | Accepted |
| [010](010-dependabot-for-dependency-updates.md)       | Use Dependabot for dependency updates                              | Accepted |
| [011](011-repository-guard-pattern.md)                | Repository guard pattern for optional workflows                    | Accepted |
| [012](012-multi-layer-security-scanning.md)           | Multi-layer security scanning in CI                                | Accepted |
| [013](013-sbom-bill-of-materials.md)                  | SBOM generation and distribution strategy                          | Accepted |
| [014](014-no-template-engine.md)                      | No template engine — manual customisation                          | Accepted |
| [015](015-no-github-directory-readme.md)              | No README.md in .github/ directory                                 | Accepted |
| [016](016-hatchling-and-hatch.md)                     | Use Hatchling (build backend) and Hatch (project manager) together | Accepted |
| [017](017-task-runner.md)                             | Use Taskfile as the project task runner                            | Accepted |
| [018](018-bandit-for-security-linting.md)             | Use Bandit for Python security linting                             | Accepted |
| [019](019-containerfile.md)                           | Use Containerfile for OCI-compatible container builds              | Accepted |
| [020](020-mkdocs-documentation-stack.md)              | Use MkDocs with Material theme for project documentation           | Accepted |
| [021](021-automated-release-pipeline.md)              | Automated release pipeline with release-please                     | Accepted |
| [022](022-rebase-merge-strategy.md)                   | Rebase and merge strategy for pull requests                        | Accepted |
| [023](023-branch-protection-rules.md)                 | Branch protection rules for main                                   | Accepted |
| [024](024-ci-gate-pattern.md)                         | CI gate pattern for branch protection                              | Accepted |
| [025](025-container-strategy.md)                      | Container strategy — production, development, orchestration        | Accepted |
| [026](026-no-pip-tools.md)                            | Do not use pip-tools for dependency management                     | Accepted |
| [027](027-database-strategy.md)                       | Raw SQL database strategy                                          | Accepted |
| [028](028-git-branching-strategy.md)                  | Git branching strategy (trunk-based)                               | Accepted |
| [029](029-testing-strategy.md)                        | Testing strategy (unit/integration split, coverage, matrix)        | Accepted |
| [030](030-label-management-as-code.md)                | Label management as code                                           | Accepted |
| [031](031-script-conventions.md)                      | Script conventions                                                 | Accepted |
| [032](032-dependency-grouping-strategy.md)            | Dependency grouping strategy                                       | Accepted |
| [033](033-prettier-for-markdown-formatting.md)        | Prettier for Markdown formatting                                   | Accepted |
| [034](034-documentation-organization-strategy.md)     | Documentation organization strategy                                | Accepted |
| [035](035-copilot-instructions-as-context.md)         | Copilot instructions as developer context                          | Accepted |
| [036](036-diagnostic-tooling-strategy.md)             | Diagnostic tooling strategy (doctor scripts and profiles)          | Accepted |
| [037](037-git-configuration-as-code.md)               | Git configuration as code                                          | Accepted |
| [038](038-vscode-workspace-configuration-strategy.md) | VS Code workspace configuration strategy                           | Accepted |
| [039](039-developer-onboarding-automation.md)         | Developer onboarding automation (bootstrap and customize)          | Accepted |
| [040](040-v1-release-readiness.md)                    | v1.0 release readiness checklist                                   | Accepted |
| [041](041-env-inspect-web-dashboard.md)               | Environment inspection web dashboard                               | Accepted |
| [042](042-script-smoke-testing.md)                    | Script smoke testing in CI                                         | Accepted |
| [043](043-collector-plugin-architecture.md)           | Environment data collector plugin architecture                     | Accepted |
| [044](044-copilot-skills-and-instructions.md)         | Copilot skills and instruction file architecture                   | Accepted |

## Archive

Deprecated, superseded, or suspended ADRs are moved to the [archive/](archive/) directory.

## References

- [ADR GitHub Organization](https://adr.github.io/)
- [Michael Nygard's article on ADRs](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
