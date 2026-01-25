# SCC Wizard

Interactive wizard plugin for creating, editing, validating, and explaining SCC organization and team configurations.

## Skills

| Skill | Command | Description |
|-------|---------|-------------|
| **org** | `/scc-wizard:org` | Create, edit, migrate, and onboard org configs |
| **team** | `/scc-wizard:team` | Create/edit team-managed team config files |
| **validate** | `/scc-wizard:validate` | Validate configs (schema + semantic checks) |
| **explain** | `/scc-wizard:explain` | Explain inheritance, delegation, why things are blocked/denied |

## Installation

### With SCC (Recommended)

Add to your org config's `defaults.enabled_plugins`:

```json
{
  "marketplaces": {
    "sandboxed-code-official": {
      "source": "github",
      "owner": "CCimen",
      "repo": "sandboxed-code-plugins"
    }
  },
  "defaults": {
    "enabled_plugins": [
      "scc-wizard@sandboxed-code-official"
    ]
  }
}
```

### Standalone Claude Code

Add the marketplace and enable the plugin in `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "sandboxed-code-official": {
      "source": {
        "source": "github",
        "repo": "CCimen/sandboxed-code-plugins"
      }
    }
  },
  "enabledPlugins": ["scc-wizard@sandboxed-code-official"]
}
```

Or install via CLI:
```bash
/plugin marketplace add CCimen/sandboxed-code-plugins
/plugin install scc-wizard@<marketplace-key>
```

### Local Development

```bash
claude --plugin-dir ./scc-wizard
```

## Quick Start

### Create a New Org Config

```
/scc-wizard:org
```

Choose **Quickstart** to get a working config in ~60 seconds with just 2 inputs:
1. Select task (Quickstart recommended)
2. Provide organization name

The wizard generates a baseline config with:
- Official plugins marketplace
- scc-safety-net enabled
- Balanced security defaults

Then optionally add teams, marketplaces, or customize security.

### Create a Team Config (Team-managed)

```
/scc-wizard:team
```

Only needed for **team-managed** teams (those with `config_source` in org config). Org-managed teams don't need separate files.

### Validate a Config

```
/scc-wizard:validate path/to/org-config.json
```

Uses `scc org validate` (or `scc team validate --file`) when available:
- Schema validation
- Basic semantic checks (org default_profile)

The wizard can also surface **advisory** warnings (delegation/allowlists/stdio MCP),
which are not enforced by the CLI unless explicitly implemented.

### Explain Config Behavior

```
/scc-wizard:explain
```

Ask questions like:
- "Why is plugin X blocked for team Y?"
- "What's the effective config for team backend?"
- "Why didn't my team config changes take effect?"

Get short answers with copy/paste fixes.

## Key Concepts

### Terminology

| User-Facing Term | Meaning |
|------------------|---------|
| **Org-managed** | Org controls plugins for everyone, no extra files needed |
| **Team-managed** | Teams maintain their own team-config.json files |
| **Mixed** | Some teams org-managed, some team-managed |

### Blocked vs Denied vs Disabled

| Term | Meaning | Source |
|------|---------|--------|
| **Blocked** | Matches `security.blocked_plugins` or `security.blocked_mcp_servers` | Org security (immutable) |
| **Denied** | Failed delegation check or allowlist check | Runtime decision |
| **Disabled** | Matches `defaults.disabled_plugins` | Org defaults (can be re-enabled) |

### Allowlist Semantics

| Field State | Behavior |
|-------------|----------|
| **Missing** (field absent) | No allowlist enforcement - allow all |
| **Empty list** `[]` | Block all additions |
| **Patterns list** `["core-*"]` | Allow only matching items |

## Documentation

See the [SCC Wizard Guides](https://scc-cli.dev/guides/wizard/overview) for detailed documentation on each skill.

## License

MIT
