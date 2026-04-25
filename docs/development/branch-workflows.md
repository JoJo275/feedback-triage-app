# Branch Workflows

<!-- TODO (template users): Update this document with your team's actual
     branch naming conventions, merge strategy preferences, and workflow
     patterns. Remove sections that don't apply to your team. -->

This guide covers branch management patterns, team collaboration workflows,
and common scenarios when working with feature branches and `main`.

For the release process itself (release-please, version bumps, CHANGELOG),
see [Releasing](../releasing.md).

---

## Branch Lifecycle

```text
create branch → commit → push → open PR → CI passes → review → merge → delete branch
```

Every code change follows this pattern. Direct pushes to `main` are blocked
by branch protection.

### Quick Reference

```bash
# Interactive branch creation (recommended)
task branch:create
# or: python scripts/git_doctor.py --new-branch

# Manual: start a new branch from latest main
git fetch origin
git switch -c feature/my-feature origin/main

# Push and set upstream tracking
git push -u origin HEAD

# After PR is merged, clean up local branch
git switch main
git pull --ff-only
git branch -d feature/my-feature
```

---

## Keeping Your Branch Up to Date

### What Does "Syncing with Main" Mean?

"Syncing with main" (also called "updating your branch") means pulling
the latest changes from `main` into your current working branch so that
your branch includes everything that has been merged to `main` since you
branched off.

Without syncing, your branch gradually falls behind. Code that was added,
fixed, or refactored on `main` won't be in your branch. This leads to:

- **Merge conflicts at PR time** — your branch and `main` diverged in
  overlapping areas, and now you have to resolve them all at once.
- **CI failures on your PR** — your code passes locally but breaks
  against the newer version of `main`.
- **Duplicated work** — you re-implement something that was already
  added to `main` by someone else.

In this project, syncing is done with **rebase** (not merge), which
replays your commits on top of the latest `main` — producing a clean,
linear history.

### How to Sync

When `main` moves ahead while you're working on a feature branch, you need
to incorporate those changes. Use **rebase**, not merge:

```bash
# Quick: one command that fetches, prunes stale refs, and syncs tags
task doctor:git:refresh

# Then rebase and push
git rebase origin/main            # replay your commits on top of updated main
git push --force-with-lease       # update remote (rebase rewrites history)
```

Or do the fetch manually:

```bash
git fetch origin                  # download latest commits
git rebase origin/main            # replay your commits on top of updated main
git push --force-with-lease       # update remote (rebase rewrites history)
```

> **Why `--force-with-lease`?** It refuses to push if someone else pushed
> to your branch since your last fetch — preventing you from accidentally
> overwriting their work. Never use bare `--force`.

### When to Rebase

<!-- TODO (template users): Adjust these guidelines based on your team's
     rebase frequency preferences. Some teams rebase daily, others only
     before merge. -->

| Situation                       | Action                                        |
| ------------------------------- | --------------------------------------------- |
| `main` has new commits you need | `git fetch origin && git rebase origin/main`  |
| CI fails due to main changes    | Rebase to get the fixes                       |
| Before requesting review        | Rebase to ensure branch is current            |
| Merge conflicts appear on PR    | Rebase locally, resolve, force-push           |
| Long-running branch (>1 week)   | Rebase periodically to avoid conflict buildup |

### Merge Bot Branches Before Creating New Branches

Before branching off `main` for new work, check whether there are pending
bot PRs (Dependabot, release-please, etc.) that can be merged first.

**Why this matters:** If you branch from `main` _before_ those bot PRs
merge, your new branch won't have their changes. When you later try to
merge your feature branch back into `main` (which now includes the bot
changes), you may face avoidable merge conflicts — especially in lockfiles,
`CHANGELOG.md`, or `pyproject.toml`.

**Before starting a new branch:**

```bash
# Check for open bot PRs on GitHub
# Merge any that are green (CI passing) and approved

# Then start your branch from the freshly-updated main
git fetch origin
git switch -c feature/my-feature origin/main
```

If a bot PR merges _after_ you've already branched, rebase onto `main`
to incorporate it early rather than waiting until your PR is ready:

```bash
git fetch origin                  # update remote-tracking branches
git rebase origin/main            # replay your commits on top of latest main
git push --force-with-lease       # safely update remote (rebase rewrites SHAs)
```

This keeps conflicts small and isolated instead of discovering them all
at PR merge time.

### Understanding "Up to Date" vs "Diverged"

The git doctor shows two related but different characteristics:

- **"Up to date with main"** — Your branch contains all commits from `main`.
  There are 0 commits on `main` that aren't reachable from your branch.
  Measured by: `git rev-list --count HEAD..origin/main` = 0.

- **"Diverged from main"** — Your branch tip (HEAD) points to a different
  commit than `main`'s tip. This happens whenever you have commits of your
  own, even if you've rebased on top of the latest `main`.

**These are not contradictory.** A branch can be both "up to date" AND
"diverged" simultaneously. This is the _normal_ state for an active feature
branch that's been rebased onto `main`:

