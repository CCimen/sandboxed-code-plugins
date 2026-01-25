# Team Config Wizard Question Bank

Reference questions for the `/scc-wizard:team` skill.

## Mode Selection

**Question:** "What would you like to do?"
**Options:**
- Create new team config
- Edit existing team config

## Team Context

**Question:** "What's the team name?"
**Hint:** This is for documentation and context; it doesn't appear in the JSON.

## Org Marketplace Context

**Question:** "Which org marketplaces are available to your team?"
**Hint:** List the marketplace names from your org config's `marketplaces` section.

**Example response:** "sandboxed-code-official, internal-gitlab"

## Marketplace Trust

**Question:** "Is your team trusted to add additional marketplaces?"
**Options:**
- Yes - Org has `trust.allow_additional_marketplaces: true` for our team
- No - We can only use org-defined marketplaces
- Not sure - Check with org admin or review org config

## Plugin Collection

**Question:** "What plugins should this team enable?"
**Hint:** Use format `plugin-name@marketplace`. Enter one per line or comma-separated.

**Example:**
```
changelog-generator@sandboxed-code-official
code-review@sandboxed-code-official
custom-tool@internal-gitlab
```

## Disabled Plugin Patterns

**Question:** "Any plugins to disable from org defaults?"
**Hint:** Use glob patterns. Leave empty if none.

**Example:**
```
legacy-tool@*
*-deprecated
```

## Marketplace Addition (If Trusted)

**Question:** "Do you want to add a team-defined marketplace?"
**Options:**
- Yes
- No

**Follow-up if Yes:**
- Marketplace name?
- Source type? (github / git / url / directory)
- [Fields based on type]

## Marketplace URL Pattern Check

**Question:** "Your org allows marketplaces from these patterns: `<patterns>`"
**Validation:** Ensure any URLs match these patterns.

## Edit Section Selection

**Question:** "What would you like to edit?"
**Options:**
- Add plugins
- Remove plugins
- Add disabled patterns
- Remove disabled patterns
- Add marketplace (if trusted)
- Remove marketplace
- Edit marketplace

## File Path Confirmation

**Question:** "Where should I write the team config?"
**Suggestions:**
- `./team-config.json`
- `./scc/team-config.json`
- Custom path

## Overwrite Confirmation

**Question:** "File already exists at `<path>`. Overwrite?"
**Options:**
- Yes, overwrite
- No, choose different path
