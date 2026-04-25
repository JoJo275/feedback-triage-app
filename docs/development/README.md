# Development Documentation

<!-- TODO (template users): Add project-specific development guides as your
     codebase grows (e.g., API conventions, database patterns, deployment). -->

Guides for developers working on this project.

## Contents

| Document                                       | Description                                        |
| ---------------------------------------------- | -------------------------------------------------- |
| [dev-setup.md](dev-setup.md)                   | Environment setup and prerequisites                |
| [development.md](development.md)               | Daily workflows (testing, linting, building)       |
| [pull-requests.md](pull-requests.md)           | PR guidelines and code review process              |
| [developer-commands.md](developer-commands.md) | Quick reference for common commands                |
| [command-workflows.md](command-workflows.md)   | How commands flow through the tooling layers       |
| [branch-workflows.md](branch-workflows.md)     | Branch management, rebase workflows, and git stash |

## Quick Links

- **New contributor?** Start with [dev-setup.md](dev-setup.md)
- **Ready to code?** See [development.md](development.md)
- **Opening a PR?** Read [pull-requests.md](pull-requests.md)
- **Need a command?** Check [developer-commands.md](developer-commands.md)
- **Branch questions?** Check [branch-workflows.md](branch-workflows.md)

## Idea Development Lifecycle

Non-trivial changes follow this lifecycle from idea to implementation:

```
idea/problem        →  explorations/           Early-stage evaluation
proposed design     →  blueprints/             Structural design shape
decision locked in  →  adr/                    Permanent decision record
build steps         →  implementation-plans/   Step-by-step execution
```

Skip stages that don't apply. Each directory has a README with guidance
and a template. See [development.md](development.md) for details.

## See Also

- [CONTRIBUTING.md](../../CONTRIBUTING.md) — Contribution guidelines
- [docs/explorations/](../explorations/) — Early-stage idea evaluation
- [docs/blueprints/](../blueprints/) — Proposed structural designs
- [docs/adr/](../adr/) — Architecture Decision Records
- [docs/implementation-plans/](../implementation-plans/) — Step-by-step build plans
- [docs/design/](../design/) — Architecture and design documentation
- [docs/notes/](../notes/) — Learning notes and references
- [docs/guide/](../guide/) — User-facing guides and troubleshooting