```text
main:     A ← B ← C           (main tip = C)
branch:   A ← B ← C ← D ← E  (branch tip = E, contains all of main's commits)

Result:
  ✅ "up to date with main"  — 0 commits behind (C is reachable from E)
  📌 "diverged from main"    — branch tip E ≠ main tip C
```

The concerning case is when a branch is **behind main AND diverged** — that
means `main` has new commits your branch doesn't have yet:

```text
main:     A ← B ← C ← F ← G       (main moved ahead)
branch:   A ← B ← C ← D ← E       (branch doesn't have F, G)

Result:
  ⚠️ "2 commit(s) behind main"  — F and G are not on this branch
  📌 "diverged from main"       — branch tip E ≠ main tip G
```

**Fix:** `git fetch origin && git rebase origin/main` to incorporate `F`
and `G` into your branch.

---

## Working with the Release PR

<!-- TODO (template users): Adjust this section based on how your team
     handles release timing. Some teams merge the Release PR immediately
     after every feature; others batch features into releases. -->

release-please automatically creates a Release PR when releasable commits
land on `main`. This PR accumulates entries until you merge it.

### Feature Branch + Open Release PR

If a release-please PR is open while you're on a feature branch:

1. **Ignore it** — finish your feature work normally
2. **Merge your feature PR** to `main`
3. release-please re-runs and updates the Release PR to include your commits
4. Merge the Release PR when ready to cut a release

### Merging Release PR Before Your Branch

If you want to ship a release of previous work before continuing:

```bash
# After merging the release-please PR on GitHub:
git fetch origin
git rebase origin/main            # incorporate version bump
git push --force-with-lease       # update your branch
```

Conflicts are unlikely since release-please only touches `CHANGELOG.md`,
`__init__.py`, and `.release-please-manifest.json`.

### Why CHANGELOG.md May Not Appear in Release PR Diffs

You might notice that `CHANGELOG.md` doesn't show up in the "Files changed"
tab of a release-please PR. This can happen for a few reasons:

- **The PR is still accumulating** — release-please updates the PR
  description and body with pending changelog entries, but the actual
  `CHANGELOG.md` file change is only part of the PR diff _after_
  release-please has processed new commits. If no releasable commits have
  landed since the PR was created or last updated, the file won't show as
  changed.
- **Force-push resets the diff base** — release-please force-pushes its
  branch. GitHub's "Files changed" tab shows the diff between the PR
  branch tip and the merge base with `main`. After a force-push, this
  recalculates — sometimes the diff appears empty or incomplete until
  GitHub finishes reindexing.
- **GitHub diff display limits** — For PRs with many changed files, GitHub
  may truncate the diff view. Scroll to the bottom of Files changed and
  look for "Load diff" or "X files not shown."

**Check the actual branch content** if you need to verify:

```bash
git fetch origin                  # ensure remote refs are current
git diff main..origin/release-please--branches--main -- CHANGELOG.md
# Show what changed in CHANGELOG.md between main and the release-please branch
```

---

## Common Scenarios

### Stale Branch Recovery

When a branch has been idle for many days and `main` has moved significantly:

```bash
git fetch origin                  # download latest commits from all remotes
git rebase origin/main            # replay your commits on top of main (may have conflicts)
# Resolve any conflicts, then:
git add <resolved-files>          # stage resolved files
git rebase --continue             # continue replaying remaining commits
git push --force-with-lease       # safely update remote branch
```

If conflicts are too complex, you can abort and start fresh:

```bash
git rebase --abort                # undo the rebase attempt
git switch -c feature/my-feature-v2 origin/main  # fresh branch
git cherry-pick <commit-shas>     # selectively bring over your work
```

### Cherry-Picking Multiple Commits into a New Branch

Sometimes you need to selectively bring specific commits from one or more
branches into a new branch — for example, extracting a subset of work from
a large branch, recovering commits from an abandoned branch, or assembling
a hotfix from commits scattered across multiple branches.

#### Basic: Cherry-Pick a Known List of Commits

If you already know the commit hashes:

```bash
git fetch origin                  # ensure you have the latest refs
git switch -c feature/extracted origin/main
                                  # create a new branch from latest main
git cherry-pick abc1234 def5678 789abcd
                                  # apply each commit in order onto the new branch
git push -u origin HEAD           # push and set upstream tracking
```

> **Commit order matters.** List the commits in chronological order
> (oldest first). If commit B depends on changes from commit A,
> cherry-picking B before A will cause conflicts.

#### Selecting Commits from `git log`

Use `git log` to identify which commits you want:

```bash
# Show compact log of a branch with commit hashes
git log --oneline feature/old-branch
# Output:
#   789abcd feat: add validation
#   def5678 feat: add form component
#   abc1234 feat: add data model
#   ...older commits...

# Show only commits unique to a branch (not on main)
git log --oneline origin/main..feature/old-branch

# Show commits by a specific author
git log --oneline --author="your-name" feature/old-branch

# Show commits touching a specific file
git log --oneline -- src/auth.py
```

Copy the hashes you want, then cherry-pick them:

```bash
git switch -c feature/extracted origin/main
git cherry-pick abc1234 def5678 789abcd
```

#### Cherry-Picking a Range of Commits

To cherry-pick a contiguous range:

