# Dashboard page layout

## Reference image

![Dashboard reference mockup](../images/Dashboard%20Mockup%201.jpg)

The image above is the visual direction reference for layout and
information density.

## Route and audience

- Route: `/w/<slug>/dashboard`
- Audience: authenticated workspace members
- Primary goal: immediate operational awareness plus direct next actions

## Dashboard success criteria

The default dashboard must let a user answer these questions quickly:

1. What is happening now?
2. What changed recently?
3. What needs action now?
4. Where is pain concentrated?
5. Is the triage process healthy?
6. Who owns the next action?

## Recommended default composition (dense mode)

| Row | Purpose | Widgets |
| --- | --- | --- |
| 1 | Fast scan KPI strip | Total signals, needs attention, high pain, median pain, median time to triage, net backlog change |
| 2 | Process health | Signals over time, status mix, aging health, backlog pressure |
| 3 | Thematic and business impact | Top tags, pain distribution, team workload, segment impact |
| 4 | Action surface | Action queue table |

This keeps the power-user density while improving execution health,
ownership, and timeliness visibility.

## Section contracts

### 1) KPI strip

Required metrics:

- Total signals
- Needs attention
- High pain signals
- Median pain score
- Median time to triage
- Net backlog change

Why: this row should answer "what changed" and "are we keeping up" in one
scan.

### 2) Process health row

Required widgets:

- Signals over time (intake trend)
- Status mix (workflow distribution)
- Aging health (open item age profile)
- Backlog pressure (attention classes)

Why: this row closes the current gap between descriptive volume and
execution health.

### 3) Thematic and business impact row

Required widgets:

- Top tags
- Pain distribution
- Team workload
- Segment impact

Why: this row shows what is hurting, who is carrying load, and which
segments matter most.

### 4) Action queue row

Rename "Recent signals" to "Action queue" and default-sort by urgency.

Recommended defaults:

- 8-10 rows visible
- Sort: needs action first
- Quick views: recent, high pain, unassigned, stale

Why: this keeps dashboard context but drives immediate action.

## Highest-value additions (priority order)

### A) Aging and timeliness

Add an "Aging health" panel with:

- Average age of open signals
- Median age of open signals
- Age buckets: 0-24h, 1-3d, 4-7d, 8-14d, 14d+
- High pain open age
- Oldest untriaged item

### B) Throughput and process output

Add throughput metrics for the active period:

- Triaged
- Resolved or closed
- Moved to planned
- Shipped
- Triage rate vs intake rate
- Net backlog change

### C) Ownership and accountability

Add a "Team workload" widget with:

- Unassigned signals
- Open by owner
- High pain by owner
- Overdue by owner
- No owner and high pain count

### D) Status mix

Add a status distribution widget and prioritize it above source
breakdown on the default dashboard.

### E) Segment impact

Add segment-weighted impact indicators:

- Top affected segment
- High pain by segment
- High-value account impact
- Repeat submitter pain concentration

### F) Signal quality and dedupe

Add quality metrics:

- Duplicate rate
- Duplicates merged this period
- Unique signals vs raw submissions
- Spam or invalid rate

### G) Trend deltas across breakdowns

Add period-over-period deltas to:

- Top tags
- Backlog categories
- Source breakdown
- Pain distribution
- Status distribution

## Canonical v2 status set

Status widgets should use the v2 status enum from the spec:

- `new`
- `needs_info`
- `reviewing`
- `accepted`
- `planned`
- `in_progress`
- `shipped`
- `closed`
- `spam`

See [../glossary.md](../glossary.md) and [../schema.md](../schema.md).

## Preset modes (optional)

Use layout presets without weakening the opinionated default.

- Dense: full operational dashboard (default)
- Medium: fewer widgets, reduced table footprint
- Light: KPI strip + trend + one action widget

The default should remain dense because it reflects SignalNest triage
behavior expectations.

## Data contract additions (recommended)

To support the additions above, extend dashboard summary payloads with
structured blocks:

- `aging_health`
- `throughput`
- `team_workload`
- `status_mix`
- `segment_impact`
- `signal_quality`

## Acceptance checks

1. A user can answer all six dashboard success questions in under 10 seconds.
2. Process health (throughput, aging, status mix, ownership) is visible above
   the fold on desktop.
3. Action queue defaults to needs-action ordering and supports quick switching.
4. Trend deltas are present in at least KPI, status, and thematic breakdowns.

## Related specs

- [README.md](README.md)
- [../information-architecture.md](../information-architecture.md)
- [../layout.md](../layout.md)
- [../ui.md](../ui.md)
- [../css.md](../css.md)
