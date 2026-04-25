# Database Design

<!-- TODO (template users): Replace this page with your actual database design
     decisions — schema, engine choice, access patterns, and constraints. The
     content below is placeholder scaffolding from the template. -->

## Overview

<!-- TODO (template users): Describe the purpose of your database, what data
     it stores, and how it fits into the broader architecture. -->

This project uses an embedded SQLite database for local development.
The canonical schema lives in [db/schema.sql](../../db/schema.sql);
incremental changes are tracked in [db/migrations/](../../db/migrations/).

## Database Engine

| Aspect       | Value                                               |
| ------------ | --------------------------------------------------- |
| **Engine**   | SQLite (development) / PostgreSQL (production)      |
| **Location** | `var/app.sqlite3`                                   |
| **Driver**   | Python stdlib `sqlite3` (no third-party dependency) |

<!-- TODO (template users): Update the engine, location, and driver to match
     your actual database choice. If you only use SQLite, remove the
     PostgreSQL reference. -->

## Schema Diagram

<!-- TODO (template users): Replace with your actual ER diagram.
     Consider using a Mermaid erDiagram block for maintainability. -->

```
┌─────────────┐       ┌─────────────┐
│   users     │       │   posts     │
├─────────────┤       ├─────────────┤
│ id (PK)     │──┐    │ id (PK)     │
│ name        │  │    │ user_id (FK)│──┐
│ email       │  └───>│ title       │  │
│ created_at  │       │ content     │  │
└─────────────┘       │ created_at  │  │
                      └─────────────┘  │
                                       │
                      ┌─────────────┐  │
                      │  comments   │  │
                      ├─────────────┤  │
                      │ id (PK)     │  │
                      │ post_id (FK)│<─┘
                      │ body        │
                      └─────────────┘
```

## Tables

### users

<!-- TODO (template users): Replace with your actual table definitions. -->

| Column       | Type      | Constraints       | Description        |
| ------------ | --------- | ----------------- | ------------------ |
| `id`         | INTEGER   | PK, AUTOINCREMENT | Unique identifier  |
| `name`       | TEXT      | NOT NULL          | Display name       |
| `email`      | TEXT      | UNIQUE, NOT NULL  | Email address      |
| `created_at` | TIMESTAMP | DEFAULT NOW       | Creation timestamp |

### posts

<!-- TODO (template users): Replace with your actual table definitions. -->

| Column       | Type      | Constraints             | Description        |
| ------------ | --------- | ----------------------- | ------------------ |
| `id`         | INTEGER   | PK, AUTOINCREMENT       | Unique identifier  |
| `user_id`    | INTEGER   | FK → users.id, NOT NULL | Author reference   |
| `title`      | TEXT      | NOT NULL                | Post title         |
| `content`    | TEXT      | NOT NULL                | Post body          |
| `created_at` | TIMESTAMP | DEFAULT NOW             | Creation timestamp |

### comments

<!-- TODO (template users): Replace with your actual table definitions. -->

| Column    | Type    | Constraints             | Description       |
| --------- | ------- | ----------------------- | ----------------- |
| `id`      | INTEGER | PK, AUTOINCREMENT       | Unique identifier |
| `post_id` | INTEGER | FK → posts.id, NOT NULL | Parent post       |
| `body`    | TEXT    | NOT NULL                | Comment text      |

## Indexes

<!-- TODO (template users): Document indexes used by your application. -->

| Index             | Table | Columns | Purpose               |
| ----------------- | ----- | ------- | --------------------- |
| `idx_users_email` | users | email   | Fast email lookups    |
| `idx_posts_user`  | posts | user_id | Posts-by-user queries |

## Migrations Strategy

- Schema changes are tracked in `db/migrations/`
- Use sequential prefixes (`001_`, `002_`) for solo/small teams
- Use timestamps (`YYYYMMDDHHMMSS_`) for larger teams
- See [db/migrations/README.md](../../db/migrations/README.md) for conventions

<!-- TODO (template users): If you adopt a migration tool (Alembic, yoyo, etc.),
     document the workflow here and update the Taskfile db:* tasks. -->

## Related Files

| Path                                   | Purpose             |
| -------------------------------------- | ------------------- |
| [db/schema.sql](../../db/schema.sql)   | Canonical schema    |
| [db/migrations/](../../db/migrations/) | Migration files     |
| [db/seeds/](../../db/seeds/)           | Seed / fixture data |
| [db/queries/](../../db/queries/)       | Reusable queries    |
| [Architecture](architecture.md)        | System overview     |
