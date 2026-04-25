# Written Resources

Self-written references, cheat sheets, and guides. Unlike
[resources_links.md](resources_links.md) (curated external links), this page
contains original content written for this project.

---

## Git Commands Reference

A practical reference for Git commands used day-to-day when working on this
project. Commands are grouped by workflow stage.

### Setup & Configuration

| Command                                            | What it does                                                               |
| -------------------------------------------------- | -------------------------------------------------------------------------- |
| `git config --global user.name "Your Name"`        | Set your name for all repos                                                |
| `git config --global user.email "you@example.com"` | Set your email for all repos                                               |
| `git config --local user.email "work@company.com"` | Override email for this repo only                                          |
| `git config --list --show-origin`                  | Show all settings and which file defines each one                          |
| `git config --show-origin <key>`                   | Show where a specific setting comes from                                   |
| `git config --global init.defaultBranch main`      | Use `main` as the default branch name for new repos                        |
| `git config --global pull.rebase true`             | Make `git pull` rebase instead of merge by default                         |
| `git config --global push.autoSetupRemote true`    | Auto-set upstream when pushing a new branch                                |
| `git config --global rerere.enabled true`          | Remember how you resolved conflicts so Git can auto-resolve them next time |
| `git config --global fetch.prune true`             | Auto-remove stale remote-tracking branches on fetch                        |

> **See also:** [git-config-reference.md](../../git-config-reference.md) for a
> comprehensive config reference with recommended values.

### Creating & Switching Branches

| Command                                        | What it does                                           |
| ---------------------------------------------- | ------------------------------------------------------ |
| `git switch main`                              | Switch to the `main` branch                            |
| `git switch -c feature/my-feature`             | Create a new branch and switch to it                   |
| `git switch -c feature/my-feature origin/main` | Create a new branch based on remote `main` (not local) |
| `git checkout -b feature/my-feature`           | Same as `switch -c` (older syntax, still works)        |
| `git branch`                                   | List local branches (current branch marked with `*`)   |
| `git branch -a`                                | List all branches (local + remote-tracking)            |
| `git branch -d feature/done`                   | Delete a local branch (only if fully merged)           |
| `git branch -D feature/abandoned`              | Force-delete a local branch (even if unmerged)         |
| `git branch --show-current`                    | Print the name of the current branch                   |
| `git branch -m old-name new-name`              | Rename a local branch                                  |

### Daily Workflow

| Command                       | What it does                                                  |
| ----------------------------- | ------------------------------------------------------------- |
| `git status`                  | Show working tree status (modified, staged, untracked files)  |
| `git status -sb`              | Short status with branch info (compact view)                  |
| `git add <file>`              | Stage a specific file for the next commit                     |
| `git add -A`                  | Stage all changes (new, modified, deleted files)              |
| `git add -p`                  | Interactively stage hunks — lets you commit parts of a file   |
| `git restore <file>`          | Discard uncommitted changes in a file (revert to last commit) |
| `git restore --staged <file>` | Unstage a file (keep changes in working directory)            |
| `git diff`                    | Show unstaged changes                                         |
| `git diff --staged`           | Show staged changes (what will go into the next commit)       |
| `git diff main..HEAD`         | Show all changes between `main` and your current branch       |

### Committing

| Command                                           | What it does                                                       |
| ------------------------------------------------- | ------------------------------------------------------------------ |
| `git commit -m "feat: add login"`                 | Commit staged changes with a message                               |
| `git commit`                                      | Open editor for a longer commit message                            |
| `git commit --amend`                              | Modify the last commit (message and/or content)                    |
| `git commit --amend --no-edit`                    | Add staged changes to the last commit without changing the message |
| `git commit --allow-empty -m "chore: trigger CI"` | Create an empty commit (useful to re-trigger workflows)            |
| `cz commit`                                       | Interactive conventional commit via commitizen                     |

> **Warning:** `--amend` rewrites history. Only amend commits that haven't
> been pushed, or use `--force-with-lease` after amending a pushed commit.

### Syncing with Remote

