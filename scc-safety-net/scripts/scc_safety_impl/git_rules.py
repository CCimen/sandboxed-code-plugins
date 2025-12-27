"""Git command analysis for detecting destructive operations.

This module analyzes git commands and returns block reasons for
destructive operations that could damage remote history or local work.

Blocked operations (v1.0):
- git push --force / -f / +refspec
- git reset --hard
- git branch -D
- git stash drop / clear
- git clean -f / -fd / -xfd
- git checkout -- <path>
- git restore <path> (worktree, not --staged)
"""

from __future__ import annotations

from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Git Global Option Handling
# ─────────────────────────────────────────────────────────────────────────────

# Git global options that take a value (skip both flag and value)
GIT_GLOBAL_OPTIONS_WITH_VALUE = frozenset({"-C", "-c", "--git-dir", "--work-tree"})

# Git global options that combine flag=value
GIT_GLOBAL_OPTIONS_COMBINED = ("--git-dir=", "--work-tree=")


def normalize_git_tokens(tokens: list[str]) -> tuple[str, list[str]]:
    """Extract subcommand and args, skipping global git options.

    Handles:
    - /usr/bin/git → git
    - git -C /path push → push
    - git --git-dir=.git push → push

    Args:
        tokens: Full command tokens starting with git

    Returns:
        Tuple of (subcommand, remaining_args)
    """
    if not tokens:
        return "", []

    # Check if first token is git (handle /usr/bin/git)
    if Path(tokens[0]).name != "git":
        return "", []

    i = 1
    while i < len(tokens):
        token = tokens[i]

        # Handle -C, -c, --git-dir, --work-tree (with separate value)
        if token in GIT_GLOBAL_OPTIONS_WITH_VALUE:
            i += 2  # Skip option and its value
        # Handle --git-dir=.git, --work-tree=/path
        elif any(token.startswith(prefix) for prefix in GIT_GLOBAL_OPTIONS_COMBINED):
            i += 1  # Skip combined option=value
        else:
            break

    if i >= len(tokens):
        return "", []

    return tokens[i], tokens[i + 1 :]


# ─────────────────────────────────────────────────────────────────────────────
# Force Push Detection
# ─────────────────────────────────────────────────────────────────────────────


def has_force_flag(args: list[str]) -> bool:
    """Detect force flags including combined short options.

    Matches: -f, --force, -xfd (contains -f)

    IMPORTANT: Only apply this function for git subcommands where -f
    means "force" (push, clean, branch -D). Do NOT apply globally -
    some subcommands use -f for different meanings.

    Args:
        args: Command arguments (after subcommand)

    Returns:
        True if force flag detected
    """
    for token in args:
        if token == "-f" or token == "--force":
            return True
        # Combined short flags: -xfd contains -f
        # Must start with - but not -- (long options)
        if token.startswith("-") and not token.startswith("--") and "f" in token:
            return True
    return False


def has_force_refspec(args: list[str]) -> bool:
    """Detect force push via +refspec patterns.

    Matches: +main, +main:main, HEAD:+main, origin/+main

    Args:
        args: Command arguments (after subcommand)

    Returns:
        True if +refspec force push pattern detected
    """
    for token in args:
        # Skip flags
        if token.startswith("-"):
            continue
        # +ref at start of token
        if token.startswith("+") and not token.startswith("++"):
            return True
        # ref:+ref pattern (e.g., HEAD:+main)
        if ":+" in token:
            return True
    return False


def has_force_with_lease(args: list[str]) -> bool:
    """Check if --force-with-lease is present (safe force push).

    Args:
        args: Command arguments

    Returns:
        True if --force-with-lease is present
    """
    return any(arg.startswith("--force-with-lease") for arg in args)


# ─────────────────────────────────────────────────────────────────────────────
# Destructive Command Detection
# ─────────────────────────────────────────────────────────────────────────────

# Block reasons with safe alternatives
BLOCK_MESSAGES = {
    "force_push": (
        "BLOCKED: Force push destroys remote history.\n\n"
        "Safe alternative: git push --force-with-lease"
    ),
    "reset_hard": (
        "BLOCKED: git reset --hard destroys uncommitted changes.\n\n"
        "Safe alternative: git stash (preserves changes)"
    ),
    "branch_force_delete": (
        "BLOCKED: git branch -D force-deletes without merge check.\n\n"
        "Safe alternative: git branch -d (requires merge check)"
    ),
    "stash_drop": (
        "BLOCKED: git stash drop permanently deletes stash entry.\n\n"
        "Safe alternative: Review with git stash list first"
    ),
    "stash_clear": (
        "BLOCKED: git stash clear permanently deletes ALL stashes.\n\n"
        "Safe alternative: Review with git stash list first"
    ),
    "clean_force": (
        "BLOCKED: git clean -f destroys untracked files.\n\n"
        "Safe alternative: git clean -n (dry-run preview)"
    ),
    "checkout_path": (
        "BLOCKED: git checkout -- <path> destroys uncommitted changes.\n\n"
        "Safe alternative: git stash (preserves changes)"
    ),
    "restore_worktree": (
        "BLOCKED: git restore <path> destroys uncommitted changes.\n\n"
        "Safe alternatives:\n"
        "  - git stash (preserves changes)\n"
        "  - git restore --staged <path> (only unstages, doesn't discard)"
    ),
}


