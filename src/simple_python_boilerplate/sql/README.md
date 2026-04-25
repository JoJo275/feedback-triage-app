# SQL Queries Module

<!-- TODO (template users): Replace the example structure below with your
     actual query organization. Delete placeholder .sql files and add your
     own. If you don't embed SQL in the package, delete this directory. -->

Application SQL queries embedded in the package.

## When to Use

Use this directory for queries that are:

- Tightly coupled to application code
- Loaded at runtime via `importlib.resources`
- Shipped with the installed package

Use `db/queries/` for:

- Standalone queries run manually or by scripts
- Queries shared across multiple applications

## Usage

```python
from importlib.resources import files

# Load a query file
query = files("simple_python_boilerplate.sql").joinpath("get_user.sql").read_text()
```

## Structure

```text
sql/
├── users/
│   ├── get_by_id.sql
│   └── search.sql
└── reports/
    └── daily_summary.sql
```

## See Also

- [db/queries/](../../../db/queries/) — Standalone reusable queries
- [db/schema.sql](../../../db/schema.sql) — Canonical database schema
- [ADR 027](../../../docs/adr/027-database-strategy.md) — Raw SQL database strategy
