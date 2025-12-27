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


def handle_status(*, json_output: bool = False) -> int:
    """Handle the --status flag for slash command.

    Args:
        json_output: If True, output JSON instead of human-readable format

    Returns:
        Exit code (always 0 for status)
    """
    policy = load_policy()

    if json_output:
        print(render_status_json(policy))
    else:
        print(render_status(policy))

    return 0


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
        # Output reason to stderr (Claude receives this)
        print(reason, file=sys.stderr)
        return get_exit_code(reason)

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
        print(f"scc-safety-net: Invalid JSON input: {e}", file=sys.stderr)
        return 0
    except Exception as e:
        # Unexpected error, allow execution but warn
        print(f"scc-safety-net: Error reading input: {e}", file=sys.stderr)
        return 0

    return handle_hook(data)


if __name__ == "__main__":
    sys.exit(main())
