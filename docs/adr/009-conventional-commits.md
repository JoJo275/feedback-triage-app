# ADR 009: Use Conventional Commits for commit messages

## Status

Accepted

## Context

Commit messages can follow various conventions:

- **Free-form** — No standard format
- **Conventional Commits** — Structured format with type prefixes
- **Gitmoji** — Emoji-based categorization
- **Project-specific** — Custom format (e.g., Jira ticket prefixes)

Standardized commit messages enable:

- Automated changelog generation
- Semantic versioning automation
- Easier code review and history navigation
- Consistent communication about changes

## Decision

Use Conventional Commits format for all commit messages:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

| Type       | Description                             |
| ---------- | --------------------------------------- |
| `feat`     | New feature                             |
| `fix`      | Bug fix                                 |
| `docs`     | Documentation only                      |
| `style`    | Formatting, no code change              |
| `refactor` | Code change that neither fixes nor adds |
| `test`     | Adding or updating tests                |
| `chore`    | Maintenance, dependencies, tooling      |
| `ci`       | CI/CD changes                           |
| `perf`     | Performance improvement                 |

### Examples

```
feat: add user authentication
fix: resolve null pointer in parser
docs: update installation instructions
chore: bump ruff to v0.4.4
ci: add Python 3.12 to test matrix
```

## Consequences

### Positive

- **Automated changelogs** — Tools can generate CHANGELOG.md from commits
- **Semantic versioning** — `feat` = minor, `fix` = patch, `BREAKING CHANGE` = major
- **Scannable history** — Type prefix makes `git log` easier to read
- **PR titles** — Same format works for pull request titles
- **Ecosystem support** — Many tools understand this format

### Negative

- **Learning curve** — Contributors must learn the format
- **Overhead** — Slightly more thought required per commit
- **Enforcement** — Requires tooling or review to enforce consistently

### Mitigations

- Document format in CONTRIBUTING.md
- Optionally add commitlint for automated enforcement
- Review PR titles during code review

## Alternatives Considered

### Free-form messages

No enforced format; developers write what they want.

**Rejected because:** Inconsistent, harder to scan, can't automate changelog generation.

### Gitmoji

Use emojis to categorize commits (🐛 for bugs, ✨ for features).

**Rejected because:** Harder to type, less grep-friendly, less tooling support than Conventional Commits.

## Implementation

- [CONTRIBUTING.md](../../CONTRIBUTING.md) — Documents commit message format for contributors
- [.github/copilot-instructions.md](../../.github/copilot-instructions.md) — Conventional commit guidance for AI-assisted development
- [.github/PULL_REQUEST_TEMPLATE.md](../../.github/PULL_REQUEST_TEMPLATE.md) — PR template encouraging conventional format

## References

- [Conventional Commits specification](https://www.conventionalcommits.org/)
- [commitlint](https://commitlint.js.org/)
- [semantic-release](https://semantic-release.gitbook.io/)
