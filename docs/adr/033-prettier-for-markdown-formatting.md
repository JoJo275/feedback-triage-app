# ADR 033: Prettier for Markdown Formatting

## Status

Accepted

## Context

Markdown files across the project (docs, READMEs, ADRs, templates) had
inconsistent formatting — different table alignment, trailing whitespace,
inconsistent line breaks, and varying list indentation. Manual enforcement
doesn't scale with 80+ markdown files, and reviewers shouldn't spend time
on whitespace. Ruff handles Python formatting but doesn't touch Markdown.

We needed an automated markdown formatter that:

- Produces consistent, deterministic output across all `.md` files
- Integrates with pre-commit so formatting is enforced before commit
- Handles tables, lists, code blocks, and frontmatter correctly
- Is widely adopted and well-maintained

## Decision

Use **Prettier** as a pre-commit hook in the `manual` stage for Markdown
formatting across all `.md` files.

**Key configuration choices:**

- **Manual stage** — not `pre-commit`. Markdown formatting is a lower-
  priority concern than code quality hooks. Running 80+ files through
  Prettier on every commit would add noticeable latency. Run it
  explicitly via `task fmt:markdown` or `pre-commit run prettier --all-files`.
- **Prose wrap: preserve** — Prettier won't rewrap paragraph text.
  This avoids noisy diffs and respects intentional line breaks in docs.
- **No `.prettierrc`** — configuration is inline in
  `.pre-commit-config.yaml` via `args:`. One fewer config file to maintain.

**Hook behavior:**

Prettier is a _formatter_, not a _linter_. When pre-commit runs it:

1. Prettier reads each file and reformats it in place
2. If any file changed, pre-commit reports the hook as **Failed** and
   shows "files were modified by this hook"
3. The user re-stages the formatted files and commits again

This "fail-and-fix" pattern is identical to how Ruff format works in
pre-commit — it's expected, not an error.

## Alternatives Considered

### markdownlint-cli2 (already in use)

markdownlint-cli2 is a _linter_ — it flags problems but doesn't auto-fix
most issues. It catches structural problems (heading levels, list
consistency) but doesn't reformat tables or normalize whitespace.

**Not a replacement because:** Linting and formatting are complementary.
markdownlint catches issues Prettier ignores (e.g., duplicate headings)
and vice versa. Both are kept.

### mdformat

Python-based markdown formatter. Smaller ecosystem, fewer users.

**Rejected because:** Prettier is the de facto standard for Markdown
formatting, has better table support, and most developers already
have it in their toolchain from JavaScript/TypeScript work.

### Do nothing

Rely on reviewers to catch formatting inconsistencies.

**Rejected because:** Doesn't scale. 80+ markdown files across docs,
ADRs, templates, and READMEs. Inconsistencies accumulate quickly and
create noisy diffs when someone runs a formatter later.

## Consequences

### Positive

- Consistent Markdown formatting across all files — no more table alignment
  debates
- Deterministic output — same input always produces the same output
- Reduced review noise — formatting is handled automatically
- Works alongside markdownlint-cli2 (linting) for comprehensive Markdown
  quality

### Negative

- Adds Node.js as a transient dependency (Prettier runs via pre-commit's
  `node` environment type, downloaded automatically)
- "Fail-and-fix" pattern can confuse developers who expect green hooks.
  Documented in troubleshooting FAQ.
- Initial run reformats many files, creating a large diff. Best done as a
  standalone `chore:` commit.

### Mitigations

- Manual stage avoids slowing down normal commits
- Documented in troubleshooting FAQ to prevent confusion
- `task fmt:markdown` provides a convenient wrapper

## Implementation

- [`.pre-commit-config.yaml`](../../.pre-commit-config.yaml) — Prettier hook definition (manual stage)
- [`Taskfile.yml`](../../Taskfile.yml) — `fmt:markdown` task wrapping the hook
- [ADR 008](008-pre-commit-hooks.md) — Pre-commit hook inventory (updated)

## References

- [Prettier documentation](https://prettier.io/docs/en/)
- [Prettier Markdown support](https://prettier.io/docs/en/options.html#prose-wrap)
- [pre-commit mirror for Prettier](https://github.com/pre-commit/mirrors-prettier)
