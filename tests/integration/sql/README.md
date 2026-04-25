# SQL Integration Tests

<!-- TODO (template users): Replace these examples with your actual test
     database setup. Delete placeholder files after adding real fixtures. -->

SQL files for database integration testing.

## Purpose

This directory holds SQL fixtures that support integration tests:

- **Setup scripts** — Create test-specific tables and data
- **Teardown scripts** — Clean up after tests
- **Expected results** — Reference data for assertion comparisons
- **Schema validation** — Scripts that verify schema correctness

## Naming Conventions

| Pattern                  | Example                  | Purpose                            |
| ------------------------ | ------------------------ | ---------------------------------- |
| `setup_<feature>.sql`    | `setup_users.sql`        | Create tables and insert test data |
| `teardown_<feature>.sql` | `teardown_users.sql`     | Drop tables or delete test data    |
| `expected_<test>.sql`    | `expected_user_list.sql` | Reference output for comparisons   |
| `validate_<check>.sql`   | `validate_schema.sql`    | Schema integrity assertions        |

## Usage with pytest

```python
import sqlite3
from pathlib import Path

FIXTURES = Path(__file__).parent / "sql"

def setup_test_db(tmp_path: Path) -> sqlite3.Connection:
    """Create an in-memory test database with fixtures."""
    conn = sqlite3.connect(":memory:")
    conn.executescript((FIXTURES / "setup_users.sql").read_text())
    return conn
```

## See Also

- [db/schema.sql](../../../db/schema.sql) — Canonical schema
- [db/seeds/](../../../db/seeds/) — Seed data (dev/test environments)
- [tests/conftest.py](../../conftest.py) — Shared pytest fixtures
- [ADR 029](../../../docs/adr/029-testing-strategy.md) — Testing strategy
