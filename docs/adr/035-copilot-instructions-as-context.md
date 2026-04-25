# ADR 035: Copilot Instructions as Developer Context

## Status

Accepted

## Context

AI coding assistants (GitHub Copilot, Claude, Cursor) work within the
project but often lack critical context: what tools are used, what
conventions to follow, what patterns to avoid, and how the project is
organized. Without this context, AI suggestions conflicted with project
conventions — suggesting Poetry instead of Hatch, creating flat-layout
imports, or missing Conventional Commits format.

GitHub Copilot supports a `.github/copilot-instructions.md` file that is
automatically included as context in every Copilot interaction within the
repository. This is an opportunity to encode project conventions in a way
that both humans and AI assistants can consume.

## Decision

Maintain a comprehensive `.github/copilot-instructions.md` file that serves
as an always-available project briefing for AI assistants.

**The file includes:**

- Project overview — what the project is and how it's structured
- Build and environment setup — Hatch, dependencies, environments
- Pre-commit hook inventory — stages, counts, key hooks
- GitHub Actions workflow summary — categories, key conventions
- Task runner shortcuts — common `task` commands
- Working style guidelines — TODOs, file sync rules, verification steps
- Review priorities — what to catch, ranked by importance
- Conventions — Python, Git, CI/CD patterns
- Common issues — known pitfalls and their fixes
- Known limitations — tech debt that doesn't need rediscovery

**Maintenance rules:**

- Update the file as part of any change that affects how an AI assistant
  should understand the codebase (new tool, new convention, new pattern)
- When numbers in this file conflict with canonical docs (`docs/design/`,
  `docs/adr/`), those docs win — this file is a quick-reference summary
- Template users get TODO comments explaining what to customize

## Alternatives Considered

### No AI context file

Let AI assistants figure out the project from source.

**Rejected because:** AI assistants re-discover project structure from
scratch each session. Without guidance, suggestions drift from conventions.
The cost of maintaining the file is low compared to the time saved
correcting bad suggestions.

### Multiple instruction files (per-directory)

VS Code supports per-directory `.github/copilot-instructions.md` and
`.instructions.md` files.

**Rejected because:** A single comprehensive file is easier to maintain
and keeps all context in one place. Per-directory files would require
syncing common information across multiple locations.

### Encode context only in code comments

Use inline comments and docstrings instead of a dedicated file.

**Rejected because:** Comments are scattered and AI assistants don't
always read every file. A dedicated instructions file is guaranteed to be
loaded as context by Copilot on every interaction.

## Consequences

### Positive

- AI suggestions align with project conventions from the first interaction
- New contributors using Copilot get accurate, context-aware assistance
- Acts as a secondary "living README" that stays current alongside docs
- Reduces time spent correcting AI-generated code that doesn't fit the
  project

### Negative

- Maintenance burden — another file to keep in sync when things change
- Risk of staleness — if not updated, AI gets wrong context (worse than
  no context)
- GitHub Copilot-specific — other AI tools may not read this file
  (though editors like Cursor support similar `.cursorrules` files)

### Mitigations

- Working style section in the file itself says to update it as part of
  any convention change
- Periodic review during doc audits catches drift
- File is human-readable too — useful as a quick project overview
  even without AI assistants

## Implementation

- [`.github/copilot-instructions.md`](../../.github/copilot-instructions.md) —
  The instructions file itself
- This file is kept in sync with the canonical project docs. When conflicts
  arise, `docs/design/` and `docs/adr/` are authoritative.

## References

- [GitHub Copilot custom instructions](https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot)
- [Cursor Rules](https://cursor.sh/docs/context/rules) — Similar concept
  for Cursor editor
