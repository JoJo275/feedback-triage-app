# ADR 020: Use MkDocs with Material theme for project documentation

## Status

Accepted

## Context

Every non-trivial project needs a documentation site that is easy to write, easy to maintain, and easy to deploy. The documentation tooling should:

1. **Use Markdown** — The team already writes Markdown in READMEs, ADRs, and inline docs.
2. **Generate API docs** — Automatically render docstrings so API reference stays in sync with code.
3. **Look professional** — A polished theme with dark mode, search, and code highlighting.
4. **Stay in the Python ecosystem** — Avoid adding Node.js or other runtime dependencies.
5. **Support local preview** — Live-reload dev server for authoring.

## Decision

Use **MkDocs** as the static site generator with the following stack:

| Component           | Package                      | Purpose                                                         |
| ------------------- | ---------------------------- | --------------------------------------------------------------- |
| Site generator      | `mkdocs>=1.6`                | Builds Markdown into a static HTML site                         |
| Theme               | `mkdocs-material>=9.4`       | Material Design theme with dark/light toggle, search, code copy |
| Markdown extensions | `pymdown-extensions>=10.0`   | Tabbed content, admonitions, syntax highlighting                |
| API docs            | `mkdocstrings[python]>=0.27` | Auto-generates reference docs from Google-style docstrings      |

Configuration lives in a single file:

```yaml
# mkdocs.yml
site_name: simple-python-boilerplate
docs_dir: docs
theme:
    name: material
plugins:
    - search
    - mkdocstrings
```

Documentation source lives in `docs/` alongside ADRs, notes, and design docs.

## Consequences

### Positive

- **Markdown-native** — No new syntax to learn; same format as READMEs and ADRs
- **API docs stay in sync** — `mkdocstrings` renders docstrings directly from source code
- **Fast iteration** — `mkdocs serve` provides live-reload during authoring
- **Rich features out of the box** — Material theme includes search, dark mode, code copy, navigation tabs
- **Python-only toolchain** — No Node.js or npm required
- **Static output** — Builds to plain HTML; can be hosted anywhere (GitHub Pages, S3, etc.)
- **Hatch integration** — `hatch run docs:serve` and `hatch run docs:build` provide convenient entry points

### Negative

- **Extra dependencies** — Four packages added to `[project.optional-dependencies.docs]`
- **Flat docs directory** — All documentation lives in `docs/`, which keeps paths simple but mixes MkDocs content with ADRs and design docs
- **Material theme lock-in** — Heavily using Material-specific features makes switching themes harder
- **Build step required** — Must run `mkdocs build` to produce the site; not just raw Markdown

### Neutral

- Documentation dependencies are isolated in an optional `docs` extra, not installed by default
- MkDocs configuration is declarative YAML, consistent with other project config files

## Alternatives Considered

### Sphinx

The traditional Python documentation tool, using reStructuredText.

**Rejected because:** reStructuredText has a steeper learning curve than Markdown. Sphinx configuration is more complex (`conf.py` with imperative Python). The team already writes Markdown everywhere else in the project.

### Docsify / VitePress / Docusaurus

JavaScript-based documentation generators.

**Rejected because:** Adds a Node.js dependency to a Python-only project. Contradicts the goal of keeping the toolchain within the Python ecosystem.

### Plain Markdown (no generator)

Serve docs directly from GitHub's Markdown rendering.

**Rejected because:** No search, no API docs generation, no consistent theme, no local preview with live-reload. Adequate for small projects but doesn't scale.

### Jupyter Book

Sphinx-based tool with MyST Markdown support.

**Rejected because:** Heavier dependency tree. Better suited for computational narratives and tutorials than API reference documentation.

## Implementation

- [mkdocs.yml](../../mkdocs.yml) — Site configuration (theme, plugins, nav, extensions)
- [docs/](../../docs/) — Documentation source files
- [pyproject.toml](../../pyproject.toml) — Dependencies in `[project.optional-dependencies.docs]`
- [pyproject.toml](../../pyproject.toml) — Hatch scripts in `[tool.hatch.envs.docs.scripts]`:
    - `hatch run docs:serve` — Live-reload dev server
    - `hatch run docs:build` — Build static site (strict mode)

## References

- [MkDocs documentation](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [mkdocstrings](https://mkdocstrings.github.io/)
- [PyMdown Extensions](https://facelessuser.github.io/pymdown-extensions/)
