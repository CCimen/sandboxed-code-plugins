"""Tests for hook orchestration and E2E flow."""

from __future__ import annotations

from typing import Any

from scc_safety_impl.hook import (
    analyze_command,
    check_command,
    get_exit_code,
    should_block,
)


class TestAnalyzeCommand:
    """Tests for analyze_command function."""

    def test_empty_command(self) -> None:
        assert analyze_command("") is None
        assert analyze_command("   ") is None

    def test_non_git_command(self) -> None:
        assert analyze_command("ls -la") is None
        assert analyze_command("python script.py") is None

    def test_safe_git_commands(self) -> None:
        assert analyze_command("git status") is None
        assert analyze_command("git log") is None
        assert analyze_command("git diff") is None
        assert analyze_command("git push origin main") is None

    def test_force_push_blocked(self) -> None:
        assert analyze_command("git push --force") is not None
        assert analyze_command("git push -f") is not None
        assert analyze_command("git push origin +main") is not None

    def test_force_with_lease_allowed(self) -> None:
        assert analyze_command("git push --force-with-lease") is None

    def test_reset_hard_blocked(self) -> None:
        assert analyze_command("git reset --hard") is not None

    def test_reset_soft_allowed(self) -> None:
        assert analyze_command("git reset --soft HEAD~1") is None

    def test_branch_force_delete_blocked(self) -> None:
        assert analyze_command("git branch -D feature") is not None

    def test_branch_safe_delete_allowed(self) -> None:
        assert analyze_command("git branch -d feature") is None

    def test_stash_drop_blocked(self) -> None:
        assert analyze_command("git stash drop") is not None

    def test_stash_pop_allowed(self) -> None:
        assert analyze_command("git stash pop") is None

    def test_clean_force_blocked(self) -> None:
        assert analyze_command("git clean -f") is not None
        assert analyze_command("git clean -xfd") is not None

    def test_clean_dry_run_allowed(self) -> None:
        assert analyze_command("git clean -n") is None

    def test_checkout_path_blocked(self) -> None:
        assert analyze_command("git checkout -- file.py") is not None

    def test_checkout_branch_allowed(self) -> None:
        assert analyze_command("git checkout main") is None

    def test_restore_worktree_blocked(self) -> None:
        assert analyze_command("git restore file.py") is not None

    def test_restore_staged_allowed(self) -> None:
        assert analyze_command("git restore --staged file.py") is None


class TestAnalyzeCommandWithWrappers:
    """Tests for analyze_command with wrapper commands."""

    def test_sudo_wrapper(self) -> None:
        assert analyze_command("sudo git push --force") is not None
        assert analyze_command("sudo git status") is None

    def test_env_wrapper(self) -> None:
        assert analyze_command("env GIT_AUTHOR=foo git push -f") is not None

    def test_command_wrapper(self) -> None:
        assert analyze_command("command git reset --hard") is not None

    def test_nohup_wrapper(self) -> None:
        assert analyze_command("nohup git push --force &") is not None


class TestAnalyzeCommandWithBashC:
    """Tests for analyze_command with bash -c patterns."""

    def test_bash_c_force_push(self) -> None:
        assert analyze_command("bash -c 'git push -f'") is not None

    def test_sh_c_force_push(self) -> None:
        assert analyze_command("sh -c 'git push --force'") is not None

    def test_bash_c_safe_command(self) -> None:
        assert analyze_command("bash -c 'git status'") is None

    def test_sudo_bash_c(self) -> None:
        assert analyze_command("sudo bash -c 'git reset --hard'") is not None

    def test_nested_bash_c(self) -> None:
        # Nested bash -c should be analyzed
        cmd = "bash -c \"bash -c 'git push -f'\""
        assert analyze_command(cmd) is not None


class TestAnalyzeCommandWithOperators:
    """Tests for analyze_command with shell operators."""

    def test_semicolon_operator(self) -> None:
        assert analyze_command("echo foo; git push --force") is not None

    def test_and_operator(self) -> None:
        assert analyze_command("git add . && git push -f") is not None

    def test_or_operator(self) -> None:
        assert analyze_command("git status || git reset --hard") is not None

    def test_pipe_operator(self) -> None:
        assert analyze_command("echo main | git push -f") is not None

    def test_safe_command_chain(self) -> None:
        assert analyze_command("git add . && git commit -m 'msg'") is None


