# React Frontend Scaffold (Phase 1)

This directory contains the Vite + React + TypeScript frontend used for the
React migration track.

Phase 1 delivers:

- authenticated app shell parity primitives (sidebar/header/content/footer)
- route-level auth + tenant context loading
- typed API client with error-envelope normalization
- shared primitives for cards, status pills, filters, tables, and modal
- unit tests for API/error normalization plus shell snapshots

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
