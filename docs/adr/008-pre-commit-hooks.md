# ADR 008: Use pre-commit hooks for automated checks

## Status

Accepted

## Context

Code quality checks (linting, formatting, type checking) can run at several points:

1. **Manually** — Developer runs tools by hand
2. **Pre-commit hooks** — Automatically on `git commit`
3. **CI only** — Checks run in GitHub Actions after push
4. **Editor/IDE** — Real-time feedback while coding

Manual checks are error-prone (easy to forget). CI-only checks provide late feedback (errors found after push). Pre-commit hooks provide immediate, automatic feedback.

## Decision

Use the `pre-commit` framework to run checks automatically at three git stages: `pre-commit` (every commit), `commit-msg` (message validation), and `pre-push` (slower/thorough checks before push). Opt-in `manual` hooks are available for heavier tools.

## Hook Inventory

### Stage: pre-commit (every `git commit`)

| Hook                                   | Source             | What it does                                                                                                                     |
| -------------------------------------- | ------------------ | -------------------------------------------------------------------------------------------------------------------------------- |
| `trailing-whitespace`                  | pre-commit-hooks   | Removes trailing whitespace                                                                                                      |
| `end-of-file-fixer`                    | pre-commit-hooks   | Ensures files end with newline                                                                                                   |
| `check-yaml`                           | pre-commit-hooks   | Validates YAML syntax                                                                                                            |
| `check-toml`                           | pre-commit-hooks   | Validates TOML syntax                                                                                                            |
| `check-json`                           | pre-commit-hooks   | Validates JSON syntax                                                                                                            |
| `check-ast`                            | pre-commit-hooks   | Validates Python syntax (catches SyntaxError)                                                                                    |
| `check-added-large-files`              | pre-commit-hooks   | Prevents files > 500 KB from being committed                                                                                     |
| `check-merge-conflict`                 | pre-commit-hooks   | Detects leftover merge conflict markers                                                                                          |
| `check-case-conflict`                  | pre-commit-hooks   | Detects files that would clash on case-insensitive filesystems                                                                   |
| `debug-statements`                     | pre-commit-hooks   | Catches `import pdb` / `breakpoint()` left in code                                                                               |
| `detect-private-key`                   | pre-commit-hooks   | Blocks private keys from being committed                                                                                         |
| `fix-byte-order-marker`                | pre-commit-hooks   | Removes UTF-8 BOM (causes subtle cross-platform bugs)                                                                            |
| `name-tests-test`                      | pre-commit-hooks   | Enforces `test_*.py` naming in `tests/` and `experiments/`                                                                       |
| `check-executables-have-shebangs`      | pre-commit-hooks   | Executables must have shebangs                                                                                                   |
| `check-shebang-scripts-are-executable` | pre-commit-hooks   | Shebang scripts must be `+x`                                                                                                     |
| `check-symlinks`                       | pre-commit-hooks   | Detects broken symlinks                                                                                                          |
| `destroyed-symlinks`                   | pre-commit-hooks   | Detects symlinks replaced by regular files (e.g. after merge)                                                                    |
| `check-vcs-permalinks`                 | pre-commit-hooks   | Catches GitHub URLs pointing to branches instead of commit SHAs                                                                  |
| `check-docstring-first`                | pre-commit-hooks   | Catches code placed before the module docstring                                                                                  |
| `no-commit-to-branch`                  | pre-commit-hooks   | Prevents direct commits to `main` / `master`                                                                                     |
| `mixed-line-ending`                    | pre-commit-hooks   | Normalises to LF (paired with `.gitattributes`)                                                                                  |
| `ruff`                                 | ruff-pre-commit    | Lint with auto-fix (replaces flake8, isort, pyupgrade, autopep8)                                                                 |
| `ruff-format`                          | ruff-pre-commit    | Format (replaces black)                                                                                                          |
| `mypy`                                 | mirrors-mypy       | Static type checking on `src/` (strict mode — matches CI)                                                                        |
| `bandit`                               | PyCQA/bandit       | Security linting (skips tests)                                                                                                   |
| `validate-pyproject`                   | validate-pyproject | Validates `pyproject.toml` against PEP 621                                                                                       |
| `typos`                                | crate-ci/typos     | Spell checking (Rust-based, fast, broad detection)                                                                               |
| `actionlint`                           | rhysd/actionlint   | Lints GitHub Actions workflow files                                                                                              |
| `check-github-workflows`               | check-jsonschema   | Schema validation for `.github/workflows/`                                                                                       |
| `check-github-actions`                 | check-jsonschema   | Schema validation for action.yml files                                                                                           |
| `check-dependabot`                     | check-jsonschema   | Schema validation for `.github/dependabot.yml`                                                                                   |
| `no-do-not-commit-marker`              | local (pygrep)     | Blocks `@@DO_NOT_COMMIT` `@@` markers                                                                                            |
| `no-secrets-patterns`                  | local (pygrep)     | Blocks hardcoded credentials / token patterns (py, toml, yaml, json, env, ini, cfg, txt, md, sh, ps1, Containerfile, Dockerfile) |
| `no-nul-bytes`                         | local (python)     | Blocks NUL bytes in text files                                                                                                   |
| `deptry`                               | local (system)     | Detects unused, missing, and transitive dependencies                                                                             |
| `check-python-support`                 | local (system)     | Verifies Python version support config is consistent across `pyproject.toml` and CI workflows                                    |
| `auto-chmod-scripts`                   | local (python)     | Auto-runs `git add --chmod=+x` on staged shebang scripts missing the executable bit                                             |
| `check-local-imports`                  | local (python)     | Enforces `# -- Local script modules` comment before local `_`-prefixed imports in scripts                                        |

