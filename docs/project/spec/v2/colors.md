# SignalNest Color System (v2)

> This document is the single source of truth for project colors in v2.
> If color values in other docs conflict with this file, this file wins.

## Scope

This file defines:

- Product UI color tokens used by the app shell and components.
- Semantic tone tokens used by status/pill styling.
- Status-to-tone mapping policy.
- Styleguide-only preset theme scope.

This file does not define spacing, radius, shadow, or motion tokens.

## Governance

1. Change this file first for any color decision.
2. Update [src/feedback_triage/static/css/tokens.css](../../../../src/feedback_triage/static/css/tokens.css) in the same PR.
3. Keep other docs as summaries that reference this file, not alternate color authorities.
4. Do not hard-code hex values in templates or component markup.
5. Components must consume `var(--color-*)` or `var(--tone-*)` tokens.

## Core Product Tokens

These tokens are normative and must match [src/feedback_triage/static/css/tokens.css](../../../../src/feedback_triage/static/css/tokens.css).

| Token | Light | Dark | Tailwind shorthand (light/dark) | Purpose |
| --- | --- | --- | --- | --- |
| `--color-bg` | `#f8fafc` | `#020617` | `slate-50` / `slate-950` | App background |
| `--color-surface` | `#ffffff` | `#0f172a` | `white` / `slate-900` | Cards and panels |
| `--color-surface-alt` | `#f1f5f9` | `#1e293b` | `slate-100` / `slate-800` | Hover rows and secondary surfaces |
| `--color-text` | `#0f172a` | `#f1f5f9` | `slate-900` / `slate-100` | Primary text |
| `--color-text-muted` | `#64748b` | `#94a3b8` | `slate-500` / `slate-400` | Secondary text |
| `--color-primary` | `#0d9488` | `#2dd4bf` | `teal-600` / `teal-400` | Primary action and brand accent |
| `--color-primary-hover` | `#0f766e` | `#5eead4` | `teal-700` / `teal-300` | Primary hover state |
| `--color-warning` | `#f59e0b` | `#fbbf24` | `amber-500` / `amber-400` | Warning and caution |
| `--color-danger` | `#e11d48` | `#fb7185` | `rose-600` / `rose-400` | Error and destructive intent |
| `--color-border` | `#e2e8f0` | `#334155` | `slate-200` / `slate-700` | Borders and dividers |
| `--color-focus` | `#14b8a6` | `#2dd4bf` | `teal-500` / `teal-400` | Focus-visible ring |

## Semantic Data/Workflow Palette

These semantic colors are also part of the v2 color system and are authoritative for charts, badges, and workflow state semantics.

| Semantic slot | Light | Dark | Tailwind shorthand (light/dark) | Typical use |
| --- | --- | --- | --- | --- |
| Brand/primary | `#0d9488` | `#2dd4bf` | `teal-600` / `teal-400` | Primary actions, neutral signal identity |
| Info/review | `#2563eb` | `#60a5fa` | `blue-600` / `blue-400` | Reviewing state, informational trend lines |
| Success/resolved | `#059669` | `#34d399` | `emerald-600` / `emerald-400` | Resolved/shipped, positive deltas |
| Warning/caution | `#f59e0b` | `#fbbf24` | `amber-500` / `amber-400` | Needs info, caution, SLA risk |
| Danger/urgent | `#e11d48` | `#fb7185` | `rose-600` / `rose-400` | Spam, destructive actions, critical urgency |
| Neutral/muted | `#64748b` | `#94a3b8` | `slate-500` / `slate-400` | Closed/inactive states, secondary data |
| Planned/theme | `#7c3aed` | `#a78bfa` | `violet-600` / `violet-400` | Planned roadmap signals and optional themed accents |
| Progress/in-flight | `#0284c7` | `#38bdf8` | `sky-600` / `sky-400` | In-progress workflows, secondary progress series |

Implementation note: if a semantic slot does not yet have a dedicated `--color-*` token in `tokens.css`, use the corresponding tone token where available, or add the token in `tokens.css` in the same PR.

