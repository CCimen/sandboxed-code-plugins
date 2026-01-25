"""Tests for policy loading and status rendering."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from scc_safety_impl.policy import (
    ALLOWED_COMMANDS,
    BLOCKED_COMMANDS,
    DEFAULT_POLICY,
    MAX_POLICY_SIZE,
    _extract_safety_net,
    _get_policy_paths,
    _load_json,
    _validate_policy_file,
    get_action,
    is_rule_enabled,
    is_scc_managed,
    load_policy,
    render_status,
    render_status_json,
)


class TestGetPolicyPaths:
    """Tests for _get_policy_paths function."""

    def test_returns_list(self, clean_env: None) -> None:
        paths = _get_policy_paths()
        assert isinstance(paths, list)
        assert len(paths) == 3

    def test_includes_env_var_when_set(self, env_policy_path: Path) -> None:
        paths = _get_policy_paths()
        assert str(env_policy_path) in paths

    def test_includes_workspace_path(self, clean_env: None) -> None:
        paths = _get_policy_paths()
        assert "./.scc/effective_policy.json" in paths

    def test_includes_cache_path(self, clean_env: None) -> None:
        paths = _get_policy_paths()
        cache_path = str(Path.home() / ".cache/scc/org_config.json")
        assert cache_path in paths


class TestLoadJson:
    """Tests for _load_json function."""

    def test_valid_json(self, tmp_path: Path) -> None:
        policy_file = tmp_path / "policy.json"
        policy_file.write_text('{"action": "warn"}')
        result = _load_json(policy_file)
        assert result == {"action": "warn"}

    def test_invalid_json(self, tmp_path: Path) -> None:
        policy_file = tmp_path / "policy.json"
        policy_file.write_text("not valid json")
        result = _load_json(policy_file)
        # Should return default policy on error
        assert result == DEFAULT_POLICY

    def test_missing_file(self, tmp_path: Path) -> None:
        policy_file = tmp_path / "nonexistent.json"
        result = _load_json(policy_file)
        assert result == DEFAULT_POLICY

    def test_non_dict_json(self, tmp_path: Path) -> None:
        policy_file = tmp_path / "policy.json"
        policy_file.write_text('["list", "not", "dict"]')
        result = _load_json(policy_file)
        assert result == DEFAULT_POLICY


class TestExtractSafetyNet:
    """Tests for _extract_safety_net function."""

    def test_direct_policy(self) -> None:
        doc = {"action": "block", "block_force_push": True}
        result = _extract_safety_net(doc)
        assert result == doc

    def test_nested_policy(self, nested_policy: dict[str, Any]) -> None:
        result = _extract_safety_net(nested_policy)
        assert result == {"action": "block", "block_force_push": True}

    def test_empty_nested(self) -> None:
        doc = {"security": {"safety_net": None}}
        result = _extract_safety_net(doc)
        assert result == DEFAULT_POLICY

    def test_unrecognized_format(self) -> None:
        doc = {"unrelated": "data"}
        result = _extract_safety_net(doc)
        assert result == DEFAULT_POLICY


class TestLoadPolicy:
    """Tests for load_policy function."""

    def test_default_when_no_files(self, clean_env: None, tmp_path: Path) -> None:
        # Change to temp dir where no policy files exist
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            policy, warning = load_policy()
            assert policy["action"] == "block"
            assert warning is None  # No warning for normal default
        finally:
            os.chdir(original_cwd)

    def test_env_var_priority(self, env_policy_path: Path, block_policy: dict[str, Any]) -> None:
        block_policy["action"] = "warn"  # Distinguish from default
        env_policy_path.write_text(json.dumps(block_policy))
        policy, warning = load_policy()
        assert policy["action"] == "warn"
        assert warning is None

    def test_ensures_action_key(self, env_policy_path: Path) -> None:
        env_policy_path.write_text('{"block_force_push": true}')
        policy, warning = load_policy()
        assert "action" in policy
        assert policy["action"] == "block"
        assert warning is None


class TestGetAction:
    """Tests for get_action function."""

    def test_block_action(self) -> None:
        assert get_action({"action": "block"}) == "block"

    def test_warn_action(self) -> None:
        assert get_action({"action": "warn"}) == "warn"

    def test_allow_action(self) -> None:
        assert get_action({"action": "allow"}) == "allow"

    def test_missing_action(self) -> None:
        assert get_action({}) == "block"

    def test_invalid_action(self) -> None:
        assert get_action({"action": "invalid"}) == "block"


class TestIsRuleEnabled:
    """Tests for is_rule_enabled function."""

    def test_enabled_rule(self) -> None:
        policy: dict[str, bool] = {"block_force_push": True}
        assert is_rule_enabled(policy, "block_force_push") is True

    def test_disabled_rule(self) -> None:
        policy: dict[str, bool] = {"block_force_push": False}
        assert is_rule_enabled(policy, "block_force_push") is False

    def test_missing_rule_defaults_true(self) -> None:
        policy: dict[str, bool] = {}
        assert is_rule_enabled(policy, "block_force_push") is True


class TestRenderStatus:
    """Tests for render_status function."""

    def test_includes_version(self) -> None:
        status = render_status({"action": "block"})
        assert "SCC Safety Net v" in status

    def test_includes_mode(self) -> None:
        status = render_status({"action": "block"})
        assert "Mode: BLOCK" in status

    def test_includes_blocked_commands(self) -> None:
        status = render_status({"action": "block"})
        for cmd in BLOCKED_COMMANDS:
            assert cmd in status or any(part in status for part in cmd.split())

    def test_includes_allowed_commands(self) -> None:
        status = render_status({"action": "block"})
        assert "Allowed:" in status
        for cmd in ALLOWED_COMMANDS:
            assert cmd in status

    def test_warn_mode_displayed(self) -> None:
        status = render_status({"action": "warn"})
        assert "Mode: WARN" in status


class TestRenderStatusJson:
    """Tests for render_status_json function."""

    def test_valid_json_output(self) -> None:
        status = render_status_json({"action": "block"})
        parsed = json.loads(status)
        assert isinstance(parsed, dict)

    def test_includes_version(self) -> None:
        status = render_status_json({"action": "block"})
        parsed = json.loads(status)
        assert "version" in parsed

    def test_includes_mode(self) -> None:
        status = render_status_json({"action": "warn"})
        parsed = json.loads(status)
        assert parsed["mode"] == "warn"

    def test_includes_rules(self) -> None:
        status = render_status_json({"action": "block"})
        parsed = json.loads(status)
        assert "rules" in parsed
        assert "block_force_push" in parsed["rules"]

    def test_includes_commands(self) -> None:
        status = render_status_json({"action": "block"})
        parsed = json.loads(status)
        assert "blocked_commands" in parsed
        assert "allowed_commands" in parsed

    def test_includes_new_rules(self) -> None:
        status = render_status_json({"action": "block"})
        parsed = json.loads(status)
        # Check new v0.2.0 rules are present
        assert "block_push_mirror" in parsed["rules"]
        assert "block_reflog_expire" in parsed["rules"]
        assert "block_filter_branch" in parsed["rules"]
        assert "block_gc_prune" in parsed["rules"]


class TestIsSccManaged:
    """Tests for is_scc_managed function."""

    def test_returns_false_when_not_set(self, clean_env: None) -> None:
        assert is_scc_managed() is False

    def test_returns_true_when_set(self, clean_env: None) -> None:
        os.environ["SCC_MANAGED"] = "1"
        try:
            assert is_scc_managed() is True
        finally:
            del os.environ["SCC_MANAGED"]

    def test_returns_false_for_other_values(self, clean_env: None) -> None:
        os.environ["SCC_MANAGED"] = "true"
        try:
            assert is_scc_managed() is False
        finally:
            del os.environ["SCC_MANAGED"]


class TestValidatePolicyFile:
    """Tests for _validate_policy_file function."""

    def test_valid_file(self, tmp_path: Path) -> None:
        policy_file = tmp_path / "policy.json"
        policy_file.write_text('{"action": "block"}')
        os.chmod(policy_file, 0o644)  # -rw-r--r--
        assert _validate_policy_file(policy_file) is None

    def test_rejects_symlink(self, tmp_path: Path) -> None:
        policy_file = tmp_path / "policy.json"
        policy_file.write_text('{"action": "block"}')
        link = tmp_path / "policy_link.json"
        link.symlink_to(policy_file)
        error = _validate_policy_file(link)
        assert error is not None
        assert "symlink" in error.lower()

    def test_rejects_directory(self, tmp_path: Path) -> None:
        error = _validate_policy_file(tmp_path)
        assert error is not None
        assert "not a regular file" in error.lower()

    def test_rejects_world_writable(self, tmp_path: Path) -> None:
        policy_file = tmp_path / "policy.json"
        policy_file.write_text('{"action": "block"}')
        os.chmod(policy_file, 0o646)  # -rw-r--rw-
        error = _validate_policy_file(policy_file)
        assert error is not None
        assert "unsafe permissions" in error.lower()

    def test_rejects_group_writable(self, tmp_path: Path) -> None:
        policy_file = tmp_path / "policy.json"
        policy_file.write_text('{"action": "block"}')
        os.chmod(policy_file, 0o664)  # -rw-rw-r--
        error = _validate_policy_file(policy_file)
        assert error is not None
        assert "unsafe permissions" in error.lower()

    def test_rejects_too_large(self, tmp_path: Path) -> None:
        policy_file = tmp_path / "policy.json"
        # Create file larger than MAX_POLICY_SIZE
        policy_file.write_text("x" * (MAX_POLICY_SIZE + 1))
        os.chmod(policy_file, 0o644)
        error = _validate_policy_file(policy_file)
        assert error is not None
        assert "too large" in error.lower()


class TestSccManagedMode:
    """Tests for SCC-managed mode behavior."""

    def test_scc_managed_requires_policy_path(self, clean_env: None, tmp_path: Path) -> None:
        os.environ["SCC_MANAGED"] = "1"
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            policy, warning = load_policy()
            assert policy["action"] == "block"  # Falls back to default
            assert warning is not None
            assert "SCC_POLICY_PATH not set" in warning
        finally:
            del os.environ["SCC_MANAGED"]
            os.chdir(original_cwd)

    def test_scc_managed_with_valid_policy(self, clean_env: None, tmp_path: Path) -> None:
        policy_file = tmp_path / "policy.json"
        policy_file.write_text('{"action": "warn"}')
        os.chmod(policy_file, 0o644)

        os.environ["SCC_MANAGED"] = "1"
        os.environ["SCC_POLICY_PATH"] = str(policy_file)
        try:
            policy, warning = load_policy()
            assert policy["action"] == "warn"
            assert warning is None
        finally:
            del os.environ["SCC_MANAGED"]
            del os.environ["SCC_POLICY_PATH"]

    def test_scc_managed_rejects_invalid_policy(self, clean_env: None, tmp_path: Path) -> None:
        policy_file = tmp_path / "policy.json"
        policy_file.write_text('{"action": "warn"}')
        os.chmod(policy_file, 0o666)  # World-writable

        os.environ["SCC_MANAGED"] = "1"
        os.environ["SCC_POLICY_PATH"] = str(policy_file)
        try:
            policy, warning = load_policy()
            assert policy["action"] == "block"  # Falls back to default
            assert warning is not None
            assert "unsafe permissions" in warning.lower()
        finally:
            del os.environ["SCC_MANAGED"]
            del os.environ["SCC_POLICY_PATH"]
