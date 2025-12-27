"""Shared fixtures for SCC Safety Net tests."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def temp_policy_file(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary policy file."""
    policy_file = tmp_path / "policy.json"
    yield policy_file


@pytest.fixture
def block_policy() -> dict[str, Any]:
    """Return a blocking policy configuration."""
    return {
        "action": "block",
        "block_force_push": True,
        "block_reset_hard": True,
        "block_branch_force_delete": True,
        "block_checkout_restore": True,
        "block_clean": True,
        "block_stash_destructive": True,
    }


@pytest.fixture
def warn_policy() -> dict[str, Any]:
    """Return a warning-only policy configuration."""
    return {
        "action": "warn",
        "block_force_push": True,
        "block_reset_hard": True,
        "block_branch_force_delete": True,
        "block_checkout_restore": True,
        "block_clean": True,
        "block_stash_destructive": True,
    }


@pytest.fixture
def allow_policy() -> dict[str, Any]:
    """Return an allow-all policy configuration."""
    return {"action": "allow"}


@pytest.fixture
def partial_policy() -> dict[str, Any]:
    """Return a policy with some rules disabled."""
    return {
        "action": "block",
        "block_force_push": True,
        "block_reset_hard": False,  # Disabled
        "block_branch_force_delete": True,
        "block_checkout_restore": False,  # Disabled
        "block_clean": True,
        "block_stash_destructive": True,
    }


@pytest.fixture
def nested_policy() -> dict[str, Any]:
    """Return a policy in nested security.safety_net format."""
    return {
        "security": {
            "safety_net": {
                "action": "block",
                "block_force_push": True,
            }
        }
    }


@pytest.fixture
def env_policy_path(tmp_path: Path) -> Generator[Path, None, None]:
    """Set up SCC_POLICY_PATH environment variable."""
    policy_file = tmp_path / "env_policy.json"
    old_value = os.environ.get("SCC_POLICY_PATH")
    os.environ["SCC_POLICY_PATH"] = str(policy_file)
    yield policy_file
    if old_value is None:
        del os.environ["SCC_POLICY_PATH"]
    else:
        os.environ["SCC_POLICY_PATH"] = old_value


@pytest.fixture
def clean_env() -> Generator[None, None, None]:
    """Clean up SCC_POLICY_PATH environment variable."""
    old_value = os.environ.get("SCC_POLICY_PATH")
    if "SCC_POLICY_PATH" in os.environ:
        del os.environ["SCC_POLICY_PATH"]
    yield
    if old_value is not None:
        os.environ["SCC_POLICY_PATH"] = old_value
