---
name: validate
description: Validates SCC org/team configs (schema + invariant + advisory checks). Guides running SCC CLI validation.
argument-hint: [path-to-json]
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash, AskUserQuestion
---

# SCC Config Validate

Validate SCC organization and team configuration files with the same rigor as SCC's own validation pipeline.

## Validation Pipeline (Mirrors SCC)

SCC uses a strict two-step validation gate:

1. **Schema validation** - JSON Schema compliance
2. **Invariant validation** - Semantic rules and cross-field consistency
3. **Version compatibility** - schema_version and min_cli_version checks

This skill follows the same pipeline and adds advisory warnings for governance best practices.

## Flow

### Step 1: Determine Input

Get file path from `$ARGUMENTS` or ask user.

If no path provided, search for common config locations:
- `./org-config.json`
- `./scc/org-config.json`
- `./team-config.json`
- `./scc/team-config.json`

### Step 2: Read and Detect Type

Read the JSON file and detect config type:

| Detection | Config Type |
|-----------|-------------|
| Has `organization` field | Org config (org-v1) |
| Has `enabled_plugins`/`disabled_plugins` + `schema_version`, no `organization` | Team config |

### Step 3: Prefer SCC CLI When Available

**Check if SCC CLI is available:**
```bash
which scc
```

**If available, run native validation:**
```bash
# For org configs
scc org validate <path>

# For team configs
scc team validate <path>
```

The CLI provides the most accurate validation. Report its output directly.

### Step 4: Static Validation (If CLI Unavailable)

Perform manual validation checks grouped by category:

## Error Categories

### 1. Schema Errors (Hard Errors)

JSON Schema violations that make the config structurally invalid.

**Check:**
- `schema_version` equals `"1.0.0"` (const)
- Required fields exist:
  - Org: `schema_version`, `organization.name`, `organization.id`
  - Team: `schema_version`
- `organization.id` matches pattern `^[a-z0-9-]+$`
- Field types are correct (strings, arrays, objects, integers)
- Enum values are valid (`network_policy`, `safety_net.action`, etc.)
- Marketplace entries have correct `source` discriminator and required fields

**Report format:**
```
SCHEMA ERROR: <what's wrong>
  Path: <JSON path, e.g., organization.id>
  Expected: <correct format/value>
  Found: <actual value>
  Fix: <minimal correction>
```

### 2. Version Compatibility Errors (Hard Errors)

Version requirements that prevent the config from loading.

**Check:**
- `schema_version` must be `"1.0.0"` (current version)
- `min_cli_version` (if present) must be a valid semver and not higher than installed SCC

**Report format:**
```
VERSION ERROR: min_cli_version requires SCC >= <version>
  Your SCC version: <installed or unknown>
  Fix: Upgrade SCC or lower min_cli_version
```

### 3. Invariant Errors (Hard Errors)

Semantic rules enforced by SCC's invariant validator. **These block config loading.**

**For org configs, check:**

| Invariant | Condition | Error |
|-----------|-----------|-------|
| `additional_plugin_not_allowed` | Team profile has `additional_plugins` that don't match `defaults.allowed_plugins` (when allowlist present) | Plugin not allowed by org allowlist |
| `mcp_not_allowed` | Team profile has `additional_mcp_servers` that don't match `defaults.allowed_mcp_servers` (when allowlist present) | MCP server not allowed by org allowlist |
| `blocked_plugin_enabled` | `defaults.enabled_plugins` contains a plugin matching `security.blocked_plugins` | Blocked plugin in defaults |
| `invalid_plugin_ref` | Plugin reference doesn't match `name@marketplace` format | Invalid plugin reference |
| `marketplace_not_found` | Plugin references marketplace not in `marketplaces` section | Unknown marketplace |

**Report format:**
```
INVARIANT ERROR: <invariant name>
  Path: <JSON path>
  Issue: <description>
  Fix: <how to resolve>
```

**Allowlist matching rules:**
- If `defaults.allowed_plugins` is **omitted** → all plugins allowed (no check)
- If `defaults.allowed_plugins` is `[]` → NO plugins allowed (all additions fail)
- If `defaults.allowed_plugins` has patterns → only matching plugins allowed

Same logic for `allowed_mcp_servers`.

### 4. stdio MCP Errors (Hard Errors)

stdio MCP servers have strict security gates.

**Check:**
- If any team has stdio MCP servers AND `security.allow_stdio_mcp` is `false` or missing → **error**
- If `command` is not an absolute path (doesn't start with `/`) → **error**
- If `allowed_stdio_prefixes` is set AND command doesn't start with any prefix → **error**

**Report format:**
```
STDIO MCP ERROR: <issue>
  Team: <team name>
  Server: <MCP server name>
  Command: <command value>
  Fix: <correction>
```

## Advisory Warnings (Do Not Block)

These are governance best practices that don't prevent the config from loading but may cause confusion or runtime denials.

### Delegation Warnings

| Warning | Condition |
|---------|-----------|
| Team additions may be denied | Team has `additional_plugins` but team name not in `delegation.teams.allow_additional_plugins` |
| MCP additions may be denied | Team has `additional_mcp_servers` but team name not in `delegation.teams.allow_additional_mcp_servers` |
| Conflicting delegation | `delegation.projects.inherit_team_delegation = false` but team has `delegation.allow_project_overrides = true` |

**Report format:**
```
WARNING: <description>
  Team: <team name>
  Note: This won't cause validation failure, but additions will be denied at runtime.
```

### Configuration Warnings

| Warning | Condition |
|---------|-----------|
| Command not found | stdio MCP command doesn't exist on host (non-blocking; runs in container) |
| Network policy override may not apply | Team has `network_policy` override (currently not applied by effective config engine) |
| Session auto_resume override may not apply | Team has `session.auto_resume` override (may not take effect) |

## Step 5: Report Results

Group and present issues by severity:

```markdown
## Validation Results for: <filename>

Config type: <Org config | Team config>

### Hard Errors (must fix)

<list schema, version, and invariant errors>

### Warnings (advisory)

<list delegation and configuration warnings>

### Summary

- Errors: <count>
- Warnings: <count>
- Status: <VALID | INVALID>
```

If there are hard errors, config will **fail** `scc org/team validate`.

## Error Resolution Guidance

For each error, provide:
1. **What's wrong** - Clear description
2. **Why SCC cares** - Security/consistency reason
3. **Where** - JSON path
4. **Minimal fix** - Exact change needed

**Example:**
```
INVARIANT ERROR: additional_plugin_not_allowed

What: Plugin "custom-tool@team-plugins" in team "dev-team" is not allowed
Why: Org has defaults.allowed_plugins set; only matching patterns are permitted
Where: profiles.dev-team.additional_plugins[0]
Fix: Either:
  1. Add "custom-tool@*" or "*@team-plugins" to defaults.allowed_plugins
  2. Remove this plugin from the team's additional_plugins
  3. Move plugin to defaults.enabled_plugins (if all teams should have it)
```

## Quick Reference: SCC Validation Behavior

| Scenario | Result |
|----------|--------|
| Schema violation | Hard error, blocks loading |
| Invariant violation | Hard error, blocks loading |
| Delegation mismatch | **No error** - runtime denial |
| Plugin blocked by security | Runtime block (not validation error) |
| Allowlist mismatch in profile | **Hard error** (invariant) |
| Allowlist mismatch at runtime | Runtime denial |
