# Web App Tooling — Learning Notes

A field guide to the web-app tools that show up in tutorials, job
listings, and "what should I use?" arguments. Written for someone who
wants to recognize each tool, know when it's the right pick, and know
what *this* repo would lose or gain by adopting it.

> Companion to:
> - [`frontend-conventions.md`](frontend-conventions.md) — the
>   conventions this project actually follows.
> - [`tool-comparison.md`](tool-comparison.md) — quick "A vs B" picks.

---

## 1. What is a web app, succinctly

A **web app** is software you use through a browser. The browser is
the runtime; HTTP is the protocol; HTML / CSS / JavaScript are the
delivery format.

In practice every web app is some combination of:

1. A **server** that owns the data and the rules (auth, validation,
   business logic). Talks to a database.
2. A **transport** — HTTP requests carrying HTML pages, JSON
   payloads, or both.
3. A **client** running in the browser — HTML for structure, CSS for
   look, JavaScript for behavior.

The interesting design choice is **where each piece of work lives**:

| Style | Where HTML is generated | Where state lives | Example |
| --- | --- | --- | --- |
| **Static site** | At build time | Nowhere (read-only) | Personal blog, docs site |
| **Server-rendered (MPA)** | On the server, per request | Server + DB | Django, Rails, this app |
| **Server-rendered + sprinkles** | Server + a dash of client JS | Server + DB | This app + htmx, Hotwire |
| **SPA (Single-Page App)** | In the browser, after a JSON fetch | Browser + server APIs | React/Vue/Svelte against a JSON API |
| **SSR'd SPA** | Server first, then hydrated in browser | Both | Next.js, Nuxt, SvelteKit |

The mistake most beginners make is **picking SPA-shaped tools for
MPA-shaped problems**. A CRUD admin tool with five pages does not
need React. A real-time collaborative whiteboard probably does.

---

## 2. The frontend stack — vocabulary first

Before naming tools, name the layers each one occupies:

| Layer | What it does | Tools that live here |
| --- | --- | --- |
| **Markup** | Structure and meaning | HTML, JSX, Vue templates, Jinja |
| **Style** | Visual presentation | CSS, Sass, Tailwind, Pico, Bootstrap |
| **Behavior** | Reactivity, state, fetches | Vanilla JS, Alpine, htmx, React, Vue, Svelte |
| **Build** | Bundling, transpiling, asset pipeline | Vite, esbuild, Webpack, Parcel |
| **Routing** | Mapping URLs to views | Browser-native, React Router, Next.js, FastAPI routes |
| **State / data** | Storing UI state, caching server data | useState, Pinia, Redux, TanStack Query, SWR |
| **Server runtime** | Python / Node / Go / Ruby / etc. | FastAPI (this), Django, Rails, Express, Next.js (server) |
| **Templating** | Server-side HTML generation | Jinja, ERB, Liquid, Tera, Razor |

Most "frameworks" bundle several layers. Picking a framework is
picking which layers to delegate.

---

## 3. CSS tooling

### Plain CSS (with custom properties + nesting)

- **What:** The language. Modern CSS (Baseline 2024) has variables,
  nesting, `:has()`, container queries, and logical properties.
- **When:** Always your default. Reach for anything else only with a
  reason.
- **Pros:** Zero build, zero deps, works forever, MDN docs are the
  spec.
- **Cons:** No tokens at compile time (use custom properties
  instead), no mixins (use `@apply` patterns or just write the rule
  twice).
- **For this repo:** Already in use. Stay here.

### Sass / SCSS

- **What:** A CSS preprocessor adding variables, mixins, partials,
  nesting (predates native CSS nesting).
- **When:** Large legacy codebases that already use it. Rare for new
  projects in 2026.
- **Pros:** Mature, well-documented, fine ergonomics.
- **Cons:** Build step. Most features are now native CSS. Adopting it
  *today* is a step backward.
- **For this repo:** No. Spec forbids preprocessors.

### Tailwind CSS

- **What:** A utility-first CSS framework. You compose styles by
  stacking class names: `<div class="flex items-center gap-2 p-4
  rounded-lg bg-slate-100">`.
