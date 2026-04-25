"""Unit tests for scripts/git_doctor.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

# scripts/ is not an installed package — add it to sys.path so we can import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from git_doctor import (
    HEALTH_CHECKS,
    HELPFUL_COMMANDS,
    SCRIPT_VERSION,
    _parse_shortstat,
    _run_git,
    check_clean_workdir,
    check_conventional_commits,
    check_fetch_recent,
    check_git_installed,
    check_gitignore_exists,
    check_gitmessage_template,
    check_inside_repo,
    check_merge_base_freshness,
    check_no_conflicts,
    check_no_detached_head,
    check_no_large_files_staged,
    check_upstream_configured,
    check_user_identity,
    get_all_remotes,
    get_branch_commit_count,
    get_commit_count,
    get_commit_frequency,
    get_contributors_count,
    get_current_branch,
    get_default_branch,
    get_file_change_summary,
    get_git_config_summary,
    get_git_config_value,
    get_local_branches,
    get_modified_files,
    get_recent_commits,
    get_remote_branches,
    get_remote_url,
    get_repo_age,
    get_stale_branches,
    get_stash_count,
    get_tags,
    get_unmerged_branches,
    get_upstream_status,
    get_working_tree_status,
    main,
    run,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_run_git(returncode: int, stdout: str, stderr: str = ""):
    """Return a patch that replaces _run_git with a fixed return value."""
    return patch("git_doctor._run_git", return_value=(returncode, stdout, stderr))


# ---------------------------------------------------------------------------
# SCRIPT_VERSION
# ---------------------------------------------------------------------------


class TestScriptVersion:
    """Validate version constant is well-formed."""

    def test_version_is_string(self):
        assert isinstance(SCRIPT_VERSION, str)

    def test_version_format(self):
        parts = SCRIPT_VERSION.split(".")
        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)


# ---------------------------------------------------------------------------
# _run_git
# ---------------------------------------------------------------------------


class TestRunGit:
    """Tests for the _run_git helper."""

    def test_returns_tuple_of_three(self):
        code, out, err = _run_git(["--version"])
        assert isinstance(code, int)
        assert isinstance(out, str)
        assert isinstance(err, str)

    def test_git_not_found(self):
        with patch("git_doctor._GIT", None):
            code, _out, err = _run_git(["status"])
            assert code == 1
            assert "git not found" in err

    def test_timeout_handled(self):
        import subprocess

        with (
            patch("git_doctor._GIT", "/usr/bin/git"),
            patch(
                "git_doctor.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="git", timeout=15),
            ),
        ):
            code, _out, err = _run_git(["log"])
            assert code == 1
            assert "timed out" in err

    def test_os_error_handled(self):
        with (
            patch("git_doctor._GIT", "/usr/bin/git"),
            patch(
                "git_doctor.subprocess.run",
                side_effect=OSError("permission denied"),
            ),
        ):
            code, _out, err = _run_git(["status"])
            assert code == 1
            assert "permission denied" in err


# ---------------------------------------------------------------------------
# _parse_shortstat
# ---------------------------------------------------------------------------


class TestParseShortstat:
    """Tests for parsing git --shortstat output."""

    def test_typical_output(self):
        text = " 3 files changed, 42 insertions(+), 10 deletions(-)"
        result = _parse_shortstat(text)
        assert result == {"files_changed": 3, "insertions": 42, "deletions": 10}

    def test_insertions_only(self):
        text = " 1 file changed, 5 insertions(+)"
        result = _parse_shortstat(text)
        assert result["files_changed"] == 1
        assert result["insertions"] == 5
        assert result["deletions"] == 0

    def test_deletions_only(self):
        text = " 2 files changed, 8 deletions(-)"
        result = _parse_shortstat(text)
        assert result["deletions"] == 8
        assert result["insertions"] == 0

    def test_empty_input(self):
        result = _parse_shortstat("")
        assert result == {"files_changed": 0, "insertions": 0, "deletions": 0}

    def test_no_changed_keyword(self):
        result = _parse_shortstat("nothing to report")
        assert result == {"files_changed": 0, "insertions": 0, "deletions": 0}


# ---------------------------------------------------------------------------
# get_current_branch
# ---------------------------------------------------------------------------


class TestGetCurrentBranch:
    """Tests for get_current_branch()."""

    def test_returns_branch_name(self):
        with _mock_run_git(0, "main"):
            assert get_current_branch() == "main"

    def test_detached_head_returns_sha(self):
        with patch(
            "git_doctor._run_git",
            side_effect=[
                (1, "", ""),  # branch --show-current fails
                (0, "abc1234", ""),  # rev-parse --short HEAD
            ],
        ):
            result = get_current_branch()
            assert "detached HEAD" in result
            assert "abc1234" in result

    def test_unknown_fallback(self):
        with patch(
            "git_doctor._run_git",
            side_effect=[
                (1, "", ""),
                (1, "", ""),
            ],
        ):
            assert get_current_branch() == "(unknown)"


# ---------------------------------------------------------------------------
# get_default_branch
# ---------------------------------------------------------------------------


class TestGetDefaultBranch:
    """Tests for get_default_branch()."""

    def test_returns_main(self):
        with _mock_run_git(0, "refs/remotes/origin/main"):
            assert get_default_branch() == "main"

    def test_returns_master(self):
        with _mock_run_git(0, "refs/remotes/origin/master"):
            assert get_default_branch() == "master"

    def test_unknown_when_no_remote(self):
        with _mock_run_git(1, ""):
            assert get_default_branch() == "(unknown)"


# ---------------------------------------------------------------------------
# get_remote_url
# ---------------------------------------------------------------------------


class TestGetRemoteUrl:
    """Tests for get_remote_url()."""

    def test_returns_url(self):
        with _mock_run_git(0, "https://github.com/user/repo.git"):
            assert get_remote_url() == "https://github.com/user/repo.git"

    def test_no_remote(self):
        with _mock_run_git(1, ""):
            assert get_remote_url() == "(no remote)"


# ---------------------------------------------------------------------------
# get_all_remotes
# ---------------------------------------------------------------------------


class TestGetAllRemotes:
    """Tests for get_all_remotes()."""

    def test_parses_remotes(self):
        output = (
            "origin\thttps://github.com/user/repo.git (fetch)\n"
            "origin\thttps://github.com/user/repo.git (push)"
        )
        with _mock_run_git(0, output):
            remotes = get_all_remotes()
            assert len(remotes) == 1
            assert remotes[0]["name"] == "origin"

    def test_empty_on_failure(self):
        with _mock_run_git(1, ""):
            assert get_all_remotes() == []


# ---------------------------------------------------------------------------
# get_local_branches
# ---------------------------------------------------------------------------


class TestGetLocalBranches:
    """Tests for get_local_branches()."""

    def test_parses_branch_info(self):
        output = "main\torigin/main\t[ahead 2]\tabc123\t3 days ago"
        with _mock_run_git(0, output):
            branches = get_local_branches()
            assert len(branches) == 1
            assert branches[0]["name"] == "main"
            assert branches[0]["tracking"] == "origin/main"
            assert branches[0]["sha"] == "abc123"

    def test_empty_on_failure(self):
        with _mock_run_git(1, ""):
            assert get_local_branches() == []


# ---------------------------------------------------------------------------
# get_remote_branches
# ---------------------------------------------------------------------------


class TestGetRemoteBranches:
    """Tests for get_remote_branches()."""

    def test_filters_head(self):
        output = "origin/main\norigin/HEAD -> origin/main\norigin/dev"
        with _mock_run_git(0, output):
            branches = get_remote_branches()
            assert "origin/main" in branches
            assert "origin/dev" in branches
            # HEAD line should be filtered out
            assert all("HEAD" not in b for b in branches)

    def test_empty_on_failure(self):
        with _mock_run_git(1, ""):
            assert get_remote_branches() == []


# ---------------------------------------------------------------------------
# get_recent_commits
# ---------------------------------------------------------------------------


class TestGetRecentCommits:
    """Tests for get_recent_commits()."""

    def test_parses_commit_log(self):
        output = "abc1234\tfeat: add feature\tAuthor\t2 days ago"
        with _mock_run_git(0, output):
            commits = get_recent_commits(1)
            assert len(commits) == 1
            assert commits[0]["sha"] == "abc1234"
            assert commits[0]["message"] == "feat: add feature"
            assert commits[0]["author"] == "Author"

    def test_empty_on_failure(self):
        with _mock_run_git(1, ""):
            assert get_recent_commits(5) == []


# ---------------------------------------------------------------------------
# get_stash_count
# ---------------------------------------------------------------------------


class TestGetStashCount:
    """Tests for get_stash_count()."""

    def test_counts_stashes(self):
        output = "stash@{0}: WIP on main\nstash@{1}: WIP on dev"
        with _mock_run_git(0, output):
            assert get_stash_count() == 2

    def test_zero_when_empty(self):
        with _mock_run_git(0, ""):
            assert get_stash_count() == 0


# ---------------------------------------------------------------------------
# get_tags
# ---------------------------------------------------------------------------


class TestGetTags:
    """Tests for get_tags()."""

    def test_returns_tags(self):
        with _mock_run_git(0, "v1.0.0\nv0.9.0"):
            tags = get_tags(5)
            assert tags == ["v1.0.0", "v0.9.0"]

    def test_empty_on_failure(self):
        with _mock_run_git(1, ""):
            assert get_tags(5) == []


# ---------------------------------------------------------------------------
# get_commit_count
# ---------------------------------------------------------------------------


class TestGetCommitCount:
    """Tests for get_commit_count()."""

    def test_returns_count(self):
        with _mock_run_git(0, "42"):
            assert get_commit_count() == 42

    def test_zero_on_failure(self):
        with _mock_run_git(1, ""):
            assert get_commit_count() == 0

    def test_zero_on_invalid(self):
        with _mock_run_git(0, "not-a-number"):
            assert get_commit_count() == 0


# ---------------------------------------------------------------------------
# get_repo_age
# ---------------------------------------------------------------------------


class TestGetRepoAge:
    """Tests for get_repo_age()."""

    def test_returns_relative_date(self):
        with patch(
            "git_doctor._run_git",
            side_effect=[
                (0, "abc123", ""),  # rev-list --max-parents=0
                (0, "8 weeks ago", ""),  # log -1 --format=%ar
            ],
        ):
            assert get_repo_age() == "8 weeks ago"

    def test_unknown_on_failure(self):
        with _mock_run_git(1, ""):
            assert get_repo_age() == "unknown"


# ---------------------------------------------------------------------------
# get_contributors_count
# ---------------------------------------------------------------------------


class TestGetContributorsCount:
    """Tests for get_contributors_count()."""

    def test_counts_unique_authors(self):
        output = "    10\tAlice\n     5\tBob\n     3\tCharlie"
        with _mock_run_git(0, output):
            assert get_contributors_count() == 3

    def test_zero_on_failure(self):
        with _mock_run_git(1, ""):
            assert get_contributors_count() == 0


# ---------------------------------------------------------------------------
# get_commit_frequency
# ---------------------------------------------------------------------------


class TestGetCommitFrequency:
    """Tests for get_commit_frequency()."""

    def test_counts_per_day(self):
        output = "2026-03-10\n2026-03-10\n2026-03-09"
        with _mock_run_git(0, output):
            freq = get_commit_frequency()
            assert freq["2026-03-10"] == 2
            assert freq["2026-03-09"] == 1

    def test_empty_on_failure(self):
        with _mock_run_git(1, ""):
            assert get_commit_frequency() == {}


# ---------------------------------------------------------------------------
# get_file_change_summary
# ---------------------------------------------------------------------------


class TestGetFileChangeSummary:
    """Tests for get_file_change_summary()."""

    def test_parses_shortstat(self):
        output = " 5 files changed, 100 insertions(+), 20 deletions(-)"
        with _mock_run_git(0, output):
            result = get_file_change_summary()
            assert result["files_changed"] == 5
            assert result["insertions"] == 100

    def test_empty_on_failure(self):
        with _mock_run_git(1, ""):
            assert get_file_change_summary() == {}


# ---------------------------------------------------------------------------
# get_working_tree_status
# ---------------------------------------------------------------------------


class TestGetWorkingTreeStatus:
    """Tests for get_working_tree_status()."""

    def test_counts_statuses(self):
        output = " M file1.py\n?? file2.py\nA  file3.py\nUU conflict.py"
        with _mock_run_git(0, output):
            status = get_working_tree_status()
            assert status["modified"] == 1
            assert status["untracked"] == 1
            assert status["staged"] == 1
            assert status["conflicted"] == 1

    def test_empty_counts_on_clean(self):
        with _mock_run_git(0, ""):
            status = get_working_tree_status()
            assert sum(status.values()) == 0


# ---------------------------------------------------------------------------
# get_upstream_status
# ---------------------------------------------------------------------------


class TestGetUpstreamStatus:
    """Tests for get_upstream_status()."""

    def test_up_to_date(self):
        def fake_run_git(args, *, timeout=15):
            if "--abbrev-ref" in args and "--symbolic-full-name" in args:
                return (0, "origin/main", "")
            return (0, "0\t0", "")

        with patch("git_doctor._run_git", side_effect=fake_run_git):
            result = get_upstream_status()
            assert "up to date" in result
            assert "origin/main" in result

    def test_ahead(self):
        def fake_run_git(args, *, timeout=15):
            if "--abbrev-ref" in args and "--symbolic-full-name" in args:
                return (0, "origin/main", "")
            return (0, "0\t5", "")

        with patch("git_doctor._run_git", side_effect=fake_run_git):
            assert "5 ahead" in get_upstream_status()

    def test_behind(self):
        def fake_run_git(args, *, timeout=15):
            if "--abbrev-ref" in args and "--symbolic-full-name" in args:
                return (0, "origin/main", "")
            return (0, "3\t0", "")

        with patch("git_doctor._run_git", side_effect=fake_run_git):
            assert "3 behind" in get_upstream_status()

    def test_no_upstream(self):
        with _mock_run_git(1, ""):
            assert get_upstream_status() == "no upstream"


# ---------------------------------------------------------------------------
# get_git_config_value
# ---------------------------------------------------------------------------


class TestGetGitConfigValue:
    """Tests for get_git_config_value()."""

    def test_returns_value(self):
        with _mock_run_git(0, "true"):
            assert get_git_config_value("core.autocrlf") == "true"

    def test_empty_on_unset(self):
        with _mock_run_git(1, ""):
            assert get_git_config_value("nonexistent.key") == ""


# ---------------------------------------------------------------------------
# get_git_config_summary
# ---------------------------------------------------------------------------


class TestGetGitConfigSummary:
    """Tests for get_git_config_summary()."""

    def test_returns_dict(self):
        def fake_run_git(args, *, timeout=15):
            if "core.autocrlf" in args:
                return (0, "false", "")
            if "pull.rebase" in args:
                return (0, "true", "")
            return (1, "", "")

        with patch("git_doctor._run_git", side_effect=fake_run_git):
            summary = get_git_config_summary()
            assert isinstance(summary, dict)
            assert summary.get("core.autocrlf") == "false"


# ---------------------------------------------------------------------------
# get_branch_commit_count
# ---------------------------------------------------------------------------


class TestGetBranchCommitCount:
    """Tests for get_branch_commit_count()."""

    def test_returns_count(self):
        with _mock_run_git(0, "100"):
            assert get_branch_commit_count("main") == 100

    def test_zero_on_failure(self):
        with _mock_run_git(1, ""):
            assert get_branch_commit_count("nonexistent") == 0


# ---------------------------------------------------------------------------
# get_unmerged_branches
# ---------------------------------------------------------------------------


class TestGetUnmergedBranches:
    """Tests for get_unmerged_branches()."""

    def test_annotates_gone_branches(self):
        def fake_run_git(args, *, timeout=15):
            if "symbolic-ref" in args:
                return (0, "refs/remotes/origin/main", "")
            if "--no-merged" in args:
                return (0, "feature-a\nfeature-b", "")
            if "-vv" in args:
                return (
                    0,
                    "feature-a\t[gone]\nfeature-b\t",
                    "",
                )
            return (1, "", "")

        with patch("git_doctor._run_git", side_effect=fake_run_git):
            result = get_unmerged_branches()
            # feature-a has [gone] tracking → skipped (assumed merged via PR)
            # feature-b has no [gone] → included
            assert len(result) == 1
            assert result[0]["name"] == "feature-b"

    def test_empty_when_unknown_default(self):
        with _mock_run_git(1, ""):
            assert get_unmerged_branches() == []


# ---------------------------------------------------------------------------
# get_modified_files
# ---------------------------------------------------------------------------


class TestGetModifiedFiles:
    """Tests for get_modified_files()."""

    def test_parses_porcelain(self):
        output = " M file1.py\n?? file2.py"
        with _mock_run_git(0, output):
            files = get_modified_files()
            assert len(files) == 2
            assert files[0]["file"] == "file1.py"
            assert files[1]["status"] == "untracked"

    def test_respects_limit(self):
        output = "\n".join(f" M file{i}.py" for i in range(20))
        with _mock_run_git(0, output):
            files = get_modified_files(limit=5)
            assert len(files) == 5


# ---------------------------------------------------------------------------
# get_stale_branches
# ---------------------------------------------------------------------------


class TestGetStaleBranches:
    """Tests for get_stale_branches()."""

    def test_returns_stale(self):
        import time

        old_ts = str(int(time.time()) - 90 * 86400)  # 90 days ago
        output = f"old-branch\t3 months ago\t{old_ts}"
        with _mock_run_git(0, output):
            stale = get_stale_branches(days=30)
            assert len(stale) == 1
            assert stale[0]["name"] == "old-branch"

    def test_empty_when_all_fresh(self):
        import time

        fresh_ts = str(int(time.time()) - 86400)  # 1 day ago
        output = f"fresh-branch\t1 day ago\t{fresh_ts}"
        with _mock_run_git(0, output):
            stale = get_stale_branches(days=30)
            assert stale == []


# ---------------------------------------------------------------------------
# Health Checks
# ---------------------------------------------------------------------------


class TestCheckGitInstalled:
    """Tests for check_git_installed()."""

    def test_pass_when_installed(self):
        with _mock_run_git(0, "git version 2.43.0"):
            passed, msg = check_git_installed()
            assert passed is True
            assert "git version" in msg

    def test_fail_when_missing(self):
        with patch("git_doctor._GIT", None):
            passed, _msg = check_git_installed()
            assert passed is False


class TestCheckInsideRepo:
    """Tests for check_inside_repo()."""

    def test_pass_inside_repo(self):
        with _mock_run_git(0, "true"):
            passed, _ = check_inside_repo()
            assert passed is True

    def test_fail_outside_repo(self):
        with _mock_run_git(1, ""):
            passed, _ = check_inside_repo()
            assert passed is False


class TestCheckCleanWorkdir:
    """Tests for check_clean_workdir()."""

    def test_pass_when_clean(self):
        with _mock_run_git(0, ""):
            passed, msg = check_clean_workdir()
            assert passed is True
            assert "clean" in msg.lower()

    def test_fail_when_dirty(self):
        with _mock_run_git(0, " M file.py\n?? new.py"):
            passed, msg = check_clean_workdir()
            assert passed is False
            assert "modified" in msg.lower() or "untracked" in msg.lower()


class TestCheckNoConflicts:
    """Tests for check_no_conflicts()."""

    def test_pass_no_conflicts(self):
        with _mock_run_git(0, ""):
            passed, _ = check_no_conflicts()
            assert passed is True

    def test_fail_with_conflicts(self):
        with _mock_run_git(0, "conflict_file.py"):
            passed, msg = check_no_conflicts()
            assert passed is False
            assert "conflict" in msg.lower()


class TestCheckNoDetachedHead:
    """Tests for check_no_detached_head()."""

    def test_pass_on_branch(self):
        with _mock_run_git(0, "refs/heads/main"):
            passed, _ = check_no_detached_head()
            assert passed is True

    def test_fail_detached(self):
        with _mock_run_git(1, ""):
            passed, _ = check_no_detached_head()
            assert passed is False


class TestCheckUpstreamConfigured:
    """Tests for check_upstream_configured()."""

    def test_pass_with_upstream(self):
        with patch(
            "git_doctor._run_git",
            side_effect=[
                (0, "main", ""),  # branch --show-current
                (0, "origin", ""),  # config branch.main.remote
            ],
        ):
            passed, _ = check_upstream_configured()
            assert passed is True

    def test_fail_without_upstream(self):
        with patch(
            "git_doctor._run_git",
            side_effect=[
                (0, "feature", ""),  # branch --show-current
                (1, "", ""),  # config fails
            ],
        ):
            passed, _ = check_upstream_configured()
            assert passed is False


class TestCheckFetchRecent:
    """Tests for check_fetch_recent()."""

    def test_fail_when_never_fetched(self):
        with patch("git_doctor.ROOT", Path("/fake/repo")):
            passed, msg = check_fetch_recent()
            assert passed is False
            assert "never fetched" in msg.lower() or "fetch" in msg.lower()


class TestCheckGitignoreExists:
    """Tests for check_gitignore_exists()."""

    def test_pass_when_present(self, tmp_path):
        (tmp_path / ".gitignore").write_text("*.pyc\n")
        with patch("git_doctor.ROOT", tmp_path):
            passed, _ = check_gitignore_exists()
            assert passed is True

    def test_fail_when_missing(self, tmp_path):
        with patch("git_doctor.ROOT", tmp_path):
            passed, _ = check_gitignore_exists()
            assert passed is False


class TestCheckNoLargeFilesStaged:
    """Tests for check_no_large_files_staged()."""

    def test_pass_nothing_staged(self):
        with _mock_run_git(0, ""):
            passed, _ = check_no_large_files_staged()
            assert passed is True


class TestCheckConventionalCommits:
    """Tests for check_conventional_commits()."""

    def test_pass_all_conventional(self):
        output = "feat: add login\nfix: resolve crash\ndocs: update readme"
        with _mock_run_git(0, output):
            passed, _ = check_conventional_commits()
            assert passed is True

    def test_fail_non_conventional(self):
        output = "feat: add login\nrandom commit message\nfix: resolve crash"
        with _mock_run_git(0, output):
            passed, msg = check_conventional_commits()
            assert passed is False
            assert "non-conventional" in msg

    def test_skips_merge_commits(self):
        output = "Merge branch 'main'\nfeat: add feature"
        with _mock_run_git(0, output):
            passed, _ = check_conventional_commits()
            assert passed is True


class TestCheckGitmessageTemplate:
    """Tests for check_gitmessage_template()."""

    def test_pass_when_no_template_file(self, tmp_path):
        with patch("git_doctor.ROOT", tmp_path):
            passed, _ = check_gitmessage_template()
            assert passed is True

    def test_pass_when_configured(self, tmp_path):
        (tmp_path / ".gitmessage.txt").write_text("template\n")
        with (
            patch("git_doctor.ROOT", tmp_path),
            _mock_run_git(0, ".gitmessage.txt"),
        ):
            passed, _ = check_gitmessage_template()
            assert passed is True


class TestCheckUserIdentity:
    """Tests for check_user_identity()."""

    def test_pass_with_identity(self):
        def fake_run_git(args, *, timeout=15):
            if "user.name" in args:
                return (0, "Test User", "")
            if "user.email" in args:
                return (0, "test@example.com", "")
            return (1, "", "")

        with patch("git_doctor._run_git", side_effect=fake_run_git):
            passed, msg = check_user_identity()
            assert passed is True
            assert "Test User" in msg

    def test_fail_missing_name(self):
        def fake_run_git(args, *, timeout=15):
            if "user.name" in args:
                return (1, "", "")
            if "user.email" in args:
                return (0, "test@example.com", "")
            return (1, "", "")

        with patch("git_doctor._run_git", side_effect=fake_run_git):
            passed, msg = check_user_identity()
            assert passed is False
            assert "user.name" in msg


class TestCheckMergeBaseFreshness:
    """Tests for check_merge_base_freshness()."""

    def test_pass_on_default_branch(self):
        with patch(
            "git_doctor._run_git",
            side_effect=[
                (0, "main", ""),  # get_current_branch
                (0, "refs/remotes/origin/main", ""),  # get_default_branch
            ],
        ):
            passed, _ = check_merge_base_freshness()
            assert passed is True


# ---------------------------------------------------------------------------
# HEALTH_CHECKS & HELPFUL_COMMANDS
# ---------------------------------------------------------------------------


class TestHealthChecks:
    """Validate the HEALTH_CHECKS registry."""

    def test_all_entries_are_callable(self):
        for name, fn in HEALTH_CHECKS:
            assert callable(fn), f"{name} is not callable"

    def test_names_are_unique(self):
        names = [name for name, _ in HEALTH_CHECKS]
        assert len(names) == len(set(names))

    def test_minimum_check_count(self):
        # Ensure we don't accidentally lose checks
        assert len(HEALTH_CHECKS) >= 10


class TestHelpfulCommands:
    """Validate HELPFUL_COMMANDS list."""

    def test_all_have_cmd_and_desc(self):
        for entry in HELPFUL_COMMANDS:
            assert "cmd" in entry
            assert "desc" in entry
            assert entry["cmd"].startswith("git ")


# ---------------------------------------------------------------------------
# run() and main()
# ---------------------------------------------------------------------------


class TestRun:
    """Tests for the run() entry point."""

    def test_json_output_is_valid_json(self, capsys):
        with (
            patch(
                "git_doctor._collect_info",
                return_value={
                    "current_branch": "main",
                    "default_branch": "main",
                    "remote_url": "https://github.com/user/repo",
                    "remotes": [],
                    "remote_branches": [],
                    "upstream_status": "up to date",
                    "local_branches": [],
                    "recent_commits": [],
                    "tags": [],
                    "stash_count": 0,
                    "commit_count": 10,
                    "repo_age": "1 month ago",
                    "contributors": 1,
                    "top_contributors": [],
                    "working_tree": {
                        "staged": 0,
                        "modified": 0,
                        "untracked": 0,
                        "conflicted": 0,
                    },
                    "release_please_branches": [],
                    "user_name": "Test",
                    "user_email": "test@test.com",
                    "branch_activity": [],
                    "working_branch_stats": {
                        "staged": {"files_changed": 0, "insertions": 0, "deletions": 0},
                        "unstaged": {
                            "files_changed": 0,
                            "insertions": 0,
                            "deletions": 0,
                        },
                        "vs_default": {
                            "files_changed": 0,
                            "insertions": 0,
                            "deletions": 0,
                        },
                    },
                    "modified_files": [],
                    "stale_branches": [],
                    "git_config": {},
                    "git_config_scopes": {},
                    "unmerged_branches": [],
                    "last_merge_from_default": {},
                    "branch_divergence": {},
                    "commit_frequency": {},
                    "file_change_summary": {},
                    "branch_characteristics": {},
                },
            ),
            patch("git_doctor._collect_health", return_value=([], 0)),
        ):
            run(output_json=True)
            captured = capsys.readouterr()
            payload = json.loads(captured.out)
            assert "version" in payload
            assert "info" in payload
            assert "health" in payload

    def test_no_color_mode(self, capsys):
        with (
            patch(
                "git_doctor._collect_info",
                return_value={
                    "current_branch": "main",
                    "default_branch": "main",
                    "remote_url": "https://github.com/user/repo",
                    "remotes": [],
                    "remote_branches": [],
                    "upstream_status": "up to date",
                    "local_branches": [],
                    "recent_commits": [],
                    "tags": [],
                    "stash_count": 0,
                    "commit_count": 10,
                    "repo_age": "1 month ago",
                    "contributors": 1,
                    "top_contributors": [],
                    "working_tree": {
                        "staged": 0,
                        "modified": 0,
                        "untracked": 0,
                        "conflicted": 0,
                    },
                    "release_please_branches": [],
                    "user_name": "Test",
                    "user_email": "test@test.com",
                    "branch_activity": [],
                    "working_branch_stats": {
                        "staged": {"files_changed": 0, "insertions": 0, "deletions": 0},
                        "unstaged": {
                            "files_changed": 0,
                            "insertions": 0,
                            "deletions": 0,
                        },
                        "vs_default": {
                            "files_changed": 0,
                            "insertions": 0,
                            "deletions": 0,
                        },
                    },
                    "modified_files": [],
                    "stale_branches": [],
                    "git_config": {},
                    "git_config_scopes": {},
                    "unmerged_branches": [],
                    "last_merge_from_default": {},
                    "branch_divergence": {},
                    "commit_frequency": {},
                    "file_change_summary": {},
                    "branch_characteristics": {},
                },
            ),
            patch("git_doctor._collect_health", return_value=([], 0)),
        ):
            run(color=False)
            captured = capsys.readouterr()
            # No ANSI escape codes in output
            assert "\033[" not in captured.out
            assert "Git Doctor" in captured.out


class TestMain:
    """Tests for main() CLI entry point."""

    def test_returns_int(self):
        with (
            patch("git_doctor.run", return_value=0),
            patch("sys.argv", ["git_doctor.py"]),
        ):
            assert main() == 0

    def test_no_color_flag(self):
        with (
            patch("git_doctor.run", return_value=0) as mock_run,
            patch("sys.argv", ["git_doctor.py", "--no-color"]),
        ):
            main()
            mock_run.assert_called_once_with(color=False, output_json=False)

    def test_json_flag(self):
        with (
            patch("git_doctor.run", return_value=0) as mock_run,
            patch("sys.argv", ["git_doctor.py", "--json"]),
        ):
            main()
            mock_run.assert_called_once_with(color=None, output_json=True)
