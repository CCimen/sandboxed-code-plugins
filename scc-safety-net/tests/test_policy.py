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
    _extract_safety_net,
    _get_policy_paths,
    _load_json,
    get_action,
    is_rule_enabled,
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
            policy = load_policy()
            assert policy["action"] == "block"
        finally:
            os.chdir(original_cwd)

    def test_env_var_priority(self, env_policy_path: Path, block_policy: dict[str, Any]) -> None:
        block_policy["action"] = "warn"  # Distinguish from default
        env_policy_path.write_text(json.dumps(block_policy))
        policy = load_policy()
        assert policy["action"] == "warn"

    def test_ensures_action_key(self, env_policy_path: Path) -> None:
        env_policy_path.write_text('{"block_force_push": true}')
        policy = load_policy()
        assert "action" in policy
        assert policy["action"] == "block"


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
        policy = {"block_force_push": True}
        assert is_rule_enabled(policy, "block_force_push") is True

    def test_disabled_rule(self) -> None:
        policy = {"block_force_push": False}
        assert is_rule_enabled(policy, "block_force_push") is False

    def test_missing_rule_defaults_true(self) -> None:
        policy = {}
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
