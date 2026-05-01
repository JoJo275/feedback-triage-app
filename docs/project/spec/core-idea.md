# SignalNest — Core Idea & Theme

> **Status:** Author's working brief for the SignalNest brand and
> v2.0 visual direction. Lives alongside [`spec-v2.md`](spec-v2.md);
> the spec inherits the Theme statement from this file. Feedback /
> pushback / actionables are tracked separately in
> [`core-idea-feedback.md`](core-idea-feedback.md).

---

## Recommended theme

**SignalNest — Calm Signal Intelligence.**

Turn noisy user feedback into clear product signals.

The app should feel like a **clean command center for sorting messy
incoming feedback into useful product decisions.** Not playful, not
corporate-boring, not cyberpunk. More like: quiet, focused,
trustworthy, organized.

---

## Theme concept

| Element            | Direction                                                       |
| ------------------ | --------------------------------------------------------------- |
| Product name       | SignalNest                                                      |
| Tagline            | _Capture the noise. Find the signal._                           |
| Visual metaphor    | Signals, threads, nests, clusters, clarity, prioritization      |
| Mood               | Calm, sharp, organized, slightly analytical                     |
| App personality    | Practical, reliable, modern, not overdesigned                   |
| Best fit           | Portfolio SaaS app that feels genuinely usable                  |

---

## Brand positioning

SignalNest is **not just a feedback form**. It is a place where
feedback becomes structured decisions.

Use language like:

- Collect feedback.
- Triage faster.
- Prioritize what matters.
- Close the loop.

Avoid making it sound like a generic survey tool.

---

## Visual style

### Main vibe

| Trait        | Recommendation                       |
| ------------ | ------------------------------------ |
| Overall look | Modern SaaS dashboard                |
| Density      | Medium-dense but readable            |
| Corners      | Rounded, but not bubbly              |
| Shadows      | Soft, minimal                        |
| Borders      | Subtle gray borders                  |
| Background   | Off-white or very dark navy-gray     |
| Accent       | Signal green/teal or warm amber      |
| Motion       | Small, functional transitions only   |

### Suggested color palette — light mode

| Role             | Color idea         | Use                                   |
| ---------------- | ------------------ | ------------------------------------- |
| Background       | Warm off-white     | Main app background                   |
| Surface          | White              | Cards, tables, panels                 |
| Primary text     | Deep slate / navy  | Main copy                             |
| Muted text       | Gray-blue          | Metadata, timestamps                  |
| Primary accent   | Teal / green       | Active states, primary actions        |
| Secondary accent | Amber              | "Needs review", "high signal", warnings |
| Danger           | Soft red           | Spam, delete, error                   |
| Border           | Pale slate         | Cards and table dividers              |

Tailwind-style approximation:

```text
Background:    slate-50  / stone-50
Surface:       white
Text:          slate-900
Muted:         slate-500
Primary:       teal-600
Primary hover: teal-700
Warning:       amber-500
Danger:        rose-600
Border:        slate-200
```

### Suggested color palette — dark mode (later)

```text
Background:        slate-950
Surface:           slate-900
Elevated surface:  slate-800
Text:              slate-100
Muted:             slate-400
Primary:           teal-400
Warning:           amber-400
Danger:            rose-400
Border:            slate-700
```

For a portfolio piece, build **light mode first**. Add dark mode
later only if the core app is solid.

---

## Typography

| Use            | Recommendation                  |
| -------------- | ------------------------------- |
| UI font        | Inter, Geist, or Source Sans 3  |
| Code/metadata  | JetBrains Mono or IBM Plex Mono |
| Tone           | Clear, compact, readable        |

Style:

- Page titles: strong, simple
- Section headers: medium weight
- Body text: readable, not tiny
- Metadata: small and muted
- Status labels: compact, uppercase or title case

Example:

> **Inbox**
> Review new feedback, merge duplicates, and route product signals.

---

## Logo / identity idea

A simple logo could combine:

| Symbol            | Meaning                |
| ----------------- | ---------------------- |
| Nest circle       | Collected feedback     |
| Signal dot/waves  | User signal            |
| Small nodes       | Clusters / related feedback |
| Check mark / spark | Actionable insight    |

**Good direction:** a small circular nest made of 2–3 curved lines,
with one signal dot in the center.

**Avoid:**

- Literal bird nest
- Overly cute mascot
- Generic chat bubble
- Huge radio-wave icon

Lucide icons that fit early:

| Icon                | Use                |
| ------------------- | ------------------ |
| Radar               | Signal detection   |
| Inbox               | Feedback intake    |
| MessageSquareText   | Feedback           |
| Tags                | Classification     |
| GitMerge            | Duplicate merge    |
| ChartNoAxesColumn   | Insights           |
| CircleDot           | Signal / status    |

---

## App layout theme

### Main app shell

Classic SaaS dashboard layout:

- Left sidebar
- Top header
- Main content area
- Right-side detail drawer (optional, later)

### Sidebar items (full)

- Dashboard
- Inbox
- Feedback
- Roadmap
- Changelog
- Users
- Settings

### Sidebar items (MVP / early upgraded version)

- Dashboard
- Inbox
- Feedback
- Tags
- Changelog
- Settings

### Inbox design

The inbox should feel like a **triage command center**.

| UI area              | Purpose                                   |
| -------------------- | ----------------------------------------- |
| Top summary cards    | New, Reviewing, High Priority, Stale      |
| Filter bar           | Type, status, tag, priority, date         |
| Feedback table/list  | Main triage queue                         |
| Status pills         | Quick workflow state                      |
| Priority badges      | Low / Medium / High / Critical            |
| Bulk actions (later) | Assign, tag, close, merge                 |
| Empty states         | Explain what to do next                   |

