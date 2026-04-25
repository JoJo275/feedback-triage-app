# Experiments

<!-- TODO (template users): Delete the example files and add your own
     experiments. Remove this directory entirely if you don't need a
     scratch space. -->

A scratch space for exploratory code, prototypes, and one-off scripts.

## Purpose

This directory is for:

- **Prototyping** — Test ideas before adding them to `src/`
- **Learning** — Try out new libraries or patterns
- **Debugging** — Isolate and reproduce issues
- **One-off scripts** — Quick utilities that don't belong in the main codebase

## Guidelines

- Code here is **not production quality** — no tests, docs, or types required
- Files may be **deleted at any time** — don't rely on anything here
- **Never import from experiments/** in production code
- Prefix files with a date or topic for organization: `2026-02-05_api_test.py`

## Examples

| File                          | Description                |
| ----------------------------- | -------------------------- |
| `example_api_test.py`         | Testing an external API    |
| `example_data_exploration.py` | Quick data analysis script |

## Cleanup

Periodically review and delete old experiments. If something proves useful,
refactor it properly into `src/` with tests, type hints, and documentation.

## See Also

- [src/](../src/) — Production source code
- [scripts/](../scripts/) — Maintained utility scripts
- [docs/notes/](../docs/notes/) — Learning notes and references
