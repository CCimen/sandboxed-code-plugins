# Project Config Wizard

Create an SCC project configuration file (.scc.yaml) through interactive conversation.

## Design Principle

**Keep it Simple**
- Project configs are for minor overrides
- Most settings should come from team/org config
- Only 2-3 questions needed

## Wizard Flow

### Question 1: Additional Plugins

```
Question: "Add plugins beyond what team config provides?"
Options:
- No additional plugins [Default - Recommended]
- Yes, add specific plugins
- Other (describe your needs)
```

If yes:
- Accept comma-separated plugin names
- Format: `plugin-name@marketplace`
- Validate against delegation rules if known

### Question 2: Session Settings

```
Question: "Override session settings?"
Options:
- Use team/org defaults [Default - Recommended]
- Custom session timeout
- Custom auto-resume setting
- Other (describe your session needs)
```

If custom timeout:
```
Question: "Session timeout (1-24 hours)?"
[Numeric input, validate range]
```

If custom auto-resume:
```
Question: "Auto-resume sessions?"
Options:
- Yes (sessions can be resumed)
- No (fresh session each time)
```

### Question 3: Output Location

```
Question: "Where should I save this config?"
Options:
- ./.scc.yaml [Recommended]
- Current directory root
- Custom path
- Don't save - just show me the content
```

### Generate & Write

1. Show YAML preview:
```yaml
# SCC Project Configuration
# Overrides team/org settings for this project

additional_plugins:
  - custom-tool@my-marketplace

session:
  timeout_hours: 8
  auto_resume: true
```

2. Validate structure (no formal schema, but check field names)

3. Write to chosen location

4. Remind: "Restart your SCC session to apply changes"

## Field Reference

Project config fields (all optional):
- `additional_plugins`: List of extra plugins for this project
- `session.timeout_hours`: Override session timeout (1-24)
- `session.auto_resume`: Override auto-resume behavior

## Notes

- Project configs are the simplest layer
- They extend (don't replace) team/org settings
- Security blocklists from org still apply
- Use sparingly - most config should be at team level