```bash
# Cherry-pick all commits from abc1234 (exclusive) through 789abcd (inclusive)
git cherry-pick abc1234..789abcd

# To include the start commit, use ^:
git cherry-pick abc1234^..789abcd  # includes abc1234 itself
```

#### Cherry-Picking All Commits from a Branch

To bring over every commit a branch has that `main` doesn't:

```bash
# Find where the branch diverged from main and cherry-pick everything after
git switch -c feature/revived origin/main
git cherry-pick origin/main..feature/old-branch
                                  # all commits on old-branch not on main
```

#### Handling Conflicts During Cherry-Pick

```bash
# If a conflict occurs mid cherry-pick:
git status                        # see which files have conflicts
# Edit the conflicted files to resolve
git add <resolved-files>          # stage the resolved files
git cherry-pick --continue        # continue with the next commit

# To skip a problematic commit:
git cherry-pick --skip            # skip this commit and continue

# To abort the entire cherry-pick operation:
git cherry-pick --abort           # return to the state before cherry-pick
```

#### Tips

- **Use `--no-commit` for squashing:** `git cherry-pick --no-commit abc def`
  applies the changes but doesn't commit — useful when you want to combine
  multiple cherry-picked commits into one.
- **Duplicate commits after cherry-pick:** Cherry-picked commits get new
  SHAs. If the original branch is later merged into `main`, Git usually
  handles it cleanly, but the commits will appear twice in `git log`.
- **Prefer rebase when possible:** If you want _all_ commits from a branch,
  rebasing is usually simpler than cherry-picking. Cherry-pick is best for
  selective extraction.

### Working on Multiple Features

Keep each feature on its own branch. Don't pile unrelated changes together:

```bash
# Feature A
git switch -c feature/add-login origin/main
                                  # new branch from main for login feature
# ... work, commit, push, open PR

# Feature B (independent of A)
git switch -c feature/add-dashboard origin/main
                                  # separate branch from main for dashboard
# ... work, commit, push, open PR
```

### Stacked Branches (Branching off a Feature Branch)

<!-- TODO (template users): Consider whether your team uses stacked branches.
     If not, this section can be removed. Stacked branches add complexity
     and are mainly useful for large features that benefit from incremental
     review. -->

Sometimes you need to build on work that's still under review:

```bash
git switch -c feature/part-2 feature/part-1   # branch from the feature, not main
```

**Warning:** When `feature/part-1` is merged via rebase+merge, its commit
SHAs change. You'll need to rebase `part-2` onto `main` afterward:

```bash
# After part-1 is merged to main:
git fetch origin                  # get the merged changes
git rebase origin/main            # part-2 now sits on main (with part-1's changes)
git push --force-with-lease       # update part-2's remote branch
```

---

## Managing Merge Conflicts

Merge conflicts are a normal part of collaborative development. They become
a real problem only when allowed to grow large. The core principle is:
**keep conflicts small, frequent, and local rather than rare and massive.**

### Why Conflicts Happen

Git raises a merge conflict when the same nearby lines in a file were
changed in incompatible ways on two different branches. If you edit
`src/auth.py` and someone else edits `docs/config.md`, there is no
conflict — even though both branches diverged from `main`.

Even edits in the _same file_ often merge cleanly if the changes are in
different functions or sections.

### What Makes Conflicts Painful

The worst merge-conflict pain comes from a combination of:

- **Long-lived branches** — the longer a branch lives, the more `main`
  moves ahead, and the more chance of overlapping changes.
- **Huge PRs** — touching 20 files across many modules means more surface
  area for conflicts.
- **Multiple people editing the same files** — especially "god files"
  that accumulate too many responsibilities.
- **Big refactors mixed with feature work** — renaming, restructuring,
  and new logic in the same PR guarantees conflict-heavy merges.
