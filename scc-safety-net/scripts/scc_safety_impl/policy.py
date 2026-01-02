"""Policy loading and status rendering for SCC Safety Net.

This module handles:
- Policy resolution from multiple sources (env, workspace, cache)
- Policy file validation (symlink, perms, size checks)
- SCC-managed mode detection and enforcement
- Fail-safe defaults when policy is unreadable
- Status rendering for the slash command output

Policy Resolution Order:
1. SCC_POLICY_PATH environment variable
2. ./.scc/effective_policy.json (workspace-local)
3. ~/.cache/scc/org_config.json (SCC cache)
4. Built-in defaults (fail-safe: block mode)

SCC-Managed Mode (SCC_MANAGED=1):
- Only loads from SCC_POLICY_PATH
- Falls back to DEFAULT_POLICY on any error (fail-safe)
- Surfaces warnings via --status and block messages
"""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Any

from . import __version__

# ─────────────────────────────────────────────────────────────────────────────
# Policy File Validation Constants
# ─────────────────────────────────────────────────────────────────────────────

# Maximum policy file size (1MB)
MAX_POLICY_SIZE = 1_000_000

# Unsafe permission bits (group-writable or world-writable)
UNSAFE_PERM_MASK = stat.S_IWGRP | stat.S_IWOTH  # 0o022

