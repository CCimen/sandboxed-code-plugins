---
name: explain
description: Explains SCC configuration inheritance, delegation, and why plugins/MCP servers are blocked or denied.
argument-hint: [optional-team] [optional-plugin-or-server]
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, AskUserQuestion
---

# SCC Config Explain

Explain SCC configuration behavior, inheritance, and why things are blocked, denied, or effective.

## Response Mode

**Default: Short answer mode** — Give the direct answer first, then offer "Show full reasoning" if user wants details.

```
Short answer: Plugin X is denied because team 'backend' is not in
delegation.teams.allow_additional_plugins.

To fix: Add "backend" to delegation.teams.allow_additional_plugins

Want full reasoning? [y/N]
```

## What This Skill Explains

1. **Inheritance model** - How org defaults → team → project merge
2. **Blocked vs Denied vs Disabled** - Why something isn't available
3. **Effective configuration** - What actually applies for a team/project
4. **Delegation chains** - Why additions succeed or fail

## Terminology

| User-Facing Term | Old Term (Never Use) |
|------------------|---------------------|
| **Team-managed** | Federated |
| **Org-managed** | Centralized |
| **Mixed** | Hybrid |

> **Note:** You may still see "federated" in schemas/docs; the wizard uses "team-managed" for clarity.

## Key Concepts (Use Correct Terminology)

### First-Class Terms

| Term | Definition | Source |
|------|------------|--------|
| **Blocked** | Matches `security.blocked_plugins` or `security.blocked_mcp_servers` | Org security section (immutable) |
| **Denied** | Failed delegation check OR allowlist check | Runtime decision |
| **Disabled** | Matches `defaults.disabled_plugins` | Org defaults (can be re-enabled) |
| **Delegated** | Team/project is allowed to add by `delegation.*` rules | Org delegation section |
| **Allowed** | Matches `defaults.allowed_*` patterns (if allowlist present) | Org defaults |
| **Effective** | Final computed value after all merges | Runtime result |

### Critical Distinctions

**Blocked vs Denied:**
- **Blocked** = Security boundary, absolutely cannot use, immutable
- **Denied** = Governance decision, could be enabled with config changes

**Allowlist mismatches:**
- In **org config validation**: Hard error (blocks loading)
- At **runtime** (project additions): Denied (tracked in `denied_additions`)

## Inheritance Model

### Merge Layers

```
Layer 1: Org config (org-v1)
   ↓ (apply defaults)
Layer 2: Team profile OR team-managed team-config
   ↓ (if delegation allows)
Layer 3: Project .scc.yaml additions
   ↓
Effective config (what actually runs)
```

### Merge Behavior by Field

| Field | Merge Rule |
|-------|------------|
| `enabled_plugins` | Accumulate (union) |
| `disabled_plugins` | Accumulate, then remove from enabled |
| `additional_mcp_servers` | Accumulate (union) |
| `security.blocked_*` | Immutable, apply to all layers |
| `session.timeout_hours` | Last-wins (team/project can override) |
| `session.auto_resume` | Currently org defaults only |
| `network_policy` | Currently org defaults only |
| `cache_ttl_hours` | Org defaults only |

### What Doesn't Override (Important Gotcha)

Currently, `compute_effective_config()` does **not** apply:
- Team-level `network_policy` override
- Team-level `session.auto_resume` override

These fields exist in the schema but may not affect the effective config.

## Workflow

### Step 1: Gather Context

Ask for relevant information:
- Org config path (or content)
- Team name (if asking about a specific team)
- Plugin or MCP server name (if asking "why is X blocked/denied?")

### Step 2: Read Configs

If file paths provided:
- Read org config
- Read team config (if team-managed)
- Read project .scc.yaml (if applicable)

### Step 3: Analyze and Explain

Based on the question type:

#### "What are the effective plugins for team X?"

1. Start with `defaults.enabled_plugins`
2. Remove any matching `defaults.disabled_plugins`
3. Add team's `additional_plugins` (if delegated and allowed)
4. Remove any matching `security.blocked_plugins`
5. List the result

#### "Why is plugin X blocked?"

Check in order:
1. Does it match `security.blocked_plugins`? → **Blocked** (immutable)
2. Does it match `defaults.disabled_plugins`? → **Disabled** (can re-enable)
3. Is team not in `delegation.teams.allow_additional_plugins`? → **Denied** (not delegated)
4. Does it not match `defaults.allowed_plugins`? → **Denied** (not in allowlist)

Report the **first** matching reason.

#### "Why is MCP server X blocked?"

