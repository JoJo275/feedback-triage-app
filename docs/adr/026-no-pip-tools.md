# ADR 026: Do not use pip-tools for dependency management

## Status

Accepted

## Context

[pip-tools](https://github.com/jazzband/pip-tools) provides `pip-compile` to
generate fully-pinned `requirements.txt` files from loose specifications, and
`pip-sync` to install exactly those pins. It is a popular choice for
reproducible dependency resolution in Python projects.

This project already uses **Hatch** for environment management and
**Hatchling** for building ([ADR 016](016-hatchling-and-hatch.md)). Hatch
creates isolated virtual environments from the dependency groups declared in
`pyproject.toml` (`[project.dependencies]`, `[project.optional-dependencies]`,
and `[tool.hatch.envs.*.dependencies]`). Adding pip-tools on top of this would
create a second, overlapping dependency management layer.

### The problem pip-tools solves

pip-tools addresses **reproducible installs** — ensuring every developer and CI
run gets exactly the same dependency versions by pinning transitive
dependencies in a lock file.

### Why that problem doesn't apply here

| Concern                           | How this project handles it                                                                                                                                                                                 |
| --------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Reproducible dev environments** | Hatch environments auto-install from `pyproject.toml` extras. Developers get consistent envs without a lock file.                                                                                           |
| **Reproducible CI**               | CI workflows install from `pyproject.toml` extras via `pip install -e ".[test]"` or Hatch envs. Pinning would require lock-file maintenance without meaningful benefit for a template repo.                 |
| **Reproducible builds**           | Build artifacts (sdist/wheel) declare dependency ranges, not pins. End users resolve versions at install time — this is standard Python packaging behavior. A lock file doesn't affect built distributions. |
| **Security auditing**             | `pip-audit` (in CI and pre-push hook) scans the resolved environment regardless of whether versions are pinned.                                                                                             |
| **Dependency drift**              | Dependabot opens PRs for new dependency versions weekly. Hatch recreates envs from current specs on each invocation.                                                                                        |

### What pip-tools would cost

- **Maintenance burden:** Every dependency change requires running
  `pip-compile` to regenerate lock files and committing the result.
  With multiple extras (`dev`, `test`, `docs`), that means multiple
  `requirements*.txt` files to keep in sync.
- **Merge conflicts:** Lock files change frequently and produce large
  diffs that conflict across branches.
- **Duplicate source of truth:** Dependencies would be declared in
  `pyproject.toml` (for Hatch and packaging) _and_ pinned in
  `requirements*.txt` (for pip-tools). Keeping both in sync is error-prone.
- **Hatch friction:** Hatch environments don't consume `requirements.txt`
  files natively — they read `pyproject.toml`. Using pip-tools would mean
  either abandoning Hatch envs or maintaining parallel install paths.

## Decision

Do not adopt pip-tools. Continue using `pyproject.toml` as the single source
of truth for all dependency specifications, with Hatch managing environments.

The commented-out `pip-tools` line in `pyproject.toml` under extras is
retained as a reference for template users who may want it for their own
projects — but it is not active in this template.

## Alternatives Considered

### pip-tools (pip-compile + pip-sync)

Generates pinned `requirements.txt` from `pyproject.toml` or `requirements.in`.

**Rejected because:** Adds a second dependency management layer that duplicates
what Hatch environments already provide. The lock-file maintenance cost
outweighs the reproducibility benefit for this project's use case.

### Poetry lock

Poetry generates a `poetry.lock` file automatically.

**Rejected because:** Would require switching from Hatchling/Hatch to Poetry
for both build backend and project management — a much larger change than just
adding pinning. See [ADR 016](016-hatchling-and-hatch.md) for why
Hatchling/Hatch was chosen.

### PDM lock

PDM supports PEP 621 metadata and generates lock files.

**Rejected because:** Similar trade-off to Poetry — would replace Hatch as the
project manager to gain lock-file support. Not justified for a template repo.

### uv lock

uv is a fast Rust-based package manager with lock-file support.

**Rejected because:** uv is rapidly evolving and may become a strong option in
the future, but as of this writing it would replace Hatch as the project
manager. The project may revisit this if uv matures into a stable Hatch
alternative. Not justified as an addition on top of the existing Hatch setup.

## Consequences

### Positive

- Single source of truth for dependencies (`pyproject.toml`)
- No lock-file maintenance or merge-conflict churn
- Hatch environments work without workarounds
- Simpler contributor onboarding — one tool, one config file

### Negative

- No guaranteed exact version reproducibility across environments (deps
  resolve at install time)
- Template users who need pinning must add pip-tools (or similar) themselves

### Mitigations

- Dependabot catches outdated or vulnerable transitive dependencies
- pip-audit scans resolved environments for known vulnerabilities
- CI runs on fresh installs, so version drift surfaces quickly as test failures
- The commented-out pip-tools entry in `pyproject.toml` makes it easy for
  template users to opt in if their project requires pinning

## Implementation

- [pyproject.toml](../../pyproject.toml) — Dependency declarations (single source of truth)
- [.github/dependabot.yml](../../.github/dependabot.yml) — Automated dependency update PRs
- [ADR 016](016-hatchling-and-hatch.md) — Hatchling + Hatch decision

## References

- [pip-tools documentation](https://pip-tools.readthedocs.io/)
- [Hatch environment docs](https://hatch.pypa.io/latest/environment/)
- [PEP 621 — Project metadata](https://peps.python.org/pep-0621/)
- [ADR 016 — Hatchling and Hatch](016-hatchling-and-hatch.md)
