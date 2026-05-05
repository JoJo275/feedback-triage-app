# Changelog

## [1.0.0](https://github.com/JoJo275/feedback-triage-app/compare/v1.0.0...v1.0.0) (2026-05-05)


### Features

* Add draft for Feedback Triage App spec v2.0 and update references ([f4428d5](https://github.com/JoJo275/feedback-triage-app/commit/f4428d531f74e32afaf9a93f216083fcbb1cb69a))
* **implementation:** add PR ledger for v2.0 phases with detailed tracking ([abc3793](https://github.com/JoJo275/feedback-triage-app/commit/abc3793c9d65f195e7b285630a422fa33ed3b649))
* introduce v2.0 specifications including multi-tenancy, rollout, schema, security, and tooling ([28c1b89](https://github.com/JoJo275/feedback-triage-app/commit/28c1b891841b9a095b382833918ebe534d9db2ac))
* ratify v2.0 spec and ADR 061 for email integration. ([587ee53](https://github.com/JoJo275/feedback-triage-app/commit/587ee5324b822430a0e9358b2cdca4bd208f636a))
* rename project from Feedback Triage to SignalNest ([09e72e0](https://github.com/JoJo275/feedback-triage-app/commit/09e72e00422e88a2024c85fa6eb5772e8076b5b1))

## 1.0.0 (2026-05-01)


### Features

* add Alembic migration setup and initial feedback_item table schema ([187edf7](https://github.com/JoJo275/feedback-triage-app/commit/187edf7cab371a386c92ace1776f6e44e91f26b0))
* add Railway setup runbook for Phase 7 deployment ([9a2d1c0](https://github.com/JoJo275/feedback-triage-app/commit/9a2d1c03e475d484a9536efaeeb309f21c86df4e))
* add validation to prevent localhost DATABASE_URL in production environment ([214f23a](https://github.com/JoJo275/feedback-triage-app/commit/214f23a3c5265f0ea2389a47b0f7a303fb93ed7b))
* enhance seed script with progress bar and self-check functionality ([c899090](https://github.com/JoJo275/feedback-triage-app/commit/c8990901b4c376ffce5b306944bb9b3974b17bcd))
* implement core application structure with FastAPI and PostgreSQL integration ([d92313e](https://github.com/JoJo275/feedback-triage-app/commit/d92313e8ea839b6f6500488c68db6c14b8284cd7))
* initial bring-up of feedback-triage-app with FastAPI and PostgreSQL skeleton ([8d2b1f0](https://github.com/JoJo275/feedback-triage-app/commit/8d2b1f09f7f1546646a6751d31dbf5b929ed59e6))
* **Phase 3:** implement feedback API with CRUD operations and database integration ([68aecf4](https://github.com/JoJo275/feedback-triage-app/commit/68aecf4d8806de00412d4087690743e6e8fcb23c))
* **Phase 4:** Implement frontend pages for feedback triage application ([ea9c734](https://github.com/JoJo275/feedback-triage-app/commit/ea9c734b0b74104ef776672f55b9d92f16cf3064))
* **Phase 5:** implement global exception handling and logging with request ID support ([6dd917a](https://github.com/JoJo275/feedback-triage-app/commit/6dd917a01334fbd59a3b8f5d2f338f40111f5fce))
* **Phase 6:** add Playwright smoke tests for critical UI paths and fixtures ([58fb2c4](https://github.com/JoJo275/feedback-triage-app/commit/58fb2c419137a1d53036d19c2a4931c0ebdcebf2))
* scaffold feedback_triage package skeleton ([bf1774d](https://github.com/JoJo275/feedback-triage-app/commit/bf1774d43e2b1b52094d5f5bac0d06c5513ad949))
* update README for v1.0 release candidate; add post-launch checklist and seed script ([30725ac](https://github.com/JoJo275/feedback-triage-app/commit/30725ac7eaadc32d09c2911a8cb96bfbc99c8116))
* update repository references in workflows and Containerfile for consistency ([1c8f50f](https://github.com/JoJo275/feedback-triage-app/commit/1c8f50fbfd4b1fba8d9747da951ecf78636660c9))
* update smoke test in container build workflow and enhance README with additional badges ([de3fe1a](https://github.com/JoJo275/feedback-triage-app/commit/de3fe1a5ab028e7e58edd1925192f6c90cfd0416))


### Bug Fixes

* **ci:** unblock devcontainer build and license check ([47aa137](https://github.com/JoJo275/feedback-triage-app/commit/47aa13746d60348557f77063351d2d7705abff5c))
* **ci:** unblock devcontainer, license, and link-check jobs ([528d764](https://github.com/JoJo275/feedback-triage-app/commit/528d764d81a87204ea20fa44ef41efe53ca3da3c))
* **ci:** unblock devcontainer, license, and link-check jobs (round 2) ([9d5023d](https://github.com/JoJo275/feedback-triage-app/commit/9d5023dcce38cf4a4a46a306a5a264116b800e5f))
* **devcontainer:** drop docker-outside-of-docker feature (Yarn-repo NO_PUBKEY) ([5f43b81](https://github.com/JoJo275/feedback-triage-app/commit/5f43b8118f10b7ea0cc34ace60f403731cf56edb))
* **devcontainer:** use sudo for task install; restore docker via outside-of-docker feature ([9aca246](https://github.com/JoJo275/feedback-triage-app/commit/9aca24652425367c799a23cb20ec45b9a052e972))
* enhance argument handling in apply-labels.sh for OWNER/REPO promotion ([6cb454a](https://github.com/JoJo275/feedback-triage-app/commit/6cb454a0be689fafb0e9a70532e75cf81d25720d))
* escape dollar sign in Railway setup documentation for clarity ([3410a64](https://github.com/JoJo275/feedback-triage-app/commit/3410a648af8cc66fe31f91a01d7ba8de242c7806))
* **pre-commit:** provision pip-audit via uv run --with ([6b79e8e](https://github.com/JoJo275/feedback-triage-app/commit/6b79e8e2c246e635971e304b5187aff68e0524af))
* update frontend smoke test documentation to reflect redirect behavior ([2597d25](https://github.com/JoJo275/feedback-triage-app/commit/2597d251512dda426cb4035f7906d27d0878f433))

## Changelog

All notable changes to this project will be documented in this file.

This changelog is **automatically generated** by [release-please](https://github.com/googleapis/release-please)
from [Conventional Commits](https://www.conventionalcommits.org/) on `main`.
Do not edit manually — changes will be overwritten on the next release.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
