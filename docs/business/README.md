# Business Documentation

This directory captures product and business decisions that support
triage, prioritization, and release planning.

Use this section for business context, not implementation details.
Engineering behavior, schema, and API contracts still live in the
project specs and ADRs.

Public/private split:
- Keep this directory public and high-level.
- Keep interview transcripts, pricing experiments, and founder strategy
	details in `business-private/`.

## Recommended reading order

1. [Naming Status](branding/naming.md)
2. [High-Level Positioning](branding/high-level-positioning.md)
3. [Overview](overview.md)
4. [Demo Data Policy](demo-data-policy.md)
5. [Product Positioning](product-positioning.md)
6. [Customer Segments](customer-segments.md)
7. [Validation Plan](validation-plan.md)
8. [Triage Operating Model](triage-operating-model.md)
9. [Metrics and Reporting](metrics-and-reporting.md)
10. [Commercialization Roadmap](commercialization-roadmap.md)
11. [Legal Readiness Checklist](legal-readiness-checklist.md)
12. [Release Readiness Checklist](release-readiness-checklist.md)

## Contents

| File | Purpose |
| --- | --- |
| [branding/naming.md](branding/naming.md) | Public naming status for repo name versus placeholder product name |
| [branding/high-level-positioning.md](branding/high-level-positioning.md) | Provisional product narrative for external context |
| [branding/logo.md](branding/logo.md) | Current logo decision status for public readers |
| [branding/slogan.md](branding/slogan.md) | Current slogan decision status for public readers |
| [branding/brand-colors.md](branding/brand-colors.md) | Current brand color decision status for public readers |
| [overview.md](overview.md) | Product posture, value proposition, and boundaries |
| [demo-data-policy.md](demo-data-policy.md) | Rules for safe synthetic/anonymized demo data in public artifacts |
| [product-positioning.md](product-positioning.md) | Category wedge, differentiators, and messaging guardrails |
| [customer-segments.md](customer-segments.md) | ICP guardrails, personas, and interview prompts |
| [validation-plan.md](validation-plan.md) | Demand hypotheses, experiments, and success criteria |
| [triage-operating-model.md](triage-operating-model.md) | Status workflow, meeting cadence, and prioritization model |
| [metrics-and-reporting.md](metrics-and-reporting.md) | KPIs, targets, and SQL snippets for recurring reporting |
| [commercialization-roadmap.md](commercialization-roadmap.md) | Staged path from free usage to paid tiers |
| [legal-readiness-checklist.md](legal-readiness-checklist.md) | Policy, compliance, and launch legal readiness checks |
| [release-readiness-checklist.md](release-readiness-checklist.md) | Go/no-go checklist for shipping updates safely |

## Maintenance cadence

- Review overview and segments at least once per quarter.
- Review KPIs monthly.
- Review release checklist before every release.
- Keep links and status names aligned with the active product spec.

## Related documentation

- [v2 Spec Overview](../project/spec/spec-v2.md)
- [v2 Business Detail](../project/spec/v2/business.md)
- [Open Questions](../project/questions.md)
- [Release Policy](../release-policy.md)