- **When:** Teams that ship UI fast, value design-system constraints,
  and don't mind verbose markup. Common with React/Vue/Svelte.
- **Pros:** Tiny final CSS (only used classes are bundled). Strong
  design constraints prevent bikeshedding. Excellent IDE tooling.
- **Cons:** Markup gets noisy. Requires a build step (Tailwind 4
  improves this). Locks visual choices into class soup — you can't
  restyle by swapping a stylesheet. The "tags carry meaning, classes
  carry style" rule (this project's frontend conventions) gets
  inverted: classes carry *both*.
- **For this repo:** No without an ADR. Conflicts with the
  vanilla-CSS-plus-tokens convention. If you ever rewrite the
  frontend with a JS framework, reconsider.

### Pico.css

- **What:** A "classless" CSS framework. Style semantic HTML
  directly: `<button>` is already styled, `<table>` is already
  styled, no class names needed.
- **When:** Static sites, admin panels, prototypes, demos. Anywhere
  you want "looks decent out of the box" without a design system.
- **Pros:** Zero build, single CSS file, ~10 KB. Pairs perfectly
  with semantic HTML. Has a dark mode and tokens.
- **Cons:** Opinionated look — every Pico site looks similar. Limited
  components (no built-in modal, no tabs).
- **For this repo:** **Strong fit.** Could replace or live alongside
  `styles.css`. One link tag, no build, supports the existing
  semantic HTML directly. Worth a small experiment branch.

### Bootstrap

- **What:** The original component-first CSS framework. Pre-built
  buttons, cards, modals, grids, navbars.
- **When:** Internal tools, dashboards where speed > distinctiveness.
  Still huge in enterprise.
- **Pros:** Massive component library, well-documented, ubiquitous.
  jQuery-free since v5.
- **Cons:** Every Bootstrap site looks the same. Heavy CSS payload
  unless purged. Components depend on specific markup structures
  (high coupling). Reads as "didn't bother on the design" in 2026.
- **For this repo:** No. Tailwind/Pico are better picks if you want a
  framework.

### Open Props / Every Layout / "no-framework" toolkits

- **What:** A library of CSS custom properties (Open Props) or
  copy-paste layout primitives (Every Layout). Not a framework —
  ingredients.
- **When:** When you want tokens or layout patterns without buying a
  framework's opinions on components.
- **Pros:** Composable. Easy to drop in.
- **Cons:** You still write components yourself.
- **For this repo:** Open Props is a reasonable source for the token
  values in `tokens.css` (recommended in `frontend-conventions.md`).

---

## 4. Behavior tooling — JS frameworks and friends

### Vanilla JavaScript (with Fetch API)

- **What:** Just JS. `addEventListener`, `fetch`, DOM APIs. Modern
  browsers expose enough to build real apps.
- **When:** Apps with little client-side state, MPA shape, < ~1000
  lines of JS. **This project.**
- **Pros:** Zero deps, zero build, zero churn. Fastest possible page
  load. Works in 10 years without a rewrite.
- **Cons:** State management, templating, and reactivity are
  manual. Scales poorly past a few thousand lines.
- **For this repo:** Already in use. Right answer for v1.0.

### htmx

- **What:** A small JS library (~14 KB) that lets HTML attributes
  drive Ajax. `<button hx-post="/api/items" hx-target="#list">` does
  what it looks like.
- **When:** Server-rendered apps that want "feels like an SPA"
  without writing client-side JS. Pairs beautifully with FastAPI,
  Django, Rails.
- **Pros:** State stays on the server. No build. No client-side
  routing. Tiny mental model. Great DX for CRUD.
- **Cons:** Server returns HTML fragments, not JSON — your API now
  does double duty (or you add a second set of endpoints). Heavy
  client-side interactions (drag-and-drop, charts) still need
  separate JS.
- **For this repo:** **Excellent fit for v2.** Tier-1 features
  (inline edit, optimistic delete, snappy filter updates) become
  one-liners. **Needs an ADR** — the spec currently says "Fetch API
  only." See [`frontend-conventions.md`](frontend-conventions.md) §5
  Tier-1 list.

