---
name: team
description: Interactive wizard to create/edit SCC team-managed team config files (team-config v1). Outputs valid JSON.
argument-hint: [create|edit] [optional-path]
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Grep, Glob, AskUserQuestion
---

# SCC Team Config Wizard

You create or edit a team-config file conforming to `supporting/team-schema.json`.

> **Important:** You only need a team-config file if your org config uses `config_source` for this team (team-managed model). If your team is org-managed (no `config_source`), you don't need this wizard — the org admin configures plugins directly in the org config.

## Output Contract (ALWAYS)

1. Short summary (3-8 bullets)
2. Exactly ONE final JSON code block
3. Ask before writing file

## Terminology

| User-Facing Term | Old Term (Never Use) |
|------------------|---------------------|
| **Team-managed** | Federated |
| **Org-managed** | Centralized |

## Context: When Team Configs Are Needed

Team configs are used by **team-managed teams** — teams that maintain their own plugin/marketplace configuration rather than having the org admin manage it inline.

**You need a team-config file when:**
- The org config has a `config_source` entry for your team (team-managed)
- You want to independently manage your team's plugins

**You do NOT need a team-config file when:**
- Your team is org-managed (no `config_source` in org config)
- The org admin manages your plugin list in `profiles.<team>.additional_plugins`

**Key points:**
- The org config must have a `config_source` for this team pointing to where this file is hosted
- The org grants trust to the team via `trust` settings
- Team configs can enable/disable plugins and optionally define marketplaces (if trusted)

**Example org profile for a team-managed team:**
```json
"profiles": {
  "platform": {
    "config_source": {
      "source": "github",
      "owner": "myorg",
      "repo": "scc-team-configs",
      "branch": "main",
      "path": "teams/platform/team-config.json"
    },
    "trust": {
      "inherit_org_marketplaces": true,
      "allow_additional_marketplaces": false
    }
  }
}
```

## Auto-Context Detection (P2)

If SCC is configured locally, try to read context automatically:

```
# Check ~/.config/scc/config.json for organization_source
# Check ~/.cache/scc/org_config.json for cached org config
```

If found, extract:
- Available marketplaces from org config
- Trust settings for this team
- Any existing team profile settings

## Flow

### Step 0: Determine Mode

If `$ARGUMENTS` contains a file path:
- If `edit` + path: Read and summarize existing config
- If `create` + path: Will write to this path
- If just path: Detect if file exists (edit) or not (create)

Otherwise, ask:
- **Create new team config**
- **Edit existing team config** (provide path)

### Step 1: Gather Team Context

Collect information about the team's position in the org:

1. **Team name** (for context and documentation)
2. **Org marketplaces available?** - Which marketplaces does the org define?
3. **Is team trusted to add marketplaces?** - Does org's `trust.allow_additional_marketplaces = true`?
4. **Marketplace source patterns** - If trusted, what URL patterns are allowed?

This context helps guide appropriate suggestions.

### Step 2: Collect enabled_plugins

Collect plugin references that this team wants to enable.

**Format:** `plugin-name@marketplace`

Example:
```json
"enabled_plugins": [
  "changelog-generator@sandboxed-code-official",
  "code-review@sandboxed-code-official"
]
```

**Guidance:**
- Always use `plugin@marketplace` format for clarity
- Plugins must come from either org-inherited marketplaces or team-defined marketplaces (if trusted)
- Check that referenced marketplaces exist

### Step 3: Collect disabled_plugins

Collect glob patterns for plugins to disable (removes from org defaults).

Example:
```json
"disabled_plugins": [
  "legacy-tool@*",
  "*-deprecated"
]
```

**Note:** disabled_plugins removes plugins from the org's `defaults.enabled_plugins` - it doesn't block plugins the team is adding.

### Step 4: Marketplaces (Only If Trusted)

**Guardrail:** Before showing marketplace options, verify the team's trust settings:
- Check `profiles.<team>.trust.allow_additional_marketplaces` in org config
- If `false` or missing, skip this step and explain why

If the org's trust grants allow additional marketplaces (`allow_additional_marketplaces: true`):

Loop to add team-defined marketplaces:

1. Ask **name** (used in `plugin@marketplace` references)
2. Ask **source type**: github / git / url / directory
3. Collect fields based on type:

| Type | Required Fields | Optional Fields |
|------|-----------------|-----------------|
| github | owner, repo | branch, path, headers |
| git | url | branch, path |
| url | url | headers, materialization_mode |
| directory | path | - |

**Important constraints:**
- Marketplace URLs must match org's `trust.marketplace_source_patterns` (if set)
- `git` source allows both `https://` and `git@` SSH URLs
- `url` source requires `https://` (HTTP forbidden)

If not trusted, explain:
> Your org profile has `allow_additional_marketplaces: false`. You can only use marketplaces defined by the org. Contact your org admin to request additional marketplace access.

### Step 5: Review + Output JSON

**Summary:**
- Team name
- Plugins enabled (count and list)
- Plugins disabled (patterns)
- Marketplaces (if any)

**Validation checks:**
- `schema_version` is `"1.0.0"`
- All plugin references use `plugin@marketplace` format
- Referenced marketplaces exist (either inherited or team-defined)
- Team-defined marketplace URLs match allowed patterns (if applicable)

**Output:**
```json
{
  "$schema": "https://scc-cli.dev/schemas/team-config.v1.json",
  "schema_version": "1.0.0",
  "enabled_plugins": [...],
  "disabled_plugins": [...],
  "marketplaces": {...}
}
```

**Offer to write:**
Ask for confirmation before writing to file. Suggest path if not provided:
- `team-config.json` (in current directory)
- `scc/team-config.json` (if in a repo root)

## Edit Mode

1. Read existing JSON file
2. Validate it conforms to team-config schema
3. Summarize current config:
   - Enabled plugins (list)
   - Disabled plugins (patterns)
   - Marketplaces (names and sources)
4. Ask what to modify:
   - Add/remove enabled plugins
   - Add/remove disabled plugin patterns
   - Add/remove/edit marketplaces (if trusted)
5. Apply changes
6. Re-validate and output final JSON
7. Offer to write back

## Key Terminology

| Term | Definition |
|------|------------|
| **Team-managed** | Team that maintains its own team-config file (NOT "federated") |
| **Org-managed** | Team whose plugins are managed in org config (NOT "centralized") |
| **Inherited marketplaces** | Marketplaces defined in org config that team can use |
| **Team-defined marketplaces** | Marketplaces the team adds (requires trust grant) |
| **Trust grant** | Org's permission for team to add marketplaces |

## Team Config Checklist (For Team-managed Teams)

When generating a team config, also output this checklist:

```markdown
## Team-managed Team Checklist

1. [ ] Host this file at: `<suggest URL based on org config_source>`
2. [ ] Ensure raw URL is accessible (for private repos, configure auth)
3. [ ] Verify org config has matching `config_source` for this team
4. [ ] Test with: `scc team validate <path-to-file>`
```

## Reference Files

- Schema: `supporting/team-schema.json`
- Question bank: `supporting/team-questions.md`
- Example: `supporting/examples/team-config.json`
