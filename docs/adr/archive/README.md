# ADR Archive

<!-- TODO (template users): This directory is ready to use as-is. No changes
     needed until you have ADRs to archive. -->

This directory contains **deprecated**, **superseded**, or **suspended** Architecture Decision Records.

## Status Definitions

| Status         | Meaning                                                        |
| -------------- | -------------------------------------------------------------- |
| **Deprecated** | The decision is no longer valid due to changed circumstances   |
| **Superseded** | A newer ADR has replaced this one (linked in the supersession) |
| **Suspended**  | The decision is on hold pending further evaluation             |

## Archive Process

When archiving an ADR:

1. Update the ADR's status in its YAML frontmatter or Status section
2. Add a brief note explaining why it was archived
3. Move the file to this directory
4. Update the main ADR index (`docs/adr/README.md`)

## Contents

The following ADRs were archived during the fork from
`simple-python-boilerplate` to `feedback-triage-app`. They documented
template-only scaffolding (env-inspection dashboard, env collectors,
bootstrap/customize tooling, doctor profiles, repository guards, etc.)
that the new project does not carry over.

| ADR                                            | Original Title                                            | Status     | Archived   |
| ---------------------------------------------- | --------------------------------------------------------- | ---------- | ---------- |
| [011](011-repository-guard-pattern.md)         | Repository guard pattern for optional workflows           | Deprecated | 2026-04-27 |
| [015](015-no-github-directory-readme.md)       | No README.md in `.github/` directory                      | Deprecated | 2026-04-27 |
| [036](036-diagnostic-tooling-strategy.md)      | Diagnostic tooling strategy (doctor scripts and profiles) | Deprecated | 2026-04-27 |
| [039](039-developer-onboarding-automation.md)  | Developer onboarding automation (bootstrap and customize) | Deprecated | 2026-04-27 |
| [040](040-v1-release-readiness.md)             | v1.0 release readiness checklist                          | Deprecated | 2026-04-27 |
| [041](041-env-inspect-web-dashboard.md)        | Environment inspection web dashboard                      | Deprecated | 2026-04-27 |
| [042](042-script-smoke-testing.md)             | Script smoke testing in CI                                | Deprecated | 2026-04-27 |
| [043](043-collector-plugin-architecture.md)    | Environment data collector plugin architecture            | Deprecated | 2026-04-27 |
