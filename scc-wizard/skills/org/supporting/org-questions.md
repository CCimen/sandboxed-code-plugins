# Org Wizard Question Bank

Reference questions for the `/scc-wizard:org` skill. Use these as templates for AskUserQuestion calls.

## Important: Terminology

**Always use user-facing terms, never architecture terms:**

| Use This | NOT This |
|----------|----------|
| Org-managed | ~~Centralized~~ |
| Team-managed | ~~Federated~~ |
| Mixed | ~~Hybrid~~ |

---

## Combined Task Menu (Step 1)

**Question:** "What would you like to do?"
**Options:**
- Create new org config (Quickstart — recommended) - Working org-config.json in ~60 seconds
- Create new org config (Guided setup) - Baseline config first, then add-ons
- Create new org config (Advanced) - Full control over every setting
- Update an existing org config file - Load and edit a JSON file
- Migrate org-managed → team-managed configs - Move teams to external files
- Generate onboarding instructions - Get hosting URL + setup command

---

## Organization Identity (Step 2)

**Prompt (free-form text, not AskUserQuestion):**

```
Organization identity

Please provide what you know (you can answer with just the name):

1. Organization name (required) — e.g. "Acme Corp"
2. Org ID / slug (optional) — lowercase, digits, hyphens (e.g. acme-corp)
3. Contact (optional) — email or URL

If you leave Org ID blank, I'll generate it from the name.
```

---

## Quickstart Next Steps (After Baseline)

**Question:** "What would you like to do next?"
**Options:**
- Generate onboarding instructions (recommended) - Get hosting URL + setup command
- Write org-config.json now - Save and exit
- Add teams/profiles - Define selectable teams
- Add an internal marketplace - Your own plugin repository
- Customize security settings - Adjust security posture

---

## Teams/Profiles - Management Model

**Question:** "Who should own the list of enabled plugins for each team?"

**Options:**
1. **Org-managed (recommended to start)**
   One org-config.json. Fastest onboarding.
   *(Teams can still own plugin content via an internal marketplace.)*

2. **Team-managed (recommended for scale)**
   Each team edits team-config.json. Less central maintenance.
   *(Requires hosting + delegation so changes apply.)*

3. **Mixed (migration-friendly)**
   Pick Org-managed or Team-managed per team.

**Decision helper:**
> **Rule of thumb:** start Org-managed for pilots / ≤5 teams. Choose Team-managed if teams need self-service approvals and you have a team owner per config.

**One-sentence explanations:**
- Org-managed: "Teams won't need extra config files. Teams can still own plugin *content* via an internal marketplace."
- Team-managed: "Each team maintains their own config file. You'll need to set up hosting and delegation."
- Mixed: "You'll choose org-managed or team-managed for each team."

**The "low maintenance without team-config files" pattern:**
> Org-managed + internal marketplace + "one plugin per team": Org config enables one stable plugin per team (e.g., `team-toolbox@internal-plugins`). The team owns the plugin content (hooks, skills, agents, MCP definitions) in their marketplace repo. The org admin rarely touches plugin lists again unless a team needs a *new* plugin entry.

---

## Team-managed Hosting

**Question:** "Where will team config files live?"
**Options:**
- Single GitHub repo (recommended) - All teams in one repo
- Single GitLab repo
- Direct HTTPS URLs [advanced]
- Per-team custom hosting [advanced]

**Follow-up (GitHub) - Single Input:**
```
Paste the GitHub repo URL (or owner/repo) where team configs will live.
Examples:
• https://github.com/Sundsvallskommun/scc-team-configs
• Sundsvallskommun/scc-team-configs
• Sundsvallskommun (I'll suggest a repo name)

Or type "later" to use placeholder paths.
```

**Parsing rules:**
- Full URL → extract owner/repo
- `owner/repo` → use directly
- `owner` only → suggest `{owner}/scc-team-configs` as repo

---

## Security Posture

**Question:** "Choose a security posture preset:"
**Options:**
- Balanced (recommended) - Block unsafe actions, unrestricted network
- Strict - Allowlists required, corp-proxy network
- Open - Warn only, minimal restrictions
- Custom - Configure each setting individually

---

## Allowlist Mode (Plugins)

