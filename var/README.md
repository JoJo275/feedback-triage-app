# var/

<!-- TODO (template users): Update this list to match your project's runtime
     artifacts. Add entries for any new generated files (logs, caches, etc.). -->

Runtime data directory for files generated at runtime that should not be
committed to version control.

## Contents

| File / Pattern          | Purpose                               | Tracked |
| ----------------------- | ------------------------------------- | ------- |
| `app.example.sqlite3`   | Example database for template users   | Yes     |
| `app.sqlite3`           | Local development database            | No      |
| `*.log`                 | Application log files                 | No      |
| `*.cache`               | Cache files                           | No      |

## Setup

```bash
# Copy the example database for local development
cp var/app.example.sqlite3 var/app.sqlite3

# Or create a fresh database from the schema
sqlite3 var/app.sqlite3 < db/schema.sql

# Apply seed data
sqlite3 var/app.sqlite3 < db/seeds/001_example_seed.sql
```

## What Gets Gitignored

Everything in `var/` is gitignored **except** `app.example.sqlite3` and
this `README.md`. This prevents accidental commits of local database state,
logs, or cached data.

> **Security:** Never store credentials, API keys, or sensitive data in
> `var/`. Use environment variables or a secrets manager instead.

## See Also

- [db/](../db/) — Schema, migrations, seeds, and queries
- [db/schema.sql](../db/schema.sql) — Canonical database schema
- [.gitignore](../.gitignore) — Ignore rules for this directory
