"""Workspace tenancy primitives (PR 1.5 / v2.0-alpha).

This package owns the request-scoped `WorkspaceContext` resolver and the
role-gate policies that every workspace-scoped route depends on. The
module is a leaf: it depends on `models`, `database`, `auth`, and
`errors`, and never imports from `routes/` or `crud/`
(see ``docs/project/spec/v2/repo-structure.md`` — Module boundaries).

See ``docs/project/spec/v2/multi-tenancy.md`` for the canonical
contract and ADR 060 for the decision record.
"""

from __future__ import annotations

from feedback_triage.tenancy.context import (
    WorkspaceContext,
    WorkspaceContextDep,
    get_current_workspace,
)
from feedback_triage.tenancy.policies import (
    require_workspace_role,
    require_writable,
)

__all__ = [
    "WorkspaceContext",
    "WorkspaceContextDep",
    "get_current_workspace",
    "require_workspace_role",
    "require_writable",
]