### Alpine.js

- **What:** A small (~15 KB) reactivity library. Sprinkles on
  existing HTML: `<div x-data="{ open: false }" x-show="open">`.
- **When:** Server-rendered apps that need *client-side* reactive
  bits (toggles, dropdowns, tabs) without a full SPA framework.
- **Pros:** Familiar Vue-like syntax. No build step (script tag).
  Composes with htmx.
- **Cons:** Behavior lives in HTML attributes — gets messy past a
  few directives. Not great for shared state across the page.
- **For this repo:** Optional companion to htmx if you find yourself
  writing repetitive vanilla-JS toggles. Otherwise vanilla is fine.

### React

- **What:** A JS library for building component-based UIs.
  Component = function returning JSX (HTML-in-JS). State via
  hooks. Industry default for SPAs.
- **When:** Apps with rich client-side state, lots of components,
  team familiarity. JSON-API + React is the textbook SPA.
- **Pros:** Huge ecosystem, jobs market, mature tooling
  (Vite/Next/Remix). Component reuse is real.
- **Cons:** Heavy mental model (hooks, effects, memoization, key
  rules). Build pipeline. Hydration costs. Versions break things.
  Overkill for ≤10 pages of CRUD.
- **For this repo:** **No.** Would mean a full rewrite, two-codebase
  setup (FastAPI as JSON API + a React app), and a build pipeline.
  None of that is justified by the feature set. If you ever build a
  collaborative dashboard with realtime updates, reconsider.

### Vue

- **What:** A progressive JS framework. Single-file components
  (`.vue` files) with `<template>`, `<script>`, `<style>`.
- **When:** Same shape as React, slightly gentler curve. Strong in
  Asia and Europe.
- **Pros:** Easier to learn than React. Excellent docs.
  Server-side rendering via Nuxt.
- **Cons:** Smaller job market than React. Still a full SPA
  framework with all the costs.
- **For this repo:** No. Same reasons as React.

### Svelte / SvelteKit

- **What:** A *compiler* (not a runtime) — components compile to
  vanilla JS. SvelteKit is the meta-framework (routing, SSR).
- **When:** New SPA projects where bundle size and runtime
  performance matter. Loved by developers in surveys.
- **Pros:** Tiny output, excellent ergonomics, fast.
- **Cons:** Smaller ecosystem than React. Job market still niche.
- **For this repo:** No. Same reasons as React, but it's the
  framework I'd reach for first if a JS framework became
  necessary.

### Solid / Qwik / Lit / others

- **What:** Niche frameworks each solving a specific problem (Solid =
  React-like with finer-grained reactivity, Qwik = resumability,
  Lit = web components).
- **When:** Specific advanced needs. Not for general adoption.
- **For this repo:** No.

### jQuery

- **What:** The 2010s DOM helper. Mostly obsolete in new code —
  modern browsers have `querySelector`, `fetch`, etc. Still common
  in legacy WordPress / Rails apps.
- **For this repo:** No. Vanilla covers it.

---

## 5. Build tooling

### No build (script tags)

- Smallest, fastest, most boring. What this project does.

### Vite

- The modern default for new JS projects. Dev server with HMR,
  production bundle via Rollup.
- Pulls in: a package.json, a node_modules, a build step in CI.
- **For this repo:** Only if a JS framework arrives.

### esbuild / SWC / Bun

- Faster build cores. Often invoked by Vite/Next under the hood.

### Webpack

- The 2010s build behemoth. Slow, complicated. Avoid in new
  projects.

### Parcel / Rollup

- Alternatives to Vite. Mature, fine, less momentum.

---

## 6. Server / backend frameworks

### FastAPI

- **What:** A Python ASGI framework focused on type-driven APIs and
  OpenAPI generation. **What this project uses.**
- **When:** API-first apps in Python. Pairs with any frontend.
- **Pros:** Pydantic-native, excellent docs, automatic OpenAPI,
  async-ready. Fast.
- **Cons:** No built-in templating opinion (you choose), no built-in
  ORM (you choose), no admin (you choose). "Choose" can be a con if
  you wanted defaults.
