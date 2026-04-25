# ADR 004: Pin GitHub Actions to commit SHAs

## Status

Accepted

## Context

GitHub Actions can be referenced in three ways:

```yaml
# By branch/tag (mutable)
uses: actions/checkout@v4
uses: actions/checkout@main

# By full commit SHA (immutable)
uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
```

Using mutable references (tags/branches) is convenient but poses security risks:

- **Tag hijacking** — Attacker compromises action repo and moves tag to malicious commit
- **Supply chain attacks** — Malicious code injected into trusted action
- **Unpredictable behavior** — Tag contents can change without notice

GitHub's security hardening guide recommends pinning to full commit SHAs.

## Decision

Pin all third-party GitHub Actions to full commit SHAs with version comments:

```yaml
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
- uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 # v5.6.0
```

## Consequences

### Positive

- **Immutable** — SHA cannot be changed; guarantees exact code runs
- **Supply chain security** — Protected against tag hijacking attacks
- **Reproducible** — Same SHA always runs same code
- **Audit trail** — Clear record of exact versions used

### Negative

- **Manual updates** — Must manually update SHAs when new versions release
- **Less readable** — SHAs are not human-friendly (mitigated by version comments)
- **Dependabot friction** — Dependabot updates SHAs but may lag behind

### Mitigations

- Add version comment after SHA for readability
- Use Dependabot to receive update PRs
- Periodically review and update action versions

## Alternatives Considered

### Pin to Major Version Tag (e.g., @v4)

```yaml
uses: actions/checkout@v4
```

**Rejected because:** Tags are mutable — an attacker who compromises the action repo could move the tag to malicious code. No guarantee of what code actually runs.

### Pin to Exact Version Tag (e.g., @v4.2.2)

```yaml
uses: actions/checkout@v4.2.2
```

**Rejected because:** Still mutable. While less likely to be moved than major tags, exact version tags can still be force-pushed.

### Pin to Branch (e.g., @main)

```yaml
uses: actions/checkout@main
```

**Rejected because:** Highly mutable, changes with every commit. Maximum risk of unexpected behavior or supply chain attack.

### Use GitHub's Immutable Actions (GHES)

GitHub Enterprise Server can enforce immutable action references.

**Not applicable:** This is a public repo on github.com, not GHES.

## Implementation

- [.github/workflows/test.yml](../../.github/workflows/test.yml) — Example: `actions/checkout@8e8c483db84b4bee98b60c0593521ed34d9990e8 # v6.0.1`
- [.github/workflows/lint-format.yml](../../.github/workflows/lint-format.yml) — All actions pinned to SHAs
- [.github/workflows/release.yml](../../.github/workflows/release.yml) — All actions pinned to SHAs
- [.github/dependabot.yml](../../.github/dependabot.yml) — Dependabot configured to update GitHub Actions

## References

- [GitHub: Security hardening for GitHub Actions](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions#using-third-party-actions)
- [Step Security: Action Hardening](https://www.stepsecurity.io/)
