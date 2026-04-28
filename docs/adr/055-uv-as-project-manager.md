# ADR 055: uv as Project Manager; hatchling as Build Backend

## Status

Accepted

Partially supersedes [ADR 016](016-hatchling-and-hatch.md) — the
env-manager half (Hatch envs, `hatch run`, `hatch shell`). The
build-backend half of ADR 016 (hatchling + hatch-vcs) stays
authoritative.

## Context

The template was originally built around Hatch for both env management
(`hatch shell`, `hatch run`, env matrices) and as the consumer of the
`hatchling` build backend.

Since then, [uv](https://docs.astral.sh/uv/) has matured into a single
static-binary tool that subsumes:

- venv creation (`python -m venv`, `pipx`)
- dependency resolution + install (`pip`, `pip-tools`)
- Python interpreter install (`pyenv`)
- tool runners (`pipx run`)
- a native `uv.lock` for reproducible installs (which Hatch lacks)

It is also 10–100× faster than the pip-based stack, which matters for
cold CI runs and Docker layer rebuilds.

## Decision

- **uv** is the project manager. `uv sync` installs from `uv.lock`,
  `uv run <cmd>` runs commands in the project env, `uv add` / `uv
  remove` edit `pyproject.toml` and refresh the lockfile.
- `uv.lock` is committed. CI uses `uv sync --frozen`; lock drift fails
  the build.
- The build backend stays **`hatchling`** with **`hatch-vcs`** for
  git-tag-based versioning. `[build-system] requires = ["hatchling",
  "hatch-vcs"]` is unchanged.
- Inside the production container, `uv pip install --system --no-cache
  <wheel>` installs the built wheel — no venv inside the container.
- `Taskfile.yml` calls `uv run …` everywhere. `hatch run …` is removed.

## Alternatives Considered

### Stay on Hatch end-to-end

**Rejected because:** no native lockfile, slower CI, and uv's tooling
posture is now the 2026 default for Python project management.

### Switch the build backend to a uv-native one

**Rejected because:** uv has no build backend of its own. `hatchling +
hatch-vcs` is small, fast, and pairs cleanly with the release flow.

### Poetry or PDM

**Rejected because:** uv covers their feature set with fewer surprises
and a cleaner install story.

## Consequences

### Positive

- One static-binary tool for env, deps, lock, and Python install.
- Reproducible installs from `uv.lock`.
- Materially faster CI cold runs.
- The container build uses `uv pip install --system` for the wheel —
  no Hatch dependency in the runtime image.

### Negative

- One-time refactor of the Taskfile, pre-commit hooks, and CI workflows
  from `hatch run` → `uv run`.
- Hatch envs (`hatch run test:cov`, matrix envs) are gone. Matrix
  testing across Python versions, when reintroduced, will use
  `uv run --python 3.X pytest`.
