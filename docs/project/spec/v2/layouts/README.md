# v2.0 page layouts

This directory holds per-page layout specs for the authenticated and
public SignalNest surfaces.

Use these files when you need to answer:

- what the page looks like,
- what sections appear on the page,
- what data populates each section,
- and what empty/error states are expected.

## Scope and authority

- Source of truth for routes and hierarchy remains
  [information-architecture.md](../information-architecture.md).
- Global visual and responsive rules remain in
  [layout.md](../layout.md).
- UI conventions and accessibility floor remain in [ui.md](../ui.md)
  and [accessibility.md](../accessibility.md).

These page files are the page-level contract layer between IA and
implementation.

## File conventions

Create one markdown file per page (for example, `dashboard.md`).
Each file should include:

1. Route and audience
2. Page purpose
3. Section-by-section layout map
4. Data population contract (which backend field feeds which section)
5. Empty / loading / error states
6. Links to implementation surfaces (template, CSS classes, backend service)

## Current pages

- [dashboard.md](dashboard.md)
