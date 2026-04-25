# ADR 022: Rebase and Merge Strategy for Pull Requests

## Status

Accepted

## Context

When merging pull requests into `main`, GitHub offers three strategies. The choice affects commit history, CHANGELOG granularity, traceability, and developer workflow.

### Strategies Compared

| Strategy                | Commits on main                     | History shape      | Original SHAs       | Merge event visible                 |
| ----------------------- | ----------------------------------- | ------------------ | ------------------- | ----------------------------------- |
| **Merge commit**        | All branch commits + 1 merge commit | Non-linear (graph) | Preserved           | Yes (merge commit with two parents) |
| **Squash and merge**    | 1 commit (PR title)                 | Linear             | Lost (all squashed) | No (single commit)                  |
| **Rebase and merge**    | All branch commits (replayed)       | Linear             | Changed (re-hashed) | No (linear replay)                  |
| **Direct push** (no PR) | Commits pushed directly             | Linear             | Preserved           | N/A (no PR)                         |

### What We Optimized For

1. **Detailed audit trail** — ability to see exactly what happened, step by step
2. **Linear history** — clean `git log` without merge commit noise
3. **Fine-grained CHANGELOG** — each meaningful commit becomes its own entry
4. **Bisectability** — `git bisect` works well with linear, atomic commits
5. **Traceability** — individual commits reference PRs and issues

### Concerns and Mitigations

#### Concern: Losing the merge event and original SHAs

With rebase+merge, the original branch commit SHAs change (rebased onto tip of main), and there is no merge commit marking "this is where PR #42 was integrated."

**Mitigation — two-layer record keeping:**

| Layer                               | Purpose                               | What it captures                                             |
| ----------------------------------- | ------------------------------------- | ------------------------------------------------------------ |
| **PR** (integration record)         | Review context, discussion, approvals | WHY the change was made, design decisions, reviewer feedback |
| **Commits** (technical audit trail) | Exact code changes, step by step      | WHAT changed and in what order                               |

The PR is preserved in GitHub's database and remains navigable. Commits reference the PR via `(#42)` in their message. GitHub's UI also links rebased commits back to the PR they came from.

#### Concern: Noisy CHANGELOG from iterative commits

If a developer writes 15 `fix:` commits that are really fixing their own mistakes within the PR, the CHANGELOG gets 15 entries.

**Mitigations:**

1. **Convention:** Use conventional prefixes (`feat:`, `fix:`) only for meaningful, reviewable changes. Use non-conventional messages for iteration (e.g., `wip`, `fixup`, `address review feedback`). Non-conventional commits are ignored by release-please.
2. **Edit the Release PR:** release-please creates a Release PR that is editable — clean up redundant entries before merging.
3. **`fixup!` commits:** Git convention for commits that should be squashed during interactive rebase. Optional, not enforced.
4. **Interactive rebase before merge:** Developers can clean up their branch with `git rebase -i` before requesting review. Optional, not required.

#### Concern: Commit message discipline

Every commit that lands on main with a conventional prefix ends up in the CHANGELOG. This requires more discipline than squash-merge (where only the PR title matters).

**Mitigations:**

- **commitizen pre-commit hook** validates commit messages locally at commit time
- **CI commit-lint workflow** validates all commits in a PR before merge
- **`cz commit`** provides an interactive helper for creating well-formed commits
- **.gitmessage.txt** template guides manual commit message writing

### Encoding Linkage in Commit Messages

With rebase+merge, the automatic "Merge pull request #123" entry is gone. To maintain traceability, commits should include PR or issue references:

```
feat: add user authentication (#42)
fix: handle empty username in auth flow (#42)
test: add auth module unit tests (#42)
```

This convention:

- Links each commit back to its integration context (the PR)
- Lets release-please include PR numbers in CHANGELOG entries
- Preserves traceability in `git log` without needing `git log --merges`
- GitHub auto-links `#42` to the PR in commit views

### GitHub Repository Settings

To enforce this strategy at the platform level:

- **Enable:** "Allow rebase merging"
- **Disable:** "Allow merge commits" and "Allow squash merging"
- **Enable:** "Automatically delete head branches" (cleanup after merge)
- **Enable:** "Always suggest updating pull request branches" (keep PRs current)

## Decision

Use **rebase and merge** as the sole merge strategy for pull requests.

Treat the **PR as the integration record** (review, discussion, approvals) and the **commit history as the technical audit trail** (what changed, in what order).

Encode PR/issue references in commit messages (e.g., `feat: add login (#42)`) to maintain traceability in linear history.

## Consequences

### Positive

- Clean, linear `git log` — easy to read and bisect
- Individual commits preserved — can navigate to specific changes within a PR
- Fine-grained CHANGELOG — each `feat:`/`fix:` commit gets its own entry
- Better `git bisect` — each commit is a discrete, testable unit
- Commit authors preserved — individual attribution maintained
- PR context still accessible via GitHub UI and `(#PR)` references

### Negative

- Original SHAs change on rebase — links to branch commits break after merge
- No visual merge point in `git log --graph` — can't see where a PR started/ended
- Requires commit message discipline — more cognitive overhead per commit
- Force-push needed when rebasing to update branch — potential for mistakes
- CI must validate individual commits, not just PR titles
- Developers must learn rebase workflow (`git rebase`, `--force-with-lease`)

## References

- [GitHub: About merge methods](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/about-merge-methods-on-github)
- [Atlassian: Merging vs Rebasing](https://www.atlassian.com/git/tutorials/merging-vs-rebasing)
- [ADR 021 — Automated release pipeline](021-automated-release-pipeline.md)
- [ADR 009 — Conventional commits](009-conventional-commits.md)
