# ADR 021: Automated Release Pipeline with release-please

## Status

Accepted

## Context

The project needs an automated release workflow that:

- Bumps versions automatically based on commit types (SemVer)
- Generates CHANGELOG entries from commit messages
- Creates git tags and GitHub Releases
- Triggers build and optional PyPI publish
- Produces reviewable/editable release content before it goes live
- Avoids CHANGELOG merge conflicts

### Tools Considered

| Tool                        | Approach                                           | Pros                                                                              | Cons                                                                                                   |
| --------------------------- | -------------------------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| **release-please** (Google) | Scans conventional commits, creates Release PR     | Auto version from commits, editable Release PR, auto tags+releases, GitHub-native | Google-maintained (may change direction), less Python-specific                                         |
| **python-semantic-release** | Parses commits, pushes tags directly               | Python-native, PyPI publishing built in                                           | No reviewable Release PR, pushes tags directly (no review step)                                        |
| **towncrier**               | Fragment files per PR, assembled at release        | Per-PR granularity, no merge conflicts                                            | Cannot auto-determine version from commits, manual version decision, requires fragment file discipline |
| **commitizen** (bump mode)  | Parses commits, bumps version                      | Python-native, also validates commits                                             | Overlaps with release-please, less GitHub integration                                                  |
| **changesets**              | Fragment-based (like towncrier, from JS ecosystem) | Popular in JS projects                                                            | Node.js oriented, fragment-based                                                                       |
| **git-cliff**               | Generates changelogs from commits                  | Fast (Rust), highly customizable templates                                        | CLI only, no PR/release automation                                                                     |
| **release-drafter**         | Generates draft release notes from PR labels       | GitHub-native, label-based categories                                             | No version bumping, no CHANGELOG file, no tag creation                                                 |

### Version Management: hatch-vcs

Separately from release automation, the project uses **hatch-vcs** to derive the package version from git tags at build time:

- `pyproject.toml` declares `dynamic = ["version"]` — no static version field
- hatch-vcs reads the latest git tag (e.g., `v1.2.0`) and generates `_version.py`
- Dev builds between releases get versions like `0.1.1.dev3+gabcdef` (PEP 440)
- The `__init__.py` fallback (`__version__ = "0.1.0"`) is updated by release-please for human readability

**Why hatch-vcs instead of a static version?**

- Single source of truth (git tags)
- No "forgot to bump the version" bugs
- Dev builds are distinguishable from releases
- Aligns with the existing Hatchling build backend

**Trade-off:** Since `pyproject.toml` has `dynamic = ["version"]`, release-please cannot update a version field there. Instead, release-please updates the `__init__.py` fallback and tracks the version in `.release-please-manifest.json`.

### Commit Validation: commitizen

To ensure commits are well-formed for release-please to parse:

- **commitizen** (Python) validates commit messages via a pre-commit hook (`commit-msg` stage)
- **CI workflow** (`commit-lint.yml`) validates all commits in a PR as a safety net
- Chosen over **commitlint** (Node.js) because: Python-native, provides `cz commit` interactive helper, configurable via `pyproject.toml`, no Node.js dependency

## Decision

Use **release-please** for automated release management, **hatch-vcs** for version derivation, and **commitizen** for commit message validation.

### Complete Flow

```
1. Developer creates feature branch, makes conventional commits
   └─ commitizen pre-commit hook validates each commit message locally
   └─ Commits include (#PR) or (#issue) references for traceability

2. Developer opens PR → PR description is for human reviewers
   └─ CI validates all commit messages (commit-lint.yml)
   └─ CI runs tests, lint, typecheck

3. Maintainer merges via Rebase+Merge
   └─ Individual commits land on main with linear history
   └─ Each conventional commit is individually readable

4. release-please scans new commits on main
   └─ Determines version bump: feat→minor, fix→patch, BREAKING→major
   └─ Creates/updates a Release PR with:
       • Updated CHANGELOG.md (generated from commits)
       • Updated __init__.py fallback version
       • Updated .release-please-manifest.json
   └─ The Release PR is EDITABLE — clean up entries before merging

5. Maintainer merges Release PR
   └─ release-please creates git tag (e.g., v1.2.0)
   └─ release-please creates GitHub Release with CHANGELOG as notes

6. Tag triggers release.yml
   └─ hatch-vcs reads tag → package version is correct
   └─ Builds sdist + wheel
   └─ Publishes to PyPI (if PUBLISH_TOKEN is configured)
   └─ Generates SBOMs
   └─ Uploads artifacts to the GitHub Release
```

### CHANGELOG Format

release-please generates entries from conventional commits. With rebase+merge, each individual commit becomes its own CHANGELOG entry:

```markdown
## [1.2.0](https://github.com/owner/repo/compare/v1.1.0...v1.2.0) (2026-03-15)

### Features

- add user authentication module (#42)
- add login CLI command (#42)
- add password hashing utility (#43)

### Bug Fixes

- handle empty username in auth flow (#44)
- correct token expiration calculation (#44)
```

Only user-facing commit types appear (`feat:`, `fix:`, `perf:`, `revert:`). Internal types (`docs:`, `refactor:`, `test:`, `ci:`, `chore:`, `style:`, `build:`) are hidden by default — configured in `release-please-config.json`.

## Consequences

### Positive

- **Zero manual release steps** — merging the Release PR does everything
- **Reviewable releases** — the Release PR is editable before merge
- **No CHANGELOG conflicts** — generated from commits, never hand-edited
- **SemVer enforced** — version bumps derived from commit types, not human judgment
- **Fine-grained entries** — rebase+merge preserves individual commits in CHANGELOG
- **Traceability** — commits reference PRs, PRs reference issues, CHANGELOG references commits

### Negative

- **Commit discipline required** — every commit message on main matters for CHANGELOG
- **Additional workflow file** — release-please.yml added to CI
- **Google dependency** — release-please is maintained by Google; could change direction
- **Two version sources** — hatch-vcs (authoritative at build) vs **init**.py fallback (human-readable)
- **Initial tag needed** — hatch-vcs needs a `v0.1.0` tag to derive version; without it, falls back to `0.0.0+unknown`

### Files Changed

- `pyproject.toml` — hatch-vcs build plugin, dynamic version, commitizen config
- `src/simple_python_boilerplate/__init__.py` — imports from generated `_version.py`
- `.gitignore` — excludes generated `_version.py`
- `.github/workflows/release-please.yml` — new workflow
- `.github/workflows/commit-lint.yml` — new workflow
- `.github/workflows/release.yml` — updated to upload to existing GitHub Release
- `.pre-commit-config.yaml` — commitizen hook replaces conventional-pre-commit
- `release-please-config.json` — release-please configuration
- `.release-please-manifest.json` — version tracking
- `CHANGELOG.md` — reformatted for release-please

## References

- [release-please documentation](https://github.com/googleapis/release-please)
- [hatch-vcs documentation](https://github.com/ofek/hatch-vcs)
- [commitizen documentation](https://commitizen-tools.github.io/commitizen/)
- [Conventional Commits specification](https://www.conventionalcommits.org/)
- [ADR 022 — Rebase+merge strategy](022-rebase-merge-strategy.md)