Example row:

> **\[Feature Request]** Better export options
> _"Would be useful to export filtered feedback to CSV..."_
> Tags: Export, Admin, Reporting · Status: Reviewing · Priority: Medium · Source: Web Form · Created: 2h ago

### Status badge design

Clear visual states. Keep labels calm — avoid overdramatic colors.

| Status      | Visual feel        |
| ----------- | ------------------ |
| New         | Neutral blue-gray  |
| Needs Info  | Amber              |
| Reviewing   | Purple / indigo    |
| Accepted    | Teal               |
| Planned     | Blue               |
| In Progress | Sky / cyan         |
| Shipped     | Green              |
| Closed      | Gray               |
| Spam        | Red                |

---

## Product language

Concise, product-management voice.

**Good copy:**

- New signal received.
- Feedback merged.
- Marked as planned.
- Status updated.
- User notified.
- No matching feedback found.
- This item may be a duplicate.

**Avoid:**

- Awesome!!!
- Your amazing feedback has been processed!
- Super-powered AI magic!

The app should feel **competent, not gimmicky**.

---

## Landing page theme

For `signalnest.app`, use a clean landing page.

### Hero

> **SignalNest**
> Capture the noise. Find the signal.
>
> A feedback triage app for turning user requests, bugs, and product
> ideas into clear next steps.

Primary CTA: **Open App**
Secondary CTA: **View Demo**

### Landing sections

| Section        | Purpose                                                                     |
| -------------- | --------------------------------------------------------------------------- |
| Hero           | Explain the product in one screen                                           |
| Problem        | Feedback gets scattered and repeated                                        |
| Solution       | Centralize, tag, prioritize, and close the loop                             |
| Feature grid   | Inbox, tags, statuses, notes, roadmap, changelog                            |
| Portfolio note | "Built as a full-stack portfolio project, usable as a real app."            |
| Footer         | Privacy, Terms, GitHub, Contact                                             |

### Page-level themes

| Page             | Theme direction                                       |
| ---------------- | ----------------------------------------------------- |
| Dashboard        | "Signal overview" with cards and small charts         |
| Inbox            | "Triage queue" with dense actionable rows             |
| Feedback detail  | "Case file" layout with timeline, notes, metadata     |
| Tags             | "Classification system"                               |
| Roadmap          | "From signals to planned work"                        |
| Changelog        | "Closed loop"                                         |
| Settings         | Clean admin controls                                  |
| Privacy / Terms  | Plain, trustworthy, minimal legalese                  |

---

## Best upgraded feature theme

For the upgraded version, organize around the workflow:

> **Intake → Triage → Prioritize → Act → Close the loop**

Map into the UI:

| Workflow step     | App feature                                 |
| ----------------- | ------------------------------------------- |
| Intake            | Submit form, public feedback                |
| Triage            | Inbox, type, status, priority               |
| Prioritize        | Tags, votes, severity, impact               |
| Act               | Roadmap, linked tasks, internal notes       |
| Close the loop    | Changelog, status emails                    |

This makes the app feel like a real product, not a random CRUD
dashboard.

---

## Suggested visual components

| Component     | Style                                           |
| ------------- | ----------------------------------------------- |
| Cards         | White, rounded-xl, subtle border                |
| Tables        | Clean rows, hover states, compact metadata     |
| Buttons       | Solid teal primary, gray secondary              |
| Badges        | Soft background + dark readable text            |
| Modals        | Simple centered or side drawer                  |
| Toasts        | Small bottom/right notifications                |
| Empty states  | Icon + short explanation + action               |
| Forms         | Spacious, clear labels, inline validation       |
| Charts        | Minimal, no chartjunk                           |
| Search        | Prominent in inbox                              |
| Filters       | Chips or dropdown row                           |

### Tailwind UI style direction (example)

```text
App background:    bg-slate-50
Cards:             bg-white border border-slate-200 rounded-2xl shadow-sm
Primary button:    bg-teal-600 hover:bg-teal-700 text-white rounded-xl
Secondary button:  bg-white border border-slate-300 text-slate-700 hover:bg-slate-50
Text:              text-slate-900
Muted:             text-slate-500
Status badge:      rounded-full px-2.5 py-1 text-xs font-medium
```

---

## App-name usage

**Use:** SignalNest

**Not:**

- Signal Nest
- Signalnest
- signalnest

In UI copy: _Welcome to SignalNest_
In logo / domain: `signalnest.app`
In repo (later, if ever): `signalnest`. Keeping the repo as
`feedback-triage-app` during development is fine — see
[ADR 057](../../adr/057-brand-vs-repo-naming.md).

---

## Final theme recommendation

Build the upgraded app as:

> **SignalNest** — a calm, modern feedback intelligence dashboard.
>
> **Visual metaphor:** signals gathered into a nest, then sorted into
> product decisions.
>
> **Style:** light SaaS dashboard, slate/white base, teal primary
> accent, amber warning accent, rounded cards, clean tables, subtle
> motion, practical copy.
>
> **Core promise:** _Capture the noise. Find the signal._

---

## Theme checklist

- [ ] Product name: SignalNest
- [ ] Domain: `signalnest.app`
- [ ] Tagline: _Capture the noise. Find the signal._
- [ ] Primary color: teal
- [ ] Secondary accent: amber
- [ ] Layout: sidebar SaaS dashboard
- [ ] Main workflow: Intake → Triage → Prioritize → Act → Close the loop
- [ ] Tone: calm, useful, trustworthy
- [ ] Avoid: gimmicky AI branding, loud colors, overcomplicated animations
