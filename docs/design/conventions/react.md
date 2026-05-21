# React Conventions

This page tracks active React conventions used in this project.

## Canonical Sources

- [React instructions](../../../.github/instructions/react.instructions.md)
- [v2 UI spec](../../project/spec/v2/ui.md)
- [v2 information architecture](../../project/spec/v2/information-architecture.md)
- [v2 testing strategy](../../project/spec/v2/testing-strategy.md)

## Working Rules

- Keep React runtime contracts aligned with backend shell templates and route bootstrap behavior.
- Use `useMemo` for expensive derived render values and `useCallback` only where stable function identity is required.
- Preserve data-loading contracts and fail-closed behavior for missing or invalid bootstrap data.

## When Changing React Conventions

1. Update canonical guidance first.
2. Update implementation and tests in the same PR.
3. Sync this page when conventions change.
