# Attic — Archived Template Code

This directory holds files retained from the original
[`simple-python-boilerplate`](https://github.com/JoJo275/simple-python-boilerplate)
template that the Feedback Triage App was forked from.

Nothing in `attic/` is imported by the running app, included in the wheel, or
considered live code. It is **read-only reference material** for two
audiences:

- The original author, who may want to lift a helper, a comment, or an
  ADR-style snippet back into the project.
- Reviewers comparing the new project's posture against the template's
  conventions.

**Do not import from `attic/` in `src/`, `tests/`, or `scripts/`.** If you
find yourself wanting to, copy the snippet you need into the live tree
explicitly so it shows up in normal lint/type/test passes.

The contents may be deleted in a future cleanup pass without notice.
