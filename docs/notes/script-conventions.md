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

> **Status (May 2026):** all 17 conventions below are now adopted as
> enforced rules in [`scripts/.instructions.md`](../../scripts/.instructions.md)
> under "Required Script Conventions." This section is preserved for
> rationale; the rule wording in the instructions file is authoritative.
> The exit-code enum lives in [`scripts/_ui.py`](../../scripts/_ui.py)
> as `ExitCode`. Existing scripts are retrofitted opportunistically when
> touched — new scripts must comply on first commit.

### 1. A standard module skeleton

Every CLI script should open in this order so navigation is muscle
memory:

```python
#!/usr/bin/env python3
"""One-line summary.

Longer description.

Usage::
    python scripts/foo.py [--flags]

Exit codes:
    0 = success
    1 = logical failure
    2 = environment failure (missing tool, missing file)
    64 = bad CLI usage
"""

from __future__ import annotations

# 1. stdlib
import argparse
import logging
import sys
...

# 2. third-party
...

# 3. project
from feedback_triage.x import y

# 4. local script modules (underscore-prefixed)
from _imports import find_repo_root, import_sibling
from _ui import UI

# 5. typing-only imports (avoid runtime cost / circular imports)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)

# --- Constants ---
SCRIPT_VERSION = "1.0.0"
THEME = "cyan"
ROOT = find_repo_root()

# --- Helpers ---
def _do_thing(...) -> ...: ...

# --- CLI ---
def _build_parser() -> argparse.ArgumentParser:
    """Build the parser as a separate function so tests can introspect it."""
    parser = argparse.ArgumentParser(
        prog="foo",
        description="...",
        epilog="Examples:\n  python scripts/foo.py --dry-run\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {SCRIPT_VERSION}"
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point. Always returns an int; never calls ``sys.exit`` itself."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(format="%(message)s", level=logging.INFO)
    ...
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

A few rules baked into that skeleton that aren't obvious from glancing
at it:

- **`main(argv=None)` accepts an explicit argv** so tests can invoke
  it without poking `sys.argv`. Never call `sys.argv` from inside
  `main()` — let argparse read from `argv`.
- **`main()` returns an int and only `if __name__ == "__main__"`
  calls `sys.exit`.** Splitting the two lets a script be imported
  (e.g. by a smoke-runner) without exiting the interpreter.
- **`_build_parser()` is its own function**, separate from `main()`.
  Tests can introspect flags, generate completions, or render `--help`
  without running side effects.
- **Exit codes are documented in the module docstring**, not just
  passed back as magic integers. Aligns with convention #3's
  `ExitCode` enum once adopted.
- **`TYPE_CHECKING` block goes after the runtime imports**, not
  scattered. Anything imported there must be referenced as a string
  forward-ref or via `from __future__ import annotations` (which the
  skeleton already enforces).
- **No `__all__`.** Scripts are CLI entry points, not libraries; an
  `__all__` list misleads readers into thinking the module is meant to
  be imported and re-exported.
- **Constants block lives between imports and helpers**, in this order:
  `SCRIPT_VERSION`, `THEME`, `ROOT`, then domain-specific constants.
  Predictable placement makes "what version is this?" a one-glance
  question.
- **Helpers are underscore-prefixed (`_do_thing`) when private to
  the script.** Public-shaped names (`do_thing`) signal "yes, you may
  import this from another script via `import_sibling`."
- **The shebang (`#!/usr/bin/env python3`) is real**, not decorative —
  the `check-shebang-scripts-are-executable` pre-commit hook will fail
  the commit if a shebanged script lacks the executable bit. Set it
  with `git add --chmod=+x scripts/foo.py` on first commit.

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

### 9. One CLI surface per script — no hidden subcommands

If a script grows a second mode that needs more than one or two flags,
split it into a second script rather than adding `argparse` subparsers.
Subcommands hide capabilities behind `--help` digging and complicate
the recommended-scripts registry. Two scripts named for what they do
beat one script with `foo serve` / `foo migrate` / `foo seed`.

### 10. Idempotency by default, destructiveness behind a flag

