# Dashboard page layout

## Route and audience

- Route: `/w/<slug>/dashboard`
- Audience: authenticated workspace members (owner, team member)
- Goal: show what needs attention now, then support drill-down into inbox

## Page purpose

The dashboard is the operational summary for one workspace. It should
prioritize action first and analytics second.

## Section layout map

1. App header
- Workspace breadcrumb
- Search field
- Right-side actions

2. Page header
- `h1` title
- One-line description
- Secondary action link to inbox

3. Filter row
- Date/source/tag/status chips
- More-filters placeholder
- Clear link

4. Summary row (4 cards)
- Needs attention
- High priority
- New this week
- Stale

5. Main work row (2 columns desktop)
- Left: triage queue preview table
- Right: attention panel shortcuts + primary CTA

6. Insight row (2 columns desktop)
- Top tags with relative bars
- Intake sparkline (last 30 days)

7. Utility row (2 columns desktop)
- Source breakdown
- Recent activity

## Data population contract

| Page section | Template field(s) | Service source |
| --- | --- | --- |
| Summary cards | `summary.cards` | `dashboard_aggregator._summary_cards` |
| Needs-attention total | derived from `summary.cards` (`new + needs_info + reviewing`) | template computation |
| Triage queue preview | `summary.recent_activity[:6]` | `dashboard_aggregator._recent_activity` |
| Attention panel counts | derived from `summary.cards` | template computation |
| Top tags | `summary.top_tags` | `dashboard_aggregator._top_tags` |
| Intake sparkline | `summary.sparkline`, `summary.sparkline_max` | `dashboard_aggregator._sparkline` |
| Source breakdown | `summary.source_breakdown` | `dashboard_aggregator._source_breakdown` |
| Recent activity | `summary.recent_activity` | `dashboard_aggregator._recent_activity` |

## States

- Empty workspace: render `pages/dashboard/empty.html`
- Populated workspace: render `pages/dashboard/index.html`
- Anonymous access: 401
- Cross-tenant slug: 404

## Implementation surfaces

- Route handler: `src/feedback_triage/pages/dashboard.py`
- Aggregation service: `src/feedback_triage/services/dashboard_aggregator.py`
- Page template: `src/feedback_triage/templates/pages/dashboard/index.html`
- Empty template: `src/feedback_triage/templates/pages/dashboard/empty.html`
- Layout CSS: `src/feedback_triage/static/css/layout.css`
- Component CSS: `src/feedback_triage/static/css/components.css`

## Related specs

- [information-architecture.md](../information-architecture.md)
- [layout.md](../layout.md)
- [ui.md](../ui.md)
- [css.md](../css.md)
