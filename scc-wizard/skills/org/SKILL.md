---
name: org
description: Create, update, migrate, and onboard SCC organization configurations with a success-first wizard.
argument-hint: [optional-path-to-org-config.json]
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Grep, Glob, AskUserQuestion
---

# SCC Org Config Wizard (v2.2)

Success-first wizard: get a working org-config.json in ≤60 seconds, then add complexity as needed.

## Output Contract (ALWAYS)

1. Show a short human summary (3-8 bullets)
2. Output exactly ONE final JSON code block (valid org config)
3. Never output multiple competing JSON drafts
4. If writing/editing files, ask permission and confirm path before Write/Edit

---

## Core Principle: Success First, Complexity Later

Users shouldn't make governance decisions before seeing a working config. Give them success first, then offer scaling options.

**Quickstart goal:** 2 inputs → working org-config.json

---

## Terminology (Use These, Not Architecture Terms)

| User-Facing Term | Meaning | Old Term (Never Use in UI) |
|------------------|---------|---------------------------|
| **Org-managed** | Org controls plugins for everyone, no extra files needed | Centralized |
| **Team-managed** | Teams maintain their own team-config.json files | Federated |
| **Mixed** | Some teams org-managed, some team-managed | Hybrid |

**Never** use "Federated", "Centralized", or "Hybrid" in user-facing prompts.

---

## Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Step 1: ONE combined "What would you like to do?" menu     │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 2: Organization Identity (single prompt)              │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 3: Generate baseline config + Review + Add-ons        │
└─────────────────────────────────────────────────────────────┘
```

---

## Step 1: Combined Task Menu (AskUserQuestion)

Use AskUserQuestion with a single question:

**Prompt:** "What would you like to do?"

| Option | Description |
|--------|-------------|
| **Create new org config (Quickstart — recommended)** | Working org-config.json in ~60 seconds. Minimal questions. |
| Create new org config (Guided setup) | Baseline config first, then choose add-ons. |
| Create new org config (Advanced) | Full control over security, delegation, allowlists. |
| Update an existing org config file | Load a local JSON file and edit it. |
| Migrate org-managed teams → team-managed configs | Move teams to external files. |
| Generate onboarding instructions | Get hosting URL + scc setup command. |

**Branch based on selection:**
- Quickstart/Guided/Advanced → Continue to Step 2
- Update → Read file, show summary, enter edit flow
- Migrate → Enter migration flow
- Onboard → Enter onboarding flow

---

## Step 2: Organization Identity (Single Prompt)

**Prompt (exact copy):**

```
Organization identity

Please provide what you know (you can answer with just the name):

1. Organization name (required) — e.g. "Acme Corp"
2. Org ID / slug (optional) — lowercase, digits, hyphens (e.g. acme-corp)
3. Contact (optional) — email or URL

If you leave Org ID blank, I'll generate it from the name.
```

**Behavior:**
- If user only types a name → auto-generate org_id by slugifying (lowercase, replace spaces/special chars with hyphens)
- Validate org_id against `^[a-z0-9-]+$`
- If invalid → single corrective question: "I couldn't generate a valid Org ID. What should it be?"

**Parsing rules:**
- Accept free-form text
- Look for patterns like "Name: X", "1. X", or just a bare name
- Extract contact if email pattern found
- Be generous in interpretation

---

## Step 3: Generate Baseline Config (Automatic)

Generate the baseline config immediately after collecting org identity.

### Baseline Template (Minimal - Use for Quickstart)

**Design principle:** Keep Quickstart baseline minimal and readable. No "policy debugging" on day one. Blocklists, allowlists, and network policies are Guided/Advanced add-ons.

```json
{
  "$schema": "https://scc-cli.dev/schemas/org-v1.json",
  "schema_version": "1.0.0",
  "organization": {
    "name": "ORG_NAME",
    "id": "org-id"
  },
  "marketplaces": {
    "official-plugins": {
      "source": "github",
      "owner": "CCimen",
      "repo": "sandboxed-code-plugins",
      "branch": "main",
      "path": "/"
    }
  },
  "defaults": {
    "enabled_plugins": ["scc-safety-net@official-plugins"]
  },
  "security": {
    "safety_net": { "action": "block" }
  }
}
```

### What the Baseline Includes

| Component | Value | Rationale |
|-----------|-------|-----------|
| `$schema` | `https://scc-cli.dev/schemas/org-v1.json` | Enables validation |
| `schema_version` | `1.0.0` | Required |
| `marketplaces.official-plugins` | GitHub: CCimen/sandboxed-code-plugins | Safe default marketplace |
| `defaults.enabled_plugins` | `["scc-safety-net@official-plugins"]` | Safety net enabled |
| `security.safety_net` | `{ "action": "block" }` | Core safety feature |

