# v2.0 — Account registry

> Topical detail file. Entry point: [`../spec-v2.md`](../spec-v2.md).
> Primary companions: [`auth.md`](auth.md),
> [`multi-tenancy.md`](multi-tenancy.md),
> [`migration-from-v1.md`](migration-from-v1.md),
> [`testing-strategy.md`](testing-strategy.md).

This file is the single source of truth for login-capable admin/demo/example
accounts referenced by the v2.0 codebase and docs.

Scope rules:

- Includes only `users`-table identities (or identity patterns used by auth tests).
- Excludes non-login addresses like `no-reply@...` and `hello@...`.
- If an account value appears elsewhere and conflicts with this file, this file wins.

---

## Canonical account list

| Key | Environment | Role / intent | Identity | Credential source | Notes |
| --- | ----------- | ------------- | -------- | ----------------- | ----- |
| `bootstrap_admin` | prod / staging at first deploy | platform `admin` bootstrap user | Email comes from `ADMIN_BOOTSTRAP_EMAIL` | Password comes from `ADMIN_BOOTSTRAP_PASSWORD` | One-time bootstrap identity used in v1->v2 cut-over; rotate/reset immediately after first sign-in. |
| `legacy_synthetic_admin` | migration + local/test fixtures | synthetic `admin` owner for legacy workspace | `legacy@signalnest.local` | Password hash sentinel: `!disabled-legacy-v1-admin!` | Not a valid Argon2 hash; login intentionally disabled. Owns `signalnest-legacy` during migration compatibility flows. |
| `demo_owner_seed` | local dev convenience seed | `team_member` user + workspace `owner` membership | `demo-owner@signalnest.app` | `ChangeMe-Demo!23` (Task task `seed:demo`) | Created only when `seed_workspace.py --create-if-missing` is used by `task seed:demo`. Local/dev only. |
| `shared_demo_user` | product demo surface | platform `demo` (read-only workspace access) | release-seeded shared login (value not hard-coded in repo) | rotated per release seed process | Demo account cannot write; all write routes return `code=demo_read_only`. |
| `test_auth_pattern` | automated tests | disposable auth test users | `*@example.com` and `*@example.test` | test password baseline: `correct horse battery staple` | Pattern-level entry; tests generate many concrete addresses under these domains. |

---

## Source map

- Bootstrap env vars and cut-over semantics:
  [`rollout.md`](rollout.md), [`migration-from-v1.md`](migration-from-v1.md)
- Synthetic legacy admin insertion and sentinel hash:
  [`../../../../alembic/versions/0002_v2_a_auth_tenancy_email_log.py`](../../../../alembic/versions/0002_v2_a_auth_tenancy_email_log.py),
  [`../../../../tests/conftest.py`](../../../../tests/conftest.py),
  [`../../../../src/feedback_triage/auth/hashing.py`](../../../../src/feedback_triage/auth/hashing.py)
- Local demo-owner seed account:
  [`../../../../Taskfile.yml`](../../../../Taskfile.yml),
  [`../../../../scripts/seed_workspace.py`](../../../../scripts/seed_workspace.py)
- Test password and identity-domain conventions:
  [`testing-strategy.md`](testing-strategy.md)

---

## Change policy

When any account identity or credential source changes:

1. Update this file first.
2. Update the implementing source (`Taskfile.yml`, migration, script, or tests).
3. In the PR description, call out the account change explicitly.