Check in order:
1. Does it match `security.blocked_mcp_servers`? → **Blocked**
2. Is it stdio type and `allow_stdio_mcp = false`? → **Blocked** (stdio gate)
3. Is stdio command not absolute path? → **Blocked** (security)
4. Is stdio command outside `allowed_stdio_prefixes`? → **Blocked** (prefix gate)
5. Is team not in `delegation.teams.allow_additional_mcp_servers`? → **Denied**
6. Does URL not match `defaults.allowed_mcp_servers`? → **Denied**

#### "Explain delegation for team X"

1. Show team's position in `delegation.teams.allow_additional_plugins`
2. Show team's position in `delegation.teams.allow_additional_mcp_servers`
3. Show `delegation.projects.inherit_team_delegation` status
4. Show team's `delegation.allow_project_overrides` setting
5. Explain what the team and its projects can/cannot add

### Step 4: Output Explanation

**Default: Short answer mode.** Structure the response:

```markdown
## Short Answer

<direct 1-2 sentence answer>

## To Fix (Copy/Paste Ready)

<JSON snippet with exact path and value to change>

---
Want full reasoning? [y/N]
```

**If user requests full reasoning:**

```markdown
## Explanation: <question summary>

### Context
<org name, team name, relevant settings>

### Answer
<direct answer to the question>

### How SCC Determines This
<step-by-step reasoning>

### What to Change (if applicable)
<JSON path and modification to change the behavior>
```

## Copy/Paste Fix Suggestions

Always provide ready-to-use JSON snippets for fixes. Examples:

**Allow a plugin pattern:**
```json
// Add to defaults.allowed_plugins
{
  "defaults": {
    "allowed_plugins": ["*@official-plugins", "core-*"]
  }
}
```

**Delegate plugin additions to a team:**
```json
// Add team to delegation.teams.allow_additional_plugins
{
  "delegation": {
    "teams": {
      "allow_additional_plugins": ["*"]  // or ["team-a", "team-b"]
    }
  }
}
```

**Enable project overrides:**
```json
// Step 1: Enable project inheritance
{
  "delegation": {
    "projects": { "inherit_team_delegation": true }
  }
}

// Step 2: Allow project overrides for specific team
{
  "profiles": {
    "backend": {
      "delegation": { "allow_project_overrides": true }
    }
  }
}
```

**Remove a plugin from blocked list:**
```json
// Remove pattern from security.blocked_plugins
// Before: ["*-experimental", "*-deprecated", "specific-plugin"]
// After:
{
  "security": {
    "blocked_plugins": ["*-experimental", "*-deprecated"]
  }
}
```

**Grant team marketplace trust:**
```json
// Enable team to add marketplaces
{
  "profiles": {
    "ai-team": {
      "trust": {
        "allow_additional_marketplaces": true,
        "marketplace_source_patterns": ["https://github.com/myorg/*"]
      }
    }
  }
}
```

## Common Questions and Answers

### Q: "Why can't team X add plugins?"

**Check:**
1. Is team in `delegation.teams.allow_additional_plugins`?
2. If delegated, does plugin match `defaults.allowed_plugins` (if set)?
3. Is plugin in `security.blocked_plugins`?

**Answer template:**
> Team "{team}" cannot add plugins because: {reason}.
> To enable: {change to make}.

### Q: "What's the difference between blocked and denied?"

**Answer:**
> - **Blocked**: Security boundary in `security.blocked_*`. Cannot be overridden by anyone. Immutable.
> - **Denied**: Governance decision. Either delegation rules or allowlist rules prevented it. Can be changed by org admin.

### Q: "Why didn't my team config changes take effect?"

**Check:**
1. Is team team-managed? Is `config_source` correct and accessible?
2. Did cache expire? (Check `defaults.cache_ttl_hours`)
3. Are the plugins properly formatted (`plugin@marketplace`)?
4. Does marketplace exist?
5. Are additions delegated and allowed?

**Quick fix if config seems stale:**
> If you changed the org config and it still acts old, clear the cache:
> ```
> rm ~/.cache/scc/org_config.json ~/.cache/scc/cache_meta.json
> ```
> Then rerun your command.

### Q: "Why is `blocked_mcp_servers` not blocking a plugin's MCP?"

**Answer:**
> `security.blocked_mcp_servers` only checks **explicitly-declared** MCP servers in org/team/project configs. It does **not** inspect MCP servers bundled inside marketplace plugins. This is intentional - plugin authors control their bundled servers.

## Cheatsheet Reference

See `supporting/explain-cheatsheet.md` for a quick reference card.
