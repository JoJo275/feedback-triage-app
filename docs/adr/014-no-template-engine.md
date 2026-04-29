# ADR 014: No Jinja templates — ship static HTML

## Status

Superseded by [ADR 051: Static HTML + Vanilla JS Frontend](051-static-html-vanilla-js.md).

> **Note on this file:** the original (template-era) decision was about
> repository-scaffolding template engines (Cookiecutter / Cruft / Copier),
> not runtime web templates. That historical reasoning is preserved
> below because it still explains why the repository is a real runnable
> project instead of a placeholder skeleton — useful context for
> downstream forks. The live runtime-frontend decision lives in
> [ADR 051](051-static-html-vanilla-js.md).

---

## Original (template-era) Context

This repository was originally a template that users cloned or generated
via GitHub's "Use this template" feature. Several tools exist to
automate that customisation:

| Tool                     | Approach                                                 | Upstream sync    | Notes                                                         |
| ------------------------ | -------------------------------------------------------- | ---------------- | ------------------------------------------------------------- |
| **Cookiecutter**         | Jinja2 templating; prompts at generation time            | None built-in    | Most popular; one-shot generation, no update path             |
| **Cookiecutter + Cruft** | Cookiecutter for generation, Cruft for upstream updates  | Yes (diff-based) | Adds update capability but couples users to the template repo |
| **Copier**               | Jinja2 templating with built-in update/migration support | Yes (native)     | Modern alternative; supports answer files and migrations      |

### Advantages of a template engine

- Users answer prompts (project name, license, features) and get a
  ready-to-go repo.
- Conditional includes can strip entire features.
- Upstream template changes can be pulled in later (Cruft, Copier).

### Disadvantages of a template engine

- **Template syntax pollutes the source.** Every file becomes a Jinja2
  template, making the repo harder to read, lint, and test as a real
  project.
- **Higher contributor barrier.** Contributors must understand the
  templating layer in addition to the project itself.
- **Higher maintenance burden.** Prompts, conditional logic, and answer
  files all need ongoing maintenance.
- **Specialised tooling knowledge required.** At least one maintainer
  must understand Cookiecutter+Cruft or Copier in detail.
- **Fragile upstream sync.** Cruft and Copier updates can produce
  painful merge conflicts on the structural changes templates tend to
  make.
- **Over-engineering.** Most users clone a template once and never pull
  upstream changes.
- **GitHub "Use this template" already works.** No extra tooling
  required for a clean copy.
- **Testing burden.** Every combination of template options must be
  tested.

## Original Decision

Do not use Cookiecutter, Cruft, Copier, or any other template engine.
Users customised the repository manually. The repository was maintained
as a **working, runnable project** — not a meta-template full of
placeholders.

## Why this is now Superseded

`feedback-triage-app` is no longer a template — it's a product. The
"don't make it a meta-template" decision is moot. The substantive
decision that survives, framed for the new project, is the
runtime-frontend one:

- **No Jinja2 inside the FastAPI app.** The frontend is plain static
  HTML served via `StaticFiles` + vanilla JS calling the JSON API.
  Documented in [ADR 051](051-static-html-vanilla-js.md).
- **One templated surface remains:** the MkDocs docs site
  ([ADR 020](020-mkdocs-documentation-stack.md)). That's a build-time
  generator, not a runtime concern.

## Consequences (still applicable)

### Positive

- The repo is a real, working project — CI passes, tests run, no
  templating layer to learn or maintain.
- No dependency on Cookiecutter / Copier / Cruft.
- The runtime app has no template engine to render or escape — fewer
  XSS surfaces, no auto-escape footguns.

### Negative

- No automated prompt-driven customisation; the
  [`scripts/customize.py`](../../scripts/customize.py) helper plus
  documentation fills that gap for downstream forks.
- No mechanism to pull upstream improvements into derived projects.

### Neutral

- If demand for a template engine grows in the future (either
  repo-scaffolding via Copier, or runtime HTML rendering via Jinja),
  either could be adopted without breaking the current setup, behind
  a fresh ADR.

## See also

- [ADR 051](051-static-html-vanilla-js.md) — the live runtime-frontend
  decision
- [ADR 020](020-mkdocs-documentation-stack.md) — MkDocs Material as the
  one templated surface
