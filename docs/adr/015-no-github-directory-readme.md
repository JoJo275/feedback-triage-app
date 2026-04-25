# ADR 015: No README.md in .github/ directory

## Status

Accepted

## Context

GitHub has a little-known README resolution order for the repository landing page. When determining which README to display, GitHub checks these locations **in priority order**:

1. `.github/README.md` (highest priority)
2. `README.md` (root)
3. `docs/README.md`

This means a `.github/README.md` — even one intended only to document the `.github/` directory contents for contributors — **silently replaces the root README.md on the repository's main page**.

This template originally included `.github/README.md` to document GitHub-specific configuration (workflows, issue templates, dependabot, etc.) for template users. The result was that visitors to the repository saw the `.github/` documentation table instead of the project's actual README.

### The root cause

GitHub treats `.github/README.md` as a **profile/landing README**, not as a directory-scoped README. This is consistent with how GitHub uses `.github/` for other special files (e.g., `FUNDING.yml`, `CODEOWNERS`, default community health files), but it is surprising because every other directory's `README.md` only renders when browsing _that_ directory.

## Alternatives Considered

| Option                       | Outcome                                                     |
| ---------------------------- | ----------------------------------------------------------- |
| Keep `.github/README.md`     | Root README not shown on repo page — confusing for visitors |
| Rename to `.github/ABOUT.md` | Doesn't auto-render on GitHub; loses discoverability        |
| Move content to `docs/`      | Content already covered by `docs/repo-layout.md`            |
| Delete `.github/README.md`   | Root README displays correctly; no information lost         |

## Decision

Do not include a `README.md` in the `.github/` directory. Documentation about `.github/` contents belongs in `docs/repo-layout.md`, which already covers the full repository structure.

## Consequences

### Positive

- The root `README.md` displays correctly on the GitHub repository page.
- No risk of accidentally overriding the project README in the future.
- One less file to maintain.

### Negative

- Browsing the `.github/` directory on GitHub won't show an auto-rendered README. Contributors must refer to `docs/repo-layout.md` for context.

### Neutral

- This is a GitHub-specific behavior. Other forges (GitLab, Gitea, etc.) may not exhibit the same priority order, but avoiding `.github/README.md` is harmless on all platforms.