- **Weak tests and CI** — even when Git merges text cleanly, the result
  can be _logically_ broken (see [semantic conflicts](#semantic-conflicts)
  below).

### Strategies That Keep Conflicts Small

#### 1. Small Branches, Short Lifetime

A branch should live for hours or a few days, not weeks.

**Bad pattern:**

- Branch off `main`
- Work for 2 weeks, touch 20 files
- Try to merge back → massive conflict mess

**Better pattern:**

- Branch off `main`
- Make one focused change
- Open PR quickly, merge quickly
- Repeat

Smaller PRs mean fewer overlapping edits, easier review, and easier
conflict resolution when conflicts do occur.

#### 2. Sync with Main Often

Don't wait until your PR is ready to incorporate changes from `main`.
Rebase regularly while working:

```bash
git fetch origin                  # download latest commits from remote
git rebase origin/main            # replay your work on top of current main
git push --force-with-lease       # update remote (safe force-push)
```

This turns one giant end-of-project conflict into a few tiny daily ones.
Each rebase session touches fewer files and the context is fresh in your
mind.

#### 3. Split Ownership and Scope

Conflicts happen most when multiple people touch the same files. Teams
reduce overlap by:

- Dividing features by subsystem or module
- Assigning clear ownership for certain areas of code
- Keeping modules cleanly separated with well-defined interfaces
- Avoiding "everyone edits everything" patterns

Good architecture reduces conflicts. If every feature requires editing
the same 3 giant files, the codebase is poorly shaped for teamwork.

#### 4. Feature Flags

A **feature flag** (also called a feature toggle) is a conditional check
in your code that controls whether a feature is active or not — without
deploying separate code. The simplest form:

```python
# settings.py or config
ENABLE_NEW_DASHBOARD = False      # flip to True when the feature is ready

# usage in application code
if settings.ENABLE_NEW_DASHBOARD:
    show_new_dashboard()
else:
    show_old_dashboard()
```

Feature flags aren't just for rollout control. They're a **branching
strategy**: unfinished work merges into `main` behind a disabled flag
rather than living on a long-running branch. This gives you:

- **Short-lived branches** — code merges early because incomplete features
  are disabled in production. The branch only needs to live long enough to
  implement one slice of the feature.
- **Fewer merge conflicts** — since the code is on `main` quickly, other
  developers already have it. No surprise conflicts weeks later.
- **Incremental delivery** — you can merge the database schema first, then
  the API, then the UI — each behind the same flag. Each PR is small and
  reviewable.
- **Safe rollbacks** — if a feature causes problems in production, flip
  the flag off instead of reverting commits or deploying a hotfix.
- **Testing in production** — enable the flag for a subset of users or
  environments (canary releases, A/B testing) before full rollout.

**Common implementations:**

| Approach                                     | Complexity | Best for                                 |
| -------------------------------------------- | ---------- | ---------------------------------------- |
| Boolean config/env variable                  | Low        | Small teams, simple on/off toggles       |
| Config file (JSON/TOML)                      | Low        | Multiple flags, environment-specific     |
| Database-backed flags                        | Medium     | Runtime toggling without redeployment    |
| Feature flag service (LaunchDarkly, Unleash) | High       | Large teams, A/B tests, gradual rollouts |

**When to use feature flags:**

- A feature takes more than a few days to build
- Multiple developers need to work on the same feature incrementally
- You want to ship code to production before the feature is complete
- You need the ability to disable a feature quickly post-deploy

**When NOT to use feature flags:**

- Simple one-PR features — just use a short-lived branch
- Refactors that don't change behavior — no need to toggle
- When the flag would never realistically be turned off

> **Cleanup matters.** Feature flags are temporary. Once a feature is
> fully rolled out and stable, remove the flag and the old code path.
> Stale flags accumulate as tech debt and make the codebase harder to
> reason about.

This is a major reason large teams can move fast with minimal merge pain.

#### 5. Communication

A lot of merge pain is a coordination problem, not a Git problem. If two
people are both rewriting the same module, they should know early. Teams
avoid this with:

- Task planning and issue assignment
- Draft PRs that signal "I'm working on this area"
- Quick messages like "I'm refactoring auth this afternoon"
- PR comments explaining what areas are affected (see
  [PR comments as communication](#pr-comments-as-communication) below)

### Semantic Conflicts

Git can merge text automatically but still miss a _logical_ conflict:

- You rename a function
- Someone else adds new calls to the old function name
- Git merges both changes cleanly (no text conflict)
- Code compiles but breaks at runtime

**The real defense is not just conflict resolution — it's:**

- Tests (catch broken behavior)
- CI (catch it before merge)
- Code review (catch it before CI)
- Small changes (reduce the surface area for these issues)

### Typical Healthy Workflow

The normal rhythm on a well-run project:

1. Branch from fresh `main`
2. Make a small, focused change
3. Push early
4. Open PR early (even as draft for visibility)
5. Sync with `main` if it moved
6. Get review, merge quickly
7. Delete branch

### Two Main Branching Styles

#### Style A: Short-lived Feature Branches

The most common approach and usually the safest default.

**Pros:**

- Clean review flow with isolated work
- Easy-to-understand PRs
- Clear mapping between branches and tasks

**Cons:**

- Conflicts grow if branches live too long
- Requires discipline to keep branches short

**Best for:** Most teams, especially small-to-medium projects.

#### Style B: Trunk-based Development

Developers integrate into `main` very frequently — often daily or
multiple times a day — usually combined with feature flags.

**Pros:**

- Minimal branch drift
- Fewer giant merges
- Faster integration feedback

**Cons:**

- Requires discipline, strong tests, and reliable CI
- Can feel intense for less experienced teams
- Needs feature flag infrastructure for incomplete work

**Best for:** Mature teams with strong CI and testing culture.

### Conflicts Are Often Overestimated

In practice, Git only raises a merge conflict when the _same nearby lines_
changed in incompatible ways. Most of the time:

- Different people edit different files → no conflict
- Same file, different sections → no conflict
- Same function, nearby lines → Git may still auto-resolve

The mental model: think of branches like leftovers. Fresh leftovers are
easy to deal with. Week-old leftovers become risky and annoying. Branches
work the same way — the longer they sit, the uglier they get.

---

## Handling CI Failures on Bot PRs

Dependabot, release-please, and other automation tools create PRs that
can fail CI for reasons unrelated to your current work. This is normal
and needs a clear handling strategy.

### When You're on a Feature Branch and a Bot PR Fails CI

You don't need to switch branches to fix a bot PR. The approach depends
on what failed:

**If the bot PR has a genuine build/test failure:**

```bash
# Option 1: Fix it from your current branch (preferred if the fix is small)
git stash                         # save uncommitted work to the stash stack

# Switch to a fix branch based on the bot's PR branch
git fetch origin                  # download the bot's branch from remote
git switch -c fix/dependabot-ci origin/dependabot/pip/ruff-0.9.0
                                  # create local branch from the bot's PR branch
# Make the fix, push, let CI re-run
git push -u origin HEAD           # push and set upstream tracking

# Return to your feature branch
git switch feature/my-feature     # switch back to your original branch
git stash pop                     # restore your uncommitted work
```

```bash
# Option 2: Fix it on the bot branch directly via GitHub
# Use the GitHub web editor or Codespaces to make a small fix
# directly on the bot's PR branch — no local branch switching needed
```

```bash
# Option 3: Close and let the bot recreate
# If the fix is too complex or the update isn't urgent, close the bot PR
# The bot will recreate it on its next schedule (usually within a day)
```

**If CI fails because of a flaky test or infra issue:**

- Re-run the failed workflow from the PR's Checks tab
- If it keeps failing, check whether `main` itself is broken first

**If CI fails because of a conflict with `main`:**

- The bot usually auto-rebases on its next run
- Or close the PR and let the bot recreate it
- Some Dependabot PRs can be rebased manually:
  comment `@dependabot rebase` on the PR

### Preventing Bot PR Conflicts

- Merge bot PRs promptly — don't let them pile up
- Merge bot PRs _before_ creating new feature branches (see
  [Merge Bot Branches First](#merge-bot-branches-before-creating-new-branches))
- Keep lockfiles and config files well-structured so bot changes are
  isolated to specific sections

### Priority of Bot PRs

| Bot PR type                   | Urgency | Action                                            |
| ----------------------------- | ------- | ------------------------------------------------- |
| Security update (Dependabot)  | High    | Merge ASAP, even if it means pausing feature work |
| Minor/patch dependency update | Medium  | Merge within a day or two if CI passes            |
| release-please PR             | Low     | Merge when you're ready to cut a release          |
| Other automated PRs           | Low     | Review and merge at your convenience              |

---

## PR Comments as Communication

PR comments aren't just for code review — they're a coordination tool
that helps your team (and your future self) understand what's happening.

### What to Communicate on PRs

- **What the PR does and why** — the PR description covers this, but
  comments can add context as the PR evolves
- **Areas of the codebase affected** — "This touches the auth module,
  heads up if you're working there too"
- **Decisions made during implementation** — "I went with approach X
  instead of Y because..."
- **Known limitations** — "This doesn't handle edge case Z yet, will
  follow up in #123"
- **Questions for reviewers** — "Not sure about this pattern, thoughts?"
- **Status updates** — "Rebased onto latest main, conflicts resolved"
  or "CI failure is flaky, re-running"

### When Comments Help Most

| Situation           | Useful comment                                             |
| ------------------- | ---------------------------------------------------------- |
| Large PR            | "Core change is in `auth.py`, rest is mechanical updates"  |
| Conflict resolution | "Resolved conflict in `config.py` by keeping both changes" |
| CI re-run           | "Test failure was flaky network timeout, re-running"       |
| Stacked PRs         | "This depends on #45, merge that first"                    |
| Design decision     | "Chose polling over webhooks because of X"                 |
| Bot PR fix          | "Added missing type stub to fix Dependabot CI failure"     |

### Comments on Your Own PRs

Don't wait for someone else to comment first. Self-review comments are
valuable — walk through your own diff and annotate anything non-obvious.
This speeds up review, documents your thinking, and often catches issues
before a reviewer does.

---

## Handling Breakage on Main

Sometimes `main` itself breaks — a flaky merge, a missed conflict, or
a dependency update that passed CI but breaks locally. When this happens
while you're on a feature branch:

```bash
# Don't rebase onto broken main — wait for the fix
# Check main's CI status on GitHub before rebasing

# If you already rebased onto broken main:
git reflog                        # find your pre-rebase state
git reset --hard HEAD@{n}         # restore to before the rebase
```

If you can fix the issue quickly, it's often worth opening a small
fix PR against `main` before continuing your feature work. This
unblocks everyone, not just you.

---

## CI Workflow Triggers

<!-- TODO (template users): Update this table if you add or remove workflows,
     or change their trigger conditions. Keep in sync with docs/workflows.md. -->

Understanding when CI runs helps avoid surprise failures:

| What you do                    | What triggers                                       |
| ------------------------------ | --------------------------------------------------- |
| Push to feature branch (no PR) | Nothing — CI only runs on PRs targeting `main`      |
| Open PR targeting `main`       | All PR workflows (lint, test, typecheck, security)  |
| Push to PR branch              | CI re-runs on the updated PR                        |
| Merge PR to `main`             | Push-to-main workflows (release-please, doctor-all) |
| release-please creates tag     | Release workflow (build, publish, SBOM)             |

> **Pre-commit hooks** are your local safety net. They catch issues before
> code reaches CI. See the [Releasing guide](../releasing.md) for hook
> installation instructions.

### Skipped Workflows

Some workflows have **repository guards** — they only run if repository
variables are set or the repo slug matches a configured value. If a workflow
shows as "skipped" in your PR checks:

1. Check the workflow's `if:` condition for a `YOURNAME/YOURREPO` guard
2. Either replace the placeholder with your repo slug, or set the
   corresponding repository variable in Settings → Variables → Actions

Common guards:

| Workflow       | Variable to enable                         |
| -------------- | ------------------------------------------ |
| Doctor All     | `ENABLE_DOCTOR_ALL` or `ENABLE_WORKFLOWS`  |
| Repo Doctor    | `ENABLE_REPO_DOCTOR` or `ENABLE_WORKFLOWS` |
| Release Please | `ENABLE_RELEASE_PLEASE`                    |
| Release        | `ENABLE_RELEASE`                           |
| Commit Lint    | `ENABLE_COMMIT_LINT`                       |

> **Skipped ≠ failed.** The CI gate treats skipped workflows as passing.
> This is by design — optional workflows shouldn't block merges.

---

## Branch Naming Conventions

| Prefix      | Use for                    | Example                    |
| ----------- | -------------------------- | -------------------------- |
| `feature/`  | New functionality          | `feature/add-login`        |
| `fix/`      | Bug fixes                  | `fix/null-byte-check`      |
| `chore/`    | Maintenance, deps          | `chore/update-ruff`        |
| `docs/`     | Documentation              | `docs/release-guide`       |
| `spike/`    | Experimental / exploratory | `spike/try-fastapi`        |
| `wip/`      | Work in progress / scratch | `wip/2026-03-06-scratch`   |
| `hotfix/`   | Urgent production fixes    | `hotfix/critical-auth-bug` |
| `release/`  | Manual release prep        | `release/v2.0.0`           |
| `refactor/` | Code restructuring         | `refactor/extract-auth`    |
| `test/`     | Test additions/experiments | `test/integration-suite`   |
| `ci/`       | CI/CD changes              | `ci/add-matrix-test`       |

> For the full branch prefixes reference, see
> [learning.md — Branch Prefixes](../notes/learning.md#branch-prefixes).

---

## Interactive Rebase — Cleaning Up History Before a PR

Before opening a PR (or before requesting review), you can clean up your
commit history using interactive rebase. This lets you squash fixup commits,
reword messages, reorder commits, or drop accidental commits.

```bash
# Rebase the last N commits interactively
git rebase -i HEAD~3              # interactively edit the last 3 commits

# Or rebase all commits since diverging from main
git rebase -i origin/main         # edit all commits unique to your branch
```

Git opens an editor showing your commits with actions:

```text
pick abc1234 feat: add data model
pick def5678 fix: typo in model
pick 789abcd feat: add validation
```

Common actions:

| Action   | What it does                                          |
| -------- | ----------------------------------------------------- |
| `pick`   | Keep the commit as-is                                 |
| `reword` | Keep the commit but edit the message                  |
| `squash` | Merge into the previous commit (combine messages)     |
| `fixup`  | Merge into the previous commit (discard this message) |
| `drop`   | Remove the commit entirely                            |
| `edit`   | Pause at this commit so you can amend it              |

**Example — squash a typo fix into the original commit:**

```text
pick abc1234 feat: add data model
fixup def5678 fix: typo in model         ← squash into abc1234, discard message
pick 789abcd feat: add validation
```

After saving and closing the editor, Git replays your commits with the
changes applied. Push with `--force-with-lease` afterward since rebase
rewrites commit SHAs.

> **Use `--fixup` commits for easy cleanup.** When you make a small fix
> to a previous commit, commit it with:
> `git commit --fixup=abc1234`
> Then `git rebase -i --autosquash origin/main` automatically marks it
> as `fixup` in the interactive editor.

---

## Undoing Common Git Mistakes

Mistakes happen. Here are safe ways to undo common ones:

### Undo the Last Commit (Keep Changes)

```bash
git reset --soft HEAD~1           # undo commit, keep changes staged
# Your changes are still in the working tree, ready to re-commit
```

### Undo the Last Commit (Discard Changes)

```bash
git reset --hard HEAD~1           # undo commit AND discard all changes
# WARNING: this is destructive — changes are gone
```

### Amend the Last Commit

```bash
# Fix the commit message
git commit --amend -m "fix: correct message"

# Add forgotten files to the last commit
git add forgotten-file.py
git commit --amend --no-edit      # add to last commit, keep same message
```

> **Never amend commits that have been pushed** to a shared branch.
> On your own feature branch, amend freely and force-push.

### Recover from a Bad Rebase

```bash
git reflog                        # show recent HEAD movements
# Find the entry before the rebase, e.g. HEAD@{3}
git reset --hard HEAD@{3}         # restore to that point
```

### Unstage Files

```bash
git restore --staged file.py      # unstage a file (keep changes in working tree)
git restore --staged .            # unstage everything
```

### Discard Uncommitted Changes

```bash
git restore file.py               # discard changes to a specific file
git restore .                     # discard all uncommitted changes
# WARNING: this is destructive — uncommitted work is lost
```

### Recover a Deleted Branch

```bash
git reflog                        # find the last commit on the deleted branch
git switch -c recovered-branch HEAD@{n}
                                  # recreate the branch at that commit
```

---

## Git Stash — Saving Work Temporarily

`git stash` saves uncommitted changes to a stack so you can switch
branches or pull updates cleanly, then restore your work afterward.

### Basic Stash Workflow

```bash
# Save current changes
git stash                         # stash all tracked modified/staged files

# Do other work (switch branches, pull, etc.)
git switch other-branch
# ...
git switch feature/my-feature     # come back

# Restore stashed changes
git stash pop                     # apply the latest stash and remove from stack
```

### Named Stashes

```bash
git stash push -m "WIP: form validation"
                                  # save with a descriptive name
git stash list                    # see all stashes with names
# stash@{0}: On feature/form: WIP: form validation
# stash@{1}: On main: quick experiment

git stash pop stash@{1}           # restore a specific stash by index
```

### Stash Specific Files

```bash
git stash push -m "just the config" -- config.py settings.toml
                                  # stash only specific files
```

### Include Untracked Files

```bash
git stash -u                      # include untracked (new) files
git stash -a                      # include untracked AND ignored files
```

### Inspect and Clean Up

```bash
git stash show                    # show file-level summary of latest stash
git stash show -p                 # show full diff of latest stash
git stash drop stash@{0}          # delete a specific stash
git stash clear                   # delete ALL stashes (be careful)
```

> **Don't use stash as long-term storage.** If you've had something
> stashed for more than a day, it probably deserves its own branch
> or a WIP commit.

---

## Git Command Quick Reference

Common commands used throughout this guide, with brief descriptions:

| Command                       | What it does                                                                 |
| ----------------------------- | ---------------------------------------------------------------------------- |
| `git fetch origin`            | Download new commits/branches/tags from remote (doesn't change working tree) |
| `git fetch --prune`           | Fetch and remove local tracking refs for deleted remote branches             |
| `git pull --ff-only`          | Update current branch only if it can fast-forward (no merge commits)         |
| `git switch -c <name> <base>` | Create a new branch from `<base>` and switch to it                           |
| `git switch <name>`           | Switch to an existing branch                                                 |
| `git rebase origin/main`      | Replay current branch's commits on top of `origin/main`                      |
| `git rebase -i HEAD~N`        | Interactively edit the last N commits                                        |
| `git push -u origin HEAD`     | Push current branch and set upstream tracking                                |
| `git push --force-with-lease` | Force-push safely (fails if remote has unexpected new commits)               |
| `git cherry-pick <hash>`      | Apply a specific commit onto the current branch                              |
| `git stash` / `git stash pop` | Temporarily save/restore uncommitted changes                                 |
| `git branch -d <name>`        | Delete a fully-merged local branch                                           |
| `git branch -D <name>`        | Force-delete a local branch (even unmerged)                                  |
| `git log --oneline`           | Show compact one-line commit log                                             |
| `git reflog`                  | Show recent HEAD movements (useful for recovery)                             |
| `git restore --staged <file>` | Unstage a file without discarding changes                                    |
| `git restore <file>`          | Discard uncommitted changes to a file                                        |
| `git reset --soft HEAD~1`     | Undo last commit, keep changes staged                                        |
| `git reset --hard HEAD~1`     | Undo last commit and discard all changes                                     |
| `git commit --amend`          | Modify the last commit (message or content)                                  |
| `git diff main..branch`       | Show what changed between main and branch                                    |
| `git rev-list --count A..B`   | Count commits reachable from B but not A                                     |

---

## Daily Workflow Cheatsheet

A condensed reference for the most common daily tasks:

### Starting Your Day

```bash
task doctor:git:refresh            # fetch, prune stale refs, sync tags
git switch my-branch              # switch to your working branch
git rebase origin/main            # get any overnight changes from main
git push --force-with-lease       # update remote if rebase applied
```

### During Development

```bash
git add -p                        # interactively stage hunks (review each change)
git commit -m "feat: add widget"  # commit with conventional message
git push                          # push to remote (upstream already set)
```

### Before Opening a PR

```bash
git fetch origin                  # ensure main is current
git rebase origin/main            # make sure you're on latest main
git rebase -i origin/main         # clean up commit history (squash fixups)
git push --force-with-lease       # update remote branch
# Open PR on GitHub
```

### After PR is Merged

```bash
git switch main                   # go back to main
git pull --ff-only                # fast-forward to latest
git branch -d my-branch           # delete the merged branch locally
task doctor:git:refresh            # fetch, prune stale refs, sync tags
# or: git fetch --prune
```

---

## Debugging Branch Issues

### "My branch has extra commits I didn't make"

This usually happens when you accidentally merged `main` instead of
rebasing, or you pulled without `--rebase`. Check your history:

```bash
git log --oneline --graph -20     # visualize recent history
```

If you see merge commits that shouldn't be there:

```bash
git rebase origin/main            # rebase should clean it up
# If that gets messy:
git reflog                        # find the commit before the problem
git reset --hard HEAD@{n}         # go back to known-good state
git rebase origin/main            # try again cleanly
```

### "My PR shows way more changes than I expected"

Your branch may have diverged from `main`. Check how many commits behind
you are:

```bash
git rev-list --count HEAD..origin/main
                                  # commits on main that you don't have
```

If the count is high, rebase:

```bash
git fetch origin
git rebase origin/main
git push --force-with-lease
```

### "CI passes locally but fails on the PR"

Your local `main` may be stale. Always compare against `origin/main`,
not your local `main`:

```bash
git fetch origin                  # update remote refs
git rebase origin/main            # use origin, not local main
# Re-run tests locally to verify
```

### "I'm on the wrong branch"

```bash
# If you haven't committed yet:
git stash                         # save work
git switch correct-branch         # switch to the right branch
git stash pop                     # restore work there

# If you already committed to the wrong branch:
git log --oneline -3              # note the commit hash(es)
git switch correct-branch         # switch to where it should go
git cherry-pick <hash>            # bring the commit over
git switch wrong-branch           # go back
git reset --hard HEAD~1           # remove the commit from wrong branch
```

### "I need to see what changed between two branches"

```bash
git diff main..my-branch          # full diff
git diff --stat main..my-branch   # file-level summary
git diff --name-only main..my-branch
                                  # just file names
git log --oneline main..my-branch # commits on my-branch not on main
```

---

## Glossary

Quick definitions of Git terms used throughout this guide:

| Term                     | Definition                                                                                                                 |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------- |
| **HEAD**                 | A pointer to the current commit your working directory is based on. Usually points to a branch name.                       |
| **origin**               | The default name for the remote repository (on GitHub). Your local repo fetches from and pushes to `origin`.               |
| **upstream**             | The remote branch your local branch tracks. Set with `git push -u` or `push.autoSetupRemote`.                              |
| **tracking branch**      | A local branch configured to follow a remote branch (e.g., `main` tracks `origin/main`).                                   |
| **remote-tracking ref**  | A read-only local reference to a remote branch (e.g., `origin/main`). Updated by `git fetch`.                              |
| **fast-forward**         | A merge where the target branch pointer simply moves forward — no merge commit needed. Happens when there's no divergence. |
| **rebase**               | Replaying your commits on top of another branch. Rewrites commit SHAs but produces a clean linear history.                 |
| **merge commit**         | A commit with two parents that joins two branches. This project avoids them (uses rebase+merge).                           |
| **force-push**           | Overwriting the remote branch with your local version. Use `--force-with-lease` for safety.                                |
| **detached HEAD**        | When HEAD points to a commit directly (not a branch). Usually unintentional — create a branch to save work.                |
| **merge-base**           | The most recent common ancestor commit between two branches. Where your branch diverged from `main`.                       |
| **reflog**               | A local log of every position HEAD has pointed to. Your safety net for recovering from mistakes.                           |
| **stash**                | A temporary storage area for uncommitted changes. Like a clipboard for your working directory.                             |
| **cherry-pick**          | Applying a specific commit from one branch onto another. Creates a new commit with a new SHA.                              |
| **interactive rebase**   | A rebase where you choose what to do with each commit (keep, squash, reword, drop, reorder).                               |
| **feature flag**         | A conditional check that enables/disables a feature at runtime, allowing incomplete code to merge to `main` safely.        |
| **diverged**             | When two branches have commits the other doesn't. Normal for feature branches vs `main`.                                   |
| **[gone]**               | Git's label for a tracking branch whose remote counterpart has been deleted (usually after PR merge).                      |
| **SHA / hash**           | The 40-character (or abbreviated 7-char) identifier for a commit. Globally unique.                                         |
| **working tree**         | The actual files on disk in your repo. Distinct from the index (staging area) and committed history.                       |
| **index / staging area** | The "prep area" between your working tree and the next commit. Files go here via `git add`.                                |

---

## Post-Merge Cleanup

After a PR is merged, clean up stale local branches:

```bash
git fetch --prune                 # update remote refs and remove stale tracking branches

# Delete local branches whose remote tracking ref is gone (merged via PR)
git branch -vv | grep ': gone]' | awk '{print $1}' | xargs git branch -d
# -vv: show tracking info | grep: find '[gone]' branches | xargs: pass to delete

# Or delete a specific branch manually:
git branch -d feature/my-feature  # -d only works if the branch is fully merged
```

The git doctor script flags stale branches (>30 days since last commit)
and branches whose remote tracking ref is `[gone]`.

For a full cleanup (delete stale branches and run `git gc`):

```bash
task doctor:git:cleanup           # delete stale branches, gc
```

---

## See Also

- [Releasing](../releasing.md) — Release process, conventional commits, version bumps
- [Pull Requests](pull-requests.md) — PR creation and review guidelines
- [Workflows](../workflows.md) — CI/CD workflow reference
- [Command Workflows](command-workflows.md) — How commands flow through the tooling layers
- [ADR 022 — Rebase+merge strategy](../adr/022-rebase-merge-strategy.md)
- [ADR 023 — Branch protection rules](../adr/023-branch-protection-rules.md)
- [Git Doctor](../../scripts/README.md) — Branch health checks and diagnostics
- [Command Reference](../reference/commands.md) — Auto-generated task & script reference
