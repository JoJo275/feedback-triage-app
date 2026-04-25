# Blueprint: [Short descriptive title]

## Status

Draft | Under Review | Accepted | Superseded by Blueprint NNN (`NNN-name.md`)

## Summary

One-paragraph description of the proposed design.

## Origin

Link to the exploration that led to this blueprint:

- Exploration NNN: Title (`../explorations/NNN-title.md`)

## Proposed Architecture

High-level description of the technical approach. Include diagrams
(Mermaid or ASCII) if they help.

```
┌──────────┐     ┌──────────┐
│ Module A  │────▶│ Module B  │
└──────────┘     └──────────┘
```

## Repo Layout

Where files will live, what directories are created or changed.

```
path/to/
├── new_directory/
│   ├── file_a.py
│   └── file_b.py
├── existing_file.py  (modified)
└── new_config.toml
```

## Components / Modules

| Component | Responsibility | Key interfaces |
| :-------- | :------------- | :------------- |
| Module A  | Does X         | `func_a()`     |
| Module B  | Does Y         | `ClassB`       |

## Tooling Impact

What tools, dependencies, or configuration changes are needed?

- **New dependencies:** List any new packages
- **Config changes:** Files that need updating (pyproject.toml, etc.)
- **CI/CD impact:** New workflows, modified gates, etc.
- **Pre-commit hooks:** New or modified hooks

## Workflow / UX

How will developers or users interact with this? Describe the typical
workflow or user experience.

## Open Design Questions

- [ ] Question 1 — needs input from X
- [ ] Question 2 — blocked on research into Y

## Constraints

- Performance requirements
- Compatibility requirements
- Security considerations

## References

- Exploration NNN: Title (`../explorations/NNN-title.md`)
- Related ADR (`../adr/NNN-related.md`)
- [External documentation](https://example.com)
