# ADR 040: v1.0 Release Readiness Checklist

## Status

Accepted

## Context

The project has been in pre-1.0 development (0.x) with `bump-minor-pre-major: true`
in `release-please-config.json`, meaning breaking changes only bumped the minor
version. Before tagging the 1.0.0 release, several configuration files and
documentation needed updating to reflect production-stable status and enable
proper SemVer behavior going forward.

Without these changes:

- Breaking changes after 1.0 would still only bump minor (violating SemVer)
- PyPI classifiers would misrepresent the project as Beta
- Commitizen would not treat breaking changes as requiring major bumps
- SECURITY.md would not reflect the supported version range
- Coverage thresholds would remain at pre-1.0 starter levels
- Pre-1.0 documentation would confuse readers about current versioning behavior

## Decision

Apply a coordinated set of changes across configuration, documentation, and
tooling to transition from pre-1.0 to production-stable 1.0:

### Configuration Changes

1. **`release-please-config.json`**: Set `bump-minor-pre-major: false` so post-1.0
   breaking changes bump major. Remove stale `_comment_todo` and `_comment_versioning`
   fields that referenced pre-1.0 setup.

2. **`pyproject.toml`**: Switch classifier from `Development Status :: 4 - Beta`
   to `Development Status :: 5 - Production/Stable`.

3. **`pyproject.toml` `[tool.commitizen]`**: Set `major_version_zero = false` so
   commitizen also treats breaking changes as requiring major version bumps.

4. **`codecov.yml`**: Raise project coverage target from 80% to 90% and patch
   coverage from 70% to 80%, as committed to in the pre-1.0 TODO.

### Documentation Changes

5. **`SECURITY.md`**: Update version support table to show `1.x` as supported
   and `< 1.0` as unsupported.

6. **`docs/release-policy.md`**: Mark the pre-1.0 versioning section as historical
   context. Update the note about reaching 1.0.0 from future tense to past tense.

7. **`docs/known-issues.md`**: Move the three Release-tagged active issues
   (bump config, classifier, coverage badge) to the Resolved table. The first two
   are resolved; the badge token remains as a separate active item with lower
   severity.

### Tooling Changes

8. **`scripts/repo_doctor.py`**: Add built-in checks for shared internal module
   dependencies (`_colors.py`, `_doctor_common.py`, `_imports.py`, `_progress.py`).
   If any module is missing or deleted, warn which scripts will break.

9. **`scripts/git_doctor.py`**: Improve the UI duplication TODO with specific
   function names and a tracking reference in `known-issues.md`.

### Release Trigger

The actual 1.0.0 release is triggered by including a `Release-As: 1.0.0` trailer
in a conventional commit message, which tells release-please to target 1.0.0
specifically regardless of the computed version bump.

## Alternatives Considered

### Gradual rollout (alpha/beta/RC series before 1.0)

Pre-release versions (1.0.0a1, 1.0.0b1, 1.0.0rc1) before the final 1.0.0.

**Rejected because:** The project is a template repository with no runtime
consumers who need a staged migration path. The configuration and documentation
changes are all internal and take effect immediately.

### Do nothing (stay on 0.x indefinitely)

Keep `bump-minor-pre-major: true` and stay pre-1.0.

**Rejected because:** SemVer 0.x signals instability. The project's tooling,
CI/CD, and conventions are mature enough to warrant 1.0. Staying on 0.x
indefinitely undermines the signal that the template is production-ready.

## Consequences

### Positive

- Breaking changes now bump major version per SemVer — clear API contract
- PyPI classifier accurately reflects production-stable status
- Coverage thresholds enforce higher quality bar going forward
- SECURITY.md gives users clear version support expectations
- Shared module dependency checker prevents silent script breakage

### Negative

- Higher coverage thresholds may require writing more tests before PRs pass
- Any accidental breaking change now results in a major version bump (2.0.0),
  which is a stronger signal than intended for minor template adjustments

### Mitigations

- Coverage thresholds can be adjusted downward if they prove too aggressive
  for the current test suite maturity
- Breaking changes should be batched into planned major releases rather than
  happening ad-hoc

## Implementation

- [release-please-config.json](../../release-please-config.json) — `bump-minor-pre-major: false`, removed TODO comments
- [pyproject.toml](../../pyproject.toml) — Production/Stable classifier, `major_version_zero = false`
- [codecov.yml](../../codecov.yml) — 90% project target, 80% patch target
- [SECURITY.md](../../SECURITY.md) — 1.x supported, < 1.0 unsupported
- [docs/release-policy.md](../release-policy.md) — Pre-1.0 section marked historical
- [docs/known-issues.md](../known-issues.md) — Release items resolved
- [scripts/repo_doctor.py](../../scripts/repo_doctor.py) — Shared module dependency check
- [scripts/git_doctor.py](../../scripts/git_doctor.py) — UI duplication TODO improved

## References

- [ADR 021](021-automated-release-pipeline.md) — Automated release pipeline with release-please
- [Semantic Versioning 2.0.0](https://semver.org/)
- [release-please documentation](https://github.com/googleapis/release-please)
- [docs/releasing.md](../releasing.md) — How to Release 1.0.0 section