- **Sweet spot:** JSON API + small static frontend, exactly this.

### Django

- **What:** The "batteries included" Python web framework. ORM,
  admin, auth, forms, templates, middleware — all in the box.
- **When:** Server-rendered apps that need auth, an admin panel, and
  rapid CRUD scaffolding. Most "boring web app" jobs.
- **Pros:** Conventions over configuration. Free admin UI is
  legendary. Mature security defaults.
- **Cons:** Sync-first (async support exists but is uneven). Class-
  based views can be opaque. Big surface area to learn.
- **For this repo:** Would have been a reasonable alternative
  starting point. Today, switching means rewriting everything; not
  worth it. **For your *next* portfolio piece**, Django demonstrates
  a different skill set — worth considering.

### Flask / Starlette / FastHTML

- **What:** Smaller Python frameworks. Flask = the OG micro-framework
  (sync). Starlette = ASGI core that FastAPI is built on. FastHTML =
  newer, server-rendered with htmx baked in.
- **When:** Flask is fine for tiny apps. Starlette if you want
  FastAPI-like primitives without Pydantic. FastHTML if you want
  htmx-first server-rendered Python.
- **For this repo:** No reason to migrate; FastAPI covers it.

### Rails / Laravel / Phoenix / Spring / .NET

- Different languages, similar shape to Django (server-rendered,
  batteries included). Worth knowing they exist; not relevant to
  this project.

### Express / NestJS / Fastify

- Node web frameworks. Express is the bare metal; NestJS is the
  "Angular for the backend"; Fastify is the fast one.
- **For this repo:** No.

### Next.js / Nuxt / SvelteKit / Remix

- "Meta-frameworks" that fuse a JS framework + SSR + routing + data
  loading.
- **When:** You want a single full-stack JS codebase, often deployed
  to Vercel.
- **Pros:** One language end-to-end, excellent DX, file-based
  routing.
- **Cons:** Hosting is opinionated (best on Vercel). Lock-in.
  Hydration tax. Pulls you toward Tailwind + React conventions.
- **For this repo:** No — different runtime entirely.

---

## 7. Database / ORM

### SQLModel (this project)

- Pydantic + SQLAlchemy mash-up. Same model defines API schema and
  DB schema.
- **Pros:** Less duplication. Type-driven.
- **Cons:** Younger than SQLAlchemy, fewer Stack Overflow answers.

### SQLAlchemy

- The Python ORM. Powerful, mature, has a Core (SQL builder) and an
  ORM layer.
- **For this repo:** Already underneath SQLModel.

### Django ORM

- Different idioms (`Model.objects.filter(...)`). Tied to Django.

### Prisma

- TypeScript-first ORM with a schema language. Common in Next.js
  apps.

### Raw SQL + a thin client (`asyncpg`, `psycopg`)

- Sometimes the right answer. Skips an abstraction layer for hot
  paths or complex queries.

### NoSQL (MongoDB, DynamoDB, Firestore)

- Different shape entirely. Good for document-heavy or extreme-scale
  use cases. Wrong for triage CRUD.

---

## 8. Hosting / runtime

| Platform | Shape | Cost shape | Right for this repo |
| --- | --- | --- | --- |
| **Railway** | PaaS (containers + plugins) | Per-second compute | **Yes — current** |
| **Render** | PaaS, similar to Railway | Per-second compute | Yes (alternative) |
| **Fly.io** | Container PaaS, region-aware | Per-second compute | Yes |
| **Heroku** | OG PaaS | Per-dyno-hour | Mostly legacy at this point |
| **Vercel** | Frontend-first, serverless functions | Per-invocation | No (Python support is limited) |
| **Cloudflare Workers / Pages** | Edge functions | Per-request | No (need a long-lived DB connection) |
| **AWS / GCP / Azure** | Raw cloud | Pay-per-resource | Overkill |
| **VPS (Hetzner, DO droplet)** | A box with SSH | Flat monthly | Fine, but you maintain it |
| **Self-host (homelab)** | Hardware | Electricity | Cute, not portfolio-friendly |

---

## 9. Pulling it together — when to use what

