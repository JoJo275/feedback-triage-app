# Script Conventions — Notes

A human-readable companion to the rules in
[`scripts/.instructions.md`](../../scripts/.instructions.md). The
instructions file is the enforced spec (Copilot reads it via `applyTo`
and pre-commit checks it). This file is the **why** — what's good
about the conventions, where they break down, and what I'd add if I
were starting from scratch.

> **For Copilot / new scripts:** the authoritative rules live in
> [`scripts/.instructions.md`](../../scripts/.instructions.md). Read
> that first when creating a script. This file is supplementary
> rationale.

---

## What the repo currently does well

| Convention | Why it's worth keeping |
| --- | --- |
| `SCRIPT_VERSION = "x.y.z"` constant | Makes `--version` trivial; lets `--smoke` print a tagged line that's grep-able in CI logs. |
| `THEME = "<color>"` per script | Visual distinction between scripts in dashboard output without a heavy theming framework. |
| Shared `_ui.UI` (header / section / kv / footer) | Scripts look like a family. Box-drawing logic lives in one place; you can't drift. |
| `_progress.ProgressBar` + `Spinner` | One opinionated answer for "show progress." Has Unicode/ASCII fallback and CI logging built in. |
| `_imports.import_sibling()` | Avoids forcing scripts to be a real Python package. Underscore prefix excludes them from the command-reference generator. |
| `argparse` everywhere with consistent flags | `--help`, `--version`, `--dry-run`, `--smoke`. Predictable surface. |
| `--smoke` self-check | Each script proves it can be imported and its data structures are consistent, without touching real systems. Cheap CI signal. |
| `logging` for diagnostics, `print()` for primary output | Lets you redirect noise (`2>/dev/null`) without losing the JSON/table the script is *for*. |
| `pathlib.Path` and arg-list `subprocess.run()` | Cross-platform + bandit-clean by default. |
| Per-file ruff ignores for scripts (T20, D) | Lets `print()` and skipped docstrings stay legal in CLIs without weakening the rules for `src/`. |
| `RECOMMENDED_SCRIPTS` registry in `_ui.py` | Single source of truth for "what should I run next?" — keeps the recommendations on every script in sync. |
| Conventional-commits-aware version bumps | Scripts are versioned independently; if you fix a bug in `bootstrap.py` you bump `bootstrap.py`'s `SCRIPT_VERSION`, not the package. |

## Where they're weak

- **`SCRIPT_VERSION` is hand-maintained.** Easy to forget on a bug fix.
  Worth a pre-commit hook that diffs the script and warns if the body
  changed but `SCRIPT_VERSION` didn't.
- **`session: object` workarounds in `seed.py`** (and similar) exist
  only to dodge mypy-strict in scripts. The cleaner answer is to add
  scripts to a relaxed mypy section in `pyproject.toml` rather than
  type-erase parameters.
- **No shared "exit code" convention.** Some scripts use `0/1`, others
  use `0/1/2/3` for warned-vs-failed. A small enum (`ExitCode.OK`,
  `WARN`, `FAIL`, `USAGE`) in `_ui.py` would make CI gating uniform.
- **No structured-output mode.** `--json` exists on a few scripts but
  isn't a convention. CI parses ad-hoc text. A standard `--format
  {text,json}` would let dashboards consume any script.
- **Smoke tests aren't auto-discovered.** Each script has `--smoke`
  but nothing iterates them in CI. A meta-script
  (`scripts/smoke_all.py`) that walks `scripts/*.py` and runs each
  with `--smoke` would catch regressions cheaply.
- **`_ui.UI.footer()` overloads** — different scripts call it with
  positional `(passed, failed, warned)` *or* with keyword args, and
  the type signature accepts both. Pick one.

## Conventions I'd add

These are recommendations, not yet enforced. If we adopt one, move
the line to `scripts/.instructions.md`.

### 1. A standard module skeleton

Every CLI script should open in this order so navigation is muscle
memory:

```python
#!/usr/bin/env python3
"""One-line summary.

Longer description.

Usage::
    python scripts/foo.py [--flags]
"""

from __future__ import annotations

# 1. stdlib
import argparse
import logging
...

# 2. third-party
...

# 3. project
from feedback_triage.x import y

# 4. local script modules (underscore-prefixed)
from _imports import find_repo_root, import_sibling
from _ui import UI

logger = logging.getLogger(__name__)

# --- Constants ---
SCRIPT_VERSION = "1.0.0"
THEME = "cyan"
ROOT = find_repo_root()

# --- Helpers ---
def _do_thing(...) -> ...: ...

# --- CLI ---
def main(argv: list[str] | None = None) -> int: ...

if __name__ == "__main__":
    sys.exit(main())
```

### 2. `--format {text,json}` instead of `--json`

One flag, two values, predictable. JSON output skips `UI` chrome and
emits a single object on stdout for piping.

### 3. Exit-code enum

```python
# _ui.py
class ExitCode(IntEnum):
    OK = 0
    WARN = 1     # ran successfully, surfaced warnings
    FAIL = 2     # logical failure
    USAGE = 64   # bad args (matches sysexits.h)
    INTERNAL = 70
```

Lets `task check` tell "lint warned" from "lint exploded."

### 4. `--quiet` / `--verbose` are universal

Two flags, three levels. Scripts always wire them to logging:

```python
parser.add_argument("-q", "--quiet", action="count", default=0)
parser.add_argument("-v", "--verbose", action="count", default=0)
level = logging.WARNING - 10 * args.verbose + 10 * args.quiet
logging.basicConfig(level=level, format="%(message)s")
```

### 5. Smoke test contract

`--smoke` must:

- Make **no** network or DB calls.
- Validate all module-level constants and data structures.
- Exit `0` on success, print `<name> <SCRIPT_VERSION>: smoke ok`.

A `scripts/smoke_all.py` runner enforces this in CI.

### 6. Side-effect scripts declare a `--dry-run`

If a script writes anywhere (DB, filesystem outside its own output,
remote API), it must accept `--dry-run` and the dry-run path must be
the *default* in unsure cases. `seed.py` and `apply_labels.py` already
do this.

### 7. Long-running steps use `pulse=True`

Steps that may block for >2s without calling `bar.update()` should set
`ProgressBar(..., pulse=True)` so the bar still animates. Avoids the
"is it hung?" problem in CI logs and on slow VMs.

### 8. No `os.environ.get("FOO", "")` scattered around

Env-var reads belong in one helper per script, near the top, with
explicit defaults and types. Easier to mock in `--smoke`.

---

## Why this lives in two files

- `scripts/.instructions.md` — short, rule-shaped, applied by Copilot
  and pre-commit. Read by tools.
- `docs/notes/script-conventions.md` (this file) — narrative, with
  rationale and trade-offs. Read by humans before *changing* the
  rules.

Cross-link both directions whenever you update either.
