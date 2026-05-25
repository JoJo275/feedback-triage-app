# Business Documentation

This directory captures product and business decisions that support
triage, prioritization, and release planning.

Use this section for business context, not implementation details.
Engineering behavior, schema, and API contracts still live in the
project specs and ADRs.

## Recommended reading order

1. [Overview](overview.md)
2. [Customer Segments](customer-segments.md)
3. [Triage Operating Model](triage-operating-model.md)
4. [Metrics and Reporting](metrics-and-reporting.md)
5. [Release Readiness Checklist](release-readiness-checklist.md)

## Contents

| File | Purpose |
| --- | --- |
| [overview.md](overview.md) | Product posture, value proposition, and boundaries |
| [customer-segments.md](customer-segments.md) | ICP guardrails, personas, and interview prompts |
| [triage-operating-model.md](triage-operating-model.md) | Status workflow, meeting cadence, and prioritization model |
| [metrics-and-reporting.md](metrics-and-reporting.md) | KPIs, targets, and SQL snippets for recurring reporting |
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
