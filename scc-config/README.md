# SCC Configuration Plugin

Interactive configuration wizard for SCC (Sandboxed Claude Code) organization, team, and project configs.

## Overview

This plugin helps you create and manage SCC configuration files through conversational AI assistance. Instead of manually editing YAML/JSON files, use natural language to configure your SCC environment.

## Features

- **Interactive Wizards**: Step-by-step guided setup for org, team, and project configs
- **Maintenance Mode**: Edit existing configs with menu-driven operations
- **Schema Validation**: Auto-validates configs after every edit
- **Config Explanation**: Understand the effective config with full inheritance chain
- **"Other" Option**: Always allows free-text input for flexibility

## Commands

| Command | Description |
|---------|-------------|
| `/scc-config:init` | Unified entry point - auto-detects what you need |
| `/scc-config:init-org` | Full organization config wizard |
| `/scc-config:init-team` | Team configuration wizard |
| `/scc-config:init-project` | Project overrides wizard |
| `/scc-config:edit` | Edit existing configs (menu-driven) |
| `/scc-config:validate` | Validate a config file against schema |
| `/scc-config:explain` | Show effective config with inheritance |

## Quick Start

### For Org Admins

```
/scc-config:init
```

Select "Organization policy" and follow the wizard. The default "Delegated" governance lets teams manage their own plugins within guardrails you define.

### For Team Leads

```
/scc-config:init-team
```

Add your team's plugin marketplace (GitHub repo, Git URL, etc.) and enable the plugins your team needs.

### For Developers

```
/scc-config:init-project
```

Add project-specific plugin overrides or session settings.

## Config Hierarchy

SCC uses a 3-layer configuration system:

```
Organization (org.yaml)
    └── Security boundaries (cannot be overridden)
    └── Default settings
    └── Delegation rules

    Team (team-config.json)
        └── Team-specific marketplaces
        └── Enabled/disabled plugins

        Project (.scc.yaml)
            └── Project-specific overrides
```

Use `/scc-config:explain` to see how these layers merge for your current context.

## Default Locations

| Config Type | Default Path |
|-------------|--------------|
| Organization | `~/.config/scc/org.yaml` |
| Team | `./.scc/team-config.json` |
| Project | `./.scc.yaml` |

## Validation Hook

This plugin includes a PostToolUse hook that automatically validates SCC config files after Edit/Write operations. If validation fails, you'll see error details immediately.

## Schema Reference

The plugin bundles the latest SCC schemas:
- `org-v1.schema.json` - Organization config schema
- `team-config.v1.schema.json` - Team config schema

## Design Philosophy

### For Org Admins
- **Governance Modeling**: Define trust levels, not plugin inventories
- **"I Don't Know Yet"**: Safe defaults when you're unsure what teams need
- **Lazy Federation**: Point to team repos without knowing their contents

### For Team Leads
- **Source-Type-First**: Where do plugins live? (before which plugins)
- **Minimal Fields**: GitHub marketplace = just owner/repo
- **Show-Then-Confirm**: Generate entry, confirm, then save

### For Everyone
- **Progressive Disclosure**: Start simple, get advanced when needed
- **Safe Previews**: Always show diff before writing
- **"Other" Option**: Free-text input for any question

## Requirements

- Claude Code with plugin support
- Python 3.8+ (for validation script)
- Optional: `jsonschema` and `PyYAML` packages for full validation

## License

MIT
