# ADR 053: Migrations as Railway Pre-Deploy Command

## Status

Accepted

## Context

Database migrations need to run on every deploy that introduces schema
changes. The three candidates on a platform like Railway:

1. **Run on app boot** — call `alembic upgrade head` from `main.py`
   before mounting routes.
2. **One-shot job before deploy** — Railway pre-deploy command, runs
   once per deploy, blocks the new container's start until success.
3. **Manual** — run migrations from a local checkout against prod.

## Decision

Configure Railway's **pre-deploy command** to run
`alembic upgrade head`. The new container only starts if the migration
succeeds. The app code itself never runs migrations.

The same image is used for the pre-deploy command and the running app.
`alembic.ini` and the `alembic/` directory are copied into the image at
`/app/` (Containerfile WORKDIR) so the command resolves the right
script paths and `target_metadata`.

## Alternatives Considered

### Run on app boot

**Rejected because:**

- Multiple replicas race on the same migration. With one replica it
  works, but the design assumes one replica.
- Failed migrations leave the container half-initialised and crashloop.
- Slow startup time hits the platform's healthcheck window.

### Manual `alembic upgrade head` from a local checkout

**Rejected because:** error-prone, divergent from the deployed image,
and no audit trail in deploy logs.

## Consequences

### Positive

- Migration failure blocks the deploy cleanly; old container keeps
  serving until the new one is healthy.
- One source of schema state per deploy, recorded in Railway logs.

### Negative

- Adds a coupling to Railway's pre-deploy feature. Migrating to another
  platform requires reconfiguring the equivalent hook.
