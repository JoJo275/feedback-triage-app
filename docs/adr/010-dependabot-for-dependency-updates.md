# ADR 010: Use Dependabot for dependency updates

## Status

Accepted

## Context

Dependencies (both Python packages and GitHub Actions) need to be kept up to date for security patches, bug fixes, and new features. Manual tracking is tedious and error-prone — vulnerabilities can go unnoticed for weeks or months.

Options considered:

- **Manual updates** — Developer checks for updates periodically
- **Renovate** — Powerful but complex configuration; self-hosted option available
- **Dependabot** — GitHub-native, zero-infrastructure, simple YAML config
- **pip-tools / pip-compile** — Handles pinning but not automated PRs

## Decision

Use GitHub Dependabot for automated dependency update PRs. Configure it in `.github/dependabot.yml` with two ecosystems:

1. **`github-actions`** — Keep workflow action versions current
2. **`pip`** — Keep Python package dependencies current

### Configuration choices

| Setting            | Value                           | Rationale                                                          |
| ------------------ | ------------------------------- | ------------------------------------------------------------------ |
| Schedule           | Weekly (Monday 9am ET)          | Batches updates without overwhelming reviewers                     |
| Rebase strategy    | Disabled                        | Avoids noisy force-pushes on open PRs                              |
| PR limit (actions) | 5                               | Actions update less frequently                                     |
| PR limit (pip)     | 10                              | More Python deps to track                                          |
| Grouping           | Minor + patch together          | Reduces PR volume; majors kept separate for breaking change review |
| Commit prefix      | `ci:` (actions), `chore:` (pip) | Aligns with Conventional Commits (ADR 009)                         |

## Consequences

### Positive

- Security vulnerabilities in dependencies are surfaced quickly via automated PRs
- Dependabot security alerts provide immediate notifications for critical CVEs
- No external service or infrastructure needed — fully GitHub-native
- Grouped PRs reduce noise while keeping major (breaking) updates visible
- Labels (`dependencies`, `github-actions`, `python`) enable easy filtering

### Negative

- Can generate many PRs if dependencies are significantly outdated
- Grouped updates may mask which specific package caused a CI failure
- Dependabot has limited customization compared to Renovate (e.g., no auto-merge rules natively)

### Neutral

- PRs still require manual review and merge — Dependabot does not auto-merge by default
- Dependabot version updates are separate from Dependabot security alerts (both should be enabled)
