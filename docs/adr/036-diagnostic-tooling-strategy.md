# ADR 036: Diagnostic Tooling Strategy (Doctor Scripts and Profiles)

## Status

Accepted

## Context

As the project's tooling grew, so did the number of things that could go
wrong in a contributor's environment: wrong Python version, missing Hatch
env, stale pre-commit hooks, misconfigured git settings, drifted repo
structure. Rather than documenting every potential issue in a
troubleshooting guide and hoping people read it, the project needed
automated diagnostic tools that check for problems and report them.

Three different concerns emerged:

1. **Environment health** — Is Python installed? Is Hatch working? Are
   pre-commit hooks installed? Is the package importable?
2. **Git configuration health** — Are recommended git settings applied?
   Are hooks installed? Is the commit template set?
3. **Repository structure health** — Do expected files exist? Are configs
   valid? Is documentation in sync?

These concerns have different audiences, trigger conditions, and
remediation paths — one tool trying to do all three would be unwieldy.

## Decision

Split diagnostics across three focused tools, each with a clear domain:

### 1. `env_doctor.py` — Environment diagnostics

Checks the local development environment: Python version, Hatch
installation, virtual environment health, pre-commit hook state,
package importability. Run after cloning or when something "doesn't
work."

### 2. `git_doctor.py` — Git configuration diagnostics

Maintains a curated catalog of 62 git config keys with recommended
values. Checks current settings against the catalog, reports drift,
and can apply fixes. Generates `git-config-reference.md` as an
editable configuration-as-code artifact.

### 3. `repo_doctor.py` — Repository structure diagnostics

Uses a profile-based rule system (`repo_doctor.d/*.toml`) to check
that expected files exist, required sections are present, and project
conventions are followed. Profiles are organized by concern (CI,
docs, security, Python, container, database).

### Shared conventions

- All three tools follow the script conventions in [ADR 031](031-script-conventions.md)
- All support `--quiet` for CI and `--dry-run` where applicable
- All use exit code 0 for pass, 1 for failures
- `doctor.py` is a lightweight wrapper that runs `env_doctor.py` and
  collects environment metadata for bug reports

### Profile system (`repo_doctor.d/`)

Repository structure checks are defined in TOML profiles rather than
hardcoded in the script:

```
repo_doctor.d/
├── ci.toml        # GitHub Actions, CI gate
├── container.toml # Containerfile, docker-compose, devcontainer
├── db.toml        # Database schema, migrations, seeds
├── docs.toml      # MkDocs, ADRs, design docs
├── python.toml    # pyproject.toml, src/ layout, tests/
├── security.toml  # SECURITY.md, scanning configs
└── README.md      # Profile conventions
```

This makes checks data-driven: template users add or remove profiles
without modifying Python code.

## Alternatives Considered

### Single monolithic doctor script

One script checks everything: environment, git, and repo structure.

**Rejected because:** The three domains have different update cadences,
different audiences (git_doctor is useful even outside this project),
and different complexity levels. Splitting keeps each tool focused and
independently usable.

### No profile system — hardcode all checks

Put all repo structure checks directly in the script.

**Rejected because:** Template users have different components (some
keep the database scaffolding, others strip it). Profiles let users
delete `db.toml` without editing Python code. Adding new check
categories is a TOML file, not a code change.

### Use an existing tool (pre-commit, CI checks only)

Rely on pre-commit hooks and CI to catch issues.

**Rejected because:** Pre-commit and CI catch code issues, not
environment misconfigurations. A developer with the wrong Python
version or missing Hatch env needs a diagnostic tool that runs
before pre-commit is even installable.

## Consequences

### Positive

- Contributors can self-diagnose issues without asking for help
- CI can run repo_doctor with `--strict` as a structural lint gate
- Profile system makes checks extensible without code changes
- git_doctor doubles as a git configuration learning tool via the
  generated reference

### Negative

- Three tools to maintain instead of one
- Profile TOML format is project-specific (no standard)
- New contributors may not know which doctor to run

### Mitigations

- `doctor.py` wrapper bundles the most common checks
- `bootstrap.py` runs env_doctor automatically
- README and troubleshooting docs point to the right tool

## Implementation

- [scripts/doctor.py](../../scripts/doctor.py) — Diagnostics bundle wrapper
- [scripts/env_doctor.py](../../scripts/env_doctor.py) — Environment diagnostics
- [scripts/git_doctor.py](../../scripts/git_doctor.py) — Git configuration diagnostics
- [scripts/repo_doctor.py](../../scripts/repo_doctor.py) — Repository structure diagnostics
- [repo_doctor.d/](../../repo_doctor.d/) — TOML check profiles
- [git-config-reference.md](../../git-config-reference.md) — Generated config reference

## References

- [ADR 031: Script conventions](031-script-conventions.md)
- [scripts/README.md](../../scripts/README.md) — Script inventory
