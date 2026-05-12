# v2.0 — Information Architecture

> Topical detail file. Entry point: [`../spec-v2.md`](../spec-v2.md).
> Cross-cutting UI rules live in [`ui.md`](ui.md). CSS plumbing
> lives in [`css.md`](css.md). Brand brief is
> [`core-idea.md`](core-idea.md).

Information architecture (IA) defines how the product's content and
pages are organised **before any visual design begins**. It is the
skeleton the rest of the UI hangs off: if the IA is wrong, no
amount of polished CSS, copy, or interaction design will rescue
the experience.

This document supersedes the older `pages.md`. It covers:

1. The IA framework — what we define and why.
2. The four good-IA principles that govern v2.0.
3. The concrete sitemap, route map, navigation structure, user
   flows, and page hierarchy for SignalNest v2.0.
4. The **pages catalog** — per-screen detail (sections,
   components, copy, empty states) for every route in the route
   map.

`ui.md` answers *"what are our UI conventions?"*. This file answers
*"what pages exist, how are they organised, and what's on each one?"*.

---

## What we define

Before any wireframe, mockup, or component lands, IA fixes the
following five surfaces:

| Surface | Question it answers | Where it lives |
| --- | --- | --- |
| **Sitemap** | Every page that exists. | [Sitemap](#sitemap) |
| **Route map** | The exact URL structure. | [Route map](#route-map) |
| **Navigation structure** | What appears in menus, and where. | [Navigation structure](#navigation-structure) |
| **User flows** | Common paths through the site. | [User flows](#user-flows) |
| **Page hierarchy** | Which pages are parent / child. | [Page hierarchy](#page-hierarchy) |

Anything not in this file is not a v2.0 page. Adding a route
requires updating this file in the same commit.

---

## Good IA principles

These four principles bind every decision below. They override
local preferences, "neater" URLs, and stylistic taste.

### Group related pages together

Pages that serve the same user goal live under the same parent in
the sitemap and the same section of the nav. The public marketing
surface (landing, pricing-style feature copy, public roadmap,
public changelog) is grouped under `/` and `/w/<slug>/...public`
endpoints; the authenticated product surface is grouped under
`/w/<slug>/...`. Grouping reduces the number of decisions a user
has to make to find what they need.

### Match the URL structure to the navigation

The URL in the address bar reflects where the user is in the site
hierarchy. The nav path *App → Settings → Members* maps to
`/w/<slug>/settings#members`, not to `/members` or
`/user/account/team`. Users who share links, use the back button,
or edit the URL directly get the result they expect.

### Avoid deep nesting beyond three levels

No v2.0 route exceeds three structural levels
(`/w/<slug>/feedback/<id>` is the deepest). If a future surface
wants a fourth level, it must either flatten the hierarchy or be
promoted to its own top-level section. Deep nesting breaks
breadcrumbs and mobile nav and signals that content can be
reorganised.

### Name pages by what the user does, not internal jargon

Page names reflect the user's task. `/inbox` (not `/triage-queue`),
`/feedback` (not `/items`), `/submitters` (not `/contacts`),
`/sign-up` (not `/registration`). Slugs that only make sense to
someone who already works on the product get renamed before they
ship.

---

## Sitemap

Tree view of every page that exists in v2.0. Indentation = nesting.

    SignalNest
    ├── Public marketing
    │   └── Landing                        (/)
    │
    ├── Auth
    │   ├── Login                          (/login)
    │   ├── Signup                         (/signup)
    │   ├── Forgot password                (/forgot-password)
    │   ├── Reset password                 (/reset-password)
    │   ├── Verify email                   (/verify-email)
    │   └── Accept invitation              (/invitations/<token>)
    │
    ├── Public workspace surface
    │   ├── Submit                         (/w/<slug>/submit)
    │   ├── Public roadmap                 (/w/<slug>/roadmap/public)
    │   └── Public changelog               (/w/<slug>/changelog/public)
    │
    ├── App (authenticated, workspace-scoped under /w/<slug>/)
    │   ├── Dashboard                      (/dashboard)
    │   ├── Inbox                          (/inbox)
    │   ├── Feedback
    │   │   ├── List                       (/feedback)
    │   │   └── Detail                     (/feedback/<id>)
    │   ├── Submitters
    │   │   ├── List                       (/submitters)
    │   │   └── Detail                     (/submitters/<id>)
    │   ├── Roadmap (management)           (/roadmap)
    │   ├── Changelog (management)         (/changelog)
    │   ├── Insights                       (/insights)
    │   └── Settings                       (/settings)
    │
    ├── Reference
    │   └── Styleguide                     (/styleguide)
    │
    └── System
        ├── 404 Not found                  (/404)
        ├── 403 Forbidden                  (/403)
        └── 500 Server error               (/500)

---

## Route map

Concrete URL structure. This is the authoritative list of routes
v2.0 ships. Anything else 404s.

    /
      login
      signup
      forgot-password
      reset-password
      verify-email
      invitations/<token>
      styleguide
      404
      403
      500

    /w/<slug>
      submit
      roadmap/public
      changelog/public

      dashboard
      inbox
      feedback
      feedback/<id>
      submitters
      submitters/<id>
      roadmap
      changelog
      insights
      settings

**URL conventions:**

- Workspace scope is always the second path segment
  (`/w/<slug>/...`). The literal `/w/` is the tenant prefix; see
  [`multi-tenancy.md`](multi-tenancy.md).
- `slug` is kebab-case, immutable after creation (see
  [Settings](#settings)).
- Resource IDs are integers in v2.0 — UUIDs are deferred.
- Public surfaces under a workspace are suffixed `/public` or
  carry no auth (`/submit`), keeping them clearly distinct from
  the management surface at the same path root.
- Query strings carry state (filters, search, pagination),
  never identity.

---

## Navigation structure

The visible nav is intentionally narrow: too many top-level items
is itself a sign the IA is wrong.

### Public (unauthenticated)

A single header on the landing page:

- Wordmark (link to `/`)
- *Log in* (link to `/login`)
- *Start free* (primary button, link to `/signup`)

Public workspace surfaces (`/w/<slug>/submit`, public roadmap,
public changelog) carry **no internal nav** at all — just the
workspace name and a *Powered by SignalNest* footer link. This is
deliberate: these pages are for outsiders, not for product
navigation.

### Authenticated (in-app)

Primary nav (left rail on `lg`, bottom bar on narrow):

1. Dashboard
2. Inbox
3. Feedback
4. Submitters
5. Roadmap
6. Changelog
7. Insights

Secondary nav (header, top-right):

- Workspace switcher (if user belongs to >1 workspace)
- Settings (gear icon, links to `/w/<slug>/settings`)
- User menu (avatar → *Sign out*)

**What is deliberately not in the nav:**

- *Public roadmap* / *Public changelog* are not in the nav — they
  are reached via per-item *Publish* toggles and a *View public
  page* link inside the management views.
- *Styleguide* is reachable by URL only; it's a reference page,
  not a product surface.
- Error pages are reached by failure, not navigation.

---

## User flows

The four flows below cover ~95% of real sessions. Each one is
deliberately short — long flows are an IA smell.

### Flow 1 — New user signs up and lands in their workspace

    Landing (/)
      → Signup (/signup)
      → [auto-create workspace + first membership]
      → Dashboard (/w/<slug>/dashboard) with "Check your email" banner

### Flow 2 — External submitter files feedback

    Public submit (/w/<slug>/submit)
      → [POST] → Thank-you confirmation on same route
      (optional) → Public roadmap (/w/<slug>/roadmap/public)

### Flow 3 — Team member triages a new item

    Login (/login)
      → Dashboard (/w/<slug>/dashboard)
      → Inbox (/w/<slug>/inbox)
      → Feedback detail (/w/<slug>/feedback/<id>)
      → [edit status / tags / priority / publish toggles]
      → back to Inbox

### Flow 4 — Closing the loop on a shipped item

    Feedback detail (/w/<slug>/feedback/<id>)
      → set status = shipped
      → toggle "Publish to changelog"
      → Changelog management (/w/<slug>/changelog)
      → write release-note text
      → [submitter is emailed automatically — see email.md]

---

## Page hierarchy

Parent/child relationships drive breadcrumbs, back-links, and the
shape of the nav. Children inherit the auth and tenancy of their
parent.

| Parent | Children |
| --- | --- |
| `/` | `/login`, `/signup`, `/forgot-password`, `/reset-password`, `/verify-email`, `/invitations/<token>`, `/styleguide`, `/404`, `/403`, `/500` |
| `/w/<slug>` (public) | `/submit`, `/roadmap/public`, `/changelog/public` |
| `/w/<slug>/dashboard` | — (leaf) |
| `/w/<slug>/inbox` | — (leaf, but cards link into filtered `/feedback` views) |
| `/w/<slug>/feedback` | `/w/<slug>/feedback/<id>` |
| `/w/<slug>/submitters` | `/w/<slug>/submitters/<id>` |
| `/w/<slug>/roadmap` | — (leaf; mirrors public version) |
| `/w/<slug>/changelog` | — (leaf; mirrors public version) |
| `/w/<slug>/insights` | — (leaf) |
| `/w/<slug>/settings` | tab anchors (`#workspace`, `#members`, `#tags`, `#profile`, `#security`) — not separate routes |

**Settings tabs are intentionally anchors, not routes**, because
they share state (the same workspace, the same user) and are
loaded together. Promoting them to routes would push the hierarchy
to four levels and violate the *avoid deep nesting* principle.

---

## Common tools

For working on the IA itself, before committing changes to this
file:

- **FigJam** or **Excalidraw** — draw the sitemap and user flows
  visually before writing the route map. Good for spotting
  orphaned pages and broken flows.
- **Whimsical** — clean flowchart and sitemap diagrams, useful
  when sharing IA proposals outside the repo.
- **Any text editor** — the route map and sitemap above are plain
  Markdown and live in this file. The diagram is the spec; the
  visual tool is scratch work.

---

# Pages catalog

The remainder of this file is the **per-screen catalog**. For every
route in the [Route map](#route-map) above it lists: who can access
it, the document sections in source order, the components used, the
empty / error states, and the page-specific copy strings.

## Page index

Public:

- [Landing (`/`)](#landing)
- [Login (`/login`)](#login)
- [Signup (`/signup`)](#signup)
- [Forgot password (`/forgot-password`)](#forgot-password)
- [Reset password (`/reset-password`)](#reset-password)
- [Verify email (`/verify-email`)](#verify-email)
- [Accept invitation (`/invitations/<token>`)](#accept-invitation)
- [Public submit (`/w/<slug>/submit`)](#public-submit)
- [Public roadmap (`/w/<slug>/roadmap/public`)](#public-roadmap)
- [Public changelog (`/w/<slug>/changelog/public`)](#public-changelog)
- [Styleguide (`/styleguide`)](#styleguide)

Authenticated, workspace-scoped (`/w/<slug>/...`):

- [Dashboard](#dashboard)
- [Inbox](#inbox)
- [Feedback list](#feedback-list)
- [Feedback detail](#feedback-detail)
- [Submitters list](#submitters-list)
- [Submitter detail](#submitter-detail)
- [Roadmap (management)](#roadmap-management)
- [Changelog (management)](#changelog-management)
- [Insights](#insights)
- [Settings](#settings)

System:

- [Errors (404 / 403 / 500)](#error-pages)

---

## Conventions used below

- **Sections** are listed top-to-bottom in source order. Each is a
  `<section>` (or `<header>` / `<main>` / `<aside>` where the tag
  is more meaningful).
- **Components** reference the vocabulary from
  [`css.md`](css.md#component-vocabulary).
- **Copy strings** in italics are the literal user-facing text;
  they live in HTML, not in JS.
- Every page sets `<title>` as `<Page> · <Workspace?> · SignalNest`.
- Every page has a skip-link to `#main` and exactly one `<h1>`.

---

<a id="landing"></a>
## Landing — `/`

**Auth:** none. Logged-in users redirect to
`/w/<their-slug>/dashboard`.

**Sections (top to bottom):**

1. **Header** — wordmark left; *Log in* / *Start free* buttons
   right.
2. **Hero** — `<h1>` *SignalNest*, subhead *Capture the noise. Find
   the signal.*, sub-subhead the locked description, CTAs *Start
   free* (primary) and *Try the demo* (secondary, scrolls to §3).
3. **Mini demo (FU1)** — interactive client-side widget
   ([`ui.md`](ui.md#mini-demo-fu1)). Anchor `#demo`.
4. **Problem** — *Feedback gets scattered and repeated.* Three
   short paragraphs.
5. **Solution** — *Centralize, tag, prioritize, close the loop.*
   Three icon + heading + sentence cards.
6. **Feature grid** — Inbox, Tags, Statuses, Notes, Submitters,
   Roadmap, Changelog, Insights. Lucide icon + label + sentence.
7. **Workflow strip** — five-step horizontal: Intake → Triage →
   Prioritize → Act → Close the loop.
8. **Portfolio note** — single sentence: *Built as a full-stack
   portfolio project, usable as a real app.*
9. **Footer** — Privacy, Terms, GitHub, Contact.

**Components:** `sn-button-primary`, `sn-button-secondary`, `sn-card`.

**Empty / error:** none — fully static.

**Tracking:** none in v2.0.

---

<a id="login"></a>
## Login — `/login`

**Auth:** redirect logged-in users to `/w/<slug>/dashboard`.

**Sections:** centered card containing email + password + *Log in*
button + *Forgot password?* link.

**Errors:** *Email or password is incorrect.* (single message; no
account-enumeration leak).

**Post-success:** redirect to `?next=` if safe, else
`/w/<slug>/dashboard`.

---

<a id="signup"></a>
## Signup — `/signup`

**Auth:** redirect logged-in users.

**Sections:** centered card. Fields:

| Field           | Notes                                                     |
| --------------- | --------------------------------------------------------- |
| Display name    | required, 1–80 chars                                      |
| Email           | required, RFC 5322 plus `EmailStr`                        |
| Password        | required, min 12 chars, Argon2id                          |
| Workspace name  | required; slug autogenerated below the field, editable    |

**Errors:** *Email already in use.* / *Workspace slug taken.* /
*Password too short.*

**Post-success:** the user is logged in immediately, an email
verification link is sent (fail-soft per [`email.md`](email.md)),
and the browser lands on `/w/<slug>/dashboard` with a banner
*Check your email to verify your address.*

---

<a id="forgot-password"></a>
## Forgot password — `/forgot-password`

Email-only form. Always shows the same success message regardless
of whether the email exists: *If an account exists for this
address, a reset link is on its way.*

---

<a id="reset-password"></a>
## Reset password — `/reset-password?token=...`

Token verified server-side. Two fields: new password + confirm.
Errors: *Reset link is invalid or expired.*, *Passwords do not
match.* On success: log the user in and redirect to dashboard with
banner *Password updated.*

---

<a id="verify-email"></a>
## Verify email — `/verify-email?token=...`

Token verified server-side. On success: banner *Email verified.*
and redirect to `/w/<slug>/dashboard`. Token expiry: 24h
([`auth.md`](auth.md)).

---

<a id="accept-invitation"></a>
## Accept invitation — `/invitations/<token>`

Shows the inviting workspace's name and the role being offered. If
the user is logged out, prompts login or signup; if logged in,
prompts *Accept invitation*. On accept, creates a row in
`workspace_memberships` and redirects to the workspace's dashboard.

Errors: *Invitation is invalid or expired.*, *You are already a
member of this workspace.*

---

<a id="public-submit"></a>
## Public submit — `/w/<slug>/submit`

**Auth:** none. Honeypot field hidden via CSS, server silently
drops non-empty submissions ([`security.md`](security.md)).

**Sections:**

1. Header with workspace name (no login link, no internal nav).
2. Form — see [`ui.md`](ui.md#public-submission-form) for fields.
3. Footer with *Powered by SignalNest* link.

**Post-success:** thank-you page with the **locked copy**
([`copy-style-guide.md`](copy-style-guide.md)):

> *Got it. Thanks for the signal. We'll let you know if we have
> questions or when this ships.*

If the submitter provided an email, also: *Watch for status
updates from us at \<their email\>.* Optional CTA *See the public
roadmap* if `published_to_roadmap` items exist.

---

<a id="public-roadmap"></a>
## Public roadmap — `/w/<slug>/roadmap/public`

**Auth:** none. Read-only.

**Sections:** workspace name banner; three columns — *Planned*,
*In progress*, *Recently shipped (last 30 days)*. Each card shows
title, type pill, tags, no submitter info.

**Empty:** *Nothing on the public roadmap yet.*

---

<a id="public-changelog"></a>
## Public changelog — `/w/<slug>/changelog/public`

**Auth:** none. Read-only. Reverse-chronological list of items
where `status = 'shipped'` and `published_to_changelog = true`.
Each entry: shipped date, title, optional release-note text.

**Empty:** *Nothing shipped yet.*

---

<a id="styleguide"></a>
## Styleguide — `/styleguide`

**Auth:** none. Authoritative reference for every component in
every theme. See [ADR 056](../../../adr/056-style-guide-page.md).

**Sections:** for each theme preset, render a section per
component (cards, buttons, pills, inputs, dialog, toast, table
row, status pill set, priority pill set, pain-dot indicator,
inline SVG charts).

---

<a id="dashboard"></a>
## Dashboard — `/w/<slug>/dashboard`

**Auth:** session + workspace membership.

**Sections:**

1. Header strip: greeting *Welcome back, \<name\>.*; current
   workspace name; primary action *New feedback*.
2. Summary cards row (5 cards): *New*, *Needs Info*, *Reviewing*,
   *High priority*, *Stale (> 14 days)*. Each card shows a count
   and links into a filtered Inbox view. *Stale* counts items where
   `created_at < now() - interval '14 days' AND status IN ('new', 'needs_info')`
   ([`glossary.md`](glossary.md)).
3. Intake sparkline card — last-30-day inline-SVG bar chart of
   feedback intake.
4. Top tags card — top 5 tags by count.
5. Recent activity card — last 10 status-change events.

**Empty (new workspace):** big illustration-free hero card —
*No feedback yet.* with two CTAs: *Share your public form* (copies
`/w/<slug>/submit` URL) and *Add your first item*.

---

<a id="inbox"></a>
## Inbox — `/w/<slug>/inbox`

**Auth:** session + workspace membership.

**Sections:**

1. Page header: `<h1>` *Inbox*, count chip e.g. *24 items*.
2. Summary cards (same five as dashboard).
3. Filter bar: Type, Status, Tag, Priority, Source, Date.
4. Search input (`description ILIKE`).
5. Table — columns: title, type, status pill, priority pill, pain
   dots, tags, submitter chip, age. Sticky header.
6. Pagination footer (skip / limit / total).

**Defaults:** filtered to `status IN ('new', 'needs_info',
'reviewing')`. The Inbox is for triage; closed and shipped items
live on the Feedback list.

**Empty:** *Inbox zero. Nice.*

---

<a id="feedback-list"></a>
## Feedback list — `/w/<slug>/feedback`

Same shell as Inbox, but with no default status filter. This is
the searchable archive across **every** status.

**Empty:** *No feedback matches these filters.*

---

<a id="feedback-detail"></a>
## Feedback detail — `/w/<slug>/feedback/<id>`

**Auth:** session + workspace membership.

**Layout:** "case file" — two-column on `lg`, stacked below.

Left column (main):

1. Header — back link to Inbox, title (editable inline by
   members), type pill, status pill, priority pill, pain dots.
2. Description block — multi-line, editable inline.
3. Internal notes — append-only thread; each note has author,
   timestamp, edit (within 15 minutes of creation —
   [`api.md`](api.md)), delete (own only).
4. Timeline — read-only system log of status changes,
   tag changes, merges.

Right column (aside):

1. Submitter card — name, email (if known), submission count, link
   to submitter detail.
2. Metadata card — created at, source, public-form URL if applicable.
3. Tags editor.
4. Publishing toggles — *Publish to roadmap*, *Publish to changelog*.
5. Danger zone — *Mark as spam*, *Merge into…*, *Delete*.

**Errors:** *This item is in another workspace.* → 404 (we do not
disclose existence across tenants).

---

<a id="submitters-list"></a>
## Submitters list — `/w/<slug>/submitters`

Table of unique submitters in the workspace: email, display name,
submission count, last-seen, link to detail.

**Empty:** *No known submitters yet. Public submissions without an
email do not appear here.*

---

<a id="submitter-detail"></a>
## Submitter detail — `/w/<slug>/submitters/<id>`

Header with email + display name + edit name. Below, a list of
every feedback item from this submitter, reverse-chronological.
Inline status pill per row.

---

<a id="roadmap-management"></a>
## Roadmap (management) — `/w/<slug>/roadmap`

Three-column kanban-style view: *Planned*, *In progress*,
*Recently shipped*. Cards drag between columns (status change is
the side effect). Each card has a *Publish to public roadmap*
toggle.

**Empty per column:** *No planned items.* / *Nothing in progress.*
/ *Nothing shipped yet.*

---

<a id="changelog-management"></a>
## Changelog (management) — `/w/<slug>/changelog`

Reverse-chronological list of `status = 'shipped'` items. Each row
shows the shipped date, title, an editable release-note field, and
the *Publish to changelog* toggle.

---

<a id="insights"></a>
## Insights — `/w/<slug>/insights`

Three cards in v2.0:

1. **Top tags** — bar chart of top 10 tags by item count.
2. **Status mix** — donut of items per status.
3. **Pain heat** — histogram of `pain_level` distribution.

All charts are inline SVG, no library.

**Empty:** *Insights appear once you have at least 10 feedback
items.*

---

<a id="settings"></a>
## Settings — `/w/<slug>/settings`

Tabbed page (`<details>`-based on narrow screens):

1. **Workspace** — editable name + read-only slug (`slug` is
   immutable in v2.0; changing it would break public form, roadmap,
   and changelog URLs already shared) + public-submit toggle.
2. **Members** *(owner only)* — table of members with role +
   *Invite* button + *Remove* per row.
3. **Tags** — CRUD for the workspace's tag library.
4. **Profile** — current user's display name + email.
5. **Security** — change password.
6. **Sign out** — explicit button at the bottom of the page.

Owner-only sections are hidden, not just disabled, for non-owners.

---

<a id="error-pages"></a>
## Error pages

| Status | Page                                              | Copy                                                        |
| ------ | ------------------------------------------------- | ----------------------------------------------------------- |
| 404    | `/404` (also rendered for cross-tenant lookups)   | *Not found.* + *Back to dashboard* button.                  |
| 403    | `/403`                                             | *You don't have access to that.*                            |
| 500    | `/500`                                             | *Something went wrong. The team has been notified.*         |

The 500 page does not echo the exception. The request id is
displayed (for support correspondence) and logged.

---

## Cross-references

- [`ui.md`](ui.md) — cross-cutting UI conventions.
- [`css.md`](css.md) — component vocabulary referenced above.
- [`layout.md`](layout.md) — page-shell composition.
- [`api.md`](api.md) — endpoints each page calls.
- [`auth.md`](auth.md) — auth state behind login / signup / reset.
- [`multi-tenancy.md`](multi-tenancy.md) — `/w/<slug>/` tenant
  prefix and isolation rules.
- [`security.md`](security.md) — public-form honeypot & CSP.
- [`core-idea.md`](core-idea.md) — voice & visual rules.