# ─────────────────────────────────────────────────────────────────────────────
# Default Policy Configuration
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_POLICY: dict[str, Any] = {
    "action": "block",
    # Remote History
    "block_force_push": True,
    "block_push_mirror": True,
    # Local History
    "block_reset_hard": True,
    "block_reflog_expire": True,
    "block_filter_branch": True,
    "block_gc_prune": True,
    # Branch
    "block_branch_force_delete": True,
    # Uncommitted Work
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
    "git push --mirror": "regular push",
    "git reset --hard": "git stash",
    "git reflog expire ...=now": "don't expire manually",
    "git gc --prune=now": "git gc (default prune)",
    "git filter-branch": "git filter-repo",
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
# SCC-Managed Mode Detection
# ─────────────────────────────────────────────────────────────────────────────


def is_scc_managed() -> bool:
    """Check if running in SCC-managed container mode.

    When SCC_MANAGED=1, the plugin:
    - Only loads policy from SCC_POLICY_PATH
    - Ignores workspace/cache policies
    - Falls back to DEFAULT_POLICY on any failure

    Returns:
        True if running in SCC-managed mode
    """
    return os.environ.get("SCC_MANAGED") == "1"


# ─────────────────────────────────────────────────────────────────────────────
# Policy File Validation
# ─────────────────────────────────────────────────────────────────────────────


def _validate_policy_file(path: Path) -> str | None:
    """Validate a policy file for security issues.

    Checks:
    - Not a symlink (prevent attacker-controlled policy)
    - Is a regular file (not directory/FIFO/device)
    - Not group-writable or world-writable (unsafe perms)
    - Not too large (DoS protection)

    Args:
        path: Path to policy file

    Returns:
        Error message if file is unsafe, None if OK
    """
    # Check symlink first (before following it)
    if path.is_symlink():
        return f"Policy file is a symlink: {path}"

    # Check it's a regular file
    if not path.is_file():
        return f"Policy path is not a regular file: {path}"

    # Get file stats
    try:
        file_stat = path.stat()
    except OSError as e:
        return f"Cannot stat policy file {path}: {e}"

    # Check permissions (group-writable or world-writable)
    if file_stat.st_mode & UNSAFE_PERM_MASK:
        return f"Policy file has unsafe permissions (group/world-writable): {path}"

    # Check size
    if file_stat.st_size > MAX_POLICY_SIZE:
        return f"Policy file too large (>{MAX_POLICY_SIZE // 1_000_000}MB): {path}"

    return None


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


def _get_active_policy_path() -> tuple[str | None, str | None]:
    """Find which policy path is actually being used.

    In SCC-managed mode, only checks SCC_POLICY_PATH.

    Returns:
        Tuple of (path string or None, validation error or None)
    """
    if is_scc_managed():
        # SCC-managed mode: only use SCC_POLICY_PATH
        path_str = os.environ.get("SCC_POLICY_PATH")
        if not path_str:
            return None, "SCC_MANAGED=1 but SCC_POLICY_PATH not set"

        path = Path(path_str)
        if not path.exists():
            return None, f"SCC_POLICY_PATH does not exist: {path_str}"

        validation_error = _validate_policy_file(path)
        if validation_error:
            return None, validation_error

        return path_str, None

    # Standard mode: check paths in priority order
    for path_str in _get_policy_paths():
        if path_str is None:
            continue

        path = Path(path_str)
        if path.exists():
            # Validate the file
            validation_error = _validate_policy_file(path)
            if validation_error:
                # In standard mode, skip invalid files and try next
                continue
            return path_str, None

    return None, None


def load_policy() -> tuple[dict[str, Any], str | None]:
    """Load SCC safety net policy with fail-safe defaults.

    Checks policy paths in priority order and returns the first
    valid policy found. Falls back to blocking defaults if no
    policy is found or if all policies are unreadable.

    In SCC-managed mode:
    - Only loads from SCC_POLICY_PATH
    - Returns DEFAULT_POLICY with warning on any failure

    Returns:
        Tuple of (policy dict, warning message or None)
        Warning is set when policy integrity failed and we fell back to defaults.
        Caller can use warning for:
        - --status: print warning + exit 1
        - block message: append note about using safe defaults
    """
    active_path, path_error = _get_active_policy_path()

    if path_error:
        # Policy integrity failure - fall back to defaults
        return dict(DEFAULT_POLICY), f"Policy integrity failure: {path_error}"

    if active_path is None:
        # No policy found - use defaults (no warning, this is normal)
        return dict(DEFAULT_POLICY), None

    # Load and parse the policy
    path = Path(active_path)
    doc = _load_json(path)
    policy = _extract_safety_net(doc)

    # Ensure action key exists
    if "action" not in policy:
        policy["action"] = "block"

    return policy, None


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


def render_status(policy: dict[str, Any], warning: str | None = None) -> str:
    """Render human-readable status for slash command.

    Args:
        policy: Policy dict from load_policy()
        warning: Optional warning message from load_policy()

    Returns:
        Formatted status string for terminal output
    """
    action = get_action(policy)
    active_path, _ = _get_active_policy_path()

    lines = [
        f"SCC Safety Net v{__version__}",
        "━" * 45,
    ]

    # Show warning if present
    if warning:
        lines.append(f"⚠️  WARNING: {warning}")
        lines.append("━" * 45)

    lines.extend(
        [
            f"Mode: {action.upper()} (default)" if action == "block" else f"Mode: {action.upper()}",
            f"Policy: {active_path or 'built-in defaults'}",
            "",
            "Blocked Operations:",
        ]
    )

    # Add blocked commands with alternatives
    for cmd, alt in BLOCKED_COMMANDS.items():
        lines.append(f"  ❌ {cmd:<28} → use {alt}")

    lines.extend(["", "Allowed:"])

    # Add allowed commands
    for cmd in ALLOWED_COMMANDS:
        lines.append(f"  ✅ {cmd}")

    return "\n".join(lines)


def render_status_json(policy: dict[str, Any], warning: str | None = None) -> str:
    """Render machine-readable JSON status.

    Args:
        policy: Policy dict from load_policy()
        warning: Optional warning message from load_policy()

    Returns:
        JSON string for programmatic consumption
    """
    active_path, _ = _get_active_policy_path()
    status: dict[str, Any] = {
        "version": __version__,
        "mode": get_action(policy),
        "policy_path": active_path,
        "rules": {
            "block_force_push": is_rule_enabled(policy, "block_force_push"),
            "block_push_mirror": is_rule_enabled(policy, "block_push_mirror"),
            "block_reset_hard": is_rule_enabled(policy, "block_reset_hard"),
            "block_reflog_expire": is_rule_enabled(policy, "block_reflog_expire"),
            "block_filter_branch": is_rule_enabled(policy, "block_filter_branch"),
            "block_gc_prune": is_rule_enabled(policy, "block_gc_prune"),
            "block_branch_force_delete": is_rule_enabled(policy, "block_branch_force_delete"),
            "block_checkout_restore": is_rule_enabled(policy, "block_checkout_restore"),
            "block_clean": is_rule_enabled(policy, "block_clean"),
            "block_stash_destructive": is_rule_enabled(policy, "block_stash_destructive"),
        },
        "blocked_commands": list(BLOCKED_COMMANDS.keys()),
        "allowed_commands": ALLOWED_COMMANDS,
    }
    if warning:
        status["warning"] = warning
    return json.dumps(status, indent=2)
