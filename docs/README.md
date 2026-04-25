# Documentation

<!-- TODO (template users): Update this README and the contents table after
     adding or removing documentation sections for your project. -->

Project documentation organized by topic.

## Contents

| Directory / File                       | Description                            |
| -------------------------------------- | -------------------------------------- |
| [adr/](adr/)                           | Architecture Decision Records          |
| [blueprints/](blueprints/)             | Proposed design shapes                 |
| [design/](design/)                     | Architecture and database design       |
| [development/](development/)           | Developer guides and setup             |
| [explorations/](explorations/)         | Early-stage idea evaluation            |
| [guide/](guide/)                       | User-facing guides and troubleshooting |
| [implementation-plans/](implementation-plans/) | Step-by-step execution details |
| [notes/](notes/)                       | Personal notes and scratchpad          |
| [reference/](reference/)               | API and configuration reference        |
| [templates/](templates/)               | Reusable file templates                |
| [index.md](index.md)                   | MkDocs home page                       |
| [labels.md](labels.md)                 | GitHub label definitions               |
| [release-policy.md](release-policy.md) | Versioning and support policy          |
| [releasing.md](releasing.md)           | Release process and checklist          |
| [repo-layout.md](repo-layout.md)       | Full annotated repository structure    |
| [sbom.md](sbom.md)                     | Software Bill of Materials             |
| [tooling.md](tooling.md)               | Tooling overview and rationale         |
| [workflows.md](workflows.md)           | GitHub Actions workflows reference     |

## Design Lifecycle

For non-trivial changes, use this optional workflow to move from idea to
implementation:

```
idea/problem → explorations/
proposed design → blueprints/
decision locked in → adr/
build steps → implementation-plans/
```

See each directory's README for when to write that kind of document.
Skip stages that don't apply — small changes can go straight to an ADR
or implementation plan.

## Quick Links

- [Development Setup](development/dev-setup.md)
- [Repository Layout](repo-layout.md)
- [Releasing](releasing.md)
- [Workflows](workflows.md)
- [Contributing](../CONTRIBUTING.md)
- [Architecture](design/architecture.md)
- [Troubleshooting](guide/troubleshooting.md)

## Building the Docs

```bash
# Serve locally with live reload
task docs:serve          # or: hatch run docs:serve

# Build in strict mode (same as CI)
task docs:build          # or: hatch run docs:build
```

## For Template Users

When using this template:

1. Update documentation to match your project
2. Copy files from [templates/](templates/) as needed
3. Keep or remove [notes/](notes/) (useful reference material)
4. Add project-specific guides to [guide/](guide/) and [development/](development/)
5. Update [index.md](index.md) and [mkdocs.yml](../mkdocs.yml) for your site
