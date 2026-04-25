#!/usr/bin/env bash
# Test the Containerfile: build image, run basic checks, and clean up.
#
# Usage:
#   bash scripts/test_containerfile.sh
#   KEEP_IMAGE=1 bash scripts/test_containerfile.sh   # skip image removal
#   VERBOSE=1 bash scripts/test_containerfile.sh      # show build output
#
# TODO (template users): Update IMAGE and MAX_SIZE_MB to match your project.
set -euo pipefail

IMAGE="simple-python-boilerplate:test"
MAX_SIZE_MB=200

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
    if [ "${KEEP_IMAGE:-0}" != "1" ]; then
        echo "--- Removing test image ---"
        docker rmi "$IMAGE" 2>/dev/null || true
    fi
}
trap cleanup EXIT

echo "=== Containerfile Test ==="

echo "--- Building image from Containerfile ---"
if [ "${VERBOSE:-0}" = "1" ]; then
    docker build -t "$IMAGE" -f Containerfile .
else
    docker build -t "$IMAGE" -f Containerfile . --quiet
fi

echo "--- Verifying entrypoint (--help) ---"
docker run --rm "$IMAGE" --help

echo "--- Checking non-root user ---"
ID_OUTPUT=$(docker run --rm --entrypoint id "$IMAGE")
echo "  $ID_OUTPUT"
if echo "$ID_OUTPUT" | grep -qE 'uid=0([^0-9]|$)'; then
    echo "ERROR: Container is running as root (uid=0)"
    exit 1
fi
if ! echo "$ID_OUTPUT" | grep -qE 'uid=[0-9]+'; then
    echo "ERROR: Could not parse uid from id output"
    exit 1
fi

echo "--- Checking Python is available ---"
docker run --rm --entrypoint python "$IMAGE" --version

echo "--- Checking image size ---"
SIZE_BYTES=$(docker image inspect "$IMAGE" --format '{{.Size}}')
SIZE_MB=$((SIZE_BYTES / 1024 / 1024))
echo "  Image size: ${SIZE_MB} MB"
if [ "$SIZE_MB" -gt "$MAX_SIZE_MB" ]; then
    echo "  WARNING: Image exceeds ${MAX_SIZE_MB} MB threshold"
fi

echo "=== Containerfile Test PASSED ==="