### What the Baseline Does NOT Include (Add via Guided/Advanced)

- `blocked_plugins` / `blocked_mcp_servers` patterns (move to Security add-on)
- `allowed_plugins` / `allowed_mcp_servers` allowlists (move to Security add-on)
- `network_policy` (defaults to unrestricted via schema)
- `delegation` rules (defaults to closed via schema)
- Teams/profiles
- Additional marketplaces
- `contact` field (optional)

---

## Step 4: Review + "What Next?" (Add-ons)

### Quickstart Review (Exact Copy)

```
✅ Baseline org config generated

What you get right now:
• Org: {org.name} ({org.id})
• Marketplace: official-plugins
• Safety: scc-safety-net enabled (blocks dangerous actions)
• Teams: not configured yet (everyone uses org defaults)

This is a minimal, working config. Add complexity later as needed.

Next step (recommended): Generate onboarding instructions
```

**Critical UX:** After Quickstart, always show a compact next-steps block with ONE recommended action to prevent drop-off.

### Quickstart Next Steps (AskUserQuestion)

**Prompt:** "What would you like to do next?"

| Option | Description |
|--------|-------------|
| **Generate onboarding instructions (recommended)** | Get hosting URL + setup command |
| Write org-config.json now | Save and exit |
| Add teams/profiles | Define selectable teams |
| Add an internal marketplace | Your own plugin repository |
| Add security rules | Blocklists, allowlists, delegation |

---

## Guided Setup Add-ons (Pick-One Loop)

After baseline config is generated, offer optional add-ons via a **pick-one loop** (works in all UIs).

**Prompt (exact copy):**

```
Optional next steps (recommended: keep it simple)

Pick one to configure now:
  1. Add teams/profiles
  2. Add an internal marketplace
  3. Allow project overrides via .scc.yaml [advanced]
  4. Generate onboarding instructions
  5. Customize security settings [advanced]
  6. Review & save
```

**After each add-on completes, return to this menu** until user selects "Review & save."

**Note:** "Team-managed configs" is NOT a separate add-on. It's a branch inside "Add teams/profiles" to reduce duplicate decisions.

---

### Add-on A: Internal Plugin Marketplace

**Prompt:**
```
Where is your internal plugin marketplace hosted?
  1. GitHub
  2. GitLab
  3. Other Git URL (HTTPS or SSH)
  4. HTTPS manifest URL
  5. Local directory (dev only)
```

**Follow-up (GitHub) - Single Input:**
```
Paste the GitHub repo URL (or owner/repo) for your internal marketplace.
Examples:
• https://github.com/myorg/claude-plugins
• myorg/claude-plugins
• myorg (I'll suggest a repo name)

Or type "skip" to configure this later.
```

**Parsing rules:**
- Full URL → extract owner/repo
- `owner/repo` → use directly
- `owner` only → suggest `{owner}/scc-plugins` as repo

**Follow-up (if only owner provided):**
```
Repo name [default: scc-plugins]:
```

**Marketplace name [default: internal-plugins]**

**Add to config:**
```json
"marketplaces": {
  "internal-plugins": {
    "source": "github",
    "owner": "USER_INPUT",
    "repo": "USER_INPUT",
    "branch": "main",
    "path": "/"
  }
}
```

Also add `"internal-plugins"` to `defaults.extra_marketplaces`.

---

### Add-on B: Define Teams/Profiles

**Prompt (exact copy):**
```
Teams/profiles

Who should own the list of enabled plugins for each team?

  1. Org-managed (recommended to start)
     One org-config.json. Fastest onboarding.
     (Teams can still own plugin content via an internal marketplace.)

  2. Team-managed (recommended for scale)
     Each team edits team-config.json. Less central maintenance.
     (Requires hosting + delegation so changes apply.)

  3. Mixed (migration-friendly)
     Pick Org-managed or Team-managed per team.
```

**Decision helper (show after menu):**
> **Rule of thumb:** start Org-managed for pilots / ≤5 teams. Choose Team-managed if teams need self-service approvals and you have a team owner per config.

