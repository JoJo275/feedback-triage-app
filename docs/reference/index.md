<!-- TODO (template users): Replace 'simple_python_boilerplate' with your
     package name throughout this page. Update the Sections table to
     reflect your actual modules. -->

# API Reference

This section contains auto-generated documentation for the
`simple_python_boilerplate` package, built directly from source code
docstrings and type annotations using
[mkdocstrings](https://mkdocstrings.github.io/).

## How it works

The `::: module.name` directive in Markdown tells `mkdocstrings` to import
the specified module and render its public API — classes, functions,
type aliases, and their docstrings — into the documentation page.

Because this project uses the **src/ layout**, the `mkdocstrings` handler is
configured with `paths: [src]` in `mkdocs.yml` so that imports resolve
correctly during the docs build.

## Sections

| Page                                        | Description                                |
| ------------------------------------------- | ------------------------------------------ |
| [API](api.md)                               | Public modules: engine, main, cli, and api |
| [Commands](commands.md)                     | Auto-generated task & script reference     |
| [Template Inventory](template-inventory.md) | Templates, examples, and file conventions  |

## Writing good docstrings

This project uses **Google-style** docstrings (enforced by Ruff's `D`
rules). A well-documented function looks like:

```python
def process_data(raw: str, *, validate: bool = True) -> dict[str, Any]:
    """Process raw input data and return structured results.

    Args:
        raw: The raw input string to process.
        validate: Whether to validate before processing.

    Returns:
        A dictionary containing the processed results.

    Raises:
        ValueError: If the input data is malformed.
    """
```

When you add or update docstrings in the source code, the API reference
updates automatically on the next build.
