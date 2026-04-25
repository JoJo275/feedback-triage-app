# ADR 025: Container Strategy — Production, Development, and Orchestration

## Status

Accepted

## Context

Modern Python projects benefit from containerization for both development consistency
and production deployment. However, "containers" can mean different things:

1. **Production containers** — Minimal images that run your application
2. **Development containers** — Full environments for writing code
3. **Container orchestration** — Tools to manage multi-container setups

These serve different purposes and shouldn't be conflated. The project needed a clear
strategy for when and how to use each approach.

## Decision

We provide three container-related configurations, each serving a distinct purpose:

### 1. Containerfile (Production)

Located at the repository root, this builds a minimal OCI-compliant image containing
only the installed application — no dev tools, no source code, no tests.

**Use case:** Deploying to production, CI/CD pipelines, distribution.

```bash
docker build -t simple-python-boilerplate -f Containerfile .
docker run --rm simple-python-boilerplate
```

### 2. Dev Container (Development)

Located in `.devcontainer/`, this configures VS Code to run inside a container with
all development tools pre-installed: Python, Node.js, pre-commit hooks, extensions.

**Use case:** Consistent development environment, onboarding new contributors, Codespaces.

```
VS Code → "Reopen in Container" → Full IDE inside container
```

### 3. Docker Compose (Orchestration)

Located at `docker-compose.yml`, this provides convenience commands for building and
running the production container locally. It can also define multi-service setups
(app + database, etc.).

**Use case:** Local testing of production build, multi-container development.

```bash
docker compose up --build
```

## Alternatives Considered

### Single Dockerfile for everything

Use one Dockerfile with build arguments to switch between dev and production modes.

**Rejected because:** Over-complicates the Dockerfile, makes each mode harder to
understand, and dev containers have their own JSON format that integrates with
VS Code features.

### Skip Docker Compose

Just use `docker build` and `docker run` commands directly.

**Rejected because:** Compose provides a declarative, version-controlled way to
specify build/run options. It's also the foundation for multi-service setups if
the project grows.

### Use Docker-in-Docker for dev container

Run Docker inside the dev container for full container workflow testing.

**Rejected because:** Adds complexity and security considerations. Users who need
to test container builds can exit the dev container and run Docker on the host.

## Consequences

### Positive

- Clear separation of concerns — each file has one purpose
- Template users can delete what they don't need
- Zero-setup development via Codespaces or Dev Containers
- Production images stay minimal (~150MB vs ~1GB+ for dev)
- Docker Compose enables easy multi-service expansion

### Negative

- Three files to maintain instead of one
- Users must understand which tool serves which purpose
- Dev container requires Docker Desktop (or Podman) installed

### Mitigations

- Clear README files explain each component
- This ADR documents the rationale
- Files are optional — template users can remove any they don't use

## Implementation

- [Containerfile](../../Containerfile) — Production container build
- [.devcontainer/devcontainer.json](../../.devcontainer/devcontainer.json) — VS Code dev container config
- [.devcontainer/README.md](../../.devcontainer/README.md) — Dev container documentation
- [docker-compose.yml](../../docker-compose.yml) — Container orchestration

## References

- [ADR 019: Containerfile](019-containerfile.md) — Original production container decision
- [Dev Containers specification](https://containers.dev/)
- [Docker Compose documentation](https://docs.docker.com/compose/)
- [GitHub Codespaces](https://github.com/features/codespaces)
