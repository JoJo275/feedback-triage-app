"""Session-per-request canary, extended for the v2 table set.

The original v1 canary lives at
``tests/test_feedback_api.py::test_patch_then_get_returns_fresh_state``
and asserts the contract for the ``feedback_item`` table only. PR 1.3b
introduces the auth + tenancy + email_log table cluster; this module
extends the canary so a session-reuse / stale-read regression on any of
the new tables fails CI in the same way.

The contract under test (per spec — Database session lifecycle):

- Each request gets its own ``Session`` via :func:`get_db`.
- ``expire_on_commit=False`` is safe **only** because that session does
  not outlive the request.
- A write committed in one request must be visible to a read issued by
  the next request, with no stale ORM identity-map state leaking
  between them.

The tests here exercise the contract directly through ``get_db``
(rather than via HTTP routes) because the v2 auth / tenancy routes do
not exist until PR 1.7+. Once those routes ship, the same invariant is
covered end-to-end by the auth flow tests.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import pytest
from sqlalchemy import select, text

from feedback_triage.database import get_db
from feedback_triage.models import User, Workspace


@pytest.fixture
def truncate_v2_tables() -> Iterator[None]:
    """Wipe every v2 table touched by this canary.

    ``CASCADE`` follows the FKs into ``workspaces``, ``sessions``, etc.
    The synthetic legacy admin / workspace re-created by Migration A is
    deleted here too; the canary only cares about post-truncate state.
    """
    from feedback_triage.database import engine

    with engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE TABLE "
                "users, workspaces, workspace_memberships, "
                "workspace_invitations, sessions, "
                "email_verification_tokens, password_reset_tokens, "
                "auth_rate_limits, email_log "
                "RESTART IDENTITY CASCADE"
            )
        )
    yield


def _next_session(gen: Iterator):  # type: ignore[no-untyped-def]
    """Drive ``get_db`` once and return its session, leaving cleanup to
    the test (which calls ``next`` again to trigger commit + close)."""
    return next(gen)


def test_user_update_visible_across_request_scoped_sessions(
    truncate_v2_tables: None,
) -> None:
    """Insert in request 1, update in request 2, read in request 3.

    If a single ``Session`` ever leaks across requests with
    ``expire_on_commit=False``, the read in request 3 sees the
    pre-update state and this test fails — same failure mode the v1
    canary catches on ``feedback_item``.
    """
    # Request 1: insert.
    gen1 = get_db()
    session1 = _next_session(gen1)
    user = User(
        email=f"canary-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="!disabled-canary!",
    )
    session1.add(user)
    with pytest.raises(StopIteration):
        next(gen1)  # triggers commit + close
    user_id = user.id
    assert user_id is not None

    # Request 2: update is_verified.
    gen2 = get_db()
    session2 = _next_session(gen2)
    fetched = session2.get(User, user_id)
    assert fetched is not None
    fetched.is_verified = True
    with pytest.raises(StopIteration):
        next(gen2)

    # Request 3: read in a fresh session must see the update.
    gen3 = get_db()
    session3 = _next_session(gen3)
    reread = session3.get(User, user_id)
    assert reread is not None
    assert reread.is_verified is True
    with pytest.raises(StopIteration):
        next(gen3)


def test_workspace_owner_fk_round_trips(truncate_v2_tables: None) -> None:
    """Cross-table FK round-trip across two request-scoped sessions.

    Catches a regression where a workspace insert that depends on a
    user committed in the previous request observes stale identity-map
    state for the FK target.
    """
    # Request 1: create the user.
    gen1 = get_db()
    session1 = _next_session(gen1)
    owner = User(
        email=f"owner-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="!disabled-canary!",
    )
    session1.add(owner)
    with pytest.raises(StopIteration):
        next(gen1)
    owner_id = owner.id
    assert owner_id is not None

    # Request 2: create the workspace pointing at the user.
    gen2 = get_db()
    session2 = _next_session(gen2)
    ws = Workspace(
        slug=f"canary-{uuid.uuid4().hex[:8]}",
        name="Canary",
        owner_id=owner_id,
    )
    session2.add(ws)
    with pytest.raises(StopIteration):
        next(gen2)
    ws_id = ws.id
    assert ws_id is not None

    # Request 3: read both back.
    gen3 = get_db()
    session3 = _next_session(gen3)
    reread_ws = session3.get(Workspace, ws_id)
    assert reread_ws is not None
    assert reread_ws.owner_id == owner_id
    rows = session3.execute(select(User).where(User.id == owner_id)).all()
    assert len(rows) == 1
    with pytest.raises(StopIteration):
        next(gen3)