### Stage: commit-msg (validates the commit message)

| Hook         | Source           | What it does                                           |
| ------------ | ---------------- | ------------------------------------------------------ |
| `commitizen` | commitizen-tools | Validates messages against Conventional Commits format |

### Stage: pre-push (slower checks before `git push`)

| Hook        | Source         | What it does                                                |
| ----------- | -------------- | ----------------------------------------------------------- |
| `tests`     | local (system) | Runs full test suite via `hatch run test`                   |
| `pip-audit` | pypa/pip-audit | Vulnerability scan against OSV / PyPI advisory DB           |
| `gitleaks`  | gitleaks       | Secret detection with 150+ curated rules + entropy analysis |

### Stage: manual (opt-in, run on demand)

| Hook                | Source                   | Why opt-in                                                              |
| ------------------- | ------------------------ | ----------------------------------------------------------------------- |
| `markdownlint-cli2` | DavidAnson               | Node-based; heavier dependency footprint                                |
| `hadolint-docker`   | hadolint                 | Requires Docker; also covered by Trivy misconfig in CI                  |
| `prettier`          | rbubley/mirrors-prettier | Node-based; normalises Markdown table alignment. Scoped to `*.md` only. |
| `forbid-submodules` | pre-commit-hooks         | Only needed if project policy forbids submodules                        |

## Alternatives Considered

### CI-only checks

Run all checks in GitHub Actions, not locally.

**Rejected because:** Late feedback; developers don't see errors until after push; wastes CI resources on obvious issues.

### Husky (Node.js)

Git hooks via npm/Node.js.

**Rejected because:** Adds Node.js dependency to a Python project; pre-commit is Python-native and well-integrated.

### Manual checks

Document commands and trust developers to run them.

**Rejected because:** Easy to forget; inconsistent across team; bad commits reach CI.

## Tool Selection Rationale

### Chosen over alternatives

| Tool chosen                        | Alternatives skipped                                | Why                                                                                                                                                                                                                             |
| ---------------------------------- | --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Ruff** (lint + format)           | flake8, isort, pyupgrade, autopep8, black, prettier | Ruff subsumes all of these in a single Rust binary. Orders of magnitude faster. Also handles YAML/TOML/JSON validation via `check-yaml`/`check-toml`/`check-json`.                                                              |
| **typos** (spellcheck)             | codespell (as a hook)                               | typos is Rust-based, faster, and has broader detection. codespell remains as a CI safety net (`spellcheck.yml`) with its independently curated wordlist — the two overlap ~80 % but each catches things the other misses.       |
| **pip-audit** (vulnerability scan) | safety                                              | pip-audit is the PyPA-maintained successor with OSV database support. safety's free tier has limitations and is no longer the recommended tool.                                                                                 |
| **gitleaks** (secret detection)    | trufflehog, git-secrets                             | gitleaks has 150+ curated rules with entropy detection, is a single Go binary, and is actively maintained. Complements the fast regex-based `no-secrets-patterns` pygrep hook.                                                  |
| **deptry** (dependency hygiene)    | —                                                   | No real alternative in the Python ecosystem. Detects unused, missing, and transitive dependencies by comparing `pyproject.toml` against actual imports. Runs as a local/system hook to access the project's installed packages. |
| **actionlint** (workflow linting)  | —                                                   | The only mature GHA workflow linter. Catches expression errors, unknown runner labels, and missing action inputs before they hit CI.                                                                                            |

