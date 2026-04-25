# ADR 011: Repository guard pattern for optional workflows

## Status

Accepted

## Context

This is a template repository. When someone creates a new project from this template (or forks it), all GitHub Actions workflows are copied over. Many workflows require additional setup (secrets, tokens, external services) that new users haven't configured yet.

Problems without a guard:

- Workflows fail immediately on forks/clones with confusing error messages
- Users waste Actions minutes on workflows they haven't set up
- Some workflows (e.g., PyPI publish, Codecov) may expose configuration issues publicly

Options considered:

- **Disable all optional workflows by default** — Rename files with `_` prefix or put in a `disabled/` folder. Users must manually enable each one.
- **Use `workflow_dispatch` only** — No automatic triggers; users must manually run each workflow. Loses the automation benefit.
- **Repository guard `if:` condition** — Workflows exist and have proper triggers but skip execution unless the repo matches a known slug or opt-in variable is set.

## Decision

Use a repository guard pattern in all optional workflows. Each workflow job includes an `if:` condition that checks one of three opt-in methods:

```yaml
if: >-
    ${{
      github.repository == 'YOURNAME/YOURREPO'
      || vars.ENABLE_WORKFLOWS == 'true'
      || vars.ENABLE_<WORKFLOW_NAME> == 'true'
    }}
```

### Three ways to opt in

| Method       | How                                                                                         | Best for                                            |
| ------------ | ------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| **Option A** | Replace `YOURNAME/YOURREPO` with your repo slug in the YAML (or run `scripts/customize.py`) | Simple, permanent                                   |
| **Option B** | Set `vars.ENABLE_WORKFLOWS = 'true'` repository variable                                    | Enable **all** workflows at once with no YAML edits |
| **Option C** | Set `vars.ENABLE_<WORKFLOW> = 'true'` repository variable                                   | Granular control over individual workflows          |

Options B and C can be combined — `ENABLE_WORKFLOWS` activates everything,
then individual `ENABLE_<WORKFLOW>` variables can be used if only some
workflows are desired (without the global variable).

## Consequences

### Positive

- Workflows are visible and well-documented from day one — users can read them to understand what's available
- No file renaming or directory juggling needed to enable/disable
- Guards are self-documenting with TODO comments explaining both options
- Repository variables (Option B) allow enabling/disabling without code changes
- Workflows don't fail on forks — they silently skip

### Negative

- Every optional workflow needs the boilerplate guard condition
- Template users must remember to opt in (guards block execution by default)
- The `YOURNAME/YOURREPO` placeholder can be confusing if not updated

### Neutral

- Core workflows (test, lint) don't need guards — they should always run
- The pattern is consistent across all optional workflows in this template
