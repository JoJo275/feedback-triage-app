# React Frontend App (Phase 2)

This directory contains the Vite + React + TypeScript frontend used for the
React migration track.

Phase 2 extends the Phase 1 shell with authenticated page routes:

- dashboard
- inbox + feedback archive
- roadmap
- changelog
- submitters
- insights
- settings

Route identity is passed from FastAPI templates through mount-node
data attributes (`data-page-key`, `data-active-section`, and
`data-legacy-url`) so one Vite entrypoint can render multiple
authenticated page surfaces behind feature flags.

## Toolchain

- Node 22.x (see .nvmrc)
- npm 10+

## Commands

- npm ci
- npm run lint
- npm run typecheck
- npm run test
- npm run build
- npm run audit

## Build output

`npm run build` writes hashed assets plus `manifest.json` to:

- ../src/feedback_triage/static/app/

FastAPI reads that manifest to resolve entry files for the React shell route.
