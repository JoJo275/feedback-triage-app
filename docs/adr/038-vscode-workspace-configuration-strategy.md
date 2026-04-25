# ADR 038: VS Code Workspace Configuration Strategy

## Status

Accepted

## Context

VS Code loads settings from multiple sources in a specific priority order.
This project supports three ways of opening the codebase:

| Open method                     | `.vscode/settings.json` | `.code-workspace` settings |
| :------------------------------ | :---------------------: | :------------------------: |
| File > Open Folder              |         Loaded          |          Ignored           |
| File > Open Workspace from File |         Loaded          |     Loaded (overrides)     |
| Codespaces / Dev Containers     |         Loaded          |          Ignored           |

If functional settings (formatters, linters, test config) are placed in the
`.code-workspace` file, they only apply when opened as a workspace — not
in Codespaces, Dev Containers, or "Open Folder" users. This creates a
fragile, hard-to-debug inconsistency.

Additionally, VS Code has a User Settings profile layer
(`%APPDATA%/Code/User/profiles/<id>/settings.json` on Windows) that applies
globally. When a setting appears in both User Settings and folder settings,
the user may see the folder setting greyed out in the Settings UI because
the User Setting takes precedence for display purposes, even though
folder-level settings do override at runtime for that workspace.

## Decision

Split editor configuration across three files with clear responsibilities:

### `.vscode/settings.json` — Single source of truth

Contains **all functional settings**: Python formatter/linter, test
discovery, file excludes, search excludes, git behavior, editor rulers,
extension-specific configuration (Ruff, Error Lens, Indent Rainbow, etc.).

This file loads regardless of how the project is opened, making it the
only reliable location for settings that affect tooling behavior.

### `.vscode/extensions.json` — Extension recommendations (Open Folder)

Lists recommended extensions for users who open the project as a folder.
VS Code shows "install recommended extensions" prompts from this file.

### `.code-workspace` — Extension recommendations + cosmetic overrides

Contains the same extension list (for "Open Workspace" users) plus an
empty settings block. Cosmetic preferences that are genuinely
workspace-specific could go here, but in practice all settings live in
`.vscode/settings.json` to avoid the "works for me but not for them"
problem.

### Why the extension list is in both files

`.vscode/extensions.json` serves "Open Folder" users. The `.code-workspace`
`extensions.recommendations` array serves "Open Workspace" users. Both
must exist because VS Code reads different files depending on the open
method. The lists are kept in sync manually.

### Greyed-out settings in the UI

Settings that appear greyed out in VS Code's Settings UI are typically
inherited from a higher-priority scope (User Settings profile). This
is cosmetic — the folder-level value still applies when working in the
project. It looks greyed out because VS Code shows the effective value
from the highest scope and indicates lower scopes are "overridden."

## Alternatives Considered

### Put everything in `.code-workspace`

Single file for all settings and extensions.

**Rejected because:** `.code-workspace` settings are ignored in three
common scenarios: Open Folder, Codespaces, and Dev Containers. Functional
settings placed here silently stop working for those users.

### Put everything in `.vscode/settings.json` only

Skip the `.code-workspace` file entirely.

**Rejected because:** The workspace file provides a useful single-click
way to open the project with the correct root folder, and its extension
recommendations serve users who prefer the workspace open method.

### Use User Settings for everything

Let each developer configure their own editor.

**Rejected because:** Project-specific settings (Python formatter = Ruff,
test framework = pytest, editor rulers at 88/120) should travel with the
repo, not require each contributor to configure manually.

## Consequences

### Positive

- Settings work identically regardless of open method
- Single file to check when debugging "my linter isn't running"
- Clear mental model: functional → `.vscode/settings.json`,
  cosmetic/personal → User Settings
- Dev Containers and Codespaces get correct settings automatically

### Negative

- Extension recommendations must be maintained in two places
  (`.vscode/extensions.json` and `.code-workspace`)
- `.code-workspace` settings block is mostly empty, which may confuse
  users who expect to find settings there
- Greyed-out settings in the UI can confuse contributors who think the
  setting isn't active

### Mitigations

- Comments in both files explain the split and why
- This ADR documents the rationale
- `.code-workspace` header comment includes a compatibility matrix

## Implementation

- [.vscode/settings.json](../../.vscode/settings.json) — All functional settings
- [.vscode/extensions.json](../../.vscode/extensions.json) — Extension recommendations (Open Folder)
- [simple-python-boilerplate.code-workspace](../../simple-python-boilerplate.code-workspace) — Extension recommendations (Open Workspace)

## References

- [VS Code Settings Precedence](https://code.visualstudio.com/docs/getstarted/settings#_settings-precedence)
- [VS Code Workspace Settings](https://code.visualstudio.com/docs/editor/workspaces)
- [ADR 025: Container strategy](025-container-strategy.md) — Dev Container uses `.vscode/settings.json`
