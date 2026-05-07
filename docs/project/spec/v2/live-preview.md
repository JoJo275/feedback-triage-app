# Local live-preview loop

> **Scope:** how to edit a CSS token, a template, a route, or a JS
> file and **see the change in your browser without opening a PR or
> waiting on Railway**. This is the everyday inner-loop workflow —
> the "tweak `--color-primary` and watch the page repaint" doc.
>
> **Audience:** anyone changing visible behaviour locally. Read
> [`theming.md`](theming.md) for *what* to edit; this file covers
> *how to see the result fast*.

---

## TL;DR — one terminal, one command

```powershell
task dev:all
```

That runs three things in the right order:

1. `task build:css` — one-shot Tailwind build so the first request
   renders correctly.
2. `uv run fastapi dev …` — FastAPI in **dev mode**, which auto-reloads
   on Python and template changes.
3. `task watch:css` — Tailwind in watch mode, rebuilding `app.css`
   on every save under `static/css/` and `templates/`.

Open <http://127.0.0.1:8000/> (or `/styleguide` for the design
sandbox), edit, **save**, hit reload. That's the whole loop.

If `task dev:all` is too noisy in one terminal, run `task dev` in
one and `task watch:css` in a second — same outcome, two panes.

---

## What auto-reloads, what you must reload

| Change                                              | Server restart? | Browser reload? |
| --------------------------------------------------- | --------------- | --------------- |
| `static/css/*.css` (tokens, components, effects, …) | no              | **yes** (Ctrl+R) |
| `tailwind.config.cjs`                               | no              | **yes**          |
| `templates/**/*.html` (Jinja)                       | no              | **yes**          |
| `static/js/*.js`                                    | no              | **yes** (hard reload — Ctrl+Shift+R — to dodge cache) |
| `static/img/*` (favicon, wordmark)                  | no              | **yes** (hard reload) |
| `src/feedback_triage/**/*.py`                       | **yes** (FastAPI reloads automatically) | yes |
| `pyproject.toml` deps                               | run `uv sync`, then restart `task dev:all` | yes |
| Alembic migration                                   | run `task migrate` in a second terminal; no restart needed | yes |
| `.env` values                                       | restart `task dev:all` | yes |

Templates and CSS never need a server restart — Jinja reloads on each
request in dev mode, and `app.css` is just a static file.

---

## The fast feedback loop for CSS

Concrete sequence for a CSS-token tweak:

1. `task dev:all` running in a terminal.
2. Open `/styleguide` — it shows every component in every state, so
   one reload validates a token change against the whole vocabulary.
3. Edit `src/feedback_triage/static/css/tokens.css`. Save.
4. The watcher prints `Done in <ms>` to the terminal. If it doesn't,
   the build broke — read the error in that pane.
5. Reload the browser. The new color/radius/shadow is live.

Steps 3–5 take about a second. There is no Railway round-trip and
no PR involved.

> **Don't edit `app.css` directly.** It's the build artifact and is
> gitignored. Edit the charter files (`tokens.css`, `base.css`,
> `layout.css`, `components.css`, `effects.css`) — see the table at
> the top of [`theming.md`](theming.md) for which one owns what.

### Try a preset without editing tokens

`/styleguide` ships with a four-way preset switcher
(`production`, `basic`, `unique`, `crazy` — see ADR 056). The
choice is scoped to that page only and persisted in
`localStorage` under `styleguide-theme`. Use it to A/B-eyeball a
palette change before you commit to editing `tokens.css`.

---

## The fast feedback loop for HTML / templates

1. `task dev:all` running.
2. Edit a `.html` file under `src/feedback_triage/templates/`. Save.
3. Reload the browser. Done.

Jinja in dev mode disables template caching, so the next request
re-parses the file. No watcher, no restart.

If a layout change spans multiple partials, hit the page that
includes them — `/styleguide` and `/inbox` between them cover
most components.

---

## The fast feedback loop for Python / routes

1. `task dev:all` running.
2. Edit `src/feedback_triage/**/*.py`. Save.
3. The terminal logs `WARNING: WatchFiles detected changes …` and
   reboots Uvicorn — usually under a second.
4. Reload the browser.

If the reload silently dies (Uvicorn exits, no new banner), the
file has a syntax or import-time error. Read the traceback in the
terminal, fix it, save again — the watcher recovers.

---

## Verifying without a deploy

Before pushing, run the same gate CI runs:

```powershell
task check          # lint + typecheck + tests + build:css
task test:e2e       # Playwright smoke (optional, gated)
```

`task check` rebuilds `app.css` from scratch, so a passing run is
the local-equivalent of "what Railway will see after deploy". If
`task dev:all` looked right and `task check` is green, the visual
will look the same in production.

---

## Common snags

| Symptom                                              | Likely cause                                                   | Fix                                                                  |
| ---------------------------------------------------- | -------------------------------------------------------------- | -------------------------------------------------------------------- |
| Edited `tokens.css`, page didn't change              | Watcher not running                                            | Start `task watch:css` (or use `task dev:all`).                      |
| Edited `app.css` directly, change vanished           | `app.css` is generated; watcher overwrote your edit            | Edit the source charter file instead. See [`theming.md`](theming.md). |
| Browser shows old CSS even after rebuild             | Browser disk cache                                             | Hard reload (Ctrl+Shift+R), or open DevTools → Network → Disable cache. |
| `task dev` crashes on boot with `app.css not found`  | First run; Tailwind never built the bundle                     | `task build:css` once, then `task dev:all`.                          |
| Tailwind class works on `/styleguide` but not on a new page | New page's template path isn't in Tailwind's `content` glob | Check `tailwind.config.cjs` `content:` — should already cover `templates/**/*.html`. |
| Token change applied in light mode, broke dark mode  | Forgot to override the same token in `:root[data-theme="dark"]` | Add the override; see [`theming.md`](theming.md) "How to change a color". |
| Python edit didn't reload                            | Editor saved to a different path (auto-save vs. workspace)     | Confirm the file on disk changed (`git status`).                     |
| Migration ran in CI but local DB out of date         | Forgot `task migrate` after pulling                            | `task migrate`; restart `task dev:all` if the model classes changed.  |

---

## What this doc is **not**

- **Not a production-deploy guide.** See
  [`rollout.md`](rollout.md) and `railway.toml` for that.
- **Not a styling decision guide.** See
  [`css.md`](css.md) for rules and [`theming.md`](theming.md) for
  recipes.
- **Not a styleguide page spec.** See
  [ADR 056](../../../adr/056-style-guide-page.md) and
  PR 4.2 / PR 4.5 in [`implementation.md`](implementation.md).

---

## Cross-references

- [`theming.md`](theming.md) — which file owns which token / class
- [`css.md`](css.md) — the four-file CSS architecture and its rules
- [`tooling.md`](tooling.md) — Tailwind Standalone CLI rationale
- [`Taskfile.yml`](../../../../Taskfile.yml) — `dev`, `dev:all`,
  `build:css`, `watch:css`, `check`
