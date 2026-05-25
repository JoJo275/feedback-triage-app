# Validation Plan

This page captures how to validate product demand and workflow value
without adding major implementation scope.

Branding note: references to SignalNest should be treated as placeholder
brand language until naming is finalized.

## Validation goals

- Confirm the target users feel the triage pain sharply.
- Confirm the workflow reduces decision latency.
- Confirm close-the-loop behavior is meaningful to users.

## Core hypotheses

| ID | Hypothesis | Validation signal |
| --- | --- | --- |
| H1 | Teams struggle to consolidate feedback across channels. | Users describe manual copy/paste and context loss. |
| H2 | A fixed status workflow improves decision speed. | Median time from new to accepted or closed decreases. |
| H3 | Shipped notifications increase trust and retention. | Users report higher confidence in follow-through. |
| H4 | Lightweight tooling beats feature-heavy suites for this segment. | Users choose simplicity over broad customization. |

## Experiment design

### Interview loop

- Run 5-8 interviews per month with target personas.
- Use consistent prompts from customer-segments.md.
- Tag pain themes and objections after each session.

### Workflow trial

- Ask pilot users to run one full triage cycle for two weeks.
- Measure item aging, status movement, and stale ratio.
- Compare to baseline process where possible.

### Outcome check

- Track whether shipped communication happened for shipped items.
- Collect qualitative feedback on clarity and trust.

## Success criteria

- At least 70% of interviewees confirm current triage pain.
- At least 50% of pilot teams continue usage after 4 weeks.
- Stale open-item ratio trends down over pilot period.
- At least one user recommends the product to a peer.

## Failure signals

- Users cannot explain why status workflow helps.
- Most value requests demand enterprise features immediately.
- Teams adopt intake but ignore triage states after week one.

## Execution cadence

| Cadence | Activity |
| --- | --- |
| Weekly | Interview synthesis and experiment notes |
| Biweekly | Pilot health review and metric check |
| Monthly | Decide continue, adjust, or pause bets |

## Artifacts to maintain

- Public summary in docs/business pages.
- Private notes in business-private/customer-interviews.md.
- Decision summary in project questions or ADR when needed.
