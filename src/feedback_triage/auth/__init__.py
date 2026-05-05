"""Authentication building blocks (PR 1.4 / v2.0-alpha).

The auth surface ships in two halves: this package owns the **plumbing**
(password hashing, session cookies, single-use tokens, FastAPI
dependencies for the request-scoped current user) and PR 1.7 owns the
HTTP routes that consume it. Splitting the work this way keeps the
crypto and DB-write paths under unit-test cover before any route is
exposed.

See ``docs/project/spec/v2/auth.md`` for the canonical contract and
``docs/adr/059-auth-model.md`` for the decision record.
"""

from __future__ import annotations
