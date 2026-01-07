# Edit Config - Maintenance Flow

Edit existing SCC configuration files through a menu-driven interface.

## Design Principle

**"Menu Loop" over "Wizard Re-run"**
- Load existing config and show summary
- Offer targeted operations
- Return to menu after each change
- Exit when user is done

## Entry Point

Usage: `/scc-config:edit [path]`

If path not provided, auto-detect from:
1. `~/.config/scc/org.yaml`
2. `./.scc/team-config.json`
3. `./.scc.yaml`

## Step 1: Load & Summarize

Read the config file and display a human-readable summary:

**For Org Config:**
```
Current Organization Configuration
==================================
Organization: Acme Corp (acme-corp)
Governance: Delegated
Teams can add plugins: Matching @acme/*
Teams can add MCP servers: No
Federated teams: frontend, backend, ml-team
Safety net: Block destructive git commands
```

**For Team Config:**
```
Current Team Configuration
==========================
Marketplaces: team-plugins (GitHub: acme/team-plugins)
Enabled plugins: 3
  - code-review@team-plugins
  - test-runner@team-plugins
  - deploy-helper@team-plugins
Disabled patterns: legacy-*
```

**For Project Config:**
```
Current Project Configuration
=============================
Additional plugins: custom-tool@marketplace
Session timeout: 8 hours
Auto-resume: enabled
```

## Step 2: Menu Loop

Present operation menu based on config type:

**Org Config Menu:**
```
Question: "What would you like to do?"
Options:
- Add a federated team
- Remove a federated team
- Change delegation rules
- Update security settings
- Add/remove blocked plugins
- Edit a team profile
- View full config (YAML)
- Other (describe change)
- Done (exit)
```

**Team Config Menu:**
```
Question: "What would you like to do?"
Options:
- Add a marketplace
- Remove a marketplace
- Enable plugins
- Disable plugins
- Remove disabled patterns
- View full config (JSON)
- Other (describe change)
- Done (exit)
```

**Project Config Menu:**
```
Question: "What would you like to do?"
Options:
- Add plugins
- Remove plugins
- Change session timeout
- Toggle auto-resume
- View full config (YAML)
- Other (describe change)
- Done (exit)
```

## Operation Handlers

### "Add a federated team" (Org)
```
Question: "Team name?"
[Free text]

Question: "Config source type?"
Options:
- GitHub repo
- Git URL
- HTTPS URL
- Other (describe)

[Source-specific questions based on selection]

Question: "Trust level?"
Options:
- Inherit org marketplaces only [Recommended]
- Can add from approved patterns
- Full marketplace autonomy
```
-> Show diff, confirm, apply, return to menu

### "Change delegation rules" (Org)
```
Question: "What should teams be allowed to add?"
Options:
- No changes to current rules
- More permissive (show current + expand options)
- More restrictive (show current + restrict options)
- Custom (describe the change)
```

### "Add a marketplace" (Team)
```
Question: "Marketplace source type?"
Options:
- GitHub repo
- Git URL
- HTTPS URL
- Local directory
- Other
```
-> Follow init-team.md marketplace flow

### "Enable plugins" (Team)
```
Question: "Plugin(s) to enable?"
Options:
- Enter plugin names (plugin@marketplace format)
- List available from marketplaces
- Other (describe)
```

### "Other (describe change)"
For any config type:
1. Accept free-text description
2. Parse intent and generate config diff
3. Show proposed changes:
```
Proposed change:
  profiles:
    ml-team:
+     delegation:
+       allow_additional_mcp_servers: true
```
4. Ask: "Apply this change?"

## Menu Loop Principle

After EVERY operation:
1. Show the diff of what changed
2. Ask for confirmation
3. Apply change to in-memory config
4. Validate against schema
5. If valid: write to file, show success
6. If invalid: show errors, offer to revert
7. **Return to menu** (don't exit)

Only exit when user selects "Done (exit)"

## State Management

Track during session:
- `currentConfig`: Original loaded config
- `draftConfig`: Working copy with changes
- `pendingChanges`: List of changes for diff display
- `configPath`: File path being edited

## Diff Display

Before each write, show what changed:
```
Changes to apply:
  delegation:
    teams:
-     allow_additional_plugins: ["@acme/*"]
+     allow_additional_plugins: ["@acme/*", "@partner/*"]
```

## Validation

Before every write:
- Org configs: Validate against org-v1.schema.json
- Team configs: Validate against team-config.v1.schema.json
- Project configs: Basic structure validation

If validation fails:
```
Validation Error:
- profiles.ml-team.config_source.url: Must start with "https://"

Options:
- Fix and retry
- Discard this change
- View full error details
```
