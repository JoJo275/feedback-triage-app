# MkDocs Build Hooks

Custom [MkDocs hooks](https://www.mkdocs.org/user-guide/configuration/#hooks)
that run during the documentation build. These are **not** git hooks or
pre-commit hooks — they are Python modules that MkDocs calls at specific
points in its build pipeline.

<!-- TODO (template users): Add or remove hooks as needed. If you have no
     repo-relative links in your docs, you can safely delete repo_links.py
     and remove the hooks: entry from mkdocs.yml. -->

---

## What Are MkDocs Hooks?

MkDocs hooks are plain Python files registered in `mkdocs.yml` under the
`hooks:` key. Each file can define one or more **event handler functions**
that MkDocs calls during the build lifecycle. They are essentially
lightweight plugins that don't require packaging or installation.

```yaml
# mkdocs.yml
hooks:
    - mkdocs-hooks/repo_links.py
```

### Available Events

| Event                 | Phase    | Purpose                                           |
| :-------------------- | :------- | :------------------------------------------------ |
| `on_startup`          | Global   | Runs once when MkDocs starts (before config load) |
| `on_shutdown`         | Global   | Runs once when MkDocs exits                       |
| `on_config`           | Global   | Modify the MkDocs config after it's loaded        |
| `on_pre_build`        | Global   | Runs before building starts                       |
| `on_files`            | Global   | Add, remove, or modify the collected file list    |
| `on_nav`              | Global   | Modify the navigation structure                   |
| `on_env`              | Global   | Modify the Jinja2 template environment            |
| `on_page_read_source` | Per-page | Override how a page's source is read              |
| `on_page_markdown`    | Per-page | Transform raw Markdown before conversion          |
| `on_page_content`     | Per-page | Transform HTML after Markdown conversion          |
| `on_page_context`     | Per-page | Modify template context before rendering          |
| `on_post_page`        | Per-page | Modify final HTML output of a page                |
| `on_post_build`       | Global   | Runs after all pages are built                    |
| `on_serve`            | Serve    | Runs when using `mkdocs serve` (dev server only)  |

Reference: <https://www.mkdocs.org/user-guide/configuration/#hooks>

### Hooks vs Plugins

| Aspect           | Hooks                           | Plugins                                  |
| :--------------- | :------------------------------ | :--------------------------------------- |
| **Location**     | Local Python files in the repo  | Installed packages (PyPI or local)       |
| **Registration** | `hooks:` key in `mkdocs.yml`    | `plugins:` key in `mkdocs.yml`           |
| **Config**       | Read `config.extra` or hardcode | Dedicated config schema via `BasePlugin` |
| **Packaging**    | None — just a `.py` file        | Requires `setup.py` / `pyproject.toml`   |
| **Best for**     | Project-specific build tweaks   | Reusable, configurable extensions        |

Use hooks for project-specific logic that doesn't need to be shared.
Promote to a plugin if the logic is reusable across multiple projects.

---

## Inventory

| Hook                   | Event              | Purpose                                                                                        |
| :--------------------- | :----------------- | :--------------------------------------------------------------------------------------------- |
| `repo_links.py`        | `on_page_markdown` | Rewrite repo-relative links (`../../pyproject.toml`) to GitHub URLs                            |
| `generate_commands.py` | `on_pre_build`     | Auto-regenerate `docs/reference/commands.md` before each build                                 |
| `include_templates.py` | `on_files`         | Force-include `docs/templates/` on all MkDocs versions (workaround for 1.6+ default exclusion) |

`repo_links.py` handles standard Markdown links, HTML `<a href>` links,
and reference-style link definitions (`[ref]: ../path`). Code blocks,
inline code, and HTML comments are automatically protected from rewriting.

---

## Adding a New Hook

1. Create a Python file in `mkdocs-hooks/` (e.g. `mkdocs-hooks/my_hook.py`)
2. Define one or more event handler functions (see table above)
3. Register it in `mkdocs.yml`:

    ```yaml
    hooks:
        - mkdocs-hooks/repo_links.py
        - mkdocs-hooks/generate_commands.py
        - mkdocs-hooks/my_hook.py
    ```

4. Update this README with the new hook's purpose
5. Test with `hatch run docs:build` and `hatch run docs:serve`

### Example Hook

```python
"""MkDocs hook: add build timestamp to page context."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.nav import Navigation
    from mkdocs.structure.pages import Page

HOOK_VERSION = "1.0.0"

def on_page_context(
    context: dict,
    *,
    page: Page,
    config: MkDocsConfig,
    nav: Navigation,
) -> dict:
    """Add build_time to the template context."""
    context["build_time"] = datetime.now(tz=timezone.utc).isoformat()
    return context
```

---

## Conventions

- **Naming:** `snake_case.py`, descriptive of what the hook does
- **Version constant:** Include `HOOK_VERSION = "x.y.z"` — bump when
  behaviour changes
- **Type hints:** Use `TYPE_CHECKING` guard for MkDocs imports (they're
  only available at build time)
- **Docstrings:** Module-level docstring explaining purpose, mechanism,
  and any configuration
- **Logging:** Use `logging.getLogger("mkdocs.hooks.<name>")` for
  build-time messages
- **Independence:** Hooks should not import from the installed package
  (`simple_python_boilerplate`). They run during docs build, not at
  application runtime.
