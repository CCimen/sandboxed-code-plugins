# SCC Org Presets (v1)

These presets provide sensible defaults for different organizational security postures.

## Strict / Fort Knox

Maximum security controls. Best for regulated industries, financial services, or high-security environments.

```json
{
  "security": {
    "blocked_plugins": ["*-experimental", "*-deprecated", "*-beta", "malicious-*"],
    "blocked_mcp_servers": ["*.untrusted.com"],
    "allow_stdio_mcp": false,
    "safety_net": { "action": "block" }
  },
  "defaults": {
    "allowed_plugins": ["MUST_CONFIGURE"],
    "allowed_mcp_servers": ["MUST_CONFIGURE"],
    "network_policy": "corp-proxy-only",
    "cache_ttl_hours": 24,
    "session": { "timeout_hours": 8, "auto_resume": false }
  },
  "delegation": {
    "teams": {
      "allow_additional_plugins": [],
      "allow_additional_mcp_servers": []
    },
    "projects": { "inherit_team_delegation": false }
  }
}
```

**Key characteristics:**
- Plugin/MCP allowlists **required** (no open additions)
- Network policy: corp-proxy-only or isolated
- Delegation: minimal or none
- stdio MCP: disabled
- Session: shorter timeout, no auto-resume

**Suggested blocked_plugins:**
- `*-experimental`
- `*-deprecated`
- `*-beta`
- `malicious-*`

## Balanced / Standard Enterprise (Recommended)

Good security with practical flexibility. Suitable for most enterprise environments.

```json
{
  "security": {
    "blocked_plugins": ["*-experimental", "*-deprecated", "malicious-*"],
    "blocked_mcp_servers": ["*.untrusted.com"],
    "allow_stdio_mcp": false,
    "safety_net": { "action": "block" }
  },
  "defaults": {
    "network_policy": "unrestricted",
    "cache_ttl_hours": 24,
    "session": { "timeout_hours": 10, "auto_resume": true }
  },
  "delegation": {
    "teams": {
      "allow_additional_plugins": ["*"],
      "allow_additional_mcp_servers": []
    },
    "projects": { "inherit_team_delegation": true }
  }
}
```

**Key characteristics:**
- Allowlists: optional (omit for open additions, or set patterns)
- Network policy: unrestricted
- Delegation: teams can add plugins broadly, MCP more restricted
- stdio MCP: disabled by default
- Session: moderate timeout, auto-resume enabled

**Suggested blocked_plugins:**
- `*-experimental`
- `*-deprecated`
- `malicious-*`

## Open / Research

Minimal restrictions. For research labs, prototyping, or trusted developer environments.

```json
{
  "security": {
    "blocked_plugins": ["malicious-*"],
    "blocked_mcp_servers": [],
    "allow_stdio_mcp": false,
    "safety_net": { "action": "warn" }
  },
  "defaults": {
    "network_policy": "unrestricted",
    "cache_ttl_hours": 12,
    "session": { "timeout_hours": 12, "auto_resume": true }
  },
  "delegation": {
    "teams": {
      "allow_additional_plugins": ["*"],
      "allow_additional_mcp_servers": ["*"]
    },
    "projects": { "inherit_team_delegation": true }
  }
}
```

**Key characteristics:**
- Allowlists: typically omitted (allow all additions)
- Network policy: unrestricted
- Delegation: permissive (teams and projects can add freely)
- stdio MCP: can be enabled with prefix restrictions
- Safety net: warn mode (allows destructive git commands with warning)
- Session: longer timeout

## Custom

When none of the presets fit, configure each setting individually:

1. **Security section:**
   - blocked_plugins patterns
   - blocked_mcp_servers patterns
   - allow_stdio_mcp (true/false)
   - allowed_stdio_prefixes (if stdio enabled)
   - safety_net action and options

2. **Defaults section:**
   - allowed_plugins (omit / [] / patterns)
   - allowed_mcp_servers (omit / [] / patterns)
   - enabled_plugins baseline
   - disabled_plugins patterns
   - network_policy
   - session settings
   - cache_ttl_hours

3. **Delegation section:**
   - teams.allow_additional_plugins
   - teams.allow_additional_mcp_servers
   - projects.inherit_team_delegation
