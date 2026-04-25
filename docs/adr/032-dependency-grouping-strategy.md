# ADR 032: Dependency Grouping Strategy

## Status

Accepted

## Context

Python projects need different dependencies for different activities:
running tests, linting, building docs, deploying. How these dependencies are
organized affects developer experience, CI speed, and Dependabot's ability
to auto-update them.

[ADR 026](026-no-pip-tools.md) decided against pip-tools for dependency
management. This ADR documents how dependencies are _grouped_ and how those
groups map to Hatch environments, `pip install` extras, and CI workflows.

### Forces

- `[project.optional-dependencies]` (PEP 621) is the standard mechanism
  for dependency groups in `pyproject.toml`
- Hatch environments consume groups via `features = [...]`
- Dependabot reads `[project.optional-dependencies]` to auto-update tool
  versions
- Groups should balance granularity (installing only what's needed) against
  simplicity (not maintaining 10 separate groups)
- `requirements.txt` and `requirements-dev.txt` must exist for tools that
  don't read `pyproject.toml` (e.g., some CI actions, Dependabot pip
  ecosystem)

## Decision

### Dependency groups

Define four groups in `[project.optional-dependencies]`:

| Group    | Contents                                                       | Purpose                        |
| :------- | :------------------------------------------------------------- | :----------------------------- |
| `test`   | pytest, pytest-cov                                             | Minimal set for running tests  |
| `dev`    | test deps + ruff, mypy, pre-commit, bandit, commitizen, deptry | Full development toolchain     |
| `extras` | pipdeptree (+ commented suggestions)                           | Helpful but not required tools |
| `docs`   | mkdocs, mkdocs-material, pymdown-extensions, mkdocstrings      | Documentation build stack      |

### Group relationships

```
test ← dev ← (default Hatch env)
              ↑
              includes test via: "simple-python-boilerplate[test]"

docs ← (docs Hatch env)
extras ← (pip install -e ".[extras]")
```

`dev` **chains** `test` by including `"simple-python-boilerplate[test]"` as a
dependency. This means installing `dev` also installs all test dependencies.
`docs` and `extras` are independent groups.

### Hatch environment mapping

| Hatch env | Features   | Python versions  | Purpose                                |
| :-------- | :--------- | :--------------- | :------------------------------------- |
| `default` | `["dev"]`  | System default   | Day-to-day development (`hatch shell`) |
| `docs`    | `["docs"]` | System default   | Documentation build and serve          |
| `test`    | `["test"]` | 3.11, 3.12, 3.13 | Multi-version test matrix              |

### requirements.txt files

Two mirror files exist for compatibility:

| File                   | Mirrors                                 | Purpose                                                            |
| :--------------------- | :-------------------------------------- | :----------------------------------------------------------------- |
| `requirements.txt`     | Runtime deps (`[project.dependencies]`) | Tools that read requirements.txt (some CI actions, Dependabot pip) |
| `requirements-dev.txt` | `test` + `dev` groups combined          | Same                                                               |

These files are **not** the source of truth — `pyproject.toml` is
([ADR 002](002-pyproject-toml.md)). They exist as compatibility shims and
should be regenerated when `pyproject.toml` changes.

### Adding a dependency

1. Add it to the appropriate group in `[project.optional-dependencies]`
2. Run any `hatch` command — Hatch auto-syncs the environment
3. Update the corresponding `requirements*.txt` if applicable

### Removing a dependency

1. Remove it from `[project.optional-dependencies]`
2. Recreate the Hatch environment:
    ```bash
    hatch env remove default   # or: hatch env prune (removes ALL envs)
    ```
3. Update `requirements*.txt` if applicable

Hatch does not auto-uninstall removed packages — the environment must be
recreated. This is a known Hatch behavior documented in
`copilot-instructions.md`.

## Alternatives Considered

### Single `dev` group with everything

Put all tools (test, lint, docs, etc.) in one `dev` group.

**Rejected because:** CI workflows that only need pytest would install
mkdocs, ruff, mypy, etc. unnecessarily. Separate groups allow leaner
CI environments and faster installs.

### Many fine-grained groups (lint, type-check, security, etc.)

Split `dev` into `lint`, `typecheck`, `security`, `commit`, etc.

**Rejected because:** Over-segmentation adds maintenance burden with
minimal benefit. The current `dev` group installs quickly (~15 seconds)
and the cognitive overhead of "which group do I need?" outweighs
the disk space savings.

### PEP 735 dependency groups (`[dependency-groups]`)

Use the newer PEP 735 specification for development dependency groups.

**Rejected because:** PEP 735 is not yet widely supported by tools
(Dependabot, pip, Hatch). `[project.optional-dependencies]` works today
with all relevant tooling. This decision should be revisited when PEP 735
adoption matures.

### pip-tools for pinning

Use `pip-compile` to generate pinned requirements files.

**Rejected because:** See [ADR 026](026-no-pip-tools.md). Dependabot
handles version updates; pinning adds maintenance overhead without
proportional benefit for a template project.

## Consequences

### Positive

- Single source of truth in `pyproject.toml` for all dependencies
- Dependabot can auto-update every tool version
- Hatch environments stay in sync with declared groups
- `pip install -e ".[dev]"` and `hatch shell` produce identical environments
- CI can install minimal groups (just `test` for the test matrix)

### Negative

- `dev` chains `test` via a self-referential dependency
  (`"simple-python-boilerplate[test]"`), which template users must update
  when renaming their project
- `requirements*.txt` files can drift from `pyproject.toml` if not manually
  updated
- Hatch's non-removal behavior on dependency deletion is a gotcha

### Mitigations

- `customize.py` updates the self-referential dependency when renaming the
  project
- `copilot-instructions.md` and `USING_THIS_TEMPLATE.md` document the
  Hatch env removal gotcha
- deptry (included in `dev`) catches unused and missing dependencies

## Implementation

- [pyproject.toml](../../pyproject.toml) — `[project.optional-dependencies]`
  and `[tool.hatch.envs.*]` sections
- [requirements.txt](../../requirements.txt) — Runtime dependency mirror
- [requirements-dev.txt](../../requirements-dev.txt) — Dev dependency mirror
- [scripts/dep_versions.py](../../scripts/dep_versions.py) — Show installed
  dependency versions

## References

- [ADR 002](002-pyproject-toml.md) — pyproject.toml as single config source
- [ADR 016](016-hatchling-and-hatch.md) — Hatch as project manager
- [ADR 026](026-no-pip-tools.md) — No pip-tools
- [PEP 621 — Storing project metadata in pyproject.toml](https://peps.python.org/pep-0621/)
- [PEP 735 — Dependency Groups](https://peps.python.org/pep-0735/)
- [Hatch environments documentation](https://hatch.pypa.io/latest/config/environment/overview/)
