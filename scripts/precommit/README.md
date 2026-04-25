# Pre-commit Scripts

<!-- TODO (template users): Replace or remove the example hook and add
     hooks specific to your project. Update the Contents table and
     ADR 008 when adding or removing hooks. -->

Custom [pre-commit](https://pre-commit.com/) hooks used by this project.

These scripts are called from `.pre-commit-config.yaml` under the `repo: local` section.

## Contents

| Script                                   | Hook ID        | Stage      | Description                                       |
| ---------------------------------------- | -------------- | ---------- | ------------------------------------------------- |
| [check_nul_bytes.py](check_nul_bytes.py) | `no-nul-bytes` | pre-commit | Fail if any staged file contains NUL (0x00) bytes |

## Adding a New Hook

1. Create a Python script in this directory (e.g., `check_something.py`)
2. Make it executable: `git add --chmod=+x scripts/precommit/check_something.py`
3. Add a shebang line: `#!/usr/bin/env python3`
4. Register it in `.pre-commit-config.yaml` under the `repo: local` section:

    ```yaml
    - repo: local
      hooks:
          - id: check-something
            name: Check something
            entry: scripts/precommit/check_something.py
            language: python
            types: [text]
    ```

5. Update this README with the new hook
6. Update the hook inventory in [ADR 008](../../docs/adr/008-pre-commit-hooks.md)

## Conventions

- **Exit code 0** = pass, **non-zero** = fail
- Accept filenames as positional arguments (pre-commit passes staged files)
- Use `argparse` for **all** argument parsing — including positional file
  arguments — to get `--help` for free and stay consistent with the
  [script conventions](../README.md#conventions)
- Include `SCRIPT_VERSION = "x.y.z"` and a `--version` flag
- Include a module-level docstring explaining what the hook checks
- Print clear error messages with filename and line number when possible
- Wrap execution in `if __name__ == "__main__":` so the hook can be
  imported for testing without side effects

## See Also

- [.pre-commit-config.yaml](../../.pre-commit-config.yaml) — Hook configuration
- [ADR 008](../../docs/adr/008-pre-commit-hooks.md) — Pre-commit hook inventory