**Question:** "Do you want a plugin allowlist (for additions)?"
**Options:**
- Open (no allowlist) - Any team/project can add any plugin (subject to blocks)
- Allowlist - Only plugins matching patterns can be added
- Block all additions - No team/project can add any plugins

**Technical mapping:**
- Open → **omit** `defaults.allowed_plugins` field
- Allowlist → set patterns like `["core-*", "*@sandboxed-code-official"]`
- Block all → set `defaults.allowed_plugins = []`

---

## Allowlist Mode (MCP Servers)

**Question:** "Do you want an MCP server allowlist (for additions)?"
**Options:**
- Open (no allowlist) - Any team/project can add any MCP server (subject to blocks)
- Allowlist - Only MCP servers matching URL patterns can be added
- Block all additions - No team/project can add any MCP servers

---

## Delegation: Team Plugin Additions

**Question:** "Which teams may add plugins beyond org defaults?"
**Options:**
- All teams - `["*"]`
- Specific teams/patterns - e.g., `["team-a", "team-b", "dev-*"]`
- No teams - `[]`

**Reframe by intent:** "Allow team profiles to have differences from org defaults"

---

## Delegation: Team MCP Additions

**Question:** "Which teams may add MCP servers?"
**Options:**
- No teams (recommended) - `[]`
- Specific teams/patterns - e.g., `["team-a", "infra-team"]`
- All teams - `["*"]`

---

## Delegation: Project Overrides

**Question:** "Enable project overrides via .scc.yaml?"
**Options:**
- No (recommended) - Only teams can add, projects inherit without additions
- Yes, for all teams - Projects can add if their team is delegated
- Yes, only for specific teams - Choose which teams allow project overrides

**Requirement if enabled:**
- `delegation.projects.inherit_team_delegation: true`
- Per-team: `profiles.<team>.delegation.allow_project_overrides: true`

---

## Marketplace Source Type

**Question:** "What type of marketplace source?"
**Options:**
- GitHub - GitHub repository (owner/repo)
- GitLab - GitLab repository
- Git URL - Generic Git URL (HTTPS or SSH)
- HTTPS URL - Direct HTTPS URL to manifest
- Directory - Local filesystem path (dev/testing only)

---

## Per-Team Management (for Mixed mode)

**Question:** "How should the '{team}' team be managed?"
**Options:**
- Org-managed - Plugin list maintained in org config
- Team-managed - Team maintains external team-config file

---

## Team Trust Grants (Team-managed only)

**Question:** "What marketplace access should this team have?"
**Options:**
- Inherit org marketplaces only - Team uses org-defined marketplaces
- Inherit + add from approved sources - Team can add marketplaces from allowed patterns
- Full marketplace control - Team can add any marketplace (high trust)

---

## Onboarding Hosting Target

**Question:** "Where will you host your org config file?"
**Options:**
- GitHub (recommended)
- GitLab
- Internal HTTPS server
- I'll handle hosting myself (just give me the snippet)

---

## Bulk Team Input

**Prompt:**
```
Enter team names (comma-separated). Example: platform, backend, ai-team

Team names become profile keys in the org config.
```

**Parsing rules:**
- Accept commas, spaces, or newlines as separators
- Trim whitespace
- Ignore empty entries
- Validate: `^[a-z0-9-]+$`

---

## Edit Section Selection

**Question:** "Which section do you want to edit?"
**Options:**
- Organization identity
- Marketplaces
- Teams/profiles
- Security settings
- Delegation rules
- Defaults

---

## Review Action Menu

**Question:** "What would you like to do?"
**Options:**
- Write org-config.json
- View JSON
- Edit (pick section)
- Quit

---

## Migration Team Selection

**Prompt:**
```
Teams available for migration:
  ☐ platform (3 plugins)
  ☐ backend (1 plugin)
  ☐ frontend (2 plugins)

Select teams to migrate (comma-separated, or 'all'):
```

---

## stdio MCP Confirmation

**Question:** "This team wants stdio MCP servers. Confirm security requirements:"
**Checklist:**
- [ ] `security.allow_stdio_mcp` is set to `true`
- [ ] All commands use absolute paths (e.g., `/usr/local/bin/npx`)
- [ ] If `allowed_stdio_prefixes` is set, commands fall under allowed paths