## Semantic Tone Tokens (Status/Pill System)

These tokens are normative and must match [src/feedback_triage/static/css/tokens.css](../../../../src/feedback_triage/static/css/tokens.css).

| Token | Light | Dark | Purpose |
| --- | --- | --- | --- |
| `--tone-info-fg` | `#1e40af` | `#bfdbfe` | Info foreground |
| `--tone-info-bg` | `#dbeafe` | `#1e3a8a` | Info background |
| `--tone-warn-fg` | `#92400e` | `#fde68a` | Warning foreground |
| `--tone-warn-bg` | `#fef3c7` | `#78350f` | Warning background |
| `--tone-ok-fg` | `#115e59` | `#99f6e4` | Success/ok foreground |
| `--tone-ok-bg` | `#ccfbf1` | `#134e4a` | Success/ok background |
| `--tone-muted-fg` | `#334155` | `#cbd5e1` | Muted foreground |
| `--tone-muted-bg` | `#e2e8f0` | `#1e293b` | Muted background |
| `--tone-danger-fg` | `#9f1239` | `#fecdd3` | Danger foreground |
| `--tone-danger-bg` | `#ffe4e6` | `#881337` | Danger background |

## Status Mapping Policy

Default status-to-tone mapping for workflow states:

| Status | Tone |
| --- | --- |
| `new` | `info` |
| `needs_info` | `warn` |
| `reviewing` | `info` |
| `accepted` | `ok` |
| `planned` | `ok` |
| `in_progress` | `ok` |
| `shipped` | `ok` |
| `closed` | `muted` |
| `rejected` | `muted` |
| `spam` | `danger` |

Accessibility rule: never rely on color alone for meaning. Keep text labels and icon affordances.

## Styleguide Preset Themes

The preset themes are for `/styleguide` preview only and are not production defaults:

- `preset-production`
- `preset-basic`
- `preset-unique`
- `preset-crazy`

These presets may override core tokens for previewing visual directions, but production UI must use the core product tokens above unless explicitly ratified by spec/ADR.

## Detailed Guidance (Restored, Fully Formatted)

This section preserves the broader design guidance and recommendations in addition to the canonical token specs above.

### Main recommendation

Use this rule everywhere:

- Teal = SignalNest brand / primary action / neutral signal identity.
- Red, amber, green, blue, slate = meaning.

Do not make teal and orange carry the whole dashboard. That will make the dashboard feel less polished and less readable.

### Recommended SignalNest palette

#### Core UI tokens

| Token | Recommended Tailwind | Hex | Use |
| --- | --- | --- | --- |
| `--color-bg` | `slate-50` | `#f8fafc` | Main app background |
| `--color-surface` | `white` | `#ffffff` | Cards, tables, panels |
| `--color-surface-alt` | `slate-100` | `#f1f5f9` | Hover rows, secondary panels |
| `--color-text` | `slate-900` | `#0f172a` | Primary text |
| `--color-text-muted` | `slate-500` | `#64748b` | Metadata, labels, timestamps |
| `--color-border` | `slate-200` | `#e2e8f0` | Card/table dividers |
| `--color-border-strong` | `slate-300` | `#cbd5e1` | Inputs, active borders |
| `--color-primary` | `teal-600` | `#0d9488` | Primary buttons, selected nav, focus identity |
| `--color-primary-hover` | `teal-700` | `#0f766e` | Primary hover |
| `--color-focus` | `teal-500` | `#14b8a6` | Focus rings |

The theming doc says color changes should be centralized in [src/feedback_triage/static/css/tokens.css](../../../../src/feedback_triage/static/css/tokens.css), with both light and dark values updated together. Keep that rule.

### Dashboard data colors

These should be separate from generic brand tokens.