### Tiny tool / personal site / docs

- **Static site generator** (Hugo, Astro, MkDocs, Eleventy) +
  **Pico.css** or plain CSS. No JS needed.

### Internal CRUD / admin panel

- **Django + Django Admin** is unbeatable for "I need data CRUD by
  Friday."
- Or **FastAPI + htmx + Pico** for a smaller, more modern feel.

### Public CRUD product (this repo)

- **FastAPI + server-rendered HTML + vanilla JS** is exactly right
  for v1.0.
- Add **htmx** for v2 to pick up snappy interactions without a
  framework.

### Realtime collaboration / dashboards / rich client

- **SPA framework** (React or Svelte) + a JSON API + WebSockets.
- Probably **Next.js** or **SvelteKit** if you want one codebase.

### High-volume API, no UI

- **FastAPI** or **Go** or **Rust (Axum)** depending on hot-path
  needs. UI is a separate consumer.

### Mobile-first

- React Native, SwiftUI, Kotlin Compose, Flutter. Out of scope here.

---

## 10. How each tool would affect *this* repo

| Tool | If adopted, what changes here | Recommendation |
| --- | --- | --- |
| **Pico.css** | One `<link>` tag added to each HTML file. `styles.css` shrinks; semantic tags get default styling. No build. | **Try in a branch.** Low risk. |
| **htmx** | One `<script>` tag. Some endpoints return HTML fragments alongside JSON. ADR required. | **Plan for v2.** High ROI for inline edit, delete confirmation, optimistic updates. |
| **Alpine.js** | Optional sidekick to htmx for client-only state. | Only if vanilla-JS toggles start repeating. |
| **Tailwind** | New build step. Existing CSS conventions inverted. Markup gets noisy. | **No.** Conflicts with frontend conventions. |
| **React/Vue/Svelte** | Frontend becomes a separate SPA. FastAPI becomes a JSON-only API. Build pipeline, hydration, two deploys. | **No** for this app. Right tool for a *different* portfolio piece. |
| **Next.js / SvelteKit** | Full rewrite, different runtime. | **No.** |
| **Django** | Full rewrite. Lose FastAPI's OpenAPI niceties; gain admin and ORM defaults. | **No.** Pick for a *next* project to demonstrate a different stack. |
| **Vite** | Build pipeline, `package.json`, node_modules. | Only if a JS framework arrives. |
| **Sass / Less** | Build step. Most features now native. | **No.** |
| **jQuery** | Library tag. Nothing it does isn't already in the platform. | **No.** |
| **Bootstrap** | Heavier than Pico, more visual conformity. | **No** — Pico does the same job better here. |
| **MongoDB / Firestore** | Different shape. Lose Postgres CHECK constraints, transactions, real SQL. | **No.** |
| **Prisma / Drizzle** | Different language entirely. | **No.** |
| **Vercel hosting** | No Python support; would need rewrite. | **No** unless rewriting. |

---

## 11. How to learn more without doom-scrolling tutorials

- **Build the same tiny app twice in two stacks.** Same UI, different
  tools. Forces you to feel the trade-offs instead of reading about
  them.
- **Read the official "Why X?" pages.** htmx, Alpine, Pico, React,
  Svelte, Django all have honest "what we're for" docs. Skip the
  influencer hot takes.
- **Look at job listings in your area** for the stack mix actually
  hired for. Tutorials chase what's trendy on Twitter; jobs lag by
  ~18 months.
- **Subscribe to one or two changelogs**, not ten newsletters.
  Suggested: the htmx blog, Simon Willison's TIL, the Pydantic /
  FastAPI release notes, MDN's "what's new in baseline" feed.

---

## 12. Where this lives

- This file — **learning** + tool comparisons that are *web-app
  specific*.
- [`tool-comparison.md`](tool-comparison.md) — broader "tool A vs B"
  picks (build tools, test runners, etc.).
- [`frontend-conventions.md`](frontend-conventions.md) — the rules
  *this* project follows, plus the v2 product roadmap.

Update this file as you encounter new tools or change your mind on
old ones. The goal is one place to *recognize* a tool, not memorize
its API.
