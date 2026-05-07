# Changelog

## [2.0.0](https://github.com/JoJo275/feedback-triage-app/compare/v1.2.0...v2.0.0) (2026-05-07)


### Features

* **docs:** pr 3.5 (phase 3 finished) - update documentation to reflect v2.0 ratification and changes ([6cdfeb2](https://github.com/JoJo275/feedback-triage-app/commit/6cdfeb25d76f89a705dbcf6911d07f246240894d))
* **email:** pr 3.1 - implement email replay functionality for failed emails ([d9d0df1](https://github.com/JoJo275/feedback-triage-app/commit/d9d0df18db77dbd539fca95c85fffef320330eab))
* **pages:** pr 3.3 -  implement management changelog and roadmap pages ([c3c2da8](https://github.com/JoJo275/feedback-triage-app/commit/c3c2da8887c09e3fc66025bc776d260631e2ca05))
* pr 3.4 - add landing page demo and dashboard templates ([6e9c3a3](https://github.com/JoJo275/feedback-triage-app/commit/6e9c3a33117bbd6514342ab558ba38654fdab400))
* **public-pages:** pr 3.2 - implement public roadmap and changelog pages with routing and templates ([596379f](https://github.com/JoJo275/feedback-triage-app/commit/596379f9266d1b22bffeb1d849e4a7d97a8de106))


### Bug Fixes

* add a fuller log of changes into pull-request-draft.md and small fixes across tests ([3b2cd5e](https://github.com/JoJo275/feedback-triage-app/commit/3b2cd5ed35f47600c76e49c99a231f692283bfec))


### Miscellaneous

* populate pull-request-draft.md ([c2cd5c4](https://github.com/JoJo275/feedback-triage-app/commit/c2cd5c4319043016c8d55213deb1154b689274c8))

## [1.2.0](https://github.com/JoJo275/feedback-triage-app/compare/v1.1.0...v1.2.0) (2026-05-07)


### Features

* **db:** pr 2.1 - implement Migration B — backfill, NOT NULL flip, status rename, and new workflow tables ([fe0ac36](https://github.com/JoJo275/feedback-triage-app/commit/fe0ac36b11473151ac6263ac58b194b3f32637a2))
* enhance workspace update and feedback submission logic with null checks and status code adjustments ([52811df](https://github.com/JoJo275/feedback-triage-app/commit/52811df797cb8a6507d5678146b837920d9e8f41))
* pr 2.2 - Add API flow tests for notes, submitters, and tags; enhance error handling tests ([eb87725](https://github.com/JoJo275/feedback-triage-app/commit/eb87725ba619500afafdcc876c445107a0c953f1))
* pr 2.3 - Add feedback triage UI components and pages ([cf16160](https://github.com/JoJo275/feedback-triage-app/commit/cf1616048d16d2e8546fb1720aa6437aa110fb1e))
* pr 2.4 - add public feedback submission endpoint and associated features ([c5e5770](https://github.com/JoJo275/feedback-triage-app/commit/c5e57703573814e8af692779e274393ea93d2adc))
* pr 2.6 (phase 2 finished) - add submitters list and detail pages with stale feedback detection ([f371937](https://github.com/JoJo275/feedback-triage-app/commit/f3719370a1b61a9e6f5e4734dada2937eb726f70))
* **settings:** pr 2.5 - add workspace settings page with public submission toggle ([2b96257](https://github.com/JoJo275/feedback-triage-app/commit/2b96257ce761d12d6c7a5876898c206337f7847c))


### Bug Fixes

* revert to HTTP_422_UNPROCESSABLE_CONTENT (HTTP_422_UNPROCESSABLE_ENTITY is deprecated in starlette) ([37de359](https://github.com/JoJo275/feedback-triage-app/commit/37de3590ac6aec8d2701a06d51efb6fd8477aafb))

## [1.1.0](https://github.com/JoJo275/feedback-triage-app/compare/v1.0.0...v1.1.0) (2026-05-06)


### Features

* Add draft for Feedback Triage App spec v2.0 and update references ([f4428d5](https://github.com/JoJo275/feedback-triage-app/commit/f4428d531f74e32afaf9a93f216083fcbb1cb69a))
* **auth:** pr 1.7 -implement v2.0 authentication flow with email verification and password reset ([a43a0c5](https://github.com/JoJo275/feedback-triage-app/commit/a43a0c5a1d7984546361e96895ce1dc9e287c2fa))
* **db:** phase 1.3b -  implement v2 auth, tenancy, and email_log tables with native enums ([872fff6](https://github.com/JoJo275/feedback-triage-app/commit/872fff6eda830a57c52bb359701c0c9bd96b4cbc))
* **email:** (pr 1.6) integrate Resend client for transactional emails ([8d30022](https://github.com/JoJo275/feedback-triage-app/commit/8d3002293a1c5e7af29ba9ce02b12aa47ac1e8ce))
* enhance templating with manifest caching and add unit tests for static_url ([a27a6b7](https://github.com/JoJo275/feedback-triage-app/commit/a27a6b7c36152a28fc353221273caa092ccec5f0))
* implement Tailwind CSS integration with standalone CLI and add style guide page ([ebd10b7](https://github.com/JoJo275/feedback-triage-app/commit/ebd10b7eb0edcf03c18afa033497b15916785fe1))
* **implementation:** add PR ledger for v2.0 phases with detailed tracking ([abc3793](https://github.com/JoJo275/feedback-triage-app/commit/abc3793c9d65f195e7b285630a422fa33ed3b649))
* introduce v2.0 specifications including multi-tenancy, rollout, schema, security, and tooling ([28c1b89](https://github.com/JoJo275/feedback-triage-app/commit/28c1b891841b9a095b382833918ebe534d9db2ac))
* **models:** introduce v2 models and enums for user roles, email status, and workspace management ([9d99345](https://github.com/JoJo275/feedback-triage-app/commit/9d99345949f8b6a0e0a1e5b9aee3d5bf8a690073))
* pr 1.4 - refactor code structure for improved readability and maintainability ([febd38e](https://github.com/JoJo275/feedback-triage-app/commit/febd38e712d47aa168212d22a3e5c7475a6e0365))
* pr 1.8 - add invitations and workspaces management endpoints ([671b522](https://github.com/JoJo275/feedback-triage-app/commit/671b5226edc7f1fe91151aa549db5e83734a2a4e))
* pr 1.9 (phase 1 finished) - implement FEATURE_AUTH gate for v2 auth surface ([54d1850](https://github.com/JoJo275/feedback-triage-app/commit/54d18500c7385cf20cf3bec897f2bb233f96f8a6))
* ratify v2.0 spec and ADR 061 for email integration. ([587ee53](https://github.com/JoJo275/feedback-triage-app/commit/587ee5324b822430a0e9358b2cdca4bd208f636a))
* rename project from Feedback Triage to SignalNest ([09e72e0](https://github.com/JoJo275/feedback-triage-app/commit/09e72e00422e88a2024c85fa6eb5772e8076b5b1))
* **tenancy:** implement WorkspaceContext and policies for multi-tenancy support ([94fea13](https://github.com/JoJo275/feedback-triage-app/commit/94fea131cc10a6529938f4e68635f64296e9c257))
* **workflows:** update license-check and link-checker workflows; add Apache-2.0 to license allow-list and exclude email templates from link checks ([9867b93](https://github.com/JoJo275/feedback-triage-app/commit/9867b9353544d1e941ac6143e43f2fe3e9ad1cd1))


### Bug Fixes

* correct formatting in script instructions for shebang line ([47913aa](https://github.com/JoJo275/feedback-triage-app/commit/47913aa7d19c185dd6c11f3265e5c3ef75495fbc))
* **docs:** update PR ledger for clarity on migration phases and deliverables ([9d99345](https://github.com/JoJo275/feedback-triage-app/commit/9d99345949f8b6a0e0a1e5b9aee3d5bf8a690073))
* **templates:** make sidebar Jinja formatter-stable ([445f8d2](https://github.com/JoJo275/feedback-triage-app/commit/445f8d23f5b2cfd94dc4797918052fd104c8b971))
* **ui:** align task-branch header/section box borders to content width ([6b6a771](https://github.com/JoJo275/feedback-triage-app/commit/6b6a771cf97de75e557b59bdf4a3b135e9de5e73))
* update PR title linting to allow uppercase subject start and improve error messaging ([33bae8f](https://github.com/JoJo275/feedback-triage-app/commit/33bae8fd77827cc02790205d97ba6530e5889a36))

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