| Meaning | Tailwind | Hex | Use |
| --- | --- | --- | --- |
| Brand / received / neutral signal | `teal-600` | `#0d9488` | Total signals, received signals, top tag bars |
| Neutral data / triaged / review | `blue-600` | `#2563eb` | Triaged, reviewing, general time-series line |
| Completed / resolved / shipped | `emerald-600` | `#059669` | Resolved, shipped, positive movement |
| Caution / needs info / SLA risk | `amber-500` | `#f59e0b` | Needs info, medium pain, warnings |
| Urgent / high pain / negative | `rose-600` | `#e11d48` | High pain, critical, errors, spam |
| Neutral / closed / inactive | `slate-500` | `#64748b` | Closed, muted, stale, archived |
| Secondary purple / planned | `violet-600` | `#7c3aed` | Planned / accepted, if you want a distinct workflow color |
| Sky / in progress | `sky-600` | `#0284c7` | In progress |

This aligns with status mapping: Needs Info is amber, Reviewing is indigo/blue-family, Accepted is teal, Planned is blue/violet-family, In Progress is sky, Shipped is green, Closed is slate, Spam is rose.

### Recommended status colors

Use these for pills, charts, filters, and status legends.

| Status | Text | Background | Border | Icon suggestion |
| --- | --- | --- | --- | --- |
| New | `teal-700` | `teal-50` | `teal-200` | Inbox / CircleDot |
| Needs info | `amber-800` | `amber-50` | `amber-200` | CircleHelp |
| Reviewing | `blue-700` | `blue-50` | `blue-200` | Eye |
| Accepted | `indigo-700` or `teal-700` | `indigo-50` or `teal-50` | `indigo-200` | CheckCircle |
| Planned | `violet-700` | `violet-50` | `violet-200` | Calendar / Map |
| In progress | `sky-700` | `sky-50` | `sky-200` | Loader / Zap |
| Shipped | `emerald-700` | `emerald-50` | `emerald-200` | Check |
| Closed | `slate-700` | `slate-100` | `slate-300` | CircleSlash / Check |
| Spam | `rose-700` | `rose-50` | `rose-200` | Ban |

Important: keep the label and icon. Status/priority pills should not rely on color alone.

### Recommended priority colors

Priority is team judgment, separate from submitter pain. Do not collapse them into one color system.

| Priority | Text | Background | Border |
| --- | --- | --- | --- |
| Low | `emerald-700` | `emerald-50` | `emerald-200` |
| Medium | `amber-800` | `amber-50` | `amber-200` |
| High | `rose-700` | `rose-50` | `rose-200` |
| Critical | `red-700` | `red-50` | `red-300` |

Use rose/red only for real urgency, not for general brand styling.

### Recommended pain colors

Pain should read as severity.

| Pain | Color | Use |
| --- | --- | --- |
| 1-2 low | `emerald-500` | Low friction |
| 3 medium-low | `lime-500` or `amber-400` | Mild friction |
| 4 medium-high | `amber-500` | Concerning |
| 5 high | `rose-600` | Severe pain |

For 5-dot displays, keep empty dots `slate-300`. Filled dots can either be all teal for quiet mode or severity-colored for dense/power mode.

Recommended:

| Location | Dot color |
| --- | --- |
| Table rows | Severity color |
| Summary cards | Severity color |
| Minimal/quiet mode | Teal filled dots |

### Recommended chart colors

#### Total signals KPI card

| Element | Color |
| --- | --- |
| Main line | `teal-600` or `blue-600` |
| Area fill | `teal-50` |
| Previous-period line | `slate-200` or `blue-100` |
| Positive delta | `emerald-600` |
| Negative delta | `rose-600` |
| Icon | `teal-600` on `teal-50` |

For Total Signals specifically, teal is recommended because it is the broad SignalNest identity metric.

#### Signals over time

| Series | Color |
| --- | --- |
| Received | `teal-600` |
| Triaged | `blue-600` |
| Resolved | `emerald-600` |
| High pain | `rose-600` |
| Needs info | `amber-500` |

Avoid using amber/orange for a normal operational line unless it means caution.

#### Top tags

Use one calm bar color:

