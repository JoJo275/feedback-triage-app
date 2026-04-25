"""Application entry points (backward-compatibility re-exports).

All entry-point functions now live in ``entry_points.py``.  This module
re-exports the four core functions so that existing imports like
``from simple_python_boilerplate.main import doctor`` continue to work.

TODO (template users): You can safely delete this file once you have
     updated any imports that reference ``main`` to use ``entry_points``
     instead.

See Also:
    - entry_points.py: All 22 CLI entry points in one place
    - cli.py: Argument parsing and command structure
    - engine.py: Core business logic
"""

from __future__ import annotations

from simple_python_boilerplate.entry_points import doctor, main, print_version, start

__all__ = ["doctor", "main", "print_version", "start"]