| Command                       | What it does                                                             |
| ----------------------------- | ------------------------------------------------------------------------ |
| `git fetch origin`            | Download latest commits/branches from remote (doesn't change your files) |
| `git pull --ff-only`          | Pull only if it's a fast-forward (no merge commit created)               |
| `git pull --rebase`           | Pull and rebase your local commits on top of remote changes              |
| `git push`                    | Push current branch to its upstream                                      |
| `git push -u origin HEAD`     | Push current branch and set upstream tracking (first push)               |
| `git push --force-with-lease` | Force-push safely — refuses if remote has commits you haven't seen       |
| `git push --force`            | Force-push unconditionally — **dangerous**, can overwrite others' work   |
| `git remote -v`               | Show remote URLs (fetch and push)                                        |

> **`--force-with-lease` vs `--force`:** Always prefer `--force-with-lease`.
> It's the safe version — it checks that the remote branch is where you
> expect it to be before overwriting. Plain `--force` overwrites blindly.

### Rebasing

Rebasing replays your commits on top of another branch. This keeps history
linear (which this project requires — see [ADR 022](../adr/022-rebase-merge-strategy.md)).

| Command                  | What it does                                                           |
| ------------------------ | ---------------------------------------------------------------------- |
| `git rebase origin/main` | Replay current branch's commits on top of remote `main`                |
| `git rebase -i HEAD~3`   | Interactive rebase — edit, reorder, squash, or drop the last 3 commits |
| `git rebase --continue`  | Continue rebase after resolving a conflict                             |
| `git rebase --abort`     | Cancel the rebase and go back to the state before it started           |
| `git rebase --skip`      | Skip the current commit during rebase (use with caution)               |

**Interactive rebase keywords:**

| Keyword  | Short | What it does                                          |
| -------- | ----- | ----------------------------------------------------- |
| `pick`   | `p`   | Keep the commit as-is                                 |
| `reword` | `r`   | Keep the commit but edit its message                  |
| `edit`   | `e`   | Pause at this commit to amend it                      |
| `squash` | `s`   | Merge into the previous commit (combine messages)     |
| `fixup`  | `f`   | Merge into the previous commit (discard this message) |
| `drop`   | `d`   | Remove the commit entirely                            |

### Resolving Merge Conflicts

When a rebase or merge hits a conflict, Git pauses and marks the conflicted
files. The general workflow:

```bash
# 1. See which files are conflicted
git status

# 2. Open each conflicted file and resolve the conflict markers:
#    <<<<<<< HEAD
#    (your changes)
#    =======
#    (incoming changes)
#    >>>>>>> branch-name

# 3. After editing, mark the file as resolved
git add <resolved-file>

# 4. Continue the rebase (or merge)
git rebase --continue    # if rebasing
# or
git merge --continue     # if merging
```

**Conflict resolution on feature branches (recommended workflow):**

```bash
git checkout your-branch          # switch to your feature branch
git fetch origin                  # download latest main
git rebase origin/main            # replay your commits on top of updated main
# resolve conflicts file-by-file, then:
git push --force-with-lease       # update the remote branch
```

> **Don't resolve conflicts in GitHub's web editor** for this project.
> It creates a merge commit, which disables the "Rebase and merge" button.
> Always rebase locally. See [Releasing — Merge Conflicts on a Feature Branch](../releasing.md#merge-conflicts-on-a-feature-branch) for full details.

### Stashing

Stash temporarily shelves changes so you can switch branches without committing
unfinished work.

| Command             | What it does                                                  |
| ------------------- | ------------------------------------------------------------- |
| `git stash`         | Stash tracked changes (staged + unstaged)                     |
| `git stash -u`      | Stash everything including untracked files                    |
| `git stash list`    | Show all stashes                                              |
| `git stash pop`     | Apply the most recent stash and remove it from the stash list |
| `git stash apply`   | Apply the most recent stash but keep it in the list           |
| `git stash drop`    | Delete the most recent stash                                  |
| `git stash show -p` | Show the diff of the most recent stash                        |

### Inspecting History

| Command                           | What it does                                                        |
| --------------------------------- | ------------------------------------------------------------------- |
| `git log --oneline`               | Compact log — one line per commit                                   |
| `git log --oneline -10`           | Show only the last 10 commits                                       |
| `git log --oneline --graph --all` | Visual branch graph of all branches                                 |
| `git log --author="Name"`         | Filter commits by author                                            |
| `git log --since="2 weeks ago"`   | Filter commits by date                                              |
| `git log main..HEAD`              | Show commits on your branch that aren't on `main`                   |
| `git show <commit>`               | Show the full diff and message of a specific commit                 |
| `git blame <file>`                | Show who last modified each line of a file                          |
| `git reflog`                      | Show history of HEAD movements — useful for recovering lost commits |

### Undoing Things

| Command                                 | What it does                                      | Safe?                              |
| --------------------------------------- | ------------------------------------------------- | ---------------------------------- |
| `git restore <file>`                    | Discard uncommitted changes in a file             | Yes (only affects working tree)    |
| `git restore --staged <file>`           | Unstage a file                                    | Yes (only affects index)           |
| `git commit --amend`                    | Rewrite the last commit                           | Rewrites history                   |
| `git revert <commit>`                   | Create a new commit that undoes a previous commit | Yes (additive)                     |
| `git reset --soft HEAD~1`               | Undo last commit, keep changes staged             | Rewrites history                   |
| `git reset --mixed HEAD~1`              | Undo last commit, keep changes unstaged (default) | Rewrites history                   |
| `git reset --hard HEAD~1`               | Undo last commit and **discard all changes**      | **Destructive** + rewrites history |
| `git reflog` + `git reset --hard <sha>` | Recover from almost any mistake using reflog      | Depends on target                  |

> **Rule of thumb:** Use `revert` for commits already pushed to a shared
> branch. Use `reset` only for local, unpushed commits.

### Tags

| Command                                | What it does                          |
| -------------------------------------- | ------------------------------------- |
| `git tag`                              | List all tags                         |
| `git tag v1.0.0`                       | Create a lightweight tag              |
| `git tag -a v1.0.0 -m "Release 1.0.0"` | Create an annotated tag (recommended) |
| `git push origin v1.0.0`               | Push a specific tag to remote         |
| `git push origin --tags`               | Push all tags to remote               |
| `git tag -d v1.0.0`                    | Delete a local tag                    |
| `git push origin :refs/tags/v1.0.0`    | Delete a remote tag                   |

> **In this project**, tags are created automatically by release-please.
> You shouldn't need to create tags manually unless doing a hotfix or
> special release.

### Cleaning Up

| Command                      | What it does                                                   |
| ---------------------------- | -------------------------------------------------------------- |
| `git branch -d feature/done` | Delete a merged local branch                                   |
| `git fetch --prune`          | Remove remote-tracking branches that no longer exist on remote |
| `git remote prune origin`    | Same as above but without fetching                             |
| `git clean -fd`              | Remove untracked files and directories (**destructive**)       |
| `git clean -fdn`             | Dry-run — show what `clean -fd` would delete                   |
| `git gc`                     | Run garbage collection to optimize the repo                    |

### Useful Aliases

These are optional but save keystrokes. Set them with
`git config --global alias.<name> "<command>"`:

```bash
git config --global alias.st "status -sb"
git config --global alias.co "checkout"
git config --global alias.sw "switch"
git config --global alias.br "branch"
git config --global alias.ci "commit"
git config --global alias.lg "log --oneline --graph --all --decorate"
git config --global alias.last "log -1 HEAD --stat"
git config --global alias.unstage "restore --staged"
git config --global alias.amend "commit --amend --no-edit"
git config --global alias.wip "commit -am 'wip: work in progress'"
```

After setting these, `git st` is equivalent to `git status -sb`, etc.

---

## See Also

- [Resources (Links)](resources_links.md) — curated external links
- [Learning](learning.md) — tips and patterns learned while working on this project
- [git-config-reference.md](../../git-config-reference.md) — comprehensive git config reference (auto-generated)
- [Releasing — Merge Conflicts](../releasing.md#merge-conflicts-on-a-feature-branch) — conflict resolution in the PR workflow
- [ADR 022 — Rebase+merge strategy](../adr/022-rebase-merge-strategy.md)
- [Pro Git book (free)](https://git-scm.com/book/en/v2)
- [Oh Shit, Git!?!](https://ohshitgit.com/)

---

## Project Health & Diagnostics

Quick commands for keeping the repo in shape. See
[commands.md](../reference/commands.md) for the full reference.

### Health Checks

| Command                      | What it does                                  |
| ---------------------------- | --------------------------------------------- |
| `task doctor:all`            | Run all health checks in one report           |
| `task doctor:env`            | Python, Hatch, tools, editable install        |
| `task doctor:repo`           | Repo structure, conventions, missing files    |
| `task doctor:git`            | Git dashboard: branches, remotes, health      |
| `task doctor:git:refresh`    | Fetch remotes, prune stale refs, sync tags    |
| `task doctor:git:cleanup`    | Delete stale local branches, run `git gc`     |
| `task doctor:git:commits`    | Detailed commit report (SHAs, per-file stats) |
| `task doctor:git:commits:md` | Write commit report to `commit-report.md`     |

### Git Config Management

| Command                                     | What it does                                 |
| ------------------------------------------- | -------------------------------------------- |
| `task doctor:git:config:export`             | Export full git config reference to Markdown |
| `task doctor:git:config:minimal`            | Apply 12 core recommended configs            |
| `task doctor:git:config:apply`              | Apply ALL catalog recommended configs        |
| `task doctor:git:config:apply -- --dry-run` | Preview changes before applying              |

### Dependency & Action Management

| Command                 | What it does                                  |
| ----------------------- | --------------------------------------------- |
| `task deps:versions`    | Show installed vs. latest dependency versions |
| `task deps:upgrade`     | Upgrade a dependency                          |
| `task actions:versions` | Show pinned GitHub Actions with version tags  |
| `task actions:upgrade`  | Upgrade pinned actions to latest              |
| `task actions:check`    | CI gate: exit non-zero if stale actions       |

### Quality Gates

| Command          | What it does                                          |
| ---------------- | ----------------------------------------------------- |
| `task check`     | Run all quality gates (lint, format, typecheck, test) |
| `task test`      | Run tests                                             |
| `task test:cov`  | Run tests with coverage                               |
| `task lint`      | Check for linting issues                              |
| `task lint:fix`  | Auto-fix linting issues                               |
| `task fmt`       | Apply formatting                                      |
| `task typecheck` | Run mypy type checker                                 |
| `task security`  | Run bandit security linter                            |
