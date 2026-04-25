#!/usr/bin/env bash
# Test the docker compose stack: build, run, validate, and clean up.
#
# Usage:
#   bash scripts/test_docker_compose.sh
#   KEEP=1 bash scripts/test_docker_compose.sh    # skip cleanup
#   VERBOSE=1 bash scripts/test_docker_compose.sh # show build output
#
# TODO (template users): Update service names and test steps to match
#   your docker-compose.yml (e.g. add health check waits, DB tests).
set -euo pipefail

# Check docker is available before doing anything
if ! command -v docker &>/dev/null; then
    echo "ERROR: docker CLI not found on PATH"
    exit 1
fi
if ! docker info &>/dev/null; then
    echo "ERROR: Docker daemon not running or not accessible"
    echo "  Start Docker Desktop or the docker service first."
    exit 1
fi

cleanup() {
    if [ "${KEEP:-0}" != "1" ]; then
        echo "--- Cleaning up containers and images ---"
        docker compose down --rmi local --volumes 2>/dev/null || true
    fi
}
trap cleanup EXIT

echo "=== Docker Compose Test ==="

echo "--- Validating compose config ---"
docker compose config --quiet

echo "--- Building image via docker compose ---"
if [ "${VERBOSE:-0}" = "1" ]; then
    docker compose build
else
    docker compose build --quiet
fi

echo "--- Verifying entrypoint (--help) ---"
docker compose run --rm app --help

echo "--- Checking non-root user ---"
ID_OUTPUT=$(docker compose run --rm --entrypoint id app)
echo "  $ID_OUTPUT"
if echo "$ID_OUTPUT" | grep -qE 'uid=0([^0-9]|$)'; then
    echo "ERROR: Container is running as root (uid=0)"
    exit 1
fi
if ! echo "$ID_OUTPUT" | grep -qE 'uid=[0-9]+'; then
    echo "ERROR: Could not parse uid from id output"
    exit 1
fi

echo "=== Docker Compose Test PASSED ==="
