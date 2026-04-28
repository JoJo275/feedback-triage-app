# ADR 052: API Versioning Under `/api/v1/`

## Status

Accepted

## Context

The first response shape change after ship will either be a versioned
upgrade or a breaking change to existing clients. Adding `/api/v1`
costs five characters now and makes the second case impossible.

Some routes — health probes, static HTML pages — are not part of the
"API contract" in the same sense, and platforms expect probes at fixed
paths.

## Decision

- All JSON routes are mounted under `/api/v1/` (e.g.
  `/api/v1/feedback`).
- HTML page routes (`/`, `/new`, `/feedback/{id}`) and probe routes
  (`/health`, `/ready`) stay **unversioned**. HTML is UI surface, not
  API contract; probes are platform contract.
- Swagger UI at `/api/v1/docs`, OpenAPI JSON at `/api/v1/openapi.json`.
- `tags=["feedback"]`, `tags=["health"]` group routes in the rendered
  docs.

A v2 surface is introduced by mounting a new sub-router at `/api/v2/`,
not by editing v1 in place.

## Alternatives Considered

### Header-based versioning (`Accept: application/vnd.feedback.v2+json`)

**Rejected because:** harder to test in a browser, harder to read in
logs, and `/api/v1/docs` is a more useful Swagger surface for a portfolio
project.

### No versioning in v1.0

**Rejected because:** the migration to versioned URLs after ship is
strictly more work than versioning from day one.

## Consequences

### Positive

- The first breaking change is a v2 mount, not a contract change.
- Platforms find probes at `/health`, `/ready` without extra config.

### Negative

- Five extra characters per route. Acceptable.
