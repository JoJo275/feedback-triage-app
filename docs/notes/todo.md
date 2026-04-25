# TODO & Ideas

Task tracking for template users and template maintainers.
Completed items are periodically archived via `python scripts/archive_todos.py`.

---

## For Template Users

<!-- TODO (template users): After forking, work through the setup checklist
     below, then delete the completed items and replace the rest of this
     section with your own project's tasks. -->

### Setup Checklist

- [ ] Run `python scripts/customize.py` to rename the package and enable workflows
- [ ] Replace placeholder code in `src/simple_python_boilerplate/` with your implementation
- [ ] Update `pyproject.toml` metadata (name, description, URLs, authors)
- [ ] Update `README.md` with your project's description and usage
- [ ] Replace `SECURITY.md` PGP key and fingerprint with your own (or remove PGP section)
- [ ] Replace Codecov badge token in `README.md` (or remove coverage badge)

### Configuration

- [ ] Review and enable optional workflows in `.github/workflows/` (set repo vars or edit guards)
- [ ] Configure secrets and environment variables for CI/CD (e.g. `CODECOV_TOKEN`, `PYPI_TOKEN`)
- [ ] Update `.github/CODEOWNERS` with your team's ownership rules
- [ ] Update `.github/FUNDING.yml` or remove if not accepting sponsorships
- [ ] Review `.github/dependabot.yml` schedule and ecosystem settings

### Cleanup

- [ ] Remove example files you don't need: `experiments/`, `db/seeds/`, `db/migrations/`
- [ ] Remove or replace `docs/templates/` examples with your own
- [ ] Update `docs/` content for your project (index, getting-started, architecture)
- [ ] Delete `docs/notes/` or repurpose for your own notes
- [ ] Review `Containerfile` and `docker-compose.yml` — update or remove if not containerising
- [ ] Adjust `MAX_IMAGE_SIZE_MB` in `scripts/test_containerfile.py` for your application

### Your Project Tasks

<!-- Add your own project-specific tasks here -->

---

## For Template Maintainers

Tasks, improvements, and ideas for the template repository itself.

### To Do

- [ ] Reconcile container-scan category: listed in both Security and Container in `USING_THIS_TEMPLATE.md`; only Security in `workflows.md`
- [ ] Extract shared UI helpers in `git_doctor.py` (`_section()`, `_kv()`, `_merge_row()`, box-drawing init) into a reusable `_UIContext` dataclass (~200 lines of duplication across 8 functions)

### Ideas for Later

- [ ] Spin-off template repos: "minimal", "library", "cli", "data-science", "web-app"
- [ ] Keep Containerfile in sync with production pipeline best practices
- [ ] Add workflow to auto-regenerate `docs/reference/commands.md` on script changes
- [ ] Consider adding `uv` as an alternative to pip for faster installs in CI
- [ ] Add smoke test for `scripts/customize.py` (ensure rename + guard enablement works end-to-end)
- [ ] Add a template-validation CI job that forks, runs `customize.py`, and verifies the result builds and passes tests
- [ ] Evaluate switching from `release-please` to `python-semantic-release` for tighter Python ecosystem integration

---

## Bookmarks

- [Python Packaging User Guide](https://packaging.python.org/)
- [Scientific Python Development Guide](https://learn.scientific-python.org/development/)
- [Hypermodern Python](https://cjolowicz.github.io/posts/hypermodern-python-01-setup/)
