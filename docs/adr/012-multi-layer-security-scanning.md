# ADR 012: Multi-layer security scanning in CI

## Status

Accepted

## Context

Python projects are vulnerable to supply-chain attacks through dependencies with known CVEs, and to code-level vulnerabilities like SQL injection, command injection, and path traversal. A single scanning tool is insufficient — different tools catch different categories of issues.

Options considered:

| Tool                           | What it catches                                             | When it runs                      |
| ------------------------------ | ----------------------------------------------------------- | --------------------------------- |
| **Dependabot alerts**          | Known CVEs in declared dependencies                         | Always (GitHub-native)            |
| **Dependabot version updates** | Outdated dependencies                                       | Weekly PRs                        |
| **dependency-review-action**   | Newly introduced vulnerable/restricted-license deps         | PR time                           |
| **pip-audit**                  | CVEs in the installed dependency tree (transitive deps too) | Push, PR, and weekly schedule     |
| **CodeQL**                     | Code-level vulnerabilities (injection, XSS, etc.)           | Push, PR, and weekly schedule     |
| **Bandit**                     | Python-specific security anti-patterns                      | Could be added later              |
| **Safety**                     | Commercial CVE database for Python                          | Requires paid license for full DB |

## Decision

Use a multi-layer approach with four complementary tools:

1. **Dependabot** (`.github/dependabot.yml`) — Automated PRs for vulnerable and outdated dependencies
2. **dependency-review-action** (`dependency-review.yml`) — Blocks PRs that introduce vulnerable or restrictively-licensed dependencies
3. **pip-audit** (`security-audit.yml`) — Audits the full installed dependency tree against OSV and PyPI databases; catches transitive dependency vulnerabilities that Dependabot may miss
4. **CodeQL** (`security-codeql.yml`) — GitHub's semantic code analysis engine; finds vulnerabilities in the project's own source code

### Why all four?

| Layer             | Dependencies (direct) | Dependencies (transitive) | Own code |
| ----------------- | :-------------------: | :-----------------------: | :------: |
| Dependabot        |          Yes          |          Partial          |    No    |
| dependency-review |          Yes          |            No             |    No    |
| pip-audit         |          Yes          |            Yes            |    No    |
| CodeQL            |          No           |            No             |   Yes    |

No single tool covers all three categories.

## Consequences

### Positive

- Comprehensive coverage across direct deps, transitive deps, and source code
- Vulnerabilities are caught at multiple stages: PR review, CI, and weekly schedule
- All tools are free for public repositories
- Results surface in GitHub's Security tab for centralized tracking
- pip-audit catches transitive dependency CVEs that Dependabot misses

### Negative

- Four security tools add CI runtime (though each is fast — typically under 5 minutes)
- Template users must opt in via repository guards for each workflow
- CodeQL requires GitHub Advanced Security (free for public repos, paid for private)
- Multiple vulnerability sources can produce duplicate alerts

### Neutral

- Bandit could be added later for Python-specific anti-pattern detection
- All security workflows run on a weekly schedule in addition to push/PR triggers to catch newly disclosed CVEs
