# Metrics and Reporting

This page defines a practical reporting layer for triage operations.

## Reporting principles

- Track a small set of metrics consistently.
- Prefer operational metrics that can drive action.
- Keep metric definitions stable over time.

## Core KPI set

| KPI | Definition | Why it matters | Suggested target |
| --- | --- | --- | --- |
| Intake volume | Count of new feedback items in period | Demand signal | Monitor trend, not absolute value |
| Active backlog | Items in new/needs_info/reviewing/accepted/planned/in_progress | Work-in-progress health | Keep age and size bounded |
| Shipped count | Items in shipped during period | Delivery throughput | Month-over-month growth |
| Stale ratio | Share of open items older than 14 days | Workflow reliability | Under 20% |
| Source diversity | Mix of source values for new items | Channel quality signal | No single source above 70% long-term |

## SQL snippets

The snippets below use PostgreSQL and the feedback_item table.

### Weekly intake volume

```sql
SELECT
  date_trunc('week', created_at) AS week_start,
  count(*) AS intake_count
FROM feedback_item
GROUP BY 1
ORDER BY 1 DESC;
```

### Current active backlog

```sql
SELECT count(*) AS active_backlog
FROM feedback_item
WHERE status IN (
  'new',
  'needs_info',
  'reviewing',
  'accepted',
  'planned',
  'in_progress'
);
```

### Stale open items (> 14 days)

```sql
SELECT
  id,
  title,
  status,
  now() - created_at AS age
FROM feedback_item
WHERE status IN (
  'new',
  'needs_info',
  'reviewing',
  'accepted',
  'planned',
  'in_progress'
)
AND created_at < now() - interval '14 days'
ORDER BY age DESC;
```

### Source mix by month

```sql
SELECT
  date_trunc('month', created_at) AS month_start,
  source,
  count(*) AS item_count
FROM feedback_item
GROUP BY 1, 2
ORDER BY 1 DESC, 3 DESC;
```

## Weekly report template

Use this short format for a recurring update:

1. Intake this week and trend versus last week.
2. Backlog size and stale ratio.
3. Top three accepted or planned items.
4. Shipped items and communication sent.
5. Risks or blockers requiring leadership input.

## Data quality checks

Before publishing metrics:

- Confirm status values match canonical enum names.
- Confirm date windows use the same timezone and interval logic.
- Confirm spam items are excluded from customer-facing summaries.
