# Pull Request Guidelines

<!-- TODO (template users): Update this guide with your project's PR
     requirements — required reviewers, CI checks, branch protection rules,
     and any domain-specific checklist items. -->

How to create, review, and merge pull requests in this project.

## Before Opening a PR

1. **Create a feature branch** from `main`

    ```bash
    git switch main
    git pull --ff-only
    git switch -c feature/your-feature-name
    ```

2. **Make your changes** with clear, atomic commits

    Follow the [Conventional Commits](https://www.conventionalcommits.org/) format (see [development.md](development.md#commit-messages-conventional-commits) for the full rules):

    ```bash
    git commit -m "feat: add user authentication"
    ```

3. **Run quality checks locally**

    **Quick (fix & test):**

    ```bash
    task check                # All quality gates in one command
    # or individually:
    ruff format . && ruff check --fix . && pytest
    ```

    **Apply fixes:**

    ```bash
    task fmt                  # Auto-format code (ruff format)
    task lint:fix             # Auto-fix lint issues (ruff check --fix)
    ```

    **Verify (CI-like):**

    ```bash
    task test                 # Tests pass
    task lint                 # Linting passes
    task typecheck            # Type checking (mypy)
    ```

    > See [developer-commands.md](developer-commands.md) for the full command reference.
    > All `task` commands wrap `hatch run` — see the [Taskfile](../../Taskfile.yml).

4. **Push your branch**

    ```bash
    git push -u origin feature/your-feature-name
    ```

## Creating a Pull Request

### Title Format

Use conventional commit style for PR titles:

| Prefix      | Use For             |
| ----------- | ------------------- |
| `feat:`     | New features        |
| `fix:`      | Bug fixes           |
| `docs:`     | Documentation only  |
| `chore:`    | Maintenance, deps   |
| `refactor:` | Code restructuring  |
| `test:`     | Adding/fixing tests |
| `ci:`       | CI/CD changes       |

**Examples:**

- `feat: add user authentication`
- `fix: resolve login timeout issue`
- `docs: update installation guide`

### Description Template

<!-- TODO (template users): Customise this PR template to include checks
     specific to your project (e.g. "Migration tested", "API docs updated",
     "Feature flag added"). Consider copying it to .github/PULL_REQUEST_TEMPLATE.md
     so GitHub pre-fills it automatically. -->

```markdown
## Summary

Brief description of what this PR does.

## Changes

- Change 1
- Change 2

## Testing

How was this tested?

## Checklist

- [ ] Tests pass locally (`task test`)
- [ ] Linting passes (`task lint`)
- [ ] Type checking passes (`task typecheck`)
- [ ] Code follows style guidelines
- [ ] Documentation updated (if user-facing changes)
- [ ] Type hints on public functions
- [ ] ADR created (if significant decision — see `docs/adr/template.md`)
- [ ] Command reference regenerated (if scripts changed — `task docs:commands`)
```

## Code Review Guidelines

### For Authors

- Prefer small, focused PRs — if larger than ~400 lines, explain why in the description
- Respond to feedback promptly
- Don't take feedback personally — it's about the code
- Explain _why_, not just _what_

### For Reviewers

- Be constructive and kind
- Explain reasoning behind suggestions
- Approve when "good enough" — perfect is the enemy of done
- Use conventional comments:

| Prefix        | Meaning                          |
| ------------- | -------------------------------- |
| `nit:`        | Minor style preference, optional |
| `suggestion:` | Consider this approach           |
| `question:`   | Need clarification               |
| `issue:`      | Must be addressed                |

### What Reviewers Look For

- [ ] Tests added or updated for new/changed behavior
- [ ] Documentation updated (if user-facing changes)
- [ ] Type hints on public functions
- [ ] Backwards compatibility considered (or breaking change noted)
- [ ] No unrelated changes bundled in
- [ ] Commit messages follow conventional format

## Merging

<!-- TODO (template users): If your team uses a different merge strategy
     (squash, merge commit), update this section and configure it in
     GitHub repository settings → General → Pull Requests. -->

### Merge Strategy

This project uses **Rebase and Merge**:

- Replays commits on top of `main` without a merge commit
- Preserves individual commit history for a linear changelog
- Keeps `main` history clean and easy to follow

> **Tip:** Keep commits atomic and well-described since they will appear individually in the main branch history.

### Before Merging

1. All CI checks pass (green checkmarks)
2. At least one approval (if required)
3. No unresolved conversations
4. Branch is up-to-date with `main`

**Updating your branch (rebase workflow):**

```bash
git fetch origin
git rebase origin/main
# Resolve any conflicts, then:
git rebase --continue
git push --force-with-lease
```

> **Solo practice note:** If branch protection requires approval, you'll need a second reviewer (collaborator or second account) or an admin bypass rule. Configure this in repository settings to avoid locking yourself out.

### After Merging

- Delete the feature branch (GitHub can do this automatically)
- Close related issues (use `Closes #123` in PR description)
- Verify the CI gate check passed on `main` after merge

## Draft PRs

Use a **Draft PR** when:

- You want CI feedback early but the work isn't ready to merge
- You're seeking early design feedback before finishing implementation
- You want to share progress without triggering review notifications

Convert to "Ready for review" when you're done.

## Branch Naming

<!-- TODO (template users): Add any project-specific branch prefixes
     (e.g. release/, hotfix/) or naming rules here. -->

```text
feature/short-description    # New features
fix/issue-description        # Bug fixes
docs/what-changed            # Documentation
chore/maintenance-task       # Maintenance
ci/workflow-change           # CI/CD changes
```

## CI Gate & Required Checks

All PRs must pass the **CI gate** (`ci-gate.yml`) before merging. The gate
aggregates required checks into a single status check for branch protection.
See [ADR 024](../adr/024-ci-gate-pattern.md) for the design.

**If a required check never appears** (stays "pending" forever), the most
common cause is a renamed workflow job. The `ci-gate.yml` references checks
by their display name — if you rename a job, update `REQUIRED_CHECKS` in
`ci-gate.yml` too.

> **Path-filtered workflows** (bandit, docs-deploy, link-checker, smoke-test) are NOT
> in the CI gate because they don't run on every PR. If they don't trigger,
> that's expected — see [workflows.md](../workflows.md) for the full list.

## Automated Labels

The `labeler.yml` workflow automatically applies labels to PRs based on
file paths changed. For example, changes under `docs/` get the `docs` label,
changes under `src/` get `python`. See [labels.md](../labels.md) for the
full label inventory and `.github/labeler.yml` for the path-to-label mapping.

<!-- TODO (template users): Customise .github/labeler.yml to match your
     project's directory structure and labeling conventions. -->

## Stacked PRs

For large features that benefit from incremental review:

1. Break the work into sequential, reviewable PRs
2. Each PR targets the previous feature branch (not `main`)
3. Merge the stack bottom-up: first PR into `main`, then rebase the rest
4. Keep each PR under ~400 lines for manageable reviews

> **Tip:** GitHub's "base branch" dropdown lets you target any branch,
> not just `main`. Use this for stacked PRs.

## See Also

- [CONTRIBUTING.md](../../CONTRIBUTING.md) — General contribution guidelines
- [labels.md](../labels.md) — Issue and PR labels
- [dev-setup.md](dev-setup.md) — Environment setup
- [development.md](development.md) — Daily workflows
- [ADR 022](../adr/022-rebase-merge-strategy.md) — Why rebase merge
- [ADR 024](../adr/024-ci-gate-pattern.md) — CI gate pattern
- [workflows.md](../workflows.md) — Full workflow inventory
