# SCC Inheritance Cheat Sheet

Quick reference for understanding SCC configuration inheritance and decisions.

## Configuration Layers

```
┌─────────────────────────────────────────┐
│           Org Config (org-v1)           │
│  • security.* (immutable boundaries)    │
│  • defaults.* (baseline settings)       │
│  • delegation.* (who can add what)      │
│  • profiles.* (team configurations)     │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│    Team Profile or Team Config          │
│  • additional_plugins                   │
│  • additional_mcp_servers               │
│  • session overrides                    │
│  • delegation.allow_project_overrides   │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Project .scc.yaml               │
│  • additional plugins (if delegated)    │
│  • additional MCP (if delegated)        │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Effective Config                │
│  (What actually runs)                   │
└─────────────────────────────────────────┘
```

## Decision Terms

| Term | Meaning | Mutability |
|------|---------|------------|
| **Blocked** | Security boundary match | Immutable |
| **Denied** | Delegation/allowlist rejection | Changeable |
| **Disabled** | In `defaults.disabled_plugins` | Re-enableable |
| **Effective** | Final computed value | Runtime result |

## Security Blocks (Immutable)

These cannot be overridden by teams or projects:

```json
{
  "security": {
    "blocked_plugins": ["*-experimental"],
    "blocked_mcp_servers": ["*.untrusted.com"],
    "allow_stdio_mcp": false,
    "allowed_stdio_prefixes": ["/usr/local/bin"]
  }
}
```

## Delegation Chain

```
Can team add plugins?
  └─ Is team in delegation.teams.allow_additional_plugins?
       ├─ No  → DENIED (not delegated)
       └─ Yes → Does plugin match defaults.allowed_plugins?
                  ├─ Field missing → ALLOWED (no allowlist)
                  ├─ Field is []   → DENIED (block all)
                  └─ Has patterns  → Match? ALLOWED : DENIED

Can project add plugins?
  └─ Is delegation.projects.inherit_team_delegation true?
       ├─ No  → DENIED
       └─ Yes → Is team's delegation.allow_project_overrides true?
                  ├─ No  → DENIED
                  └─ Yes → Same allowlist check as team
```

## Merge Behavior

| Field Type | Behavior |
|------------|----------|
| Plugins (enabled) | Accumulate (union of all layers) |
| Plugins (disabled) | Accumulate, remove from enabled |
| MCP servers | Accumulate (union of all layers) |
| Security blocks | Apply to all (immutable) |
| Session timeout | Last-wins (team/project override) |
| Network policy | Org defaults only* |
| Cache TTL | Org defaults only |

*Team `network_policy` may not currently affect effective config.

## Allowlist Semantics

| Field State | Meaning |
|-------------|---------|
| **Missing** | No allowlist → allow all additions |
| **Empty `[]`** | Block all additions |
| **Has patterns** | Only allow matching additions |

```json
// No allowlist (allow all)
{
  "defaults": {
    "enabled_plugins": ["..."]
    // allowed_plugins is OMITTED
  }
}

// Block all additions
{
  "defaults": {
    "allowed_plugins": []
  }
}

// Allowlist mode
{
  "defaults": {
    "allowed_plugins": ["core-*", "*@official-plugins"]
  }
}
```

## stdio MCP Gates

All must pass for stdio MCP to work:

1. `security.allow_stdio_mcp = true`
2. `command` starts with `/` (absolute path)
3. If `allowed_stdio_prefixes` set → command under one prefix

## Why Something Might Not Work

| Symptom | Likely Cause |
|---------|--------------|
| Plugin not appearing | Blocked, denied, or marketplace missing |
| Team additions ignored | Not delegated or not in allowlist |
| Project additions ignored | `inherit_team_delegation = false` or `allow_project_overrides = false` |
| MCP server not connecting | Blocked, stdio gates failed, or URL pattern mismatch |
| Config changes not taking effect | Cache TTL hasn't expired |

## Quick Debugging

1. **Check security blocks first** - These are absolute
2. **Check delegation** - Is the team/project allowed to add?
3. **Check allowlists** - If present, does addition match patterns?
4. **Check marketplace** - Does the referenced marketplace exist?
5. **Check cache** - Has `cache_ttl_hours` passed since last fetch?