**One-sentence explanation after selection:**
- Org-managed: "Org-managed means teams won't need extra config files. Teams can still own plugin *content* via an internal marketplace."
- Team-managed: "Team-managed means each team maintains their own config file. You'll need to set up hosting and delegation."
- Mixed: "You'll choose org-managed or team-managed for each team."

**Team names prompt (for all options):**
```
Enter team names (comma-separated). Example: platform, backend, ai-team

Team names become profile keys in the org config.
```

#### If Org-managed (Recommended)

For each team, only ask **description** (optional) and whether to add plugins now:

```
For team '{team}':
• description (optional)
• additional plugins now? (optional, comma-separated plugin@marketplace)
```

**Org-managed behavior:**
- Create `profiles.{team}` with description
- Set `delegation.allow_project_overrides: false` by default
- Do NOT show team-level `network_policy` or `session.auto_resume` (not applied at runtime)
- Team `session.timeout_hours` CAN be offered (it IS applied)

**If user adds per-team plugins:**
- Ensure those teams are covered by `delegation.teams.allow_additional_plugins` (baseline already has `["*"]`)

**Example output:**
```json
"profiles": {
  "platform": {
    "description": "Platform engineering team",
    "additional_plugins": ["terraform@official-plugins"]
  },
  "backend": {
    "description": "Backend services team"
  }
}
```

#### If Team-managed (Advanced)

**Only ask hosting AFTER user chooses team-managed.**

**Prompt:**
```
Team-managed configs

Each team maintains a team-config.json file.
Org still enforces immutable security boundaries (blocked plugins/MCP, stdio gate, safety net).

Where will team config files live?
  1. Single GitHub repo (recommended) — all teams in one repo
  2. Single GitLab repo
  3. Direct HTTPS URLs [advanced]
  4. Per-team custom hosting [advanced]
```

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

**Optional follow-ups (only if needed):**
- Branch [default: main]
- Base path [default: teams/]

**Create `profiles.<team>.config_source` entries (GitHub):**
```json
"profiles": {
  "platform": {
    "config_source": {
      "source": "github",
      "owner": "{owner}",
      "repo": "{repo}",
      "branch": "{branch}",
      "path": "teams/platform/team-config.json"
    },
    "trust": {
      "allow_additional_marketplaces": false,
      "marketplace_source_patterns": []
    }
  }
}
```

**For GitLab:**
```json
"config_source": {
  "source": "gitlab",
  "owner": "{owner}",
  "repo": "{repo}",
  "branch": "{branch}",
  "path": "teams/platform/team-config.json"
}
```

**For Direct HTTPS URLs:**
```json
"config_source": {
  "source": "url",
  "url": "https://example.com/scc/teams/platform/team-config.json"
}
```

**After collecting teams, offer stub generation:**
```
Do you want me to generate starter team-config.json files for all teams now?
  1. Yes (recommended) — I'll create stub files you can customize
  2. No — just show me the expected paths
```

**If Yes:** Generate minimal team-config stubs:
```json
{
  "$schema": "https://scc-cli.dev/schemas/team-config.v1.json",
  "schema_version": "1.0.0",
  "enabled_plugins": []
}
```

Write to `teams/{team}/team-config.json` for each team.

**If No:** Show expected paths and commands:
```
Expected team config files:
• teams/platform/team-config.json
• teams/backend/team-config.json
• teams/ai-team/team-config.json

To create each one, run:
  /scc-wizard:team create teams/platform/team-config.json
  /scc-wizard:team create teams/backend/team-config.json
  /scc-wizard:team create teams/ai-team/team-config.json
```

**Output guidance:**
- Don't dump multiple team-config JSON blocks inline
- Always show full command paths (never `/scc-wizard:team:create` or other colon variants)

#### If Mixed

Ask for each team: Org-managed or Team-managed?
Apply appropriate logic per team.

---

### Add-on C: Allow Project Overrides (.scc.yaml)

**Prompt:**
```
Project overrides (advanced)

Allow repos to add extra plugins/MCP servers via .scc.yaml
(only when allowed by org + team delegation).

Enable project overrides?
  1. No (recommended)
  2. Yes, for all teams
  3. Yes, only for specific teams
```

If enabled:
- Set `delegation.projects.inherit_team_delegation: true`
- For selected teams: `profiles.<team>.delegation.allow_project_overrides: true`

**Warning if teams not delegated:**
If user enables project overrides but team delegation is closed, warn:
"Project overrides require team delegation. Enable team differences from org defaults?"

---

### Add-on D: Generate Onboarding Instructions

