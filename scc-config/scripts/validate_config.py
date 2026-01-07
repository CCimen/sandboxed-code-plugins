#!/usr/bin/env python3
"""
SCC Config Validation Script

Validates SCC configuration files against their JSON schemas.
Used by PostToolUse hook to auto-validate after Edit/Write operations.

Exit codes:
  0 - Valid (or not an SCC config file)
  1 - Warning (valid but notable issues)
  2 - Invalid (schema validation failed)
"""

import json
import os
import re
import sys
from pathlib import Path

# Try to import jsonschema, gracefully handle if not available
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

# Try to import yaml parser
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def get_plugin_root() -> Path:
    """Get the plugin root directory."""
    # CLAUDE_PLUGIN_ROOT is set by Claude Code when running hooks
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if plugin_root:
        return Path(plugin_root)
    # Fallback: assume script is in scripts/ directory
    return Path(__file__).parent.parent


def get_edited_file() -> str | None:
    """Get the file path that was just edited from environment."""
    # Claude Code sets these for PostToolUse hooks
    tool_input = os.environ.get("TOOL_INPUT", "{}")
    try:
        input_data = json.loads(tool_input)
        return input_data.get("file_path") or input_data.get("path")
    except json.JSONDecodeError:
        return None


def is_scc_config(filepath: str) -> tuple[bool, str]:
    """
    Check if a file is an SCC config and determine its type.

    Returns:
        (is_config, config_type) where config_type is one of:
        'org', 'team', 'project', or '' if not a config
    """
    path = Path(filepath)
    name = path.name.lower()

    # Check by filename patterns
    if name.startswith("org") and name.endswith((".yaml", ".yml", ".json")):
        return True, "org"
    if name.startswith("team-config") and name.endswith(".json"):
        return True, "team"
    if name == ".scc.yaml" or name == ".scc.yml":
        return True, "project"
    if name == "team-config.json":
        return True, "team"

    # Check by path patterns
    path_str = str(path)
    if "/.scc/" in path_str or "\\.scc\\" in path_str:
        if name.endswith(".json"):
            return True, "team"

    return False, ""


def load_schema(config_type: str) -> dict | None:
    """Load the JSON schema for the given config type."""
    plugin_root = get_plugin_root()
    schema_map = {
        "org": "org-v1.schema.json",
        "team": "team-config.v1.schema.json",
    }

    schema_file = schema_map.get(config_type)
    if not schema_file:
        return None

    schema_path = plugin_root / "schemas" / schema_file
    if not schema_path.exists():
        return None

    try:
        with open(schema_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def load_config(filepath: str) -> tuple[dict | None, str]:
    """
    Load a config file.

    Returns:
        (config_dict, error_message)
    """
    path = Path(filepath)

    if not path.exists():
        return None, f"File not found: {filepath}"

    try:
        content = path.read_text()
    except OSError as e:
        return None, f"Cannot read file: {e}"

    # Try JSON first
    if path.suffix == ".json":
        try:
            return json.loads(content), ""
        except json.JSONDecodeError as e:
            return None, f"Invalid JSON: {e}"

    # Try YAML
    if path.suffix in (".yaml", ".yml"):
        if not HAS_YAML:
            return None, "YAML parser not available (install PyYAML)"
        try:
            return yaml.safe_load(content), ""
        except yaml.YAMLError as e:
            return None, f"Invalid YAML: {e}"

    return None, f"Unknown file type: {path.suffix}"


def validate_config(config: dict, schema: dict) -> list[str]:
    """
    Validate config against schema.

    Returns list of error messages (empty if valid).
    """
    if not HAS_JSONSCHEMA:
        # Can't validate without jsonschema, assume valid
        return []

    errors = []
    validator = jsonschema.Draft7Validator(schema)

    for error in validator.iter_errors(config):
        path = ".".join(str(p) for p in error.absolute_path) or "(root)"
        errors.append(f"{path}: {error.message}")

    return errors


def check_semantic_rules(config: dict, config_type: str) -> list[str]:
    """
    Check semantic rules beyond JSON schema.

    Returns list of warning messages.
    """
    warnings = []

    if config_type == "org":
        # Check org ID pattern
        org_id = config.get("organization", {}).get("id", "")
        if org_id and not re.match(r"^[a-z0-9-]+$", org_id):
            warnings.append(
                f"organization.id '{org_id}' should be lowercase with hyphens only"
            )

        # Check for contradictions in allowed/blocked
        blocked = set(config.get("security", {}).get("blocked_plugins", []))
        allowed = set(config.get("defaults", {}).get("allowed_plugins", []))
        overlap = blocked & allowed
        if overlap:
            warnings.append(
                f"Plugins both blocked and allowed: {', '.join(overlap)}"
            )

    elif config_type == "team":
        # Check plugin format
        for plugin in config.get("enabled_plugins", []):
            if "@" not in plugin:
                warnings.append(
                    f"Plugin '{plugin}' should be in format 'name@marketplace'"
                )

        # Check marketplace references
        marketplaces = set(config.get("marketplaces", {}).keys())
        for plugin in config.get("enabled_plugins", []):
            if "@" in plugin:
                mp = plugin.split("@")[1]
                # Only warn if not a common/default marketplace
                if mp not in marketplaces and mp not in ("default", "official"):
                    warnings.append(
                        f"Plugin '{plugin}' references undefined marketplace '{mp}'"
                    )

    return warnings


def main() -> int:
    """Main entry point."""
    # Get the file that was edited
    filepath = get_edited_file()
    if not filepath:
        # No file info, nothing to validate
        return 0

    # Check if it's an SCC config
    is_config, config_type = is_scc_config(filepath)
    if not is_config:
        # Not an SCC config, nothing to do
        return 0

    # Load the config
    config, error = load_config(filepath)
    if error:
        print(f"[scc-config] Error loading {filepath}: {error}", file=sys.stderr)
        return 2

    if config is None:
        return 0

    # Load schema (if available for this type)
    schema = load_schema(config_type)

    # Validate against schema
    errors = []
    if schema:
        errors = validate_config(config, schema)

    # Check semantic rules
    warnings = check_semantic_rules(config, config_type)

    # Report results
    if errors:
        print(f"[scc-config] Validation errors in {filepath}:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 2

    if warnings:
        print(f"[scc-config] Warnings in {filepath}:", file=sys.stderr)
        for warn in warnings:
            print(f"  - {warn}", file=sys.stderr)
        return 1

    # Valid
    print(f"[scc-config] {filepath} is valid ({config_type} config)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