| Element | Color |
| --- | --- |
| Bar fill | `teal-600` |
| Bar track | `slate-100` |
| Up delta | `emerald-600` |
| Down delta | `rose-600` |
| Tag chip | `slate-100` or `teal-50` |

Do not give each tag a random bright color. It makes comparison harder.

#### Status mix

Use the status colors above. This is one of the few places where multiple colors are appropriate because each color maps to a meaningful workflow state.

#### Pain distribution

Use:

| Segment | Color |
| --- | --- |
| Low | `emerald-500` |
| Medium | `amber-500` |
| High | `rose-600` |

This is more instantly readable than a teal/orange-only scale.

### Sidebar recommendation

For the upgraded dashboard, a dark sidebar is recommended.

| Token | Tailwind | Hex |
| --- | --- | --- |
| Sidebar bg | `slate-950` | `#020617` |
| Sidebar border | `slate-800` | `#1e293b` |
| Sidebar text | `slate-300` | `#cbd5e1` |
| Sidebar muted | `slate-400` | `#94a3b8` |
| Sidebar active bg | `teal-600/15` or `blue-600/20` | tokenized alpha |
| Sidebar active text | `white` | `#ffffff` |
| Sidebar active rail | `teal-500` | `#14b8a6` |

This helps the app feel less generic while keeping main content readable.

### Buttons and interaction colors

| Component | Recommendation |
| --- | --- |
| Primary button | `bg-teal-600 hover:bg-teal-700 text-white` |
| Secondary button | `bg-white border border-slate-300 text-slate-700 hover:bg-slate-50` |
| Destructive button | `bg-rose-600 hover:bg-rose-700 text-white` |
| Link | `text-teal-700 hover:text-teal-800` |
| Focus ring | `ring-2 ring-teal-500/30` |

Primary buttons as teal and secondary buttons as white/slate should stay.

### CSS token proposal

```css
:root {
  /* Core surfaces */
  --color-bg: #f8fafc;              /* slate-50 */
  --color-surface: #ffffff;         /* white */
  --color-surface-alt: #f1f5f9;     /* slate-100 */
  --color-border: #e2e8f0;          /* slate-200 */
  --color-border-strong: #cbd5e1;   /* slate-300 */

  /* Text */
  --color-text: #0f172a;            /* slate-900 */
  --color-text-muted: #64748b;      /* slate-500 */
  --color-text-subtle: #94a3b8;     /* slate-400 */

  /* Brand */
  --color-primary: #0d9488;         /* teal-600 */
  --color-primary-hover: #0f766e;   /* teal-700 */
  --color-primary-soft: #ccfbf1;    /* teal-100 */
  --color-focus: #14b8a6;           /* teal-500 */

  /* Semantic */
  --color-info: #2563eb;            /* blue-600 */
  --color-info-soft: #dbeafe;       /* blue-100 */

  --color-success: #059669;         /* emerald-600 */
  --color-success-soft: #d1fae5;    /* emerald-100 */

  --color-warning: #f59e0b;         /* amber-500 */
  --color-warning-soft: #fef3c7;    /* amber-100 */

  --color-danger: #e11d48;          /* rose-600 */
  --color-danger-soft: #ffe4e6;     /* rose-100 */

  --color-neutral: #64748b;         /* slate-500 */
  --color-neutral-soft: #f1f5f9;    /* slate-100 */

  /* Optional workflow colors */
  --color-planned: #7c3aed;         /* violet-600 */
  --color-planned-soft: #ede9fe;    /* violet-100 */

  --color-progress: #0284c7;        /* sky-600 */
  --color-progress-soft: #e0f2fe;   /* sky-100 */

  /* Sidebar */
  --color-sidebar-bg: #020617;      /* slate-950 */
  --color-sidebar-surface: #0f172a; /* slate-900 */
  --color-sidebar-border: #1e293b;  /* slate-800 */
  --color-sidebar-text: #cbd5e1;    /* slate-300 */
  --color-sidebar-muted: #94a3b8;   /* slate-400 */
  --color-sidebar-active: #14b8a6;  /* teal-500 */
}
```

Dark theme:

