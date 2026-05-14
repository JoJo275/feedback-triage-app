# Total signals widget update (reference parity)

> Doc-only implementation note. This file defines the target information model.
> No runtime code changes are included in this step.

## Reference image

![Total signals reference widget](../images/Photos_f0DnP5JH5S.png)

## Objective

Change the current **Total signals** KPI widget to match the reference widget
in terms of information shown.

## Required information (must match reference)

1. Title label: `Total signals`
2. Top-right utility/settings icon
3. Primary metric value with thousands separator (example: `1,248`)
4. Period-over-period percentage delta with directional indicator
   (example: `+18%`)
5. Comparison caption line (example: `vs May 5 - May 11`)
6. Bottom sparkline showing the period trend

## Data contract for the widget

| Field | Type | Example | Notes |
| --- | --- | --- | --- |
| `label` | string | `Total signals` | Fixed widget title |
| `value` | integer | `1248` | Displayed with thousands separator |
| `delta_pct` | number | `18.0` | Signed value used for trend direction |
| `delta_direction` | enum | `up` | `up` \| `down` \| `flat` |
| `comparison_label` | string | `vs May 5 - May 11` | Human-readable period baseline |
| `sparkline_points` | number[] | `[4, 6, 5, 8, ...]` | Ordered time-series points |

## Display rules

- Keep the value as the primary visual emphasis.
- Show `+` for positive percent changes and `-` for negative changes.
- Keep the comparison caption on its own line directly below the value/delta row.
- Keep sparkline in the lower area of the card and aligned to the same date window
  used for `comparison_label`.

## Acceptance checklist (documentation target)

1. The widget displays all six required information elements listed above.
2. The comparison caption format uses `vs <date range>`.
3. The trend indicator and percentage reflect the same sign as `delta_pct`.
4. The sparkline is present even when the period has low variance.
5. This change remains doc-only in this phase (no template/JS/API edits yet).

## Out of scope in this step

- No implementation in `src/feedback_triage/`.
- No API payload migration in this document-only change.
- No dashboard layout reorder or density preset changes.

## Related docs

- [../layouts/dashboard.md](../layouts/dashboard.md)
- [../ui.md](../ui.md)
- [dashboard-vanilla-js.md](dashboard-vanilla-js.md)
