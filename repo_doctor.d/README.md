# repo_doctor.d/ — Optional Profile Rules

<!-- TODO (template users): Add custom profiles for your project's specific
     checks. Modify existing profiles to match your actual file layout. -->

Extra rule sets for `scripts/repo_doctor.py`. These are **not** loaded by
default — activate them on the CLI or in `.repo-doctor.toml`.

## Available Profiles

| Profile     | File             | What it checks                                                       |
| ----------- | ---------------- | -------------------------------------------------------------------- |
| `python`    | `python.toml`    | Packaging, typing, linting, coverage, bandit, editorconfig           |
| `docs`      | `docs.toml`      | MkDocs structure, ADRs, dev guides, standard files, workflows ref    |
| `db`        | `db.toml`        | Schema, migrations, seeds, bootstrap scripts, schema consistency     |
| `ci`        | `ci.toml`        | Workflow hardening, pinning, Dependabot, CI gate, labeler            |
| `container` | `container.toml` | Containerfile hygiene, ignore files, multi-stage, docker-compose     |
| `security`  | `security.toml`  | Security policy, bandit config, secret scanning, audits, env guards  |

## Usage

**CLI (one-off):**

```bash
python scripts/repo_doctor.py --profile python --profile docs
python scripts/repo_doctor.py --profile all          # load every profile
python scripts/repo_doctor.py --profile db --include-info
```

**Config (persistent):** add to `.repo-doctor.toml`:

```toml
[doctor]
profiles = ["python", "docs"]
```

## Adding a New Profile

1. Create `repo_doctor.d/<name>.toml`.
2. Add `[[rule]]` entries using the same schema as `.repo-doctor.toml`.
3. Update the table above.

## See Also

- [scripts/repo_doctor.py](../scripts/repo_doctor.py) — The repo doctor script
- [.repo-doctor.toml](../.repo-doctor.toml) — Base configuration (if exists)
- [scripts/doctor.py](../scripts/doctor.py) — Diagnostics bundle for bug reports