Running a script twice should leave the system in the same state as
running it once. Anything that destroys data (truncate, force-push,
delete file) must require an explicit flag (`--reset`, `--force`)
*and* refuse to act if the destructive flag is the only signal of
intent. `seed.py`'s "refuse if non-empty unless `--force` or
`--reset`" is the pattern.

### 11. `task` shortcut for every user-facing script

If a human is expected to run it more than once, it gets a Taskfile
entry. Internal scripts (called by other scripts or by CI only) stay
out of `Taskfile.yml` to keep `task --list` short. The litmus test:
"would a new contributor look for this in `task --list`?"

### 12. Shared modules stay shared — don't fork

When two scripts grow the same helper, extract to `_<name>.py` instead
of copy-pasting. The `_`-prefix convention already excludes them from
the command-reference generator. Keep helpers small and single-purpose;
when one starts hosting a class hierarchy, that's a sign it should
move into `src/feedback_triage/` or its own package.

### 13. Output is line-oriented and grep-friendly

Even with `UI` chrome, the load-bearing lines (`PASS`, `FAIL`, the
JSON blob, the file paths) should be on their own lines, prefixable,
and contain no Unicode characters that ASCII grep won't match. Pretty
boxes are *around* the data, not woven into it.

### 14. Errors include the next action

When a script exits non-zero, the last line should tell the caller
what to do — not just what's wrong. "DATABASE_URL not set; export it
or copy `.env.example` to `.env`" beats "DATABASE_URL not set." This
is what turns a script from "tool I run" into "tool that teaches."

### 15. Every script's `--help` shows real examples

`argparse`'s `epilog=` is underused. Two or three concrete invocations
at the bottom of `--help` save more time than a paragraph of prose.

```python
parser = argparse.ArgumentParser(
    description="Seed feedback_item with demo rows.",
    epilog=(
        "Examples:\n"
        "  python scripts/seed.py --dry-run\n"
        "  python scripts/seed.py --reset\n"
        "  python scripts/seed.py --force   # adds duplicates\n"
    ),
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
```

### 16. Color is decoration, never the only signal

`Colors` and `status_icon()` already respect `NO_COLOR`. Make sure the
*meaning* is in the text too — never rely on red-vs-green alone, since
a CI log viewer or color-blind reader sees neither. `status_icon()`
gives you the icon; the icon plus the word ("FAIL: …") is the rule.

### 17. Name boolean flags for the action, not the state

`--no-color` (action) is clearer than `--monochrome` (state).
`--force` (action) beats `--unsafe` (state). Verbs in the flag name
let `--help` read as a list of things the script can do.

---

## Quality-of-life upgrades worth a half-day each

Sized to a single afternoon's work. Pick the one most likely to fail
in production and start there.

| Upgrade | Effort | Payoff |
| --- | --- | --- |
| `scripts/smoke_all.py` runner | S | Catches dead imports and broken constants in every script in one CI step. |
| `ExitCode` enum + adoption pass | S | CI gates can distinguish warnings from failures. |
| `--format json` standardization | M | Lets the dashboard / future tooling consume any script as data. |
| `_env.py` helper for env-var loading | S | One place to mock for tests; one place to document defaults. |
| `_cli.py` with `make_parser(name, version, description)` factory | M | Eliminates the boilerplate ten lines at the top of every script's `main()`. |
| Type-hint `Session` properly in scripts | S | Removes the `session: object` workaround in `seed.py` once mypy config is relaxed for `scripts/`. |
| Single `--config` flag honoring `pyproject.toml` `[tool.scripts.*]` | M | Per-script defaults without env-var sprawl. |
| Coverage on `scripts/` (currently excluded) | M | Surfaces dead code in scripts the same way it does in `src/`. |

---

## Why this lives in two files

- `scripts/.instructions.md` — short, rule-shaped, applied by Copilot
  and pre-commit. Read by tools.
- `docs/notes/script-conventions.md` (this file) — narrative, with
  rationale and trade-offs. Read by humans before *changing* the
  rules.

Cross-link both directions whenever you update either.
