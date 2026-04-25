# API

<!-- TODO (template users): Replace the module directives below with your
     own package modules. The ::: directive tells mkdocstrings to import
     and document the specified module.
     Example: ::: my_project.core

     After replacing placeholder code in src/, update this page to reflect
     your actual module structure. Remove modules that don't exist and add
     new ones as you create them. Each ::: directive auto-generates docs
     from the module's docstrings and type annotations. -->

Auto-generated from source docstrings and type annotations. See
[index.md](index.md) for how mkdocstrings works and docstring conventions.

---

## Engine

Core business logic — version info, environment diagnostics, and data
processing. This module is interface-agnostic and contains no CLI or HTTP
dependencies.

::: simple_python_boilerplate.engine
    options:
      show_source: false
      heading_level: 3

## Main

Application entry points — the glue between CLI parsing and engine logic.
Configured as console scripts in `pyproject.toml` under
`[project.scripts]`.

<!-- TODO (template users): After customising your entry points in
     pyproject.toml [project.scripts], update this section to document
     your actual entry points. -->

::: simple_python_boilerplate.main
    options:
      show_source: false
      heading_level: 3

## CLI

Command-line interface definitions and argument parsing. Uses `argparse`
from the standard library.

<!-- TODO (template users): If you switch to click, typer, or another CLI
     framework, update the description above and ensure mkdocstrings can
     document the new command structure. -->

::: simple_python_boilerplate.cli
    options:
      show_source: false
      heading_level: 3

## API Layer

HTTP/REST interface helpers. Currently a placeholder — choose a framework
(FastAPI, Flask, etc.) and implement.

<!-- TODO (template users): Once you've chosen a web framework:
     1. Implement endpoints in api.py
     2. Update this description
     3. Consider adding request/response model docs here
     4. If not building a web API, remove this section entirely -->

::: simple_python_boilerplate.api
    options:
      show_source: false
      heading_level: 3

## Dev Tools

Development utilities (not part of the public API). Provides cache cleanup
and build artifact removal used by `scripts/clean.py` and `task clean`.

<!-- TODO (template users): If you add development-only utilities to
     dev_tools/, document them here. If you don't need this subpackage,
     remove both the directory and this section. -->

::: simple_python_boilerplate.dev_tools
    options:
      show_source: false
      heading_level: 3

---

## See Also

- [API Reference index](index.md) — How mkdocstrings works, docstring conventions
- [Architecture](../design/architecture.md) — Module responsibilities and data flow
- [Source code](https://github.com/JoJo275/simple-python-boilerplate/tree/main/src/simple_python_boilerplate) — Browse on GitHub

<!-- TODO (template users): Update the GitHub link above to point to your
     actual repository. -->
