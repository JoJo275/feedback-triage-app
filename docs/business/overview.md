# Business Overview

This page defines the business posture for the feedback triage web app
prototype and keeps scope decisions explicit.

Branding note: the commercial product name is not finalized.
Any use of SignalNest/Signalnest is placeholder branding.

## Product summary

The product helps small teams collect customer feedback in one place,
triage it through an opinionated workflow, and close the loop when work
ships.

## Problem statement

Teams lose useful feedback because it is spread across channels and
triaged inconsistently. The result is duplicate work, unclear priorities,
and delayed customer follow-up.

## Value proposition

- Centralize feedback intake into one system.
- Use a consistent status workflow for triage and planning.
- Notify submitters when shipped work closes the loop.
- Keep the product surface small so setup and daily use are simple.

## Target customer profile

- Team size: 1 to 20 people.
- Stage: solo founder, early startup, or internal product tooling team.
- Need: lightweight triage without the overhead of enterprise suites.

See [Customer Segments](customer-segments.md) for details.

## Business posture

| Area | Current stance |
| --- | --- |
| Pricing | Free at v2.0; no billing workflow |
| Deployment model | Single app deployment for fast iteration |
| Go-to-market | Portfolio-first and organic distribution |
| Data posture | Keep personal data minimal and explicit |

## Deliberate non-goals

- No AI auto-triage in v2.0.
- No voting or popularity mechanics.
- No broad integration marketplace in v2.0.
- No enterprise auth stack in v2.0.

These constraints keep the product focused and reduce support load.

## 6-12 month business goals

| Goal | Why it matters | Example target |
| --- | --- | --- |
| Increase active workspaces | Validates demand | At least 5 active workspaces |
| Improve closed-loop behavior | Proves value delivery | At least 10 shipped items with notifications |
| Reduce stale backlog | Protects trust | New and needs_info items older than 14 days stay below 20% |

## Source of truth links

- [v2 Spec](../project/spec/spec-v2.md)
- [v2 Business Detail](../project/spec/v2/business.md)
- [v2 Rollout Plan](../project/spec/v2/rollout.md)
