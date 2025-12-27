"""Policy loading and status rendering for SCC Safety Net.

This module handles:
- Policy resolution from multiple sources (env, workspace, cache)
- Fail-safe defaults when policy is unreadable
- Status rendering for the slash command output

Policy Resolution Order:
1. SCC_POLICY_PATH environment variable
2. ./.scc/effective_policy.json (workspace-local)
3. ~/.cache/scc/org_config.json (SCC cache)
4. Built-in defaults (fail-safe: block mode)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from . import __version__

# ─────────────────────────────────────────────────────────────────────────────
# Default Policy Configuration
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_POLICY: dict[str, Any] = {
    "action": "block",
    "block_force_push": True,
    "block_reset_hard": True,
    "block_branch_force_delete": True,
    "block_checkout_restore": True,
    "block_clean": True,
    "block_stash_destructive": True,
}

# ─────────────────────────────────────────────────────────────────────────────
# Blocked/Allowed Commands for Status Display
# ─────────────────────────────────────────────────────────────────────────────

BLOCKED_COMMANDS: dict[str, str] = {
    "git push --force": "--force-with-lease",
    "git push +refspec": "--force-with-lease",
    "git reset --hard": "git stash",
    "git checkout -- *": "git stash",
    "git restore <path>": "git stash (--staged is allowed)",
    "git clean -f": "git clean -n (dry-run)",
    "git branch -D": "git branch -d",
    "git stash drop": "review with git stash list first",
}

ALLOWED_COMMANDS: list[str] = [
    "git push --force-with-lease",
    "git restore --staged <path>",
    "git clean -n/--dry-run",
]


# ─────────────────────────────────────────────────────────────────────────────
# Policy Resolution
# ─────────────────────────────────────────────────────────────────────────────


def _get_policy_paths() -> list[str | None]:
    """Return policy paths in priority order.

    Priority:
    1. SCC_POLICY_PATH environment variable
    2. ./.scc/effective_policy.json (workspace-local)
    3. ~/.cache/scc/org_config.json (SCC cache)

    Returns:
        List of paths to check, may contain None for missing env var
    """
    return [
        os.environ.get("SCC_POLICY_PATH"),
        "./.scc/effective_policy.json",
        str(Path.home() / ".cache/scc/org_config.json"),
    ]


def _load_json(path: Path) -> dict[str, Any]:
    """Load JSON file with fail-safe error handling.

    Args:
        path: Path to JSON file

    Returns:
        Parsed JSON as dict, or default policy on any error
    """
    try:
        content = path.read_text(encoding="utf-8")
        data = json.loads(content)
        if isinstance(data, dict):
            return data
        return dict(DEFAULT_POLICY)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        # Fail-safe: return default blocking policy
        return dict(DEFAULT_POLICY)


def _extract_safety_net(doc: dict[str, Any]) -> dict[str, Any]:
    """Extract safety_net config from org config structure.

    Handles multiple config formats:
    - Direct policy: {"action": "block", ...}
    - Nested: {"security": {"safety_net": {...}}}

    Args:
        doc: Parsed JSON document

    Returns:
        Normalized policy dict
    """
    # Check for nested security.safety_net structure
    if isinstance(doc.get("security"), dict):
        safety_net = doc["security"].get("safety_net")
        if isinstance(safety_net, dict):
            return safety_net
        # security exists but no safety_net: use defaults
        if "safety_net" in doc["security"]:
            return dict(DEFAULT_POLICY)

    # Check if doc itself looks like a policy (has action or block_* keys)
    policy_keys = {"action", "block_force_push", "block_reset_hard"}
    if policy_keys & set(doc.keys()):
        return doc

    # Not a recognizable format, use defaults
    return dict(DEFAULT_POLICY)


def _get_active_policy_path() -> str | None:
    """Find which policy path is actually being used.

    Returns:
        Path string of active policy, or None if using defaults
    """
    for path in _get_policy_paths():
        if path and Path(path).exists():
            return path
    return None


def load_policy() -> dict[str, Any]:
    """Load SCC safety net policy with fail-safe defaults.

    Checks policy paths in priority order and returns the first
    valid policy found. Falls back to blocking defaults if no
    policy is found or if all policies are unreadable.

    Returns:
        Policy dict with at least 'action' key
    """
    for path_str in _get_policy_paths():
        if path_str is None:
            continue

        path = Path(path_str)
        if path.exists():
            doc = _load_json(path)
            policy = _extract_safety_net(doc)
            # Ensure action key exists
            if "action" not in policy:
                policy["action"] = "block"
            return policy

    # No policy found, return fail-safe defaults
    return dict(DEFAULT_POLICY)


def get_action(policy: dict[str, Any]) -> str:
    """Get the action mode from policy.

    Args:
        policy: Policy dict

    Returns:
        Action string: 'block', 'warn', or 'allow'
    """
    action = policy.get("action", "block")
    if action in ("block", "warn", "allow"):
        return action
    return "block"  # Invalid action defaults to block


def is_rule_enabled(policy: dict[str, Any], rule: str) -> bool:
    """Check if a specific rule is enabled.

    Args:
        policy: Policy dict
        rule: Rule name (e.g., 'block_force_push')

    Returns:
        True if rule is enabled, defaults to True for safety
    """
    return policy.get(rule, True)


# ─────────────────────────────────────────────────────────────────────────────
# Status Rendering
# ─────────────────────────────────────────────────────────────────────────────


def render_status(policy: dict[str, Any]) -> str:
    """Render human-readable status for slash command.

    Args:
        policy: Policy dict from load_policy()

    Returns:
        Formatted status string for terminal output
    """
    action = get_action(policy)
    active_path = _get_active_policy_path()

    lines = [
        f"SCC Safety Net v{__version__}",
        "━" * 45,
        f"Mode: {action.upper()} (default)" if action == "block" else f"Mode: {action.upper()}",
        f"Policy: {active_path or 'built-in defaults'}",
        "",
        "Blocked Operations:",
    ]

    # Add blocked commands with alternatives
    for cmd, alt in BLOCKED_COMMANDS.items():
        lines.append(f"  ❌ {cmd:<20} → use {alt}")

    lines.extend(["", "Allowed:"])

    # Add allowed commands
    for cmd in ALLOWED_COMMANDS:
        lines.append(f"  ✅ {cmd}")

    return "\n".join(lines)


def render_status_json(policy: dict[str, Any]) -> str:
    """Render machine-readable JSON status.

    Args:
        policy: Policy dict from load_policy()

    Returns:
        JSON string for programmatic consumption
    """
    status = {
        "version": __version__,
        "mode": get_action(policy),
        "policy_path": _get_active_policy_path(),
        "rules": {
            "block_force_push": is_rule_enabled(policy, "block_force_push"),
            "block_reset_hard": is_rule_enabled(policy, "block_reset_hard"),
            "block_branch_force_delete": is_rule_enabled(policy, "block_branch_force_delete"),
            "block_checkout_restore": is_rule_enabled(policy, "block_checkout_restore"),
            "block_clean": is_rule_enabled(policy, "block_clean"),
            "block_stash_destructive": is_rule_enabled(policy, "block_stash_destructive"),
        },
        "blocked_commands": list(BLOCKED_COMMANDS.keys()),
        "allowed_commands": ALLOWED_COMMANDS,
    }
    return json.dumps(status, indent=2)
