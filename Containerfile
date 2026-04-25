# ──────────────────────────────────────────────────────────────
# Containerfile (OCI-compatible, works with Podman and Docker)
# ──────────────────────────────────────────────────────────────
# Builds a minimal container image for the application.
#
# Usage:
#   podman build -t simple-python-boilerplate -f Containerfile .
#   podman run --rm simple-python-boilerplate
#
# Or with Docker:
#   docker build -t simple-python-boilerplate -f Containerfile .
#   docker run --rm simple-python-boilerplate
#
# Multi-stage build:
#   Stage 1 (builder) – installs build tools + builds the wheel
#   Stage 2 (runtime) – copies only the installed package into
#                        a slim image with no build tooling
#
# Pinning the base image:
#   The base image is pinned to a specific digest for reproducible
#   builds. To update, run:
#     docker pull python:3.12-slim
#     docker inspect --format='{{index .RepoDigests 0}}' python:3.12-slim
#   Then replace the digest below.
# ──────────────────────────────────────────────────────────────

# Base image digest — pin for reproducibility (update via comment above)
ARG PYTHON_BASE=python:3.12-slim@sha256:41563b9752d16a220983617270a893a0ddd478717e1b9af7ca1df5c5fdb13c34

# ── Stage 1: Build ────────────────────────────────────────────
FROM ${PYTHON_BASE} AS builder

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Install build tool first (layer cached independently of source changes)
COPY pyproject.toml README.md LICENSE ./
RUN python -m pip install --no-cache-dir build

# Allow CI to inject the version when .git is unavailable inside the container.
# Usage: podman build --build-arg VERSION=$(git describe --tags) ...
ARG VERSION=""
ENV SETUPTOOLS_SCM_PRETEND_VERSION=${VERSION}

# Copy source and directories referenced by force-include in pyproject.toml
COPY src/ src/
COPY scripts/ scripts/
COPY tools/ tools/
COPY repo_doctor.d/ repo_doctor.d/
RUN python -m build --wheel --outdir /build/dist

# ── Stage 2: Runtime ──────────────────────────────────────────
FROM ${PYTHON_BASE} AS runtime

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# OCI image metadata
# See: https://github.com/opencontainers/image-spec/blob/main/annotations.md
# TODO (template users): Replace the source URL, title, and description below
#   with your own repository slug and project details.
LABEL org.opencontainers.image.title="simple-python-boilerplate" \
      org.opencontainers.image.description="A Python boilerplate project" \
      org.opencontainers.image.source="https://github.com/JoJo275/simple-python-boilerplate" \
      org.opencontainers.image.licenses="Apache-2.0"

# Don't run as root
RUN groupadd --gid 1000 app \
    && useradd --uid 1000 --gid app --create-home app

WORKDIR /app

# Install only the built wheel (no build tools in final image)
COPY --from=builder /build/dist/*.whl /tmp/
RUN python -m pip install --no-cache-dir /tmp/*.whl \
    && rm -rf /tmp/*.whl

USER app

# Basic health check — override in docker-compose or orchestrator as needed
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import simple_python_boilerplate" || exit 1

# Healthcheck — uncomment if this becomes an HTTP service:
# HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
#   CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]

# Default command — runs the CLI entry point
# TODO (template users): Replace "spb" with your package's actual CLI entry
#   point, or switch to CMD ["python", "-m", "your_package"] if you don't
#   define a console_scripts entry point.
ENTRYPOINT ["spb"]
