# Team Config Wizard

Create an SCC team configuration file (team-config.json) through interactive conversation.

## Design Principle

**"Source-Type-First"**
- Ask where plugins live before asking which plugins
- Minimal required fields (GitHub: just owner/repo)
- Default to simplest option

## Wizard Flow

### Phase 1: Marketplace Setup (START HERE)

```
Question: "Where do your team's plugins live?"
Options:
- Use org/default marketplace only [Simplest - Recommended]
- Add a GitHub marketplace
- Add a Git URL marketplace
- Use local directory (for development)
- Other (describe your plugin source)
```

**If GitHub marketplace:**
```
Question: "GitHub owner (organization or username)?"
[Free text input]

Question: "Repository name?"
[Free text input]

Question: "Branch?"
Options:
- main [Default]
- master
- Other (specify branch name)
```

Generate and show:
```json
{
  "team-marketplace": {
    "source": "github",
    "owner": "[user-input]",
    "repo": "[user-input]",
    "branch": "main"
  }
}
```
Ask: "Add this marketplace?"

**If Git URL:**
```
Question: "Git clone URL (HTTPS or SSH)?"
[Free text - validate starts with https:// or git@]
```

**If Local directory:**
```
Question: "Path to local marketplace directory?"
[Free text - suggest current directory]
```

Repeat: "Add another marketplace?"

### Phase 2: Enable Plugins

```
Question: "Which plugins should be enabled?"
Options:
- Enter plugin names manually (plugin-name@marketplace format)
- List available from marketplaces (if discoverable)
- Skip for now (configure later)
- Other (describe what plugins you need)
```

For manual entry, accept comma-separated or one-by-one:
- Validate format: `plugin-name@marketplace-name`
- Show each added plugin for confirmation

### Phase 3: Disable Patterns (Advanced, Optional)

```
Question: "Disable any plugins from org defaults?"
Options:
- No disabled plugins [Default]
- Disable specific plugins by pattern
- Other (describe what to disable)
```

If disabling:
- Accept glob patterns (e.g., `legacy-*`, `deprecated-*`)
- Explain: "These patterns will remove matching plugins from org defaults"

### Phase 4: Review & Generate

1. Show JSON preview:
```json
{
  "schema_version": 1,
  "enabled_plugins": [
    "my-plugin@team-marketplace"
  ],
  "marketplaces": {
    "team-marketplace": {
      "source": "github",
      "owner": "myorg",
      "repo": "team-plugins"
    }
  }
}
```

2. Validate against team-config.v1.schema.json

3. Ask for output location:
```
Question: "Where should I save this config?"
Options:
- ./.scc/team-config.json [Recommended]
- Current directory (./team-config.json)
- Custom path
- Don't save - just show me the content
```

4. After writing, remind: "Restart your SCC session to apply changes"

## Schema Reference

Use the bundled `schemas/team-config.v1.schema.json` for:
- Field validation
- Marketplace source types (github, git, url, directory)

Key fields:
- `schema_version`: 1 (integer, not string)
- `enabled_plugins`: array of "plugin@marketplace" strings
- `disabled_plugins`: array of glob patterns
- `marketplaces`: object with marketplace definitions

## Marketplace Source Types

### GitHub
```json
{
  "source": "github",
  "owner": "org-or-user",
  "repo": "repo-name",
  "branch": "main",
  "path": "/"
}
```

### Git
```json
{
  "source": "git",
  "url": "https://gitlab.example.com/plugins.git",
  "branch": "main",
  "path": "/"
}
```

### URL
```json
{
  "source": "url",
  "url": "https://example.com/marketplace.json"
}
```

### Directory (local development)
```json
{
  "source": "directory",
  "path": "./local-plugins"
}
```
