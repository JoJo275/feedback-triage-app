# ADR 037: Git Configuration as Code

## Status

Accepted

## Context

Git has 500+ configuration keys, most with sensible defaults but many
that meaningfully affect daily workflow (rebase vs merge on pull, pruning
stale branches, diff algorithm, commit signing). Teams spend time
debugging inconsistent behavior caused by different git configurations
across developers' machines.

The project needed a way to:

1. Document which git settings are recommended and why
2. Let developers review and apply settings declaratively
3. Provide a curated subset for first-time setup
4. Generate a human-readable reference that doubles as documentation

## Decision

Manage git configuration declaratively through `git_doctor.py` and a
Markdown reference file (`git-config-reference.md`).

### Curated catalog

The script maintains a catalog of 62 commonly used git config keys
across 17 sections. Each entry has:

- Technical description (one line)
- Beginner-friendly explanation (blockquote)
- Recommended value and scope
- Valid values and scopes
- Current value (populated at export time)
- Desired value/scope (editable by the user)

### Workflow

```bash
# Generate the reference file (captures current values)
python scripts/git_doctor.py --export-config

# Edit git-config-reference.md — set Desired value + Desired scope

# Preview changes
python scripts/git_doctor.py --apply-from git-config-reference.md --dry-run

# Apply changes
python scripts/git_doctor.py --apply-from git-config-reference.md
```

### Presets

Two preset modes for convenience:

| Preset                        | Keys | Use case                   |
| :---------------------------- | ---: | :------------------------- |
| `--apply-recommended`         |   62 | Full catalog baseline      |
| `--apply-recommended-minimal` |   12 | Core high-impact keys only |

Both support `--dry-run` for previewing.

### Why Markdown (not TOML/YAML)

The reference file uses Markdown tables because:

- It renders nicely on GitHub and in documentation
- It is human-readable without tooling
- It serves double duty as documentation and configuration
- Template users can read the explanations alongside the settings

The trade-off is that parsing Markdown tables is more fragile than
structured formats, but the script handles this reliably and validates
that both Desired columns are set before applying.

## Alternatives Considered

### Plain dotfiles (`.gitconfig` template)

Ship a `.gitconfig` file that users copy to their home directory.

**Rejected because:** Overwrites any existing configuration without
visibility into what changed. No explanation of what each setting does.
No per-key control.

### TOML/YAML config file

Store desired git settings in a structured data file.

**Rejected because:** Loses the documentation benefit. Developers would
need to look up what each key does separately. The Markdown format
combines config and docs in one file.

### Only check, never apply

Report drift but require manual `git config` commands to fix.

**Rejected because:** Too much friction. If you know what's wrong and
what the fix is, automating the apply step saves time and reduces errors.

## Consequences

### Positive

- Consistent git configuration across team members
- Self-documenting — the reference file teaches git config concepts
- Declarative — changes are reviewed before applying
- Minimal preset provides a safe entry point for new developers
- Generated file stays current with actual values on each export

### Negative

- Markdown parsing is more fragile than structured formats
- The catalog must be manually curated (new git versions add keys)
- Template users may not realize the reference file is editable

### Mitigations

- Strict validation: both Desired columns must be set; partial entries
  are skipped with clear error messages
- `--dry-run` prevents accidental changes
- Section in the file itself explains the edit-and-apply workflow

## Implementation

- [scripts/git_doctor.py](../../scripts/git_doctor.py) — Config catalog, export, and apply logic
- [git-config-reference.md](../../git-config-reference.md) — Generated reference file
- [ADR 036](036-diagnostic-tooling-strategy.md) — Overall diagnostic architecture

## References

- [git-config documentation](https://git-scm.com/docs/git-config)
- [ADR 036: Diagnostic tooling strategy](036-diagnostic-tooling-strategy.md)
