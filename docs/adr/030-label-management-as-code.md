# ADR 030: Label Management as Code

## Status

Accepted

## Context

GitHub labels are used for issue triage, PR categorization, and workflow
automation (e.g., the labeler workflow auto-applies labels based on changed
files). Without a defined strategy, labels drift: different contributors create
ad-hoc labels with inconsistent names, colors, and descriptions, making
filtering and automation unreliable.

### Forces

- Labels must be reproducible — a new fork or template instance should get
  the same label set without manual setup
- The labeler workflow and PR templates reference specific label names; if
  labels are missing, automation silently fails
- GitHub's default labels are a reasonable starting point but insufficient
  for a project with structured workflows
- Labels should be reviewable and version-controlled like any other
  project configuration

## Decision

Manage labels as **JSON files** in a `labels/` directory, applied via a
script (`scripts/apply_labels.py`) and a shell wrapper
(`scripts/apply-labels.sh`).

### File structure

```
labels/
├── baseline.json    # Core labels (mirrors GitHub defaults + project needs)
└── extended.json    # Additional labels for mature projects
```

### JSON format

Each file contains an array of label objects:

```json
[
    {
        "name": "bug",
        "description": "Something isn't working",
        "color": "d73a4a"
    }
]
```

### Label taxonomy

**Baseline labels** (always applied) cover:

- **Type:** `bug`, `enhancement`, `documentation`, `question`
- **Triage:** `duplicate`, `invalid`, `wontfix`, `good first issue`,
  `help wanted`
- **Automation:** `dependencies`, `github_actions` (used by Dependabot
  and the labeler workflow)

**Extended labels** (optional, for teams that want finer granularity) add:

- **Priority:** `priority: critical`, `priority: high`, `priority: medium`,
  `priority: low`
- **Status:** `status: in-progress`, `status: blocked`, `status: needs-review`
- **Area/scope** labels for larger projects

### Application

```bash
# Apply baseline labels
python scripts/apply_labels.py baseline

# Apply extended labels
python scripts/apply_labels.py extended

# Via shell wrapper (for CI)
./scripts/apply-labels.sh
```

The script uses the GitHub CLI (`gh`) to create or update labels. It is
idempotent — running it multiple times produces the same result.

### Automation integration

- **`.github/labeler.yml`** — auto-labels PRs based on changed file paths
- **`.github/workflows/labeler.yml`** — runs the labeler on PR events
- **Issue templates** — suggest labels in the template frontmatter

## Alternatives Considered

### GitHub's default labels only

Rely on the labels GitHub creates automatically for new repositories.

**Rejected because:** Defaults are generic and don't include labels needed
for automation (`dependencies`, `github_actions`) or team workflow
(`priority:`, `status:`). No version control, no reproducibility.

### Labels defined in a workflow

Define labels directly in a GitHub Actions workflow using `gh label create`.

**Rejected because:** Scatters label definitions across workflow YAML files.
JSON files are easier to read, diff, and maintain. The script approach
separates data (JSON) from logic (Python).

### YAML label files

Use YAML instead of JSON for label definitions.

**Rejected because:** JSON is sufficient for this flat data structure and
doesn't require a YAML parser dependency. JSON is also natively supported
by GitHub's API response format, making round-tripping easier.

### github-label-sync (npm package)

Use the `github-label-sync` npm tool to manage labels.

**Rejected because:** Adds a Node.js dependency to a Python project. The
custom script is ~50 lines and uses `gh` CLI, which is already available
in CI environments and recommended by other project tooling.

## Consequences

### Positive

- Labels are version-controlled — changes are reviewable in PRs
- Reproducible — new forks/instances get the correct label set automatically
- Idempotent — safe to re-run at any time
- Two-tier system (baseline + extended) lets teams choose their complexity level
- JSON format is simple, widely understood, and diff-friendly

### Negative

- Requires `gh` CLI to be installed and authenticated
- Label changes require running the script — no auto-sync on push
- Deleting a label from JSON doesn't delete it from GitHub (additive only)

### Mitigations

- `gh` is pre-installed in GitHub Actions runners and commonly available
  locally
- The Taskfile provides a `task labels:baseline` shortcut for easy application
- Additive-only behavior is safer — accidental deletions are prevented

## Implementation

- [labels/baseline.json](../../labels/baseline.json) — Core label definitions
- [labels/extended.json](../../labels/extended.json) — Extended label set
- [scripts/apply_labels.py](../../scripts/apply_labels.py) — Label application script
- [scripts/apply-labels.sh](../../scripts/apply-labels.sh) — Shell wrapper
- [docs/labels.md](../../docs/labels.md) — Label documentation

## References

- [GitHub REST API — Labels](https://docs.github.com/en/rest/issues/labels)
- [GitHub CLI (`gh label`)](https://cli.github.com/manual/gh_label)
