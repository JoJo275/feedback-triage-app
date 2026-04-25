# ADR 014: No template engine — manual customisation

## Status

Accepted

## Context

This repository is a template that users clone or generate via GitHub's "Use this template" feature. After creation, users must tailor the boilerplate to their project by removing, keeping, or modifying files and configuration.

Several tools exist to automate this kind of template customisation:

| Tool                     | Approach                                                 | Upstream sync    | Notes                                                         |
| ------------------------ | -------------------------------------------------------- | ---------------- | ------------------------------------------------------------- |
| **Cookiecutter**         | Jinja2 templating; prompts at generation time            | None built-in    | Most popular; one-shot generation, no update path             |
| **Cookiecutter + Cruft** | Cookiecutter for generation, Cruft for upstream updates  | Yes (diff-based) | Adds update capability but couples users to the template repo |
| **Copier**               | Jinja2 templating with built-in update/migration support | Yes (native)     | Modern alternative; supports answer files and migrations      |

### Advantages of a template engine

- Users answer prompts (project name, license, features) and get a ready-to-go repo.
- Conditional includes can strip entire features (e.g., "Do you want SBOM workflows?").
- Upstream template changes can be pulled in later (Cruft, Copier).

### Disadvantages of a template engine

- **Template syntax pollutes the source.** Every file becomes a Jinja2 template (`{{ project_name }}`, `{% if feature_x %}`), making the repo harder to read, lint, and test as a real project.
- **Higher contributor barrier.** Contributors must understand the templating layer in addition to the project itself.
- **Higher maintenance burden.** The template engine configuration, prompts, conditional logic, and answer files all need ongoing maintenance alongside the actual project code.
- **Specialised tooling knowledge required.** At least one maintainer must understand how Cookiecutter+Cruft or Copier works — their config formats, update mechanisms, edge cases, and debugging workflows. This is niche knowledge that not every Python developer has.
- **Fragile upstream sync.** Cruft and Copier updates work well for simple changes but can produce painful merge conflicts on structural changes — the exact kind templates tend to make.
- **Over-engineering for the use case.** Most users clone a template once and never pull upstream changes. The ongoing maintenance cost of a templating layer is not justified by occasional upstream syncs.
- **GitHub "Use this template" already works.** GitHub's native template feature gives users a clean copy with full history control, no extra tooling required.
- **Testing burden.** Every combination of template options must be tested. A matrix of optional features leads to exponential test configurations.

## Decision

Do not use Cookiecutter, Cruft, Copier, or any other template engine. Users customise the repository manually after cloning or using GitHub's "Use this template" button.

The repository is maintained as a **working, runnable project** — not a meta-template full of Jinja2 placeholders. This means:

1. All files are valid, lintable, and testable as-is.
2. Users delete what they don't need (e.g., remove `db/` if no database, remove `sbom.yml` if no SBOM).
3. Users search-and-replace the package name (`simple_python_boilerplate` → their project name).
4. TODO comments and the [USING_THIS_TEMPLATE.md](../USING_THIS_TEMPLATE.md) guide highlight the key customisation points.

## Consequences

### Positive

- The template is a real, working project — CI passes, tests run, linting is clean.
- No templating layer to learn, maintain, or debug.
- Contributors can work on the template as a normal Python project.
- No dependency on external tooling (Cookiecutter, Copier, Cruft).
- GitHub's native "Use this template" is sufficient and requires zero setup.

### Negative

- Users must manually delete files and features they don't want.
- No automated prompt-driven customisation — users must read the docs to know what to change.
- No built-in mechanism to pull upstream template improvements into derived projects. Users who want updates must cherry-pick or manually diff.

### Neutral

- The [USING_THIS_TEMPLATE.md](../USING_THIS_TEMPLATE.md) guide and TODO comments serve as the "customisation prompt" — they tell users what to change, just not automatically.
- If demand for a template engine grows in the future, Copier could be adopted without breaking the existing manual workflow (since Copier can work with a real project structure).
