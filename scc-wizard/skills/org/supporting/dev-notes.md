# Org Wizard Development Notes

Internal planning and verification notes. Not used at runtime.

## Success Criteria

| Metric | Target |
|--------|--------|
| Quickstart completion time | ≤60 seconds |
| Quickstart input count | **Exactly 2** (task + org identity) |
| First-time user success rate | 90%+ get valid config |
| Governance question timing | AFTER baseline, inside add-ons |

## Verification Tests

### Quickstart Test (Critical)
1. Run `/scc-wizard:org`
2. Select "Create new org config (Quickstart — recommended)" from combined menu
3. Enter org name (e.g., "Sundsvalls kommun")
4. Verify auto-generated org_id shown
5. Get valid org-config.json with sandboxed-code-official + safety-net
6. **Must complete with exactly 2 inputs (task selection + org identity)**

### Guided Setup Test
1. Run through Quickstart
2. At "Would you like to add anything?" select "Add teams/profiles"
3. Choose "Org-managed (recommended)"
4. Enter team names
5. Verify teams added inline (no config_source, no hosting questions)

### Project Overrides Test
1. Run Guided Setup
2. At add-ons, select "Allow project overrides via .scc.yaml"
3. Verify prompt asks "Enable project overrides? (No/Yes for all/Yes for specific)"
4. If "Yes", verify `delegation.projects.inherit_team_delegation: true` is set
5. Verify appropriate teams get `profiles.<team>.delegation.allow_project_overrides: true`

### Team-managed Test
1. Run Guided Setup
2. Select "Add teams/profiles" → "Team-managed"
3. Verify hosting questions appear
4. Verify `config_source` is generated as a ConfigSource object (not a string)
5. Verify output shows expected team-config paths

### Terminology Test
1. Should NEVER see "Federated", "Centralized", or "Hybrid" in UI
2. Should see "Org-managed", "Team-managed", and "Mixed" instead

### Baseline Config Validation (Minimal Quickstart)
Generated Quickstart baseline must include ONLY:
- `schema_version: "1.0.0"`
- `$schema: "https://scc-cli.dev/schemas/org-v1.json"`
- `organization.name` and `organization.id`
- `marketplaces.sandboxed-code-official` with correct GitHub source
- `defaults.enabled_plugins: ["scc-safety-net@sandboxed-code-official"]`
- `security.safety_net: { "action": "block" }`

**Must NOT include in Quickstart baseline:**
- `blocked_plugins` / `blocked_mcp_servers` (move to Security add-on)
- `allowed_plugins` / `allowed_mcp_servers` (move to Security add-on)
- `network_policy` (schema default is sufficient)
- `delegation` (schema defaults are sufficient)
- `extra_marketplaces` (not needed if not using additional marketplaces)

**Design principle:** No "policy debugging" on day one. Keep baseline short enough that an org leader will actually read it.

### Onboarding Format Validation
User config `organization_source` must be an **object** with:
- `url` field (required)
- `auth` and `auth_header` fields (optional, for private repos)

Example:
```json
{
  "config_version": "1.0.0",
  "organization_source": {
    "url": "https://raw.githubusercontent.com/owner/repo/main/org-config.json"
  }
}
```

### config_source Format Validation
Profile `config_source` must be a **ConfigSource object**, not a string.

GitHub example:
```json
"config_source": {
  "source": "github",
  "owner": "myorg",
  "repo": "scc-team-configs",
  "branch": "main",
  "path": "teams/platform/team-config.json"
}
```

URL example:
```json
"config_source": {
  "source": "url",
  "url": "https://example.com/scc/teams/platform/team-config.json"
}
```
