"""Tests for git command analysis rules."""

from __future__ import annotations

from scc_safety_impl.git_rules import (
    analyze_branch,
    analyze_checkout,
    analyze_clean,
    analyze_git,
    analyze_push,
    analyze_reset,
    analyze_restore,
    analyze_stash,
    has_force_flag,
    has_force_refspec,
    has_force_with_lease,
    normalize_git_tokens,
)


class TestNormalizeGitTokens:
    """Tests for normalize_git_tokens function."""

    def test_empty_tokens(self) -> None:
        assert normalize_git_tokens([]) == ("", [])

    def test_not_git_command(self) -> None:
        assert normalize_git_tokens(["python", "script.py"]) == ("", [])

    def test_simple_git_command(self) -> None:
        result = normalize_git_tokens(["git", "push", "origin"])
        assert result == ("push", ["origin"])

    def test_full_path_git(self) -> None:
        result = normalize_git_tokens(["/usr/bin/git", "push"])
        assert result == ("push", [])

    def test_git_with_c_dir_flag(self) -> None:
        result = normalize_git_tokens(["git", "-C", "/path", "push", "origin"])
        assert result == ("push", ["origin"])

    def test_git_with_c_flag(self) -> None:
        result = normalize_git_tokens(["git", "-c", "user.name=foo", "push"])
        assert result == ("push", [])

    def test_git_with_git_dir(self) -> None:
        result = normalize_git_tokens(["git", "--git-dir=/path/.git", "status"])
        assert result == ("status", [])

    def test_git_with_work_tree(self) -> None:
        result = normalize_git_tokens(["git", "--work-tree=/path", "diff"])
        assert result == ("diff", [])

    def test_git_with_multiple_global_options(self) -> None:
        result = normalize_git_tokens(["git", "-C", "/path", "--git-dir=.git", "push", "-f"])
        assert result == ("push", ["-f"])


class TestHasForceFlag:
    """Tests for has_force_flag function."""

    def test_empty_args(self) -> None:
        assert has_force_flag([]) is False

    def test_no_force(self) -> None:
        assert has_force_flag(["origin", "main"]) is False

    def test_short_force(self) -> None:
        assert has_force_flag(["-f"]) is True

    def test_long_force(self) -> None:
        assert has_force_flag(["--force"]) is True

    def test_combined_flags_with_f(self) -> None:
        assert has_force_flag(["-xfd"]) is True
        assert has_force_flag(["-fd"]) is True

    def test_long_flag_no_force(self) -> None:
        assert has_force_flag(["--follow"]) is False

    def test_force_in_middle(self) -> None:
        assert has_force_flag(["origin", "-f", "main"]) is True


class TestHasForceRefspec:
    """Tests for has_force_refspec function."""

    def test_empty_args(self) -> None:
        assert has_force_refspec([]) is False

    def test_no_plus(self) -> None:
        assert has_force_refspec(["origin", "main"]) is False

    def test_plus_at_start(self) -> None:
        assert has_force_refspec(["+main"]) is True
        assert has_force_refspec(["origin", "+main"]) is True

    def test_plus_in_refspec(self) -> None:
        assert has_force_refspec(["+main:main"]) is True

    def test_colon_plus_pattern(self) -> None:
        assert has_force_refspec(["HEAD:+main"]) is True

    def test_double_plus_not_force(self) -> None:
        # ++ is not a force pattern
        assert has_force_refspec(["++something"]) is False

    def test_flags_skipped(self) -> None:
        assert has_force_refspec(["-u", "origin", "+main"]) is True


class TestHasForceWithLease:
    """Tests for has_force_with_lease function."""

    def test_empty_args(self) -> None:
        assert has_force_with_lease([]) is False

    def test_no_force_with_lease(self) -> None:
        assert has_force_with_lease(["--force"]) is False

    def test_force_with_lease(self) -> None:
        assert has_force_with_lease(["--force-with-lease"]) is True

    def test_force_with_lease_value(self) -> None:
        assert has_force_with_lease(["--force-with-lease=main"]) is True


class TestAnalyzePush:
    """Tests for analyze_push function."""

    def test_normal_push(self) -> None:
        assert analyze_push(["origin", "main"]) is None

    def test_force_flag(self) -> None:
        assert analyze_push(["--force"]) is not None
        assert analyze_push(["-f"]) is not None

    def test_force_refspec(self) -> None:
        assert analyze_push(["+main"]) is not None
        assert analyze_push(["origin", "+main:main"]) is not None

    def test_force_with_lease_allowed(self) -> None:
        assert analyze_push(["--force-with-lease"]) is None
        assert analyze_push(["--force-with-lease", "origin", "main"]) is None

    def test_combined_flags(self) -> None:
        assert analyze_push(["-fu"]) is not None


class TestAnalyzeReset:
    """Tests for analyze_reset function."""

    def test_soft_reset(self) -> None:
        assert analyze_reset(["--soft", "HEAD~1"]) is None

    def test_mixed_reset(self) -> None:
        assert analyze_reset(["--mixed", "HEAD~1"]) is None
        assert analyze_reset(["HEAD~1"]) is None  # Default is mixed

    def test_hard_reset(self) -> None:
        assert analyze_reset(["--hard"]) is not None
        assert analyze_reset(["--hard", "HEAD~1"]) is not None


class TestAnalyzeBranch:
    """Tests for analyze_branch function."""

    def test_list_branches(self) -> None:
        assert analyze_branch([]) is None
        assert analyze_branch(["-a"]) is None

    def test_safe_delete(self) -> None:
        assert analyze_branch(["-d", "feature"]) is None

    def test_force_delete_uppercase_d(self) -> None:
        assert analyze_branch(["-D", "feature"]) is not None

    def test_delete_with_force(self) -> None:
        assert analyze_branch(["--delete", "--force", "feature"]) is not None


