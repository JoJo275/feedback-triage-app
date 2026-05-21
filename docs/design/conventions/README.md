# Design Conventions

Central home for project conventions used by frontend design and implementation docs.

## Purpose

Use this directory for conventions that are expected to be followed in daily work, such as:

- CSS and design token conventions
- HTML semantics and accessibility conventions
- React structure and data-loading conventions

## Conventions Index

| Document | Scope |
| --- | --- |
| [css.md](css.md) | CSS, tokens, component naming, and styling workflow expectations |
| [html.md](html.md) | Semantic HTML, accessibility structure, and form/interaction markup patterns |
| [react.md](react.md) | React runtime, component/hook conventions, and integration contracts |

## Existing Canonical Sources

During migration into this directory, these documents remain authoritative:

- [Frontend conventions notes](../../notes/frontend-conventions.md)
- [v2 CSS spec](../../project/spec/v2/css.md)
- [v2 UI spec](../../project/spec/v2/ui.md)
- [v2 accessibility spec](../../project/spec/v2/accessibility.md)

## Maintenance Rule

When adding or moving conventions:

1. Update canonical spec/design docs first.
2. Update this index in the same PR.
3. Remove stale duplicates instead of maintaining competing guidance.
