# ADR 057: Brand vs. repository naming — SignalNest / feedback-triage-app

## Status

Accepted

## Context

The project is published under two names that mean different things:

- **Brand / product name:** SignalNest. This is what the deployed app
  calls itself in the UI, what the custom domain `signalnest.app`
  resolves to, and what a user or reviewer sees.
- **Repository / package name:** `feedback-triage-app` (repo slug) and
  `feedback_triage` (Python package). This is the engineering identity
  used in source control, container registry, CI badges, ADR history,
  and import statements.

The question came up: should the GitHub repo be renamed to
`signalnest` so the names align? GitHub will set up an HTTP redirect
from the old slug to the new one when a repo is renamed, so the
mechanical cost is real but bounded. The strategic question is whether
the alignment is worth the churn.

What a rename would touch:

- GitHub Pages URL (`jojo275.github.io/feedback-triage-app/` →
  `…/signalnest/`). GitHub redirects HTTP, but external badges,
  embeds, and bookmarks may not pick up the redirect cleanly.
- GHCR image (`ghcr.io/jojo275/feedback-triage-app` →
  `…/signalnest`). Existing image tags don't migrate automatically;
  Containerfile `org.opencontainers.image.title/source/url` labels
  need updating in the same change.
- `release-please-config.json`, `container-structure-test.yml`,
  `mkdocs.yml` (`repo_url`), `CHANGELOG.md` history references,
  `.github/workflows/*.yml`, the devcontainer name, the VS Code
  workspace file name, every ADR that quotes the slug.
- Every existing local clone needs `git remote set-url`.
- The Python package `feedback_triage` doesn't change with a repo
  rename — leaving the repo at `signalnest` and the package at
  `feedback_triage` is *more* confusing, not less. A real alignment
  requires a package rename too, which is a separate, larger
  migration touching every `from feedback_triage…` import.

The brand/repo split is also common precedent: `microsoft/vscode`
ships VS Code; `getsentry/sentry`, `denoland/deno`, etc., all keep an
engineering-name repo for a brand-name product.

## Decision

Keep the names split:

- **Repository slug:** `feedback-triage-app`. Do not rename.
- **Python package:** `feedback_triage`. Do not rename.
- **Brand / product name:** SignalNest. Used in:
  - `<title>` and `<h1>` of every HTML page.
  - The README header callout.
  - `mkdocs.yml` `site_name`.
  - The custom domain `signalnest.app` (Cloudflare Registrar — see
    [`docs/notes/domain-and-cloudflare.md`](../notes/domain-and-cloudflare.md)).
  - Marketing surfaces and screenshots.

Both names are documented in the README header so a reviewer landing
on the repo immediately sees the relationship.

A future rename remains possible. If it ever happens, it should be its
own dedicated PR after v1.0 ships, paired with a `feedback_triage →
signalnest` package rename so the names align everywhere at once, and
captured as its own ADR superseding this one. Do not rename only the
repo — partial alignment is worse than the current split.

## Alternatives Considered

### Rename the repo to `signalnest` now

Run the GitHub rename, fix all hardcoded references, accept the
broken external links during the transition.

**Rejected because:** the package would still be `feedback_triage`,
which makes the inconsistency worse than the current state. A clean
rename means renaming both, which is a v3.0-sized migration. Doing it
mid-development of v2.0 burns time on no user-visible value.

### Rename only the package, keep the repo

Rename `feedback_triage` to `signalnest` while leaving the repo slug.

**Rejected because:** flips the inconsistency without resolving it.
Same effort as a full rename without the alignment payoff.

### Drop the SignalNest brand and use `feedback-triage-app` everywhere

Make the engineering name the user-facing name too.

**Rejected because:** `feedback-triage-app` is a description, not a
product name. A custom domain (`feedback-triage-app.app` is also
unavailable as a brand) and a portfolio presence both benefit from a
real product name. The brand is already in use on the live deploy.

## Consequences

### Positive

- Zero churn on existing infrastructure, badges, image tags, links,
  and clones.
- The brand/repo split mirrors well-known projects and is easy to
  document in the README.
- Future rename remains an option — this ADR doesn't foreclose it,
  it just defers it until both names can be aligned at once.

### Negative

- Two names for one project is mildly confusing on first encounter.
- New contributors must mentally map "SignalNest" (what the app is
  called) ↔ "feedback-triage-app" (where the code lives).
- Documentation must be careful: user-facing copy says "SignalNest";
  engineering docs (ADRs, repo layout, CI) say `feedback-triage-app`.

### Neutral

- The custom domain `signalnest.app` works regardless of repo name.
- Open-source citation conventions (cite the repo URL) are unaffected.

### Mitigations

- Document the split prominently in the README header (already done).
- Reference both names in the v2.0 spec so future authors don't
  re-litigate this decision.
- If a rename ever lands, this ADR's Status flips to "Superseded by
  ADR XXX" and the new ADR documents the simultaneous repo + package
  rename.

## Implementation

- [`README.md`](../../README.md) — header callout naming both.
- [`mkdocs.yml`](../../mkdocs.yml) — `site_name: SignalNest`.
- [`src/feedback_triage/static/`](../../src/feedback_triage/static/) —
  `<title>` and `<h1>` use SignalNest.
- [`docs/notes/domain-and-cloudflare.md`](../notes/domain-and-cloudflare.md) —
  `signalnest.app` configuration.
- [`docs/project/spec/spec-v2.md`](../project/spec/spec-v2.md) —
  Naming section.

## References

- [ADR 056: Style guide page with theme demos](056-style-guide-page.md)
- [`docs/notes/buying-a-domain.md`](../notes/buying-a-domain.md)
- [`docs/notes/domain-and-cloudflare.md`](../notes/domain-and-cloudflare.md)
