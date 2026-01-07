# Organization Config Wizard

Create an SCC organization configuration file (org.yaml) through interactive conversation.

## Design Principle

**"Governance Modeling" over "Inventory Management"**
- Ask about trust levels and delegation policies
- Don't require admins to know what each team needs upfront
- "I don't know yet" is a valid, common choice

## Wizard Flow

### Phase 1: Organization Identity

Ask these questions (can combine into one AskUserQuestion):

1. **Organization name** (free text input)
2. **Organization ID** - auto-suggest lowercase-kebab from name
   - Example: "Acme Corporation" -> suggest "acme-corp"

### Phase 2: Governance Model (KEY DECISION)

```
Question: "How should teams access tools and plugins?"
Options:
- Centralized (admins choose all plugins for everyone)
- Delegated (teams choose within guardrails you define) [Recommended]
- Federated (teams maintain their own config repos)
- Other (describe your governance model)
```

### Phase 3: "I Don't Know Yet" Path

```
Question: "Do you know what specific tools teams will need?"
Options:
- Yes, I'll configure specifics now
- Not sure yet - set safe defaults that teams can extend [Common choice]
- Other (describe)
```

**If "Not sure yet":**
```
Question: "How strict should the default guardrails be?"
Options:
- Strict (no additional plugins, no MCP servers)
- Balanced (teams can add plugins by pattern, no MCP) [Recommended]
- Flexible (teams can add most plugins and some MCP servers)
- Other (describe your security posture)
```

### Phase 4: Delegation Rules (if Delegated/Federated)

```
Question: "How should teams add their own tools?"
Options:
- They can't (central control only)
- From org-approved patterns (e.g., @myorg/*)
- From any trusted marketplace [Recommended]
- Full autonomy (teams decide everything)
- Other (describe)
```

```
Question: "Should teams be able to add MCP servers?"
Options:
- No (most secure) [Default]
- Only from approved patterns
- Yes, teams can define their own
- Other (describe your MCP policy)
```

### Phase 5: Team Federation (if Federated chosen)

```
Question: "Where do teams store their config files?"
Options:
- Per-team GitHub repos [Most common]
- Per-team GitLab repos
- Central monorepo with team directories
- Custom URL endpoints
- Other (describe)
```

For each federated team, collect:
- Team name (free text)
- Config source (GitHub owner/repo OR Git URL OR HTTPS URL)
- Trust level:
  - Inherit org marketplaces only [Recommended]
  - Can add from approved patterns
  - Full marketplace autonomy

Repeat: "Add another federated team?"

### Phase 6: Security Baseline

```
Question: "Safety net for destructive git commands?"
Options:
- Block all destructive commands (safest) [Default]
- Warn but allow
- Disabled
- Other (custom safety rules)
```

### Phase 7: Review & Generate

1. Show **Policy Sentence Summary**:
```
Configuration Summary:
- Teams may add plugins matching: @myorg/*
- Teams may add MCP servers: No
- Federated teams: frontend, backend, ml-team
- Trust level: Official marketplaces only
- Safety net: Block destructive git commands
```

2. Show YAML preview (full config)

3. Ask for output location (see init.md)

4. Validate against org-v1.schema.json before writing

5. After writing, generate **"Next Steps for Teams"** snippet:
```
Next Steps for Team Leads:
1. Create .scc/team-config.json in your repository
2. Run: /scc-config:init-team
3. Or manually add:
   {
     "schema_version": 1,
     "enabled_plugins": ["your-plugin@marketplace"]
   }
```

6. Remind: "Restart your SCC session to apply changes"

## Schema Reference

Use the bundled `schemas/org-v1.schema.json` for:
- Field validation
- Property descriptions for help text
- Enum values for option lists

Key fields to populate:
- `schema_version`: "1.0.0"
- `organization.name`, `organization.id`
- `security.safety_net`
- `defaults.allowed_plugins`, `defaults.allowed_mcp_servers`
- `delegation.teams.allow_additional_plugins`
- `delegation.teams.allow_additional_mcp_servers`
- `profiles` (for federated teams with `config_source`)
