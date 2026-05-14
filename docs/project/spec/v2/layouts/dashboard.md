# Dashboard page layout

## Reference image

![Dashboard reference mockup](../images/Dashboard%20Mockup%201.jpg)

This image is the visual direction for density and composition.

## Route and audience

- Route: `/w/<slug>/dashboard`
- Audience: authenticated workspace members
- Goal: immediate operational awareness plus direct next actions

## Dashboard questions this page must answer

1. What is happening now?
2. What changed recently?
3. What needs action now?
4. Where is the biggest pain?
5. Is the process healthy?
6. Who owns the next action?

## Design stance

- Keep the dense default.
- Improve operational usefulness by emphasizing execution health,
  timeliness, throughput, and ownership.
- Do not reduce the page to analytics-only summary cards.

## Recommended dense default layout

| Row | Purpose | Widgets |
| --- | --- | --- |
| Toolbar | Scope and controls | Search, date range, filters, saved views, new signal |
| 1 | Fast scan KPI strip | Total signals, needs action, high pain signals, median time to triage, net backlog change |
| 2 | Operational health | Signals over time, status mix, aging or SLA |
| 3 | Themes and impact | Top tags, pain distribution, segment impact, source breakdown (optional priority) |
| 4 | Execution | Team workload, backlog or needs attention |
| 5 | Workbench surface | Action queue table |

## Toolbar contract

Keep the existing filter model and add explicit view controls:

- Filters: date range, source, product area, tag, segment, status
- Controls: view density selector, customize widgets, saved views
- Primary action: new signal

## Row contracts

### Row 1: KPI strip

Required KPIs:

- Total signals
- Needs action
- High pain signals
- Median time to triage
- Net backlog change

Notes:

- "Needs action" is preferred over "Needs attention" for operational clarity.
- Median pain score can remain on the page, but it is secondary to median
  time to triage for default KPI prominence.

### Row 2: Operational health

#### Signals over time

Use three lines in the same chart:

- Received
- Triaged
- Resolved

Reason: intake-only trend lines hide whether the team is keeping up.

#### Status mix

Show distribution across the v2 status workflow to reveal bottlenecks.

#### Aging or SLA

Required fields:

- Average age of open items
- Median age of open items
- Buckets: 0-24h, 1-3d, 4-7d, 8-14d, 14d+
- Oldest untriaged
- High pain over SLA

Reason: backlog count alone can hide stale, high-severity risk.

### Row 3: Themes and impact

#### Top tags

Show:

- count
- percentage
- period delta
- unresolved count (if available)

#### Pain distribution

Show low/medium/high distribution and call out:

- high pain unresolved
- high pain unassigned

#### Segment impact

Show impact by segment and severity, for example:

- high pain by segment
- top affected segment
- repeat submitter pain concentration

#### Source breakdown

Keep this visible in dense mode, but treat it as lower priority than
status, aging, and ownership widgets.

### Row 4: Execution

#### Team workload

Required columns:

- owner
- open
- high pain
- overdue

Always include unassigned totals.

#### Backlog or needs attention

Recommended categories:

- unassigned high pain
- new and untriaged
- over SLA
- returning customer pain
- escalated
- potential duplicates
- waiting on submitter

### Row 5: Action queue

Rename the table from "Recent signals" to "Action queue".

Recommended defaults:

- 8-10 rows
- urgency-first sorting
- quick views: needs action, recent, high pain, unassigned, stale, duplicates

Recommended columns:

- type
- title
- submitter
- source
- pain
- priority
- status
- owner
- age
- tags

Default sort strategy should prioritize:

1. high pain
2. unassigned
3. over SLA
4. needs_info and reviewing
5. recency within those groups

## Preset behavior

| Preset | Behavior |
| --- | --- |
| Dense (default) | Full operational dashboard |
| Medium | Hide lower-priority widgets (often source breakdown, some impact widgets) |
| Light | KPI strip + signals over time + needs action + action queue |
| Custom | User-controlled widget visibility and order |

## Default visibility guidance

| Area | Widget | Default visibility |
| --- | --- | --- |
| KPI | Total signals | Required |
| KPI | Needs action | Required |
| KPI | High pain signals | Required |
| KPI | Median time to triage | Required |
| KPI | Net backlog change | Required |
| Health | Signals over time | Required |
| Health | Status mix | Required |
| Health | Aging or SLA | Required |
| Themes | Top tags | Required |
| Themes | Pain distribution | Recommended |
| Themes | Segment impact | Recommended |
| Themes | Source breakdown | Optional in non-dense modes |
| Execution | Team workload | Recommended |
| Execution | Backlog or needs attention | Required |
| Workbench | Action queue | Required |

## Canonical v2 status set

Status widgets and filters should use:

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

## Data contract additions

To support this layout, extend dashboard summary payloads with:

- `kpi` including `needs_action`, `median_time_to_triage`, `net_backlog_change`
- `throughput` including received, triaged, resolved period totals
- `status_mix`
- `aging_health`
- `team_workload`
- `segment_impact`
- `signal_quality`
- `action_queue` with urgency sort metadata

## Acceptance checks

1. The six dashboard questions are answerable in under 10 seconds.
2. Process health is visible above the fold on desktop.
3. Action queue defaults to urgency-first ordering.
4. Aging, status mix, and ownership are all represented in the default dense view.
5. Dense, medium, and light presets can switch without breaking page semantics.

## Related specs

- [README.md](README.md)
- [../information-architecture.md](../information-architecture.md)
- [../layout.md](../layout.md)
- [../ui.md](../ui.md)
- [../css.md](../css.md)
- [../implementations/total-signals-widget.md](../implementations/total-signals-widget.md)
