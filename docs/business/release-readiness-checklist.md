# Release Readiness Checklist

Use this checklist before tagging or deploying a release that changes
triage behavior, status logic, or customer communication.

## Product readiness

- [ ] Scope and outcomes are documented.
- [ ] Status transitions are validated against the operating model.
- [ ] Non-goals are unchanged or explicitly updated.
- [ ] User-visible copy has been reviewed.

## Data and workflow readiness

- [ ] Any migration impact is documented.
- [ ] Existing feedback items have safe fallback behavior.
- [ ] Backlog triage owners are assigned for rollout week.
- [ ] Dashboard and reporting queries still work.

## Delivery readiness

- [ ] API and page behavior is covered by tests.
- [ ] Docs are updated in the same PR.
- [ ] Rollback plan is documented.
- [ ] On-call owner or responsible maintainer is known.

## Communication readiness

- [ ] Internal summary is ready (what changed, why, impact).
- [ ] External changelog entry draft is ready.
- [ ] Customer notification copy is reviewed if needed.

## Post-release checks (24-48h)

- [ ] Error rates and health probes are normal.
- [ ] No unexpected backlog spike in new or needs_info.
- [ ] Shipped notifications are delivering correctly.
- [ ] Any follow-up fixes are captured and prioritized.

## Suggested owners

| Area | Suggested owner |
| --- | --- |
| Product readiness | Product owner |
| Data/workflow readiness | Product owner + engineering lead |
| Delivery readiness | Engineering lead |
| Communication readiness | Product owner or support owner |
| Post-release checks | On-call maintainer |