```css
:root[data-theme="dark"] {
  --color-bg: #020617;              /* slate-950 */
  --color-surface: #0f172a;         /* slate-900 */
  --color-surface-alt: #1e293b;     /* slate-800 */
  --color-border: #334155;          /* slate-700 */
  --color-border-strong: #475569;   /* slate-600 */

  --color-text: #f8fafc;            /* slate-50 */
  --color-text-muted: #cbd5e1;      /* slate-300 */
  --color-text-subtle: #94a3b8;     /* slate-400 */

  --color-primary: #2dd4bf;         /* teal-400 */
  --color-primary-hover: #5eead4;   /* teal-300 */
  --color-primary-soft: #134e4a;    /* teal-900 */
  --color-focus: #2dd4bf;           /* teal-400 */

  --color-info: #60a5fa;            /* blue-400 */
  --color-info-soft: #1e3a8a;       /* blue-900 */

  --color-success: #34d399;         /* emerald-400 */
  --color-success-soft: #064e3b;    /* emerald-900 */

  --color-warning: #fbbf24;         /* amber-400 */
  --color-warning-soft: #78350f;    /* amber-900 */

  --color-danger: #fb7185;          /* rose-400 */
  --color-danger-soft: #881337;     /* rose-900 */

  --color-neutral: #94a3b8;         /* slate-400 */
  --color-neutral-soft: #1e293b;    /* slate-800 */

  --color-planned: #a78bfa;         /* violet-400 */
  --color-planned-soft: #4c1d95;    /* violet-900 */

  --color-progress: #38bdf8;        /* sky-400 */
  --color-progress-soft: #0c4a6e;   /* sky-900 */

  --color-sidebar-bg: #020617;
  --color-sidebar-surface: #0f172a;
  --color-sidebar-border: #1e293b;
  --color-sidebar-text: #cbd5e1;
  --color-sidebar-muted: #94a3b8;
  --color-sidebar-active: #2dd4bf;
}
```

### What to change in docs

In [docs/project/spec/v2/core-idea.md](core-idea.md), change the color section from mostly teal + amber to:

```md
### Color philosophy

SignalNest uses two color layers:

1. **Brand/UI layer** - teal is the primary product color. It is used
   for primary actions, active navigation, focus rings, neutral signal
   identity, and non-semantic decoration.

2. **Semantic/data layer** - familiar colors are used when color
   communicates meaning:
   - blue = neutral information / review / triage
   - green = success / resolved / shipped / improving
   - amber = caution / needs info / SLA risk
   - rose = high pain / urgent / negative / spam
   - slate = closed / muted / inactive / structure

Brand color must not override semantic clarity.
```

In [docs/project/spec/v2/theming.md](theming.md), add this note under "How to change a color":

```md
Do not introduce one-off chart/status colors in templates. Add a token
first, then consume it through Tailwind or an `sn-*` component class.
Status, priority, pain, and chart colors must come from the semantic
token set.
```

This matches the existing rule that token changes belong in [src/feedback_triage/static/css/tokens.css](../../../../src/feedback_triage/static/css/tokens.css), component styling belongs in `components.css`, and decorative effects belong in `effects.css`.

### Final recommendation

Keep teal as the SignalNest identity. Keep amber as a warning/needs-info color. Add a clearer semantic system:

- Teal = brand / received / neutral signal
- Blue = review / triage / neutral data
- Green = resolved / shipped / improving
- Amber = needs info / caution / SLA risk
- Rose = high pain / urgent / negative / spam
- Slate = closed / inactive / structure

This makes the dashboard feel more polished than a scattered teal/orange setup while preserving the SignalNest brand.

## Related References

- [docs/project/spec/v2/css.md](css.md)
- [docs/project/spec/v2/theming.md](theming.md)
- [docs/project/spec/v2/layout.md](layout.md)
- [docs/project/spec/v2/core-idea.md](core-idea.md)
- [src/feedback_triage/static/css/tokens.css](../../../../src/feedback_triage/static/css/tokens.css)
