#!/usr/bin/env python3
"""SCC Safety Net - PreToolUse hook for blocking destructive git commands.

This script serves two purposes:
1. PreToolUse Hook: Receives JSON on stdin, analyzes Bash commands, blocks destructive git ops
2. Status Command: With --status flag, displays current policy configuration

Hook Contract:
- Input: JSON on stdin with tool_name, tool_input, cwd
- Output: stderr for block/warn messages
- Exit 0: Allow execution
- Exit 2: Block execution

Usage:
    # As PreToolUse hook (receives JSON on stdin):
    echo '{"tool_name":"Bash","tool_input":{"command":"git push -f"}}' | python3 scc_safety_net.py

    # As status command:
    python3 scc_safety_net.py --status
    python3 scc_safety_net.py --status --json
"""

from __future__ import annotations

import json
import sys
from typing import Any

from scc_safety_impl.hook import analyze_command, get_exit_code
from scc_safety_impl.policy import load_policy, render_status, render_status_json
from scc_safety_impl.redact import safe_output


def handle_status(*, json_output: bool = False) -> int:
    """Handle the --status flag for slash command.

    Args:
        json_output: If True, output JSON instead of human-readable format

    Returns:
        Exit code (0 for success, 1 if policy warning exists)
    """
    policy, warning = load_policy()

    if json_output:
        print(render_status_json(policy, warning))
    else:
        print(render_status(policy, warning))

    # Exit 1 if there's a policy integrity warning (SCC-managed mode)
    return 1 if warning else 0


def handle_hook(data: dict[str, Any]) -> int:
    """Handle PreToolUse hook execution.

    Args:
        data: Parsed JSON from stdin

    Returns:
        Exit code (0 for allow, 2 for block)
    """
    # Only process Bash tool calls
    tool_name = data.get("tool_name", "")
    if tool_name != "Bash":
        return 0

    # Extract command from tool_input
    tool_input = data.get("tool_input", {})
    if not isinstance(tool_input, dict):
        return 0

    command = tool_input.get("command", "")
    if not command:
        return 0

    # Get cwd for context (optional)
    cwd = data.get("cwd")

    # Analyze the command
    reason = analyze_command(command, cwd=cwd)

    if reason:
        exit_code = get_exit_code(reason)

        # If blocking (exit code 2), check for policy integrity warnings
        # Only append warning when actually blocking (not for warnings)
        if exit_code == 2:
            _policy, policy_warning = load_policy()
            if policy_warning:
                reason = f"{reason}\n\nNote: {policy_warning}; using safe defaults."

        # Output reason to stderr (Claude receives this)
        # Use safe_output to redact any secrets and truncate long output
        print(safe_output(reason), file=sys.stderr)
        return exit_code

    return 0


def main() -> int:
    """Main entry point for the hook script.

    Returns:
        Exit code
    """
    # Handle --status flag
    if len(sys.argv) > 1:
        if sys.argv[1] == "--status":
            json_output = len(sys.argv) > 2 and sys.argv[2] == "--json"
            return handle_status(json_output=json_output)
        elif sys.argv[1] == "--help":
            print(__doc__)
            return 0

    # Normal hook flow: read JSON from stdin
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        # Invalid JSON, allow execution but warn
        # Use safe_output to prevent leaking secrets from malformed input
        print(safe_output(f"scc-safety-net: Invalid JSON input: {e}"), file=sys.stderr)
        return 0
    except Exception as e:
        # Unexpected error, allow execution but warn
        print(safe_output(f"scc-safety-net: Error reading input: {e}"), file=sys.stderr)
        return 0

    return handle_hook(data)


if __name__ == "__main__":
    sys.exit(main())
