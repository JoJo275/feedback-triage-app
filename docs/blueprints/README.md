# Blueprints

Proposed design shapes for ideas that have passed the exploration stage.

Blueprints answer: **"Assuming we do this, what should it look like
structurally?"**

## When to Write a Blueprint

Write a blueprint when:

- An exploration has concluded with "proceed"
- You need to define the structural shape before writing code
- The design involves multiple components, modules, or config changes
- Reviewers need a technical picture before approving the work

Skip blueprints for small, well-understood changes — go straight to an ADR
or implementation plan.

## Lifecycle

```
idea/problem → explorations/
proposed design → blueprints/     (this directory)
decision locked in → adr/
build steps → implementation-plans/
```

## What Goes in a Blueprint

- **Proposed architecture** — High-level technical design
- **Repo layout** — Where new files live, what changes
- **Components / modules** — What pieces exist and their responsibilities
- **Tooling impact** — New deps, config changes, CI impact
- **Workflow / UX** — How developers interact with it
- **Open design questions** — Unresolved decisions

## Format

Each blueprint follows the structure in [template.md](template.md).
Copy the template to a new file with a descriptive name:

```
docs/blueprints/NNN-short-description.md
```

Number sequentially (001, 002, ...) to maintain order.

## Statuses

| Status           | Meaning                                     |
| :--------------- | :------------------------------------------ |
| **Draft**        | Still being designed                         |
| **Under Review** | Shared for feedback                          |
| **Accepted**     | Design approved; move to ADR + impl plan     |
| **Superseded**   | Replaced by a newer blueprint                |

## Index

<!-- Add blueprints here as they are created:

| #   | Title                             | Status |
| :-- | :-------------------------------- | :----- |
| 001 | [Title](001-short-description.md) | Draft  |
-->

| #   | Title                                                                        | Status   |
| :-- | :--------------------------------------------------------------------------- | :------- |
| 001 | [Environment inspection web dashboard](001-env-inspect-web-dashboard.md)     | Accepted |