### Explicitly not adopted

| Tool                      | Why skipped                                                                                                                                                                                                                                                 |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **prettier**              | ~~Originally skipped.~~ Now included as a **manual** hook scoped to Markdown only (`types_or: [markdown]`). Markdown table alignment is the one formatting gap Ruff and markdownlint can't fill. The Node dependency is acceptable for a manual-stage hook. |
| **pyupgrade**             | Ruff's `UP` rules include all pyupgrade checks. Running both is redundant.                                                                                                                                                                                  |
| **autopep8**              | Same as above — Ruff's formatter and linter cover all autopep8 fixes.                                                                                                                                                                                       |
| **black**                 | `ruff-format` is a drop-in replacement, faster, and configured alongside the linter.                                                                                                                                                                        |
| **isort**                 | `ruff check` with isort rules (`I`) handles import sorting.                                                                                                                                                                                                 |
| **codespell** (as a hook) | typos is faster and broader. codespell runs in CI (`spellcheck.yml`) as a complementary safety net.                                                                                                                                                         |
| **safety**                | pip-audit is the maintained PyPA successor. safety's free tier scans an older database subset.                                                                                                                                                              |
| **Husky**                 | Node.js-based git hooks. Adds a Node dependency to a Python project; pre-commit is Python-native.                                                                                                                                                           |

## Consequences

### Positive

- **Automatic** — No manual step to forget
- **Fast feedback** — Errors caught before commit, not after push
- **Consistent** — Same checks for all developers
- **Prevents bad commits** — Can't commit code that fails checks
- **CI backup** — CI still runs checks for contributors who skip hooks
- **Layered security** — Fast regex secrets check on commit, thorough gitleaks scan on push

### Negative

- **Setup required** — Developers must run `pre-commit install` (+ `--hook-type commit-msg` and `--hook-type pre-push`)
- **Can be bypassed** — `git commit --no-verify` skips hooks
- **Slower commits** — Adds time to commit process (mitigated: most hooks are sub-second)
- **Initial friction** — May block commits until code is fixed
- **deptry requires project venv** — Runs as local/system hook via `hatch run`; won't work in pre-commit's isolated env

### Mitigations

- Document setup in CONTRIBUTING.md
- Keep hooks fast (Ruff and typos are Rust-based, sub-second)
- Move slow hooks to `pre-push` stage (tests, pip-audit, gitleaks)
- CI runs same checks as safety net
- Allow `--no-verify` for WIP commits (CI will catch issues)

## Implementation

- [.pre-commit-config.yaml](../../.pre-commit-config.yaml) — Full hook configuration
- [\_typos.toml](../../_typos.toml) — typos spellchecker config (explicit pointer via `--config`)
- [pyproject.toml](../../pyproject.toml) — `[tool.deptry]` and `[tool.bandit]` configuration; `pre-commit` and `deptry` in dev dependencies
- [CONTRIBUTING.md](../../CONTRIBUTING.md) — Setup instructions for contributors

## References

- [pre-commit documentation](https://pre-commit.com/)
- [pre-commit hooks directory](https://pre-commit.com/hooks.html)
- [Ruff documentation](https://docs.astral.sh/ruff/)
- [typos documentation](https://github.com/crate-ci/typos)
- [deptry documentation](https://deptry.com/)
- [pip-audit documentation](https://github.com/pypa/pip-audit)
- [gitleaks documentation](https://github.com/gitleaks/gitleaks)
- [actionlint documentation](https://github.com/rhysd/actionlint)
