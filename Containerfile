# syntax=docker/dockerfile:1.7
# ──────────────────────────────────────────────────────────────
# Containerfile — Feedback Triage App
# OCI-compatible (Docker, Podman, BuildKit).
# ──────────────────────────────────────────────────────────────
# Multi-stage:
#   Stage 1 (builder-frontend) — runs scripts/build_css.py, which
#                        downloads the Tailwind Standalone CLI binary
#                        and emits the hashed app.<hash>.css plus
#                        manifest.json into src/feedback_triage/static/css/.
#   Stage 2 (builder)  — uses `uv build` (which calls hatchling) to produce
#                        the project wheel. Source tree includes the CSS
#                        artifacts copied in from stage 1 so the wheel
#                        ships them.
#   Stage 3 (runtime)  — slim Python image. Installs only the wheel via
#                        `uv pip install --system --no-cache`, then drops
#                        privileges. No source tree, no build tools, no
#                        .git in the final image. The Tailwind binary is
#                        not in the runtime image.
#
# Refresh base/uv digests with Dependabot's `docker` ecosystem block.
# ──────────────────────────────────────────────────────────────

# Pinned base image. Refresh via:
#   docker pull python:3.13-slim
#   docker inspect --format='{{index .RepoDigests 0}}' python:3.13-slim
# Refreshed 2026-04-28.
ARG PYTHON_BASE=python:3.13-slim@sha256:a0779d7c12fc20be6ec6b4ddc901a4fd7657b8a6bc9def9d3fde89ed5efe0a3d

# Pinned uv binary image. Refresh via:
#   docker pull ghcr.io/astral-sh/uv:latest
#   docker inspect --format='{{index .RepoDigests 0}}' ghcr.io/astral-sh/uv:latest
ARG UV_IMAGE=ghcr.io/astral-sh/uv@sha256:3b7b60a81d3c57ef471703e5c83fd4aaa33abcd403596fb22ab07db85ae91347

# ── Stage 1: Frontend (Tailwind CSS) ──────────────────────────
FROM ${PYTHON_BASE} AS builder-frontend

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Download CA certs are already in slim; ca-certificates is enough for
# the GitHub release fetch performed by scripts/build_css.py.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build-fe

# scripts/build_css.py walks up looking for pyproject.toml to anchor
# the repo root; copy it for that purpose only (not for installing).
COPY pyproject.toml ./
COPY tailwind.config.cjs ./
COPY scripts/_imports.py scripts/build_css.py scripts/

# Tailwind's content globs scan templates, the whole static tree
# (HTML + JS), and routes/*.py for class names. Copy all four so the
# container build sees the same source surface as a local build.
COPY src/feedback_triage/static/ src/feedback_triage/static/
COPY src/feedback_triage/templates/ src/feedback_triage/templates/
COPY src/feedback_triage/routes/ src/feedback_triage/routes/

# Build CSS. The script downloads the Tailwind binary into .tools/ and
# writes app.<hash>.css + manifest.json into the css/ source dir.
RUN python scripts/build_css.py

# ── Stage 2: Build wheel ──────────────────────────────────────
FROM ${PYTHON_BASE} AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Bring in uv (the binary, no Python deps).
COPY --from=ghcr.io/astral-sh/uv@sha256:3b7b60a81d3c57ef471703e5c83fd4aaa33abcd403596fb22ab07db85ae91347 /uv /usr/local/bin/uv

WORKDIR /build

# Allow CI to inject the version when .git is unavailable inside the build.
# Usage: docker build --build-arg VERSION=$(git describe --tags --always) ...
ARG VERSION=""
ENV SETUPTOOLS_SCM_PRETEND_VERSION=${VERSION} \
    HATCH_BUILD_HOOK_VCS_FALLBACK_VERSION=${VERSION}

# Copy only what hatchling needs to build the wheel. Source last so deps
# layer-cache independently.
COPY pyproject.toml README.md LICENSE ./
COPY src/ src/

# Overlay the hashed CSS + manifest produced by builder-frontend.
COPY --from=builder-frontend \
    /build-fe/src/feedback_triage/static/css/ \
    src/feedback_triage/static/css/

RUN uv build --wheel --out-dir /build/dist

# ── Stage 2: Runtime ──────────────────────────────────────────
FROM ${PYTHON_BASE} AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

LABEL org.opencontainers.image.title="feedback-triage-app" \
      org.opencontainers.image.description="FastAPI + PostgreSQL feedback triage service" \
      org.opencontainers.image.source="https://github.com/JoJo275/feedback-triage-app" \
      org.opencontainers.image.licenses="Apache-2.0"

# uv used only for the wheel install step. Drop after install if you want
# an even leaner runtime; left in for ad-hoc `uv pip` debugging on Railway.
COPY --from=ghcr.io/astral-sh/uv@sha256:3b7b60a81d3c57ef471703e5c83fd4aaa33abcd403596fb22ab07db85ae91347 /uv /usr/local/bin/uv

# Non-root user for the app process.
RUN groupadd --gid 1000 app \
    && useradd --uid 1000 --gid app --create-home app

WORKDIR /app

# Install the built wheel + its runtime deps from PyPI into the system
# Python (no venv inside the container, per ADR 055 / spec).
COPY --from=builder /build/dist/*.whl /tmp/
RUN uv pip install --system --no-cache /tmp/*.whl \
    && rm -rf /tmp/*.whl

# Copy alembic config + migrations so the Railway pre-deploy command can
# run `alembic upgrade head`. They live at /app/ to match WORKDIR.
COPY alembic.ini ./
COPY alembic/ alembic/

USER app

EXPOSE 8000

# Healthcheck hits /health (liveness only). /ready bounces on DB blips
# and would cause container restart loops if used here.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; \
import os; \
sys.exit(0) if urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8000\")}/health', timeout=4).status == 200 else sys.exit(1)" \
    || exit 1

# Default command — Railway overrides with $PORT.
CMD ["sh", "-c", "uvicorn feedback_triage.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