**Prompt:**
```
Onboarding

Where will you host your org config file (org-config.json)?
  1. GitHub (recommended)
  2. GitLab
  3. Internal HTTPS server
  4. I'll handle hosting myself (just give me the snippet)
```

**Follow-up (GitHub) - Single Input:**
```
Paste the GitHub repo URL (or owner/repo) where org-config.json will live.
Examples:
• https://github.com/Sundsvallskommun/scc-config
• Sundsvallskommun/scc-config
• Sundsvallskommun (I'll suggest a repo name)

Or type "later" to get a placeholder URL.
```

**Parsing rules:**
- Full URL → extract owner/repo
- `owner/repo` → use directly
- `owner` only → suggest `{owner}/scc-config` as repo
- "later" → use placeholder `https://raw.githubusercontent.com/<owner>/<repo>/main/org-config.json`

**Optional follow-ups (only if needed):**
- Branch [default: main]
- File path [default: org-config.json]

**Follow-up: Public vs Private (AskUserQuestion):**
```
Will users be able to fetch this org-config URL without authentication?
  1. Yes (public repo or URL)
  2. No (private; token required)
```

**Output (Public):**
```
Onboarding Instructions
━━━━━━━━━━━━━━━━━━━━━━━

1. Host org-config.json at:
   https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}

2. Users run:
   scc setup --org https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}

3. Or add to ~/.config/scc/config.json:
   {
     "config_version": "1.0.0",
     "organization_source": {
       "url": "https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
     }
   }

Note: Org config URLs must be HTTPS.
```

**Output (Private/Token Required):**
```
Onboarding Instructions (Private Hosting)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Host org-config.json at:
   https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}

2. Users need a token with read access to the repo.

3. Users run:
   GITHUB_TOKEN=<token> scc setup --org https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}

4. Or add to ~/.config/scc/config.json:
   {
     "config_version": "1.0.0",
     "organization_source": {
       "url": "https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}",
       "auth": "env:GITHUB_TOKEN",
       "auth_header": "Authorization"
     }
   }

Notes:
• If you use `Authorization`, SCC will automatically prefix your token with `Bearer ` unless it already starts with `Bearer ` or `Basic `.
• Org config URLs must be HTTPS.
```

---

### Add-on E: Customize Security Settings

**Prompt:**
```
Security preset:
  1. Balanced (recommended) — Block unsafe actions, unrestricted network
  2. Strict — Allowlists required, corp-proxy network
  3. Open — Warn only, minimal restrictions
  4. Custom — Configure each setting
```

**If Custom:** Enter detailed security configuration flow with questions for:
- `blocked_plugins` patterns
- `blocked_mcp_servers` patterns
- `allow_stdio_mcp` (true/false)
- `safety_net.action` (block/warn/off)
- `network_policy` (unrestricted/corp-proxy/airgapped)
- `allowed_plugins` patterns (or omit for open)
- `allowed_mcp_servers` patterns (or omit for open)

---

## Review & Save (Simplified Action Menu)

Replace verbose step counters with a clean action menu.

**Summary panel (exact copy):**
```
Review

• Org: {name} ({id})
• Marketplaces: {list}
• Defaults: {enabled_plugins}
• Teams: {none | count + model}
• Delegation: {short summary}

What would you like to do?
  1. Write org-config.json
  2. View JSON
  3. Edit (pick section)
  4. Quit
```

**Default path suggestion:** `./org-config.json`

**After writing:**
```
✓ Saved to ./org-config.json

Next: host it + run `scc setup --org <url>`
```

---

## Advanced Mode Additions

In Advanced mode, after Step 2 (org identity), ask about:

1. **Security preset** (Balanced/Strict/Open/Custom)
2. **Delegation: team plugin additions** (All teams/Specific patterns/None)
3. **Delegation: team MCP additions** (All teams/Specific patterns/None)
4. **Delegation: project inheritance** (Yes/No)
5. **Allowlists** (Open/Patterns/Block all)
6. **Additional marketplaces** (before teams)
7. **Teams/profiles** with full options

---

## Update Existing Config Flow

When user selects "Update an existing org config file":

1. **Ask for path:**
   ```
   Path to org config file [default: ./org-config.json]:
   ```

2. **Read and validate:**
   - Check JSON syntax
   - Check schema version
   - Report any validation errors

3. **Show current summary:**
   ```
   Current Configuration
   ━━━━━━━━━━━━━━━━━━━━━
   • Org: {name} ({id})
   • Marketplaces: {count}
   • Teams: {count} ({model})
   • Security: {preset or "Custom"}
   • Delegation: {summary}
   ```

