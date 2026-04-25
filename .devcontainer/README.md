# Dev Container

<!-- TODO (template users): Review devcontainer.json and update the Python
     version, extensions, and postCreateCommand for your project. Remove
     features you don't need (e.g., Node.js if you have no JS tooling). -->

This folder configures a VS Code [Dev Container](https://code.visualstudio.com/docs/devcontainers/containers)
for consistent development environments.

## Quick Start

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Podman)
2. Install the [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension in VS Code
3. Open this repo in VS Code
4. Click "Reopen in Container" when prompted (or run `Dev Containers: Reopen in Container` from the command palette)

VS Code will build the container and set up your environment automatically.

### Exiting the Container

To return to local (non-container) development:

- **Command palette** (`Ctrl+Shift+P`) → **Dev Containers: Reopen Folder Locally**
- Or simply **close the VS Code window** — the container stops automatically

Your files are not affected. The container shares your project files via a
volume mount, so everything you edited is still on your local disk.

## What's Included

- Python 3.12 with pip and Hatch (environment management)
- Node.js LTS (for pre-commit hooks like markdownlint, prettier)
- Task runner (go-task)
- All Python dev dependencies installed via Hatch
- Pre-commit hooks configured (pre-commit, commit-msg, pre-push)
- VS Code extensions for Python, TOML, YAML, Markdown, Git
- mypy type checker extension

## GitHub Codespaces

This configuration also works with [GitHub Codespaces](https://github.com/features/codespaces).
Click the green "Code" button on GitHub and select "Open with Codespaces" to get a
browser-based development environment with zero local setup.

## Dev Container vs Containerfile

| Aspect          | Dev Container (`.devcontainer/`) | Containerfile (repo root)     |
| --------------- | -------------------------------- | ----------------------------- |
| **Purpose**     | Development environment          | Production runtime            |
| **Contains**    | All dev tools, editors, linters  | Minimal app only              |
| **Image size**  | Large (~1GB+)                    | Small (~150MB)                |
| **User**        | Interactive development          | Run the application           |
| **When to use** | `code .` → "Reopen in Container" | `docker build` → `docker run` |

They serve completely different purposes and don't share configuration.

## Using Hatch Inside the Container

Once the container is running, use Hatch for all commands:

```bash
hatch shell                    # Enter the dev environment
hatch run test                 # Run tests
hatch run lint                 # Lint
hatch run docs:serve           # Serve docs locally
task check                     # All quality gates (via Task runner)
```

## Rebuilding the Dev Container

When `devcontainer.json` changes (e.g., new features, extensions, or
`postCreateCommand` updates), VS Code won't pick them up automatically.
You must rebuild:

1. Open the command palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
2. Run **Dev Containers: Rebuild Container** (keeps your workspace files)
   — or **Rebuild Without Cache** if you want a completely fresh image

Alternatively from the terminal:

```bash
# Force a full rebuild from scratch
devcontainer up --remove-existing-container --workspace-folder .
```

Rebuild is needed after changes to:

- `devcontainer.json` (image, features, postCreateCommand, extensions)
- Dockerfile / base image references
- Feature versions

It is **not** needed for changes to `pyproject.toml` dependencies —
run `hatch env remove default && hatch env create default` inside the
running container instead.

## Further Reading

- [CONTRIBUTING.md](../CONTRIBUTING.md) — Full contributing guide
- [docs/development/dev-setup.md](../docs/development/dev-setup.md) — Detailed dev environment setup
- [docs/guide/troubleshooting.md](../docs/guide/troubleshooting.md) — Troubleshooting
- [docs/design/tool-decisions.md](../docs/design/tool-decisions.md) — Why these tools were chosen
