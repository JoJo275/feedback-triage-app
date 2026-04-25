# ADR 019: Use Containerfile for OCI-compatible container builds

## Status

Accepted

## Context

This project needs a reproducible way to build, test, and deploy the application in isolated environments. Container images solve the "works on my machine" problem and are the standard for modern deployment pipelines.

### Containerfile vs Dockerfile

The file is named `Containerfile` (not `Dockerfile`) for OCI compatibility:

| Aspect             | Dockerfile                    | Containerfile                    |
| ------------------ | ----------------------------- | -------------------------------- |
| **Standard**       | Docker-specific convention    | OCI-standard name                |
| **Docker support** | Native                        | Supported via `-f Containerfile` |
| **Podman support** | Supported via `-f Dockerfile` | Native                           |
| **Syntax**         | Identical                     | Identical                        |

The syntax is the same — only the filename differs. Using `Containerfile` signals that the project is not locked to Docker and works with any OCI-compliant runtime (Podman, Docker, Buildah, etc.).

### Build strategy

The `Containerfile` uses a **multi-stage build**:

| Stage       | Purpose             | Contents                              |
| ----------- | ------------------- | ------------------------------------- |
| **builder** | Build the wheel     | Python, pip, build tools, source code |
| **runtime** | Run the application | Python (slim), installed wheel only   |

This produces a minimal final image with no build tooling, source code, or development dependencies.

### Security considerations

- **Non-root user** — The runtime stage creates and switches to an unprivileged `app` user
- **No build tools in final image** — Reduces attack surface
- **`--no-cache-dir`** — Prevents pip from storing downloaded packages in the image
- **Pinned base image** — Uses `python:3.12-slim` for a specific, reproducible base

## Alternatives Considered

| Option                          | Pros                                              | Cons                                           |
| ------------------------------- | ------------------------------------------------- | ---------------------------------------------- |
| **No container**                | Simpler, fewer files                              | No deployment story, environment inconsistency |
| **Docker Compose**              | Multi-service orchestration                       | Overkill for a single-service app              |
| **Nix / Guix**                  | Fully reproducible builds                         | Very steep learning curve, niche adoption      |
| **Containerfile (multi-stage)** | Minimal image, OCI-standard, wide tooling support | Requires container runtime for local use       |

## Decision

Maintain a `Containerfile` at the project root using a multi-stage build:

1. **Stage 1 (builder)** — Installs build tools, copies source, builds a wheel with `python -m build`
2. **Stage 2 (runtime)** — Copies only the built wheel into a slim base image, installs it, runs as non-root

Usage:

```bash
# Podman
podman build -t simple-python-boilerplate -f Containerfile .
podman run --rm simple-python-boilerplate

# Docker
docker build -t simple-python-boilerplate -f Containerfile .
docker run --rm simple-python-boilerplate
```

## Consequences

### Positive

- Reproducible builds — same image regardless of host OS or Python installation
- Minimal attack surface — no build tools, source code, or dev dependencies in the final image
- OCI-compatible — works with Docker, Podman, Buildah, and any OCI runtime
- Layer caching — dependency installation is cached separately from source code changes
- Non-root by default — follows container security best practices

### Negative

- Requires a container runtime (Docker or Podman) for local use
- Image must be rebuilt when dependencies or code change
- Adds a file to maintain as the project evolves (Python version, base image updates)

### Neutral

- The `Containerfile` builds the same wheel that `hatch build` produces — no divergence in packaging
- Container builds are not yet integrated into CI; this can be added later as a build/publish workflow
