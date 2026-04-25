# Implementation Plans

Execution details for approved designs.

Implementation plans answer: **"What files change, in what order, with
what milestones?"**

## When to Write an Implementation Plan

Write an implementation plan when:

- A blueprint has been accepted and an ADR is locked in
- The work spans multiple files, phases, or sessions
- Sequencing matters (migrations, breaking changes, dependency order)
- You need a checklist to track progress and verify completeness

Skip for small changes that fit in a single commit.

## Lifecycle

```
idea/problem → explorations/
proposed design → blueprints/
decision locked in → adr/
build steps → implementation-plans/    (this directory)
```

## What Goes in an Implementation Plan

- **Step-by-step task order** — Phased, with file-level detail
- **Migrations / refactors** — Before/after state and migration steps
- **Sequencing** — What depends on what
- **Testing checklist** — How to verify each phase
- **Rollout notes** — Deployment, feature flags, rollback plan

## Format

Each plan follows the structure in [template.md](template.md).
Copy the template to a new file with a descriptive name:

```
docs/implementation-plans/NNN-short-description.md
```

Number sequentially (001, 002, ...) to maintain order.

## Statuses

| Status        | Meaning                                |
| :------------ | :------------------------------------- |
| **Draft**     | Plan is being written                   |
| **In Progress** | Work is underway                     |
| **Completed** | All tasks done, verified                |
| **Abandoned** | Plan dropped; document why              |

## Index

<!-- Add plans here as they are created:

| #   | Title                             | Status |
| :-- | :-------------------------------- | :----- |
| 001 | [Title](001-short-description.md) | Draft  |
-->

| #   | Title                                                                    | Status |
| :-- | :----------------------------------------------------------------------- | :----- |
| 001 | [Environment inspection web dashboard](001-env-inspect-web-dashboard.md) | Draft  |
