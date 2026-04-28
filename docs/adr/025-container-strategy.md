# ADR 025: Container Strategy for v1.0

## Status

Accepted

Refines [ADR 019: Containerfile](019-containerfile.md) for this project's
runtime stack.

## Context

`feedback-triage-app` ships as a containerised FastAPI service deployed
to Railway, fronted by a managed Postgres. We need a container story
that covers three audiences without conflating them:

1. **Production** — the image Railway runs.
2. **Local development** — what a contributor runs to work on the app.
3. **Local production-likeness** — what a contributor runs to
   reproduce the production image on their machine.

The template-era ADR (which classified containers into "production /
dev / orchestration" abstractly) does not capture the concrete shape of
this project's stack. This ADR replaces it.

## Decision

### Production image — `Containerfile` at the repo root

A multi-stage OCI image. Stage 1 (`builder`) uses the official `uv`
image to build a wheel via `uv build --wheel`. Stage 2 (`runtime`) is
a slim Python base. The wheel is installed system-wide via
`uv pip install --system --no-cache <wheel>`. **No virtualenv inside
the container.**

Runtime invariants:

- Non-root user `app` (uid 1000); `WORKDIR /app`.
- `ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1`.
- `EXPOSE 8000`; `CMD ["uvicorn", "feedback_triage.main:app", "--host", "0.0.0.0", "--port", "8000"]`.
- `HEALTHCHECK` polls `GET /health` every 30s. `/health` is liveness
  (process up); `/ready` is readiness (DB reachable). The container's
  HEALTHCHECK uses `/health` to avoid restart loops when Postgres
  blips — see [ADR 053](053-migrations-as-pre-deploy-command.md).
- Base image and `uv` image are **digest-pinned** before any tagged
  release (`v0.1.0+`). The `latest` tags in `Containerfile` are TODOs
  during pre-1.0 churn only.
- Migrations are **never** run from `main.py` on boot. Railway's
  pre-deploy command runs `alembic upgrade head`. See
  [ADR 053](053-migrations-as-pre-deploy-command.md).

### Local development — `docker compose up`

`docker-compose.yml` defines two services:

- `db` — `postgres:16-alpine` with a named volume `pgdata`,
  `pg_isready` healthcheck, and the credentials from `.env`.
- `app` — the same image as production, gated behind the
  `container` profile so `task up` (no profile) starts only Postgres.

Day-to-day, contributors run the app with `task dev` (FastAPI's
auto-reload server on the host) against the Compose-managed Postgres.
The `container` profile is only used when reproducing the production
image locally:

```bash
docker compose --profile container up --build
```

### Dev container — kept, but lightweight

`.devcontainer/devcontainer.json` is retained from the template as
optional infrastructure for Codespaces / VS Code Remote Containers
contributors. It is not required for development; the host-toolchain
path (`uv sync` + `task up` + `task dev`) is the documented default.

### Production target — Railway

Railway is the target platform ([ADR 053](053-migrations-as-pre-deploy-command.md)):

- Image is built from `Containerfile` on every push to `main`.
- `alembic upgrade head` runs as the pre-deploy command.
- The container starts only if migrations succeed.
- Continuous deploy from `main`; no separate staging environment in
  v1.0.

## Alternatives Considered

### Single Dockerfile with build args for dev/prod

**Rejected because:** the dev container has its own JSON contract for
VS Code (`devcontainer.json`); folding it into the production
Dockerfile loses that integration and complicates both surfaces.

### Run migrations from `main.py` on boot

**Rejected because:** crashloops, race conditions across replicas, and
slow startup. See [ADR 053](053-migrations-as-pre-deploy-command.md)
for the full reasoning.

### Bundle a venv in the runtime image

**Rejected because:** `uv pip install --system` writes directly into
the image's site-packages and removes the activation dance. A venv
inside a container is the worst of both worlds.

### Distroless runtime base

**Deferred.** Listed as a future hardening step. `python:3.13-slim`
keeps the iteration cost low for v1.0; switching to distroless is a
mechanical change once the surface stabilises.

## Consequences

### Positive

- One image runs in CI, locally (via the `container` profile), and on
  Railway. Reproducibility is a property of the file, not the platform.
- `uv` makes the build fast: a clean `uv build --wheel` resolves
  against the committed `uv.lock` in seconds.
- Non-root + `HEALTHCHECK` + digest-pinned base satisfies the spec's
  Container Hardening section.
- Migrations as a pre-deploy step keep the runtime image idempotent
  and crash-safe.

### Negative

- Two compose profiles (`default` for `db`, `container` for `app`)
  is a small cognitive cost; documented in
  [README.md](../../README.md) and [`Taskfile.yml`](../../Taskfile.yml).
- Pre-deploy migrations couple deployment to Railway's feature; moving
  off Railway requires reconfiguring the equivalent hook on the new
  platform.

## Implementation

- [`Containerfile`](../../Containerfile)
- [`docker-compose.yml`](../../docker-compose.yml)
- [`.dockerignore`](../../.dockerignore)
- [`Taskfile.yml`](../../Taskfile.yml) — `up`, `down`, `container:build`,
  `container:run`
- [`container-structure-test.yml`](../../container-structure-test.yml)

## See also

- [ADR 019](019-containerfile.md) — original Containerfile decision
- [ADR 053](053-migrations-as-pre-deploy-command.md) — migrations as
  pre-deploy command
- [ADR 055](055-uv-as-project-manager.md) — uv as project manager
