# Release Policy

<!-- TODO (template users): Review this entire document and adapt it to
     your project's actual release cadence, support commitments, and API
     surface. The policies below are reasonable defaults — adjust the
     support window, deprecation timeline, and public API definition to
     match your project's reality. -->

This document describes when and how releases are made.

---

## Versioning Scheme

This project follows [Semantic Versioning](https://semver.org/) (SemVer):

| Version           | When to Increment                 | Example           |
| ----------------- | --------------------------------- | ----------------- |
| **MAJOR** (X.0.0) | Breaking changes to public API    | `1.0.0` → `2.0.0` |
| **MINOR** (0.X.0) | New features, backward compatible | `1.0.0` → `1.1.0` |
| **PATCH** (0.0.X) | Bug fixes, backward compatible    | `1.0.0` → `1.0.1` |

Version bumps are **determined automatically** by [release-please](https://github.com/googleapis/release-please) from conventional commit prefixes — no manual version decisions needed.

### How the Version Is Derived

The package version comes from **git tags** via [hatch-vcs](https://github.com/ofek/hatch-vcs) at build time:

- `pyproject.toml` declares `dynamic = ["version"]` — there is no static version field
- hatch-vcs reads the latest git tag (e.g., `v1.2.0`) and generates `_version.py`
- Dev builds between releases get PEP 440 versions like `0.1.1.dev3+gabcdef`
- The `__init__.py` fallback is updated by release-please for human readability

### Pre-1.0 Versioning (Historical)

> **Note:** This section describes behavior before the 1.0 release and is
> retained for historical context. As of 1.0, `bump-minor-pre-major` is
> `false` in [`release-please-config.json`](../release-please-config.json)
> and breaking changes bump the major version per SemVer.

While `bump-minor-pre-major` was `true`:

| Commit type       | Version bump      | Example           |
| ----------------- | ----------------- | ----------------- |
| `fix:` / `perf:`  | Patch             | `0.6.0` → `0.6.1` |
| `feat:`           | Minor             | `0.6.0` → `0.7.0` |
| `BREAKING CHANGE` | Minor (not major) | `0.6.0` → `0.7.0` |

Reaching `1.0.0` was achieved by using the `Release-As: 1.0.0` trailer
in a conventional commit message. See [How to Release 1.0.0](releasing.md#how-to-release-100)
for the approaches available (`Release-As` trailer, manual PR edit, or manifest update).
After `1.0.0`, breaking changes bump major as expected by SemVer.

### Pre-release Versions

| Suffix     | Meaning           | Stability                             |
| ---------- | ----------------- | ------------------------------------- |
| `1.0.0a1`  | Alpha             | Incomplete, may change significantly  |
| `1.0.0b1`  | Beta              | Feature complete, may have bugs       |
| `1.0.0rc1` | Release candidate | Ready for release unless issues found |

---

## Release Cadence

This project does **not** follow a fixed release schedule. Releases are made when:

- Significant features are complete
- Security vulnerabilities need patching
- Critical bugs are fixed

---

## What Triggers a Release

release-please scans conventional commits on `main` and creates (or updates) a
Release PR when it finds **releasable** commit types:

| Commit Prefix                                                      | Version Bump          | Appears in CHANGELOG             |
| ------------------------------------------------------------------ | --------------------- | -------------------------------- |
| `fix:`                                                             | Patch                 | Yes                              |
| `perf:`                                                            | Patch                 | Yes                              |
| `feat:`                                                            | Minor                 | Yes                              |
| `BREAKING CHANGE`                                                  | Major (minor pre-1.0) | Yes                              |
| `revert:`                                                          | Patch                 | Yes                              |
| `docs:`, `chore:`, `refactor:`, `test:`, `ci:`, `style:`, `build:` | —                     | Hidden (no release on their own) |

Hidden types are grouped under the releasable commits if releasable types exist in the same batch.
A push consisting only of hidden types (e.g., `docs:` or `chore:`) will **not** create a Release PR.

### When Releases Happen

| Situation       | Action                                                  |
| --------------- | ------------------------------------------------------- |
| Security fix    | Merge fix → merge Release PR ASAP                       |
| Bug fix         | Merge fix → merge Release PR (batched unless critical)  |
| New feature     | Merge feature → merge Release PR after testing and docs |
| Breaking change | Planned, documented, migration guide provided           |

---

## Backward Compatibility

### What We Consider "Public API"

<!-- TODO (template users): Update this list to reflect your actual
     exported API surface. The items below are placeholders from the
     boilerplate. -->

- Exported functions/classes from `simple_python_boilerplate`
- CLI commands and their arguments
- Configuration file formats

### What Is NOT Public API

- Internal modules (prefixed with `_`)
- Test utilities
- Development scripts
- File/directory structure

Changes to non-public API do not require a major version bump.

---

## Deprecation Policy

<!-- TODO (template users): Adapt the deprecation timeline to your release
     cadence. "At least one minor release" may not be enough for projects
     with long release cycles. -->

Before removing features:

1. Mark as deprecated in documentation and code (warnings)
2. Keep deprecated feature for at least one minor release
3. Document migration path
4. Remove in next major version

Example deprecation warning:

```python
import warnings

def old_function():
    warnings.warn(
        "old_function is deprecated, use new_function instead",
        DeprecationWarning,
        stacklevel=2
    )
    return new_function()
```

---

## Support Policy

<!-- TODO (template users): Adjust the support window (6 months, 12 months,
     etc.) based on your project's maintenance capacity and user expectations. -->

| Version        | Support Level                  |
| -------------- | ------------------------------ |
| Latest major   | Full support (bugs + features) |
| Previous major | Security fixes only (6 months) |
| Older versions | No support                     |

---

## Release Process

Releases are **fully automated** via [release-please](https://github.com/googleapis/release-please).
See [releasing.md](releasing.md) for the step-by-step guide.

### Summary

1. Conventional commits land on `main` (via rebase+merge)
2. release-please creates a **Release PR** with version bump + CHANGELOG update
3. Review and (optionally edit) the Release PR, then merge it
4. release-please creates a **git tag** and **GitHub Release**
5. The tag triggers [`release.yml`](../.github/workflows/release.yml) which builds, publishes, and attaches artifacts

**No manual version bumping, tagging, or CHANGELOG editing required.**

---

## See Also

- [Releasing](releasing.md) — Step-by-step release instructions
- [CHANGELOG.md](../CHANGELOG.md) — Version history
- [ADR 021](adr/021-automated-release-pipeline.md) — Decision record for the release pipeline
- [release-please-config.json](../release-please-config.json) — release-please configuration
- [release-please docs](https://github.com/googleapis/release-please)
- [hatch-vcs docs](https://github.com/ofek/hatch-vcs)
- [Semantic Versioning](https://semver.org/)
