# ADR 014: No Jinja templates — ship static HTML

## Status

Superseded by [ADR 051: Static HTML + Vanilla JS Frontend](051-static-html-vanilla-js.md).

## Why this ADR exists

This file was inherited from the `simple-python-boilerplate` template,
where it argued against repository-scaffolding template engines
(Cookiecutter / Cruft / Copier). That framing no longer applies to
`feedback-triage-app` — this is a product, not a template.

The substantive decision that survives the fork is **no Jinja2 in the
runtime web app; the frontend is plain static HTML served via
`StaticFiles` + vanilla JS calling the JSON API**. That decision is
documented in full in [ADR 051](051-static-html-vanilla-js.md).

## Original (template-era) text — for history only

> Do not use Cookiecutter, Cruft, Copier, or any other template engine.
> Users customise the repository manually after cloning or using
> GitHub's "Use this template" button. The repository is maintained
> as a working, runnable project, not a meta-template full of
> placeholders.

That decision is moot post-fork; the template engines being rejected
were repo-generation tools, not runtime web frameworks.

## See also

- [ADR 051](051-static-html-vanilla-js.md) — the live decision
- [ADR 020](020-mkdocs-for-documentation.md) — MkDocs Material is the
  one templated surface that remains (for the docs site)
