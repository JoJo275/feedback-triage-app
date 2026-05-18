# React Frontend Scaffold (Phase 0)

This directory contains the Vite + React + TypeScript scaffold used for
React migration Phase 0.

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

FastAPI reads that manifest to resolve entry files for the Phase 0 React shell
route.
