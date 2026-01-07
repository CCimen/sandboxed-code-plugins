# Explain Config

Show the effective SCC configuration with full inheritance chain explanation.

## Usage

```
/scc-config:explain
```

## Purpose

SCC configs have a 3-layer inheritance:
1. **Organization** (org.yaml) - Security boundaries, defaults
2. **Team** (team-config.json) - Team-specific plugins, marketplaces
3. **Project** (.scc.yaml) - Project-specific overrides

This command shows the **merged effective config** and explains which layer set each value.

## Discovery

Look for configs in order:
1. `~/.config/scc/org.yaml` (or `$SCC_ORG_CONFIG`)
2. `./.scc/team-config.json` (or closest parent directory)
3. `./.scc.yaml` (current directory)

## Output Format

### Effective Configuration
```
Effective SCC Configuration
===========================

Organization: Acme Corp (acme-corp)
  Source: ~/.config/scc/org.yaml

Team Profile: backend
  Source: ~/.config/scc/org.yaml (profiles.backend)

Security Boundaries (from org - cannot be overridden):
  - Blocked plugins: *-malicious-*, untrusted-*
  - Blocked MCP servers: *.evil.com/*
  - Allow stdio MCP: No
  - Safety net: Block destructive git commands

Effective Plugins:
  From org defaults:
    - scc-safety-net@sandboxed-code-official

  From team config (.scc/team-config.json):
    + code-review@team-plugins
    + test-runner@team-plugins

  From project (.scc.yaml):
    + custom-tool@marketplace

  Disabled (by team):
    - legacy-tool@* (pattern match)

Effective Marketplaces:
  sandboxed-code-official (org default)
    Source: github:CCimen/sandboxed-code-plugins

  team-plugins (team config)
    Source: github:acme/team-plugins

Delegation Status:
  Team can add plugins: Yes (matching @acme/*)
  Team can add MCP: No
  Project can override: Yes (via team delegation)

Session Settings:
  Timeout: 8 hours (from project, overrides org default of 24)
  Auto-resume: Yes (from org default)
```

### Conflict Resolution Display

When values conflict, show resolution:
```
Session Timeout:
  Org default: 24 hours
  Team override: (none)
  Project override: 8 hours
  -> Effective: 8 hours (project wins)
```

### Blocked Items Explanation

When something is blocked, explain why:
```
Blocked Items:

  Plugin "internal-tool@untrusted-marketplace":
    Reason: Matches org blocklist pattern "untrusted-*"
    Blocked at: Organization level
    Cannot be overridden by: Team or Project

  MCP Server "https://random.api.com/mcp":
    Reason: Team not granted MCP server permissions
    Blocked at: Delegation rules
    To enable: Org admin must set allow_additional_mcp_servers for team
```

## Questions to Answer

This command should answer:
1. "What plugins are active for my current session?"
2. "Why can't I use plugin X?"
3. "Where is setting Y coming from?"
4. "What can my team change vs what's locked by org?"

## Machine-Readable Option

For scripting, support JSON output:
```
/scc-config:explain --format=json
```

Returns structured JSON with all layers and effective values.

## Troubleshooting Mode

If issues detected:
```
Potential Issues:

  Warning: Team config references marketplace "custom-mp" but it's not defined
  Suggestion: Add marketplace definition or check name spelling

  Warning: Project enables plugin "tool@mp" but team doesn't have delegation rights
  Suggestion: Ask org admin to update delegation.teams.allow_additional_plugins
```