class TestAnalyzeCommandWithPolicy:
    """Tests for analyze_command with custom policies."""

    def test_allow_policy_skips_checks(self, allow_policy: dict[str, Any]) -> None:
        result = analyze_command("git push --force", policy=allow_policy)
        assert result is None

    def test_warn_policy_returns_warning(self, warn_policy: dict[str, Any]) -> None:
        result = analyze_command("git push --force", policy=warn_policy)
        assert result is not None
        assert result.startswith("WARNING:")

    def test_block_policy_returns_block(self, block_policy: dict[str, Any]) -> None:
        result = analyze_command("git push --force", policy=block_policy)
        assert result is not None
        assert not result.startswith("WARNING:")

    def test_disabled_rule_skipped(self, partial_policy: dict[str, Any]) -> None:
        # block_reset_hard is False in partial_policy
        result = analyze_command("git reset --hard", policy=partial_policy)
        assert result is None  # Not blocked because rule is disabled


class TestShouldBlock:
    """Tests for should_block function."""

    def test_none_reason(self) -> None:
        assert should_block(None) is False

    def test_block_reason(self) -> None:
        assert should_block("BLOCKED: Force push") is True

    def test_warning_reason(self) -> None:
        assert should_block("WARNING: Force push") is False


class TestGetExitCode:
    """Tests for get_exit_code function."""

    def test_none_reason(self) -> None:
        assert get_exit_code(None) == 0

    def test_block_reason(self) -> None:
        assert get_exit_code("BLOCKED: Force push") == 2

    def test_warning_reason(self) -> None:
        assert get_exit_code("WARNING: Force push") == 0


class TestCheckCommand:
    """Tests for check_command convenience function."""

    def test_allowed_command(self) -> None:
        exit_code, reason = check_command("git status")
        assert exit_code == 0
        assert reason is None

    def test_blocked_command(self) -> None:
        exit_code, reason = check_command("git push --force")
        assert exit_code == 2
        assert reason is not None


class TestEndToEnd:
    """End-to-end integration tests simulating hook behavior."""

    def test_full_hook_flow_block(self) -> None:
        """Simulate full PreToolUse hook flow for blocked command."""
        # Simulated JSON input
        hook_input = {
            "tool_name": "Bash",
            "tool_input": {"command": "git push --force origin main"},
            "cwd": "/workspace/project",
        }

        command = hook_input["tool_input"]["command"]
        exit_code, reason = check_command(command)

        assert exit_code == 2
        assert reason is not None
        assert "force" in reason.lower() or "Force" in reason

    def test_full_hook_flow_allow(self) -> None:
        """Simulate full PreToolUse hook flow for allowed command."""
        hook_input = {
            "tool_name": "Bash",
            "tool_input": {"command": "git push origin main"},
            "cwd": "/workspace/project",
        }

        command = hook_input["tool_input"]["command"]
        exit_code, reason = check_command(command)

        assert exit_code == 0
        assert reason is None

    def test_non_bash_tool_ignored(self) -> None:
        """Non-Bash tools should be ignored."""
        hook_input = {
            "tool_name": "Write",
            "tool_input": {"path": "/file.txt", "content": "data"},
        }

        # Non-Bash tools don't have "command" key, so would return None
        command = hook_input.get("tool_input", {}).get("command", "")
        exit_code, reason = check_command(command)

        assert exit_code == 0

    def test_complex_attack_vector(self) -> None:
        """Test protection against bypass attempts."""
        # Various bypass attempts that should all be blocked
        attacks = [
            "sudo bash -c 'git push -f'",
            "env HOME=/tmp git push --force",
            "git -C /path push --force",
            "echo foo && git reset --hard",
            "/usr/bin/git push +main",
            "bash -c \"bash -c 'git branch -D main'\"",
        ]

        for attack in attacks:
            exit_code, reason = check_command(attack)
            assert exit_code == 2, f"Attack should be blocked: {attack}"
