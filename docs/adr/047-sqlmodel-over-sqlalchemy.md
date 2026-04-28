# ADR 047: SQLModel over Plain SQLAlchemy

## Status

Accepted

## Context

The project needs an ORM and request/response schemas. The two natural
options:

- **SQLAlchemy 2.x + Pydantic** — two parallel class hierarchies, manual
  mapping between them.
- **SQLModel** — by the FastAPI author; one class can serve as both the
  table model and a base for request/response schemas.

For a single-table CRUD app the duplication of two parallel hierarchies
buys little.

## Decision

Use SQLModel for the `FeedbackItem` table model. Schemas
(`FeedbackCreate`, `FeedbackUpdate`, `FeedbackResponse`,
`FeedbackListEnvelope`) remain **separate Pydantic models** rather than
being derived from the SQLModel via `table=False` subclasses, because:

- The API contract should be free to drift from the DB shape (e.g.
  `password` columns, internal flags) without coupling.
- Explicit schemas make the OpenAPI surface easier to read.

SQLModel sits on top of SQLAlchemy 2.x; if the project ever outgrows
SQLModel, switching to plain SQLAlchemy is a mechanical migration.

## Alternatives Considered

### Plain SQLAlchemy 2.x + Pydantic

**Rejected because:** for a single-table app, the boilerplate of mirrored
classes is friction without benefit at this scale.

### Tortoise / Piccolo / SQLAlchemy Core

**Rejected because:** SQLAlchemy is the ecosystem default; SQLModel
consumes that ecosystem. Niche ORMs add a learning surface for no win.

## Consequences

### Positive

- One typed class per table.
- Direct interop with Pydantic v2.
- The escape hatch is short: SQLModel rows are SQLAlchemy ORM instances.

### Negative

- SQLModel's release cadence is slower than SQLAlchemy's. Pin a known-
  good floor and bump deliberately.
