# ADR 025: Container Strategy for v1.0

## Status

Accepted

Refines [ADR 019: Containerfile](019-containerfile.md) for this project's
runtime stack.

## Context

`feedback-triage-app` ships as a containerised FastAPI service deployed
to Railway, fronted by a managed Postgres. "Containers" can mean
different things, and conflating them is the most common cause of
configuration drift:

1. **Production containers** — minimal images that run the application.
2. **Development containers** — full IDE environments for writing code.
3. **Container orchestration** — multi-service local stacks (app + DB).

We need an explicit answer for each.

## Decision

We provide three container-related configurations, each serving a
distinct purpose. This is a refinement of the template-era
[ADR 019](019-containerfile.md) and the original three-purpose
breakdown — the structure survives, the contents are project-specific.

### 1. `Containerfile` — production image

A multi-stage OCI image at the repo root.

**Stage 1 (`builder`)** uses the official `uv` image to build a wheel
via `uv build --wheel` against the committed `uv.lock`.

**Stage 2 (`runtime`)** is a slim Python base. The wheel is installed
system-wide via `uv pip install --system --no-cache <wheel>`. **No
virtualenv inside the container** — `uv pip install --system` writes
directly into site-packages and removes the activation dance.

Runtime invariants:

- Non-root user `app` (uid 1000); `WORKDIR /app`.
- `ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1`.
- `EXPOSE 8000`; `CMD ["uvicorn", "feedback_triage.main:app", "--host", "0.0.0.0", "--port", "8000"]`.
- `HEALTHCHECK` polls `GET /health` every 30s. `/health` is liveness
  (process up); `/ready` is readiness (DB reachable). Container's
  HEALTHCHECK uses `/health` to avoid restart loops when Postgres
  blips — see [ADR 053](053-migrations-as-pre-deploy-command.md).
- Base image and `uv` image are **digest-pinned** before any tagged
  release (`v0.1.0+`). The `latest` tags in `Containerfile` are TODOs
  during pre-1.0 churn only.
- Migrations are **never** run from `main.py` on boot. Railway's
  pre-deploy command runs `alembic upgrade head`. See
  [ADR 053](053-migrations-as-pre-deploy-command.md).

```bash
# Build & run the production image locally
docker build -t feedback-triage-app -f Containerfile .
docker run --rm -p 8000:8000 --env-file .env feedback-triage-app
```

### 2. Dev Container — `.devcontainer/devcontainer.json`

Configures VS Code to run inside a container with the project toolchain
pre-installed (`uv`, Python 3.13, Task, pre-commit, the recommended
extensions). Inherited from the template; retained as optional
infrastructure for Codespaces / VS Code Remote Containers.

Use case: consistent onboarding for contributors who want one-click
setup. Not required for development; the host-toolchain path
(`uv sync` + `task up` + `task dev`) is the documented default.

### 3. `docker-compose.yml` — local orchestration

Two services:

- **`db`** — `postgres:16-alpine` with a named volume `pgdata`,
  `pg_isready` healthcheck, and the credentials from `.env`.
- **`app`** — the same image as production, gated behind the
  `container` profile so `task up` (no profile) starts only Postgres.

Day-to-day: run `task dev` (FastAPI auto-reload on the host) against
the Compose-managed Postgres. The `container` profile is for
reproducing the production image locally:

```bash
docker compose --profile container up --build
```

### 4. Production target — Railway

- Image is built from `Containerfile` on every push to `main`.
- `alembic upgrade head` runs as the pre-deploy command.
- The container starts only if migrations succeed.
- Continuous deploy from `main`; no separate staging environment in
  v1.0.

## Alternatives Considered

### Single Dockerfile with build args for dev/prod

Use one Dockerfile with `--build-arg MODE=dev|prod` to switch behaviour.

**Rejected because:** the dev container has its own JSON contract for
VS Code (`devcontainer.json`); folding it into the production
Dockerfile loses that integration and complicates both surfaces.

### Skip Docker Compose

Use bare `docker build` and `docker run` commands.

**Rejected because:** Compose gives a declarative, version-controlled
record of how the local stack runs, and the multi-service shape
(app + Postgres) makes it strictly necessary in v1.0.

### Run migrations from `main.py` on boot

**Rejected because:** crashloops, race conditions across replicas,
slow startup. See [ADR 053](053-migrations-as-pre-deploy-command.md)
for full reasoning.

### Bundle a venv in the runtime image

**Rejected because:** `uv pip install --system` writes directly into
the image's site-packages and removes the activation dance. A venv
inside a container is the worst of both worlds.

### Distroless runtime base

**Deferred.** Listed as a future hardening step. `python:3.13-slim`
keeps iteration cost low for v1.0; switching to distroless is a
mechanical change once the surface stabilises.

### Docker-in-Docker for dev container

Run Docker inside the dev container for full container-workflow testing.

**Rejected because:** adds complexity and security considerations.
Contributors who need to test container builds can exit the dev
container and run Docker on the host.

## Consequences

### Positive

- Clear separation of concerns — each file has one purpose
  (`Containerfile` for prod, `.devcontainer/` for IDE,
  `docker-compose.yml` for local orchestration).
- One image runs in CI, locally (via the `container` profile), and on
  Railway. Reproducibility is a property of the file, not the platform.
- `uv` makes the build fast: a clean `uv build --wheel` resolves
  against the committed `uv.lock` in seconds.
- Production image stays small (~150 MB) because dev tools never enter
  the runtime stage.
- Non-root + `HEALTHCHECK` + digest-pinned base satisfies the spec's
  Container Hardening section.
- Migrations as a pre-deploy step keep the runtime image idempotent
  and crash-safe.

### Negative

- Three files (`Containerfile`, `.devcontainer/devcontainer.json`,
  `docker-compose.yml`) to maintain instead of one.
- Two compose profiles (`default` for `db`, `container` for `app`)
  is a small cognitive cost.
- Dev container path requires Docker Desktop (or Podman) installed.
- Pre-deploy migrations couple deployment to Railway's feature; moving
  off Railway requires reconfiguring the equivalent hook on the new
  platform.

### Mitigations

- Each file's role is documented in [README.md](../../README.md) and
  [`Taskfile.yml`](../../Taskfile.yml) (`task up`, `task down`,
  `task container:build`, `task container:run`).
- This ADR is the single reference for "which file does what".
- Files are independently optional — a contributor who never uses dev
  containers does not need to touch `.devcontainer/`.

## Implementation

- [`Containerfile`](../../Containerfile)
- [`docker-compose.yml`](../../docker-compose.yml)
- [`.dockerignore`](../../.dockerignore)
- [`.devcontainer/devcontainer.json`](../../.devcontainer/devcontainer.json)
- [`Taskfile.yml`](../../Taskfile.yml) — `up`, `down`, `container:build`,
  `container:run`
- [`container-structure-test.yml`](../../container-structure-test.yml)

## See also

- [ADR 019](019-containerfile.md) — original Containerfile decision
- [ADR 053](053-migrations-as-pre-deploy-command.md) — migrations as
  pre-deploy command
- [ADR 055](055-uv-as-project-manager.md) — uv as project manager
- [Dev Containers specification](https://containers.dev/)
- [Docker Compose documentation](https://docs.docker.com/compose/)
