# ADR 034: Documentation Organization Strategy

## Status

Accepted

## Context

As the project grew to 80+ documentation files, the flat `docs/` directory
became unwieldy. Files for different audiences (new users, daily
contributors, reference lookups, internal notes) were mixed together.
Navigation in MkDocs became cluttered and it was hard to know where a new
file should go.

We needed a directory structure that:

- Separates docs by audience and purpose
- Scales as the project adds more documentation
- Maps cleanly to MkDocs navigation (`nav:` in `mkdocs.yml`)
- Makes it obvious where new files belong

## Decision

Organize `docs/` into purpose-based subdirectories using the
[Diátaxis](https://diataxis.fr/) framework as a guide:

```text
docs/
├── guide/              # How-to guides — task-oriented walkthroughs
│   ├── getting-started.md
│   └── troubleshooting.md
├── development/        # Developer workflow docs — daily contributor reference
│   ├── dev-setup.md
│   ├── development.md
│   ├── developer-commands.md
│   ├── pull-requests.md
│   └── command-workflows.md
├── design/             # Architecture and design docs — system internals
│   ├── architecture.md
│   ├── ci-cd-design.md
│   ├── database.md
│   └── tool-decisions.md
├── reference/          # API and technical reference — lookup-oriented
│   ├── index.md
│   └── api.md
├── adr/                # Architecture Decision Records
├── notes/              # Internal notes, learning, resources (not shipped)
│   ├── learning.md
│   ├── resources.md
│   ├── tool-comparison.md
│   ├── todo.md
│   └── archive.md
├── templates/          # Reusable templates for issues, PRs, security policies
└── (top-level files)   # Cross-cutting docs: index, workflows, tooling, etc.
```

**Key principles:**

- **`guide/`** — "How do I…?" content aimed at users and new contributors
- **`development/`** — Daily workflow reference for active contributors
- **`design/`** — System architecture docs for understanding why things
  are the way they are
- **`reference/`** — Auto-generated and lookup-oriented technical docs
- **`notes/`** — Informal, internal-only notes that may not ship to
  production docs site. Learning journals, bookmarks, and working notes
- **`adr/`** — Decision records (existing convention, preserved)
- **`templates/`** — Boilerplate files for issues, PRs, and policies
- **Top-level files** — Topics that span multiple categories (index,
  workflows, repo layout, tooling, releasing)

## Alternatives Considered

### Flat structure (everything in `docs/`)

All markdown files directly under `docs/`.

**Rejected because:** Doesn't scale past ~20 files. Finding related files
requires scanning the entire directory. MkDocs nav becomes a flat list.

### Audience-based structure (`docs/user/`, `docs/maintainer/`, `docs/admin/`)

Organize by who reads the doc.

**Rejected because:** Many docs are read by multiple audiences. A
troubleshooting guide is useful for users AND maintainers. Purpose-based
(what kind of content) has clearer boundaries than audience-based (who
reads it).

### Diátaxis strict (tutorials, how-to, reference, explanation)

Pure Diátaxis with exactly four directories.

**Rejected because:** Too rigid for this project. We need `adr/`, `notes/`,
`templates/`, and `development/` as distinct categories. Diátaxis is a
useful mental model but forcing everything into four buckets creates
awkward placements.

## Consequences

### Positive

- Clear mental model for where files belong — new docs have an obvious home
- MkDocs navigation maps directly to directory structure
- `notes/` separates informal content from polished docs
- Scales to hundreds of files without becoming unmanageable

### Negative

- Existing cross-references break when files move (one-time migration cost)
- Some files could arguably go in multiple directories — requires judgment
- Top-level files are a catch-all that could grow over time

### Mitigations

- MkDocs handles relative links, so most references update with file moves
- Document the placement rules in this ADR so future contributors know
  where things go
- Review top-level files periodically — if a category emerges, create a
  subdirectory

## Implementation

- [`mkdocs.yml`](../../mkdocs.yml) — Navigation structure reflecting directories
- [`docs/README.md`](../README.md) — Documentation index with directory guide
- Each subdirectory has a `README.md` explaining its purpose

## References

- [Diátaxis framework](https://diataxis.fr/) — Documentation system
  architecture guide
- [MkDocs navigation](https://www.mkdocs.org/user-guide/writing-your-docs/#configure-pages-and-navigation) — How `nav:` maps to files