def analyze_push(args: list[str]) -> str | None:
    """Analyze git push for destructive patterns.

    Blocks:
    - git push --force
    - git push -f
    - git push +refspec

    Allows:
    - git push --force-with-lease
    """
    # Allow --force-with-lease (safe)
    if has_force_with_lease(args):
        return None

    # Block --force, -f, or combined flags containing 'f'
    if has_force_flag(args):
        return BLOCK_MESSAGES["force_push"]

    # Block +refspec patterns
    if has_force_refspec(args):
        return BLOCK_MESSAGES["force_push"]

    return None


def analyze_reset(args: list[str]) -> str | None:
    """Analyze git reset for destructive patterns.

    Blocks:
    - git reset --hard

    Allows:
    - git reset (default mixed)
    - git reset --soft
    - git reset --mixed
    """
    if "--hard" in args:
        return BLOCK_MESSAGES["reset_hard"]
    return None


def analyze_branch(args: list[str]) -> str | None:
    """Analyze git branch for destructive patterns.

    Blocks:
    - git branch -D (force delete)
    - git branch --delete --force

    Allows:
    - git branch -d (safe delete with merge check)
    """
    # Check for -D specifically (uppercase)
    if "-D" in args:
        return BLOCK_MESSAGES["branch_force_delete"]

    # Check for combined --delete --force
    has_delete = "--delete" in args or any(
        a.startswith("-") and not a.startswith("--") and "d" in a.lower() for a in args
    )
    if has_delete and "--force" in args:
        return BLOCK_MESSAGES["branch_force_delete"]

    return None


def analyze_stash(args: list[str]) -> str | None:
    """Analyze git stash for destructive patterns.

    Blocks:
    - git stash drop
    - git stash clear

    Allows:
    - git stash (push)
    - git stash pop
    - git stash apply
    - git stash list
    """
    if not args:
        return None

    subcommand = args[0]
    if subcommand == "drop":
        return BLOCK_MESSAGES["stash_drop"]
    if subcommand == "clear":
        return BLOCK_MESSAGES["stash_clear"]

    return None


def analyze_clean(args: list[str]) -> str | None:
    """Analyze git clean for destructive patterns.

    Blocks:
    - git clean -f
    - git clean -fd
    - git clean -xfd
    - Any combination containing -f without -n/--dry-run

    Allows:
    - git clean -n (dry-run)
    - git clean --dry-run
    """
    # Allow dry-run mode
    has_dry_run = "-n" in args or "--dry-run" in args
    if has_dry_run:
        return None

    # Block any force flag (including combined like -xfd)
    if has_force_flag(args):
        return BLOCK_MESSAGES["clean_force"]

    return None


def analyze_checkout(args: list[str]) -> str | None:
    """Analyze git checkout for destructive patterns.

    Blocks:
    - git checkout -- <path>
    - git checkout HEAD -- <path>
    - git checkout <branch> -- <path> (when reverting changes)

    Allows:
    - git checkout <branch> (switching branches)
    - git checkout -b <branch> (creating branch)
    """
    if not args:
        return None

    # Look for -- separator (indicates path checkout)
    try:
        separator_idx = args.index("--")
        # If there are paths after --, this is a destructive path checkout
        if separator_idx < len(args) - 1:
            return BLOCK_MESSAGES["checkout_path"]
    except ValueError:
        pass

    return None


def analyze_restore(args: list[str]) -> str | None:
    """Analyze git restore for destructive patterns.

    Blocks:
    - git restore <path> (worktree restore)
    - git restore --worktree <path>

    Allows:
    - git restore --staged <path> (only unstages)
    """
    if not args:
        return None

    # Allow --staged only (safe: just unstages)
    has_staged = "--staged" in args or "-S" in args
    has_worktree = "--worktree" in args or "-W" in args

    # If only --staged and not --worktree, it's safe
    if has_staged and not has_worktree:
        return None

    # Check if there are path arguments (non-flag arguments)
    paths = [a for a in args if not a.startswith("-")]
    if paths:
        # Has paths and either:
        # - explicit --worktree, or
        # - no --staged (worktree is default for paths)
        if has_worktree or not has_staged:
            return BLOCK_MESSAGES["restore_worktree"]

    return None


# ─────────────────────────────────────────────────────────────────────────────
# Main Analysis Entry Point
# ─────────────────────────────────────────────────────────────────────────────


def analyze_git(tokens: list[str]) -> str | None:
    """Analyze git command tokens for destructive operations.

    Args:
        tokens: Command tokens starting with 'git'

    Returns:
        Block message if destructive, None if allowed
    """
    subcommand, args = normalize_git_tokens(tokens)

    if not subcommand:
        return None

    # Route to specific analyzers
    analyzers = {
        "push": analyze_push,
        "reset": analyze_reset,
        "branch": analyze_branch,
        "stash": analyze_stash,
        "clean": analyze_clean,
        "checkout": analyze_checkout,
        "restore": analyze_restore,
    }

    analyzer = analyzers.get(subcommand)
    if analyzer:
        return analyzer(args)

    return None
