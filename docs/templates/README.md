# Templates

Reusable file templates that you can copy and adapt for your project.

<!-- TODO (template users): After copying the templates you need, you can
     delete this entire docs/templates/ directory to keep your repository
     clean. Only keep templates you haven't copied yet. -->

---

## Security Policy Templates

Choose **one** security policy template based on whether you want a bug
bounty program:

| Template                                           | Use When                                                    |
| -------------------------------------------------- | ----------------------------------------------------------- |
| [SECURITY_no_bounty.md](SECURITY_no_bounty.md)     | Standard security policy without bug bounty (most projects) |
| [SECURITY_with_bounty.md](SECURITY_with_bounty.md) | Security policy that includes a bug bounty program          |
| [BUG_BOUNTY.md](BUG_BOUNTY.md)                     | Standalone bug bounty policy (link from SECURITY.md)        |

### How to Use

1. Choose the template that fits your needs
2. Copy it to the root of your repository as `SECURITY.md`
3. Replace all placeholders marked with `TODO` (project name, contact info,
   scope, repository URLs, email addresses)
4. If using the bounty template, also copy `BUG_BOUNTY.md` to your root
   and update it
5. Enable GitHub Security Advisories in your repo settings
   (Settings → Security → Private vulnerability reporting)
6. Delete the template warning banner from the copied file

> **Tip:** The root [SECURITY.md](../../SECURITY.md) is already a working
> policy for this template repo. These templates are more detailed
> alternatives for projects that need them.

---

## Pull Request Templates

| Template                                       | Description                       |
| ---------------------------------------------- | --------------------------------- |
| [pull-request-draft.md](pull-request-draft.md) | Working draft for PR descriptions |

### How to Use

1. Use as a scratch pad to draft your PR description before pasting into
   GitHub
2. The actual PR template used by GitHub is at
   `.github/PULL_REQUEST_TEMPLATE.md`

---

## Issue Templates

The `issue_templates/` directory contains GitHub issue template examples:

| Directory          | Format                                  |
| ------------------ | --------------------------------------- |
| `issue_forms/`     | YAML-based issue forms (recommended)    |
| `legacy_markdown/` | Markdown-based templates (older format) |

### How to Use

1. Copy templates to `.github/ISSUE_TEMPLATE/` in your repository
2. Customize the fields and labels for your project
3. See [GitHub's documentation](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository)
   for details

---

## After Copying

Once you've copied the templates you need, you can delete this
`docs/templates/` directory to keep your repository clean.

## See Also

- [docs/adr/template.md](../adr/template.md) — ADR template
- [.github/PULL_REQUEST_TEMPLATE.md](../../.github/PULL_REQUEST_TEMPLATE.md) — Active PR template
- [.github/ISSUE_TEMPLATE/](../../.github/ISSUE_TEMPLATE/) — Active issue templates
