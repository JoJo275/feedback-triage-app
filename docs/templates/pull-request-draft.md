<!-- WORKING COPY — edit freely, this does NOT affect .github/PULL_REQUEST_TEMPLATE.md -->
<!-- Use this file to draft your PR description before pasting it into GitHub. -->
<!-- Branch: wip/2026-05-05 -->
<!--
  Suggested PR title (conventional commit format — type: description):

    feat(css): tailwind plumbing + four-file architecture + /styleguide stub

  Available prefixes:
    feat:     — new feature or capability
    fix:      — bug fix
    docs:     — documentation only
    chore:    — maintenance, no production code change
    refactor: — code restructuring, no behavior change
    test:     — adding or updating tests
    ci:       — CI/CD workflow changes
    style:    — formatting, no logic change
    perf:     — performance improvement
    build:    — build system or dependency changes
    revert:   — reverts a previous commit
-->

<!-- Suggested labels: feat, css, frontend, v2.0, phase-1 -->

<!--
  ╔══════════════════════════════════════════════════════════════╗
  ║  This PR description is for HUMAN REVIEWERS.                 ║
  ║                                                              ║
  ║  Release automation (release-please) reads individual        ║
  ║  commit messages on main — not this description.             ║
  ║  Write commits with conventional format (feat:, fix:, etc.)  ║
  ║  and include (#PR) or (#issue) references in each commit.    ║
  ║                                                              ║
  ║  This template captures: WHY you made changes, HOW to test   ║
  ║  them, and WHAT reviewers should focus on.                   ║
  ╚══════════════════════════════════════════════════════════════╝
-->

## Description

PR 1.1 of v2.0 Phase 1 (Alpha). Stands up the Tailwind CSS pipeline,
the four-file CSS architecture from `docs/project/spec/v2/css.md`,
the first Jinja-rendered page, and the `/styleguide` stub. No DB,
no auth, no API changes — pure frontend plumbing so every later
PR has a stylesheet to link to.

**What changes you made:**

- Added `tailwind.config.cjs` (tokens-via-CSS-vars palette,
  `darkMode: 'selector'`, content globs that cover templates,
  static HTML, JS, and route Python).
- Added the four-file CSS architecture under
  `src/feedback_triage/static/css/` (`tokens.css`, `base.css`,
  `layout.css`, `components.css`, `effects.css`) plus the
  thin `input.css` orchestrator.
- Added `scripts/build_css.py` — cross-platform wrapper around
  the Tailwind Standalone CLI. On first run it downloads the
  pinned binary (`v3.4.13`) into `.tools/`, **verifies SHA256**
  against the in-script pin, builds, hashes the output to
  `app.<hash>.css`, and writes `manifest.json` for cache-busting.
  Honors `TAILWINDCSS_BIN` env var so CI can pre-stage the
  binary.
- Added `task setup:css` / `task build:css` / `task watch:css`.
  `task check` now depends on `build:css` so a clean clone
  produces the bundle as part of the gate. `task dev` runs a
  one-shot CSS build before starting the API server.
- Added `src/feedback_triage/templating.py` — single
  `Jinja2Templates` instance plus a `static_url` helper that
  reads `manifest.json` and falls back to the unhashed filename
  when the manifest is missing (so the page still renders before
  someone runs `task build:css`).
- Added `src/feedback_triage/templates/_base.html` (the project's
  first Jinja base template) and `templates/styleguide.html`
  (empty shell, populated as components arrive in later PRs).
- Added `GET /styleguide` to `src/feedback_triage/routes/pages.py`.
- New `builder-frontend` stage in the `Containerfile`: downloads
  Tailwind, builds CSS, and overlays the hashed bundle into the
  wheel-build stage. The runtime image is unchanged — no Tailwind
  binary in production.
- `.gitignore` ignores `.tools/`. `static/css/.gitignore` ignores
  `app.css`, `app.*.css`, and `manifest.json` (all generated).
- New smoke test `test_styleguide_page_renders` confirms the
  `/styleguide` route returns 200, links the hashed CSS, and
  includes the `sn-skip-link`.

**Why you made them:**

`docs/project/spec/v2/css.md` is the authoritative answer for
*"how does CSS work in v2.0?"* — but until this PR there was no
plumbing to back any of it up. This PR is the smallest possible
slice that makes every claim in `css.md` testable: the build
pipeline exists, the file split exists, the dark-mode token
override is wired, the styleguide route returns 200. Later PRs
populate the styleguide and migrate the v1 pages onto the new
shell.

ADR 058 (Tailwind via Standalone CLI) and ADR 056 (style guide
page) prescribe this approach.

## Related Issue

N/A — implementation of `docs/project/spec/v2/implementation.md`
PR 1.1.

## Type of Change

- [x] ✨ New feature (non-breaking change that adds functionality)
- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🔧 Refactor (no functional changes)
- [ ] 🧪 Test update

## How to Test

**Steps:**

1. From a clean clone (or after deleting `.tools/` and
   `src/feedback_triage/static/css/app.*.css`):
   ```powershell
   uv sync
   task build:css
   ```
   Expect: `Downloading Tailwind v3.4.13 …`, then
   `SHA256 verified: …`, then `Wrote app.<hash>.css and manifest.json`.
2. Run the gate:
   ```powershell
   task check
   ```
   Expect: 56 tests pass, mypy + ruff clean, CSS rebuilt as part of
   the gate.
3. Boot the app and visit `/styleguide`:
   ```powershell
   task dev
   ```
   Expect: 200, page background is the slate-50 token, the
   "Token sanity check" card has a soft shadow.

**Test command(s):**

```bash
task check
uv run pytest tests/test_pages.py -v
uv run python scripts/build_css.py --smoke
```

**Screenshots / Demo (if applicable):**

`/styleguide` is intentionally empty in this PR (component rows
land in later PRs). The single visible card is the wiring
sanity-check.

## Risk / Impact

**Risk level:** Low

**What could break:**

- A clean clone with no internet egress to `github.com/tailwindlabs/`
  cannot run `task build:css` until someone pre-stages the binary
  via `TAILWINDCSS_BIN`. CI runners with restricted egress need
  either a cached binary or that env var.
- `task dev` now runs `task build:css` first, so first-boot is
  slower (one-time download on first ever run; ~250 ms thereafter).
- The `Containerfile` grew a new stage; image build time goes up
  by the duration of one CSS build (~1–2 s plus the binary
  download on cold cache).
- The `Browserslist: caniuse-lite is outdated` warning is emitted
  by the Tailwind v3.4.13 binary on every build. It's bundled and
  cosmetic; the only fix is bumping `TAILWIND_VERSION`. Not in
  scope here.

**Rollback plan:** Revert this PR. No data migration, no schema,
no deployed surface change other than the new `/styleguide` URL
(which 404s after revert).

## Dependencies (if applicable)

**Depends on:** Phase 0 (closed 2026-05-04). Ratification of ADR
056 and ADR 058 (both already accepted).

**Blocked by:** N/A.

## Breaking Changes / Migrations (if applicable)

None.

## Checklist

- [x] My code follows the project's style guidelines
- [x] I have performed a self-review of my code
- [x] I have commented my code, particularly in hard-to-understand areas
- [x] I have made corresponding changes to the documentation
- [x] No new warnings (or explained in Additional Notes — see Browserslist note above)
- [x] I have added tests that prove my fix is effective or that my feature works
- [x] Relevant tests pass locally (`task check` green; 56 passed, 3 deselected)
- [x] No security concerns introduced (or flagged for review)
- [x] No performance regressions expected

## Reviewer Focus (Optional)

- `scripts/build_css.py` — confirm the SHA256 verification logic
  reads correctly. The Windows-x64 digest was captured locally
  (TOFU) on 2026-05-05; other platform entries are blank and
  emit a warning until populated by someone building on that
  platform.
- `Containerfile` — confirm the `builder-frontend` stage's
  `COPY` paths line up and that the runtime stage still has no
  Tailwind binary.
- `tailwind.config.cjs` `content` globs — make sure no class-
  emitting source path is missing (current set: templates,
  static HTML, static JS, routes Python).
- `src/feedback_triage/templating.py` — `static_url` falls back
  silently when the manifest is missing; confirm that's the
  desired behavior vs. raising.

## Additional Notes

- **Tailwind binary integrity.** `_PLATFORM_SHA256` in
  `scripts/build_css.py` only has the Windows-x64 digest pinned
  today. Linux/macOS digests are blank and the script logs a
  warning when an unpinned platform downloads. Follow-up: capture
  digests on the Railway build container (linux-x64) and on a
  macOS host, fold them into the same dict.
- **`task dev` + watcher.** Doesn't run the watcher in parallel —
  Task's `cmds` is sequential. Run `task watch:css` in a second
  terminal during dev. Adding a `dev:all` that orchestrates both
  needs a small process supervisor (`concurrently`-equivalent in
  Python, or a tiny `asyncio` runner); deferred.
- **mkdocs `--strict` warning.** `uv run mkdocs build --strict`
  exits 1 on `main` already due to a Material for MkDocs
  framework deprecation notice (MkDocs 2.0). Pre-existing,
  unrelated to this PR.
- **What lands in the next PR (1.2).** Three ADR drafts (062,
  063, 064). Doc-only, no code touch.
