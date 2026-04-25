# ADR 016: Use Hatchling (build backend) and Hatch (project manager) together

## Status

Accepted

## Context

Python packaging involves two distinct concerns:

1. **Building distributions** — creating sdist/wheel artifacts from source code.
2. **Managing the development workflow** — creating environments, running tests, linting, formatting, publishing, etc.

These are separate tools that are often confused because they share a name:

| Tool          | Role                                  | Runs when                                              |
| ------------- | ------------------------------------- | ------------------------------------------------------ |
| **Hatchling** | Build backend (like setuptools)       | `pip install .`, `python -m build`, `hatch build`      |
| **Hatch**     | Project manager (like tox/nox + venv) | `hatch run`, `hatch shell`, `hatch env`, `hatch build` |

### Key mental model

- **Hatchling** = "how to build the package"
- **Hatch** = "how to work on the project and trigger builds/tests/publishing"

Hatchling is declared in `[build-system]` and is used by _any_ PEP 517 installer (pip, build, etc.) — it does not require Hatch to be installed. Hatch is a CLI tool that _uses_ Hatchling under the hood for builds, but also manages environments, scripts, and version bumping.

### Why use both

Using both gives you a single `pyproject.toml` that can define:

- **Build backend** (Hatchling) — via `[build-system]`
- **What goes into distributions** (include/exclude rules) — via `[tool.hatch.build.targets.*]`
- **Version source/bumping rules** — via `[tool.hatch.version]`
- **Dev/test/lint environments and scripts** (Hatch) — via `[tool.hatch.envs.*]`

## Alternatives Considered

| Option                  | Pros                                      | Cons                                      |
| ----------------------- | ----------------------------------------- | ----------------------------------------- |
| **setuptools + tox**    | Mature, widely known                      | Two config formats, verbose setup         |
| **setuptools + nox**    | Flexible (Python-based config)            | Still two separate tools/configs          |
| **Hatchling + tox/nox** | Hatchling for build, tox/nox for workflow | Mixes ecosystems unnecessarily            |
| **Flit**                | Simple, minimal config                    | No environment management, fewer features |
| **PDM**                 | PEP 582 support, lock files               | Smaller community, different philosophy   |
| **Hatchling + Hatch**   | Single ecosystem, single config file      | Less familiar to some developers          |

## Decision

Use Hatchling as the build backend and Hatch as the project manager. Both are configured in `pyproject.toml`:

```toml
# Build backend (Hatchling)
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

# Build targets (Hatchling reads these)
# [tool.hatch.build.targets.sdist]
# [tool.hatch.build.targets.wheel]

# Project management (Hatch reads these)
[tool.hatch.envs.default]
[tool.hatch.envs.test]
```

Developers who don't want Hatch can still `pip install -e ".[dev]"` and run tools directly — Hatchling works with any PEP 517 installer.

## Consequences

### Positive

- One config file (`pyproject.toml`) for both build and workflow configuration.
- Hatch handles environment creation, dependency syncing, and script running.
- Test matrix support (`[[tool.hatch.envs.test.matrix]]`) for multi-version testing.
- No lock-in — Hatchling works independently of Hatch, so `pip install .` always works.

### Negative

- Developers must understand the Hatchling vs Hatch distinction.
- Hatch is less established than tox in some ecosystems.

### Neutral

- The project also supports a manual `pip install -e ".[dev]"` + direct commands workflow for developers who prefer not to install Hatch.
