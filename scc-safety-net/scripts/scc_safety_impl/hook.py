"""Main hook orchestration for SCC Safety Net.

This module provides the core hook logic that:
1. Receives command strings from the PreToolUse hook
2. Tokenizes and analyzes commands for destructive patterns
3. Returns block reasons based on policy configuration

The hook contract uses exit code 2 + stderr for blocking:
- Exit 0: Allow execution (no output or warn message)
- Exit 2: Block execution (stderr contains reason)
"""

from __future__ import annotations

from typing import Any

from .git_rules import analyze_git
from .policy import get_action, is_rule_enabled, load_policy
from .shell import extract_all_commands

# ─────────────────────────────────────────────────────────────────────────────
# Rule to Policy Mapping
# ─────────────────────────────────────────────────────────────────────────────

# Maps git subcommands to their policy rule names
SUBCOMMAND_TO_RULE: dict[str, str] = {
    "push": "block_force_push",
    "reset": "block_reset_hard",
    "branch": "block_branch_force_delete",
    "stash": "block_stash_destructive",
    "clean": "block_clean",
    "checkout": "block_checkout_restore",
    "restore": "block_checkout_restore",
    # Catastrophic commands (v0.2.0)
    "reflog": "block_reflog_expire",
    "gc": "block_gc_prune",
    "filter-branch": "block_filter_branch",
}


# ─────────────────────────────────────────────────────────────────────────────
# Command Analysis
# ─────────────────────────────────────────────────────────────────────────────


def analyze_command(
    command: str,
    *,
    cwd: str | None = None,
    policy: dict[str, Any] | None = None,
) -> str | None:
    """Analyze a command string for destructive git operations.

    This is the main entry point for hook analysis. It:
    1. Tokenizes the command (handles shell operators, bash -c)
    2. Checks each extracted command against git rules
    3. Applies policy configuration to determine action

    Args:
        command: Full command string to analyze
        cwd: Current working directory (optional, for future use)
        policy: Policy dict (loads from config if not provided)

    Returns:
        Block reason string if command should be blocked, None if allowed
    """
    if not command or not command.strip():
        return None

    # Load policy if not provided
    if policy is None:
        policy, _warning = load_policy()

    action = get_action(policy)

    # If policy is set to allow, skip all checks
    if action == "allow":
        return None

    # Extract all commands from the input (handles bash -c, &&, etc.)
    for tokens in extract_all_commands(command):
        if not tokens:
            continue

        # Check if this is a git command
        first_cmd = tokens[0].split("/")[-1]  # Handle /usr/bin/git
        if first_cmd != "git":
            continue

        # Analyze the git command
        reason = analyze_git(tokens)
        if reason:
            # Check if the specific rule is enabled
            subcommand = tokens[1] if len(tokens) > 1 else ""
            rule = SUBCOMMAND_TO_RULE.get(subcommand)

            if rule and not is_rule_enabled(policy, rule):
                continue  # Rule disabled, skip this check

            # Return reason based on action mode
            if action == "block":
                return reason
            elif action == "warn":
                # Warn mode: return reason but caller uses exit 0
                return f"WARNING: {reason}"

    return None


def should_block(reason: str | None) -> bool:
    """Determine if a reason indicates blocking vs warning.

    Args:
        reason: Reason string from analyze_command

    Returns:
        True if command should be blocked (exit 2), False otherwise
    """
    if reason is None:
        return False
    return not reason.startswith("WARNING:")


def get_exit_code(reason: str | None) -> int:
    """Get the appropriate exit code for the hook.

    Hook exit code contract:
    - 0: Allow execution
    - 2: Block execution

    Args:
        reason: Reason string from analyze_command

    Returns:
        Exit code (0 or 2)
    """
    if should_block(reason):
        return 2
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# Convenience Functions
# ─────────────────────────────────────────────────────────────────────────────


def check_command(command: str) -> tuple[int, str | None]:
    """Check a command and return exit code and reason.

    Convenience function that combines analysis and exit code determination.

    Args:
        command: Command string to check

    Returns:
        Tuple of (exit_code, reason_or_none)
    """
    reason = analyze_command(command)
    exit_code = get_exit_code(reason)
    return exit_code, reason
