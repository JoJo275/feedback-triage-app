# Triage Operating Model

This page defines how teams use the workflow consistently.

## Principles

- Keep intake simple.
- Make status ownership explicit.
- Prefer small, reversible decisions.
- Close the loop when value is delivered.

## Status workflow and intent

Use the canonical status enum from the application:

`new -> needs_info -> reviewing -> accepted -> planned -> in_progress -> shipped`

Additional terminal statuses:

- `closed` for items intentionally stopped.
- `spam` for invalid or abusive submissions.

## Status ownership and exit criteria

| Status | Default owner | Exit criteria |
| --- | --- | --- |
| new | Inbox owner | Item has enough context to route |
| needs_info | Inbox owner | Missing context resolved or item closed |
| reviewing | Product owner | Decision made: accepted, closed, or spam |
| accepted | Product owner | Prioritized into a delivery window |
| planned | Product owner + engineering lead | Work is scoped and sequenced |
| in_progress | Engineering owner | Work reaches releasable state |
| shipped | Product owner | Release note published and notifications handled |
| closed | Product owner | Decision documented and communicated |
| spam | Inbox owner | Item classified and removed from active flow |

## Weekly operating rhythm

1. Monday intake review: clean up new and spam quickly.
2. Mid-week triage: move qualified items through reviewing.
3. Friday planning sync: update accepted/planned/in_progress items.
4. Release follow-up: confirm shipped items and external communication.

## Prioritization model

Use a lightweight score to compare candidates:

- Impact: 1-5
- Strategic fit: 1-5
- Confidence: 1-5
- Effort: 1-5

Priority score:

`(Impact + Strategic fit + Confidence) / Effort`

Use score as guidance, then apply judgment for urgency and risk.

## SLA targets

| Step | Target |
| --- | --- |
| new to first review | Within 2 business days |
| needs_info follow-up | Within 3 business days |
| accepted/planned refresh | At least every 14 days |
| shipped communication | Within 1 business day of status change |

## Operational anti-patterns

- Letting items sit in new without owners.
- Marking planned before problem framing is clear.
- Using shipped without a customer-facing update.
- Treating score as the only decision input.