4. **Ask what to edit:**
   ```
   Which section to edit?
     1. Organization identity
     2. Marketplaces
     3. Teams/profiles
     4. Security settings
     5. Delegation rules
     6. Defaults
   ```

5. **Edit section, then loop back to summary**

6. **Offer to save when done**

---

## Migration Flow (Org-managed → Team-managed)

When user selects "Migrate org-managed teams → team-managed configs":

1. **Load existing config**

2. **Identify org-managed teams:**
   - Teams with inline `additional_plugins` but no `config_source`

3. **Ask which teams to migrate:**
   ```
   Teams available for migration:
     ☐ platform (3 plugins)
     ☐ backend (1 plugin)
     ☐ frontend (2 plugins)

   Select teams to migrate (comma-separated, or 'all'):
   ```

4. **Collect hosting details** (same as team-managed flow)

5. **Generate:**
   - Updated org config with `config_source` entries
   - Team config content for each migrated team

6. **Show migration summary and offer stub generation:**
   ```
   Migration Summary
   ━━━━━━━━━━━━━━━━━
   • 3 teams migrated to team-managed
   • 1 team remains org-managed

   Files to create:
   • teams/platform/team-config.json
   • teams/backend/team-config.json
   • teams/frontend/team-config.json

   Do you want me to generate these team-config files now?
     1. Yes (recommended)
     2. No (show commands instead)
   ```

   **If No, show full commands:**
   ```
   To create each file, run:
     /scc-wizard:team create teams/platform/team-config.json
     /scc-wizard:team create teams/backend/team-config.json
     /scc-wizard:team create teams/frontend/team-config.json
   ```

---

## Runtime Rules (Must Respect)

The wizard must understand SCC's actual runtime behavior:

### Delegation Behavior

- Team profile additions (`profiles.<team>.additional_plugins`) are only applied when the team matches `delegation.teams.allow_additional_plugins`. Otherwise they will be **denied** at runtime.

- Project additions require BOTH:
  - `delegation.projects.inherit_team_delegation: true`
  - `profiles.<team>.delegation.allow_project_overrides: true`

### Allowlist Semantics

| Intent | JSON | Behavior |
|--------|------|----------|
| Allow all | **Omit field** | No enforcement |
| Block all | `[]` | Empty array blocks everything |
| Allow patterns | `["core-*"]` | Only matching allowed |

**Never** replace omission with `[]` unless user explicitly wants "deny all".

### Fields That Don't Apply Per-Team (Hide in Quickstart/Guided)

Based on runtime `compute_effective_config()`:
- `profiles.{team}.network_policy` — NOT applied per-team
- `profiles.{team}.session.auto_resume` — NOT applied per-team

**DO apply per-team:**
- `profiles.{team}.session.timeout_hours` — IS applied

---

## Input Validation Rules

| Field | Rule | Error Message |
|-------|------|---------------|
| `org_id` | `^[a-z0-9-]+$` | "Use only lowercase letters, numbers, hyphens. Try: {suggested}" |
| `org_name` | Non-empty | "Organization name is required" |
| Team names | `^[a-z0-9-]+$` | "Team '{name}' has invalid characters. Use: {suggested}" |
| Email | Valid format or empty | "Invalid email format. Example: admin@example.com" |
| GitHub owner | `^[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?$` | "GitHub owner must start/end with alphanumeric, can contain hyphens" |

---

## Navigation & Safety

At complex prompts, remind users:
```
(Type 'back' to go to previous step, 'quit' to exit without saving)
```

Never save files without explicit confirmation.

---

## Smart Auto-Detection (P2)

### Detect Existing SCC Configuration

```python
# Check ~/.config/scc/config.json
if scc_config_exists:
    "Found existing SCC configuration"
    "Organization: {org_name} at {org_url}"

    Would you like to:
    1. Edit the active org config
    2. Create a new org config
    3. Start fresh (ignore existing)
```

### Detect Cached Org Config

```python
# Check ~/.cache/scc/org_config.json
if cached_org_config:
    "Found cached org config from {url}"
    "Last updated: {timestamp}"

    Would you like to edit this config?
```

---

## Reference Files (Advanced Mode Only)

- Schema: `supporting/org-schema.json`
- Presets: `supporting/org-presets.md`
- Questions: `supporting/org-questions.md`
- Examples: `supporting/examples/`

Quickstart and Guided modes use embedded defaults.

