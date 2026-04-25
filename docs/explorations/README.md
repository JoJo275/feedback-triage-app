# Explorations

Early-stage thinking about ideas, problems, and potential directions.

Explorations answer: **"Do we need this? What problem is it solving? What
options exist? What are the tradeoffs?"**

## When to Write an Exploration

Write an exploration when:

- A new idea or need surfaces that isn't obviously right or wrong
- You want to evaluate multiple options before committing
- The cost, risk, or scope is unclear and needs investigation
- You need to build consensus before designing a solution

Don't write an exploration for straightforward changes — jump straight to
an ADR or implementation plan instead.

## Lifecycle

```
idea/problem → explorations/    (this directory)
proposed design → blueprints/
decision locked in → adr/
build steps → implementation-plans/
```

## What Goes in an Exploration

- **Problem statement** — What's broken or missing?
- **Why this might matter** — Who benefits? What's the cost of inaction?
- **Alternatives** — At least two options, including "do nothing"
- **Risks** — What could go wrong?
- **Whether it's worth doing at all** — Honest assessment

## Format

Each exploration follows the structure in [template.md](template.md).
Copy the template to a new file with a descriptive name:

```
docs/explorations/NNN-short-description.md
```

Number sequentially (001, 002, ...) to maintain order.

## Statuses

| Status                    | Meaning                                   |
| :------------------------ | :---------------------------------------- |
| **Draft**                 | Still being written or researched          |
| **Under Discussion**      | Shared for feedback, no conclusion yet     |
| **Concluded — Proceed**   | Worth doing; move to blueprint or ADR      |
| **Concluded — Declined**  | Not worth doing; document why and archive  |

## Index

<!-- Add explorations here as they are created:

| #   | Title                              | Status                 |
| :-- | :--------------------------------- | :--------------------- |
| 001 | [Title](001-short-description.md)  | Draft                  |
-->

| #   | Title                                                                  | Status |
| :-- | :--------------------------------------------------------------------- | :----- |
| 001 | [Environment inspection web dashboard](001-env-inspect-web-dashboard.md) | Concluded — Proceed |
