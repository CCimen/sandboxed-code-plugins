# Validate Config

Validate SCC configuration files against their JSON schemas.

## Usage

```
/scc-config:validate [path]
```

If path not provided, auto-detect and validate all found configs:
1. `~/.config/scc/org.yaml`
2. `./.scc/team-config.json`
3. `./.scc.yaml`

## Detection Logic

Determine config type by:
1. **Filename**:
   - `org*.yaml` or `org*.json` -> org config
   - `team-config*.json` -> team config
   - `.scc.yaml` or `.scc.json` -> project config

2. **Content structure**:
   - Has `organization` field -> org config
   - Has `schema_version` as integer -> team config
   - Has `additional_plugins` -> project config

## Validation Process

### For Org Configs
1. Parse YAML/JSON
2. Validate against `schemas/org-v1.schema.json`
3. Check semantic rules:
   - `organization.id` matches pattern `^[a-z0-9-]+$`
   - `schema_version` matches `^1\.[0-9]+\.[0-9]+$`
   - All `config_source` URLs are valid
   - No blocked plugins in allowed lists (contradiction check)

### For Team Configs
1. Parse JSON
2. Validate against `schemas/team-config.v1.schema.json`
3. Check semantic rules:
   - `schema_version` is exactly 1
   - Plugin format matches `plugin-name@marketplace`
   - Marketplace names are unique
   - Referenced marketplaces exist in config

### For Project Configs
1. Parse YAML
2. Basic structure validation (no formal schema)
3. Check:
   - `session.timeout_hours` is 1-24 if present
   - Plugin names are valid format

## Output Format

### Success
```
Validation Results
==================
File: ~/.config/scc/org.yaml
Type: Organization Config
Status: VALID

Schema: org-v1.schema.json
Fields validated: 12
Warnings: 0
```

### Warnings (valid but notable)
```
Validation Results
==================
File: ./.scc/team-config.json
Type: Team Config
Status: VALID (with warnings)

Warnings:
- Line 5: Plugin "legacy-tool@default" may be deprecated
- Line 12: Marketplace "internal" has no authentication configured
```

### Errors
```
Validation Results
==================
File: ~/.config/scc/org.yaml
Type: Organization Config
Status: INVALID

Errors:
- Line 3: "organization.id" must match pattern ^[a-z0-9-]+$
  Found: "Acme Corp" (contains uppercase and space)
  Suggestion: Use "acme-corp" instead

- Line 15: "profiles.backend.config_source.url" must be https://
  Found: "http://internal.git/config.json"
  Suggestion: Change to https:// or use "git" source type

- Line 22: Missing required field "schema_version"
  Suggestion: Add "schema_version": "1.0.0" at root level
```

## Quick Fix Suggestions

When errors are found, offer to fix:
```
Question: "Would you like me to fix these issues?"
Options:
- Yes, fix all automatically [Recommended]
- Show me fixes one by one
- No, I'll fix manually
```

For automatic fixes:
1. Generate corrected config
2. Show diff
3. Ask for confirmation before writing

## Integration with Hooks

This validation logic is also used by:
- PostToolUse hook (auto-validate after edits)
- init-*.md commands (validate before writing)
- edit.md command (validate before saving)
