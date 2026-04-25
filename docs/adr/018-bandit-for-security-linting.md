# ADR 018: Use Bandit for Python security linting

## Status

Accepted — extends [ADR 012 (multi-layer security scanning)](012-multi-layer-security-scanning.md)

## Context

ADR 012 established a multi-layer security scanning strategy covering dependencies (Dependabot, pip-audit, dependency-review) and source code (CodeQL). However, CodeQL is a general-purpose analysis engine — it catches broad vulnerability categories but is not Python-specific.

Bandit is a purpose-built Python security linter that detects anti-patterns unique to the language:

| Category             | Examples                                              |
| -------------------- | ----------------------------------------------------- |
| **Injection**        | `subprocess` with `shell=True`, SQL string formatting |
| **Cryptography**     | Use of MD5/SHA1 for security, weak random generators  |
| **Credentials**      | Hardcoded passwords, API keys in source               |
| **Unsafe functions** | `eval()`, `exec()`, `yaml.load()` without safe loader |
| **File handling**    | Insecure temp file creation, path traversal risks     |

## Alternatives Considered

| Option          | Pros                                         | Cons                                                                    |
| --------------- | -------------------------------------------- | ----------------------------------------------------------------------- |
| **CodeQL only** | Already in CI, general-purpose               | Misses Python-specific anti-patterns                                    |
| **Safety**      | Comprehensive CVE database                   | Requires paid license for full DB; dependency-focused, not code-focused |
| **Semgrep**     | Powerful pattern matching, custom rules      | Heavier setup, commercial model for advanced features                   |
| **Bandit**      | Python-specific, fast, well-maintained, free | Narrower scope than Semgrep                                             |

### Where Bandit runs in the pipeline

| Layer                | When               | Purpose                                          |
| -------------------- | ------------------ | ------------------------------------------------ |
| **Pre-commit hook**  | Before each commit | Immediate feedback, blocks insecure code locally |
| **`task security`**  | On-demand          | Manual scan during development                   |
| **Nightly workflow** | Daily at 03:00 UTC | Catches issues in code that bypassed pre-commit  |

## Decision

Add Bandit as a security linting layer alongside the existing tools from ADR 012:

- **Dependency** — Added to `[project.optional-dependencies].dev` in `pyproject.toml` (PEP 621, Dependabot-updatable)
- **Configuration** — `[tool.bandit]` in `pyproject.toml` with `exclude_dirs = ["tests", ".venv"]` and `skips = ["B101"]` (assert is acceptable)
- **Pre-commit** — Added to `.pre-commit-config.yaml` with `bandit[toml]` for pyproject.toml config support
- **CI** — Nightly GitHub Actions workflow (`bandit.yml`) for scheduled scanning
- **Taskfile** — `task security` for on-demand local scans

## Consequences

### Positive

- Fills the Python-specific gap that CodeQL does not cover
- Fast feedback loop — catches issues at commit time, not just in CI
- Configuration lives in `pyproject.toml` alongside all other tool config (ADR 002)
- Dependabot can auto-update the bandit version

### Negative

- Adds another security tool to maintain (though configuration is minimal)
- May produce false positives that require `# nosec` annotations or skip rules
- Pre-commit hook adds a few seconds to commit time

### Neutral

- Bandit does not replace CodeQL — they are complementary (Bandit catches Python patterns, CodeQL catches data-flow vulnerabilities)
- The `B101` skip (assert statements) aligns with the project convention of allowing asserts outside production code
