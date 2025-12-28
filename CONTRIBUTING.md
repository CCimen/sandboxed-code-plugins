# Contributing to Sandboxed Code Plugins

Want to add a plugin to this marketplace? Follow these guidelines.

## Plugin Requirements

### Directory Structure

```
your-plugin/
├── .claude-plugin/
│   └── plugin.json      # Required: Plugin manifest
├── README.md            # Required: Plugin documentation
├── hooks/
│   └── hooks.json       # Optional: Hook configurations
├── commands/            # Optional: Slash commands
├── scripts/             # Optional: Implementation code
└── tests/               # Recommended: Test suite
```

### plugin.json Manifest

```json
{
  "name": "your-plugin",
  "version": "0.1.0",
  "description": "What your plugin does",
  "author": { "name": "Your Name" },
  "license": "MIT"
}
```

## Submission Process

1. Fork this repository
2. Create your plugin directory following the structure above
3. Add your plugin name to `.claude-plugin/marketplace.json`
4. Submit a pull request with:
   - Clear description of what the plugin does
   - Test coverage for critical functionality
   - Documentation in your plugin's README.md

## Quality Standards

- [ ] All tests pass
- [ ] No security vulnerabilities
- [ ] Clear, documented behavior
- [ ] Follows existing code patterns

## Questions?

Open an issue or discussion on the repository.
