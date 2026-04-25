# Issue Templates Archive

<!-- TODO (template users): Activate any templates you need by copying them
     to .github/ISSUE_TEMPLATE/. Delete this directory when you're done. -->

This directory stores issue templates that are **not active** in `.github/ISSUE_TEMPLATE/`.

## Active Templates

Only the essential templates live in `.github/ISSUE_TEMPLATE/`:

- `bug_report.yml` — Bug reports
- `feature_request.yml` — Feature requests
- `documentation.yml` — Documentation issues
- `config.yml` — Template chooser configuration

## Archived Templates

### `issue_forms/` — GitHub Issue Forms (YAML)

Additional structured templates (design proposals, performance reports, etc.).
To activate one, copy it to `.github/ISSUE_TEMPLATE/`.

| Template                                                 | Purpose                                       |
| -------------------------------------------------------- | --------------------------------------------- |
| [design_proposal.yml](issue_forms/design_proposal.yml)   | Propose architectural or design changes       |
| [general.yml](issue_forms/general.yml)                   | General-purpose issue                         |
| [other.yml](issue_forms/other.yml)                       | Anything that doesn't fit other categories    |
| [performance.yml](issue_forms/performance.yml)           | Report performance regressions or bottlenecks |
| [question.yml](issue_forms/question.yml)                 | Ask a question about the project              |
| [refactor_request.yml](issue_forms/refactor_request.yml) | Request a code refactor or cleanup            |
| [test_failure.yml](issue_forms/test_failure.yml)         | Report a flaky or failing test                |

### `legacy_markdown/` — Markdown Templates

Older `.md`-based templates. GitHub Issue Forms (`.yml`) are preferred because
they enforce required fields and provide structured input. These are kept for
reference or for repos that prefer the free-form markdown style.

| Template                                                   | Purpose                                   |
| ---------------------------------------------------------- | ----------------------------------------- |
| [bug_report.md](legacy_markdown/bug_report.md)             | Report a bug (markdown version)           |
| [design_proposal.md](legacy_markdown/design_proposal.md)   | Propose design changes (markdown version) |
| [documentation.md](legacy_markdown/documentation.md)       | Report documentation issues               |
| [feature_request.md](legacy_markdown/feature_request.md)   | Request a new feature                     |
| [general.md](legacy_markdown/general.md)                   | General-purpose issue                     |
| [other.md](legacy_markdown/other.md)                       | Anything else                             |
| [performance.md](legacy_markdown/performance.md)           | Performance regression report             |
| [question.md](legacy_markdown/question.md)                 | Ask a question                            |
| [refactor_request.md](legacy_markdown/refactor_request.md) | Request a refactor or cleanup             |
| [test_failure.md](legacy_markdown/test_failure.md)         | Report a flaky or failing test            |

## How to Activate a Template

```bash
cp docs/templates/issue_templates/issue_forms/design_proposal.yml .github/ISSUE_TEMPLATE/
```

Or just drag and drop the file in your code editor.

## See Also

- [.github/ISSUE_TEMPLATE/](../../../.github/ISSUE_TEMPLATE/) — Active issue templates
- [GitHub docs: Configuring issue templates](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository)