class TestAnalyzeStash:
    """Tests for analyze_stash function."""

    def test_stash_push(self) -> None:
        assert analyze_stash([]) is None
        assert analyze_stash(["push"]) is None

    def test_stash_pop(self) -> None:
        assert analyze_stash(["pop"]) is None

    def test_stash_apply(self) -> None:
        assert analyze_stash(["apply"]) is None

    def test_stash_list(self) -> None:
        assert analyze_stash(["list"]) is None

    def test_stash_drop(self) -> None:
        assert analyze_stash(["drop"]) is not None
        assert analyze_stash(["drop", "stash@{0}"]) is not None

    def test_stash_clear(self) -> None:
        assert analyze_stash(["clear"]) is not None


class TestAnalyzeClean:
    """Tests for analyze_clean function."""

    def test_dry_run(self) -> None:
        assert analyze_clean(["-n"]) is None
        assert analyze_clean(["--dry-run"]) is None
        assert analyze_clean(["-n", "-f"]) is None  # Dry run takes precedence

    def test_force_clean(self) -> None:
        assert analyze_clean(["-f"]) is not None
        assert analyze_clean(["--force"]) is not None

    def test_force_directory(self) -> None:
        assert analyze_clean(["-fd"]) is not None
        assert analyze_clean(["-df"]) is not None

    def test_force_ignored(self) -> None:
        assert analyze_clean(["-xfd"]) is not None


class TestAnalyzeCheckout:
    """Tests for analyze_checkout function."""

    def test_switch_branch(self) -> None:
        assert analyze_checkout(["main"]) is None
        assert analyze_checkout(["-b", "feature"]) is None

    def test_checkout_path(self) -> None:
        assert analyze_checkout(["--", "file.py"]) is not None

    def test_checkout_head_path(self) -> None:
        assert analyze_checkout(["HEAD", "--", "file.py"]) is not None

    def test_checkout_branch_path(self) -> None:
        assert analyze_checkout(["main", "--", "file.py"]) is not None

    def test_separator_without_path(self) -> None:
        # Just -- without files after it (edge case)
        assert analyze_checkout(["--"]) is None


class TestAnalyzeRestore:
    """Tests for analyze_restore function."""

    def test_empty_args(self) -> None:
        assert analyze_restore([]) is None

    def test_staged_only(self) -> None:
        assert analyze_restore(["--staged", "file.py"]) is None
        assert analyze_restore(["-S", "file.py"]) is None

    def test_worktree_restore(self) -> None:
        assert analyze_restore(["file.py"]) is not None
        assert analyze_restore(["--worktree", "file.py"]) is not None
        assert analyze_restore(["-W", "file.py"]) is not None

    def test_both_staged_and_worktree(self) -> None:
        assert analyze_restore(["--staged", "--worktree", "file.py"]) is not None
        assert analyze_restore(["-S", "-W", "file.py"]) is not None


class TestAnalyzeGit:
    """Integration tests for analyze_git function."""

    def test_non_git_command(self) -> None:
        assert analyze_git(["python", "script.py"]) is None

    def test_git_without_subcommand(self) -> None:
        assert analyze_git(["git"]) is None

    def test_force_push(self) -> None:
        assert analyze_git(["git", "push", "--force"]) is not None
        assert analyze_git(["git", "push", "-f"]) is not None
        assert analyze_git(["git", "push", "origin", "+main"]) is not None

    def test_force_with_lease(self) -> None:
        assert analyze_git(["git", "push", "--force-with-lease"]) is None

    def test_reset_hard(self) -> None:
        assert analyze_git(["git", "reset", "--hard"]) is not None

    def test_reset_soft(self) -> None:
        assert analyze_git(["git", "reset", "--soft"]) is None

    def test_branch_force_delete(self) -> None:
        assert analyze_git(["git", "branch", "-D", "feature"]) is not None

    def test_branch_safe_delete(self) -> None:
        assert analyze_git(["git", "branch", "-d", "feature"]) is None

    def test_stash_drop(self) -> None:
        assert analyze_git(["git", "stash", "drop"]) is not None

    def test_stash_pop(self) -> None:
        assert analyze_git(["git", "stash", "pop"]) is None

    def test_clean_force(self) -> None:
        assert analyze_git(["git", "clean", "-f"]) is not None
        assert analyze_git(["git", "clean", "-xfd"]) is not None

    def test_clean_dry_run(self) -> None:
        assert analyze_git(["git", "clean", "-n"]) is None

    def test_checkout_path(self) -> None:
        assert analyze_git(["git", "checkout", "--", "file.py"]) is not None

    def test_checkout_branch(self) -> None:
        assert analyze_git(["git", "checkout", "main"]) is None

    def test_restore_worktree(self) -> None:
        assert analyze_git(["git", "restore", "file.py"]) is not None

    def test_restore_staged(self) -> None:
        assert analyze_git(["git", "restore", "--staged", "file.py"]) is None

    def test_full_path_git(self) -> None:
        assert analyze_git(["/usr/bin/git", "push", "--force"]) is not None

    def test_git_with_global_options(self) -> None:
        assert analyze_git(["git", "-C", "/path", "push", "-f"]) is not None

    def test_unknown_subcommand(self) -> None:
        assert analyze_git(["git", "status"]) is None
        assert analyze_git(["git", "log"]) is None
        assert analyze_git(["git", "diff"]) is None
