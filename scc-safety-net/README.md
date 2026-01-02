# SCC Safety Net

A Claude Code plugin that blocks destructive git commands before they execute. Protects remote history and uncommitted work from accidental force pushes, hard resets, and file deletions.

Part of the [SCC (Sandboxed Code CLI)](https://github.com/CCimen/scc) ecosystem.

> **Part of [Sandboxed Code Plugins](https://github.com/CCimen/sandboxed-code-plugins)** - the official plugin marketplace for Claude Code

## What Gets Blocked

| Command | Risk | Use Instead |
|---------|------|-------------|
| `git push --force` | Overwrites remote history | `git push --force-with-lease` |
| `git push +main` | Force push via refspec | `git push --force-with-lease` |
| `git push --mirror` | Overwrites entire remote | `git push` (regular) |
| `git reset --hard` | Destroys uncommitted changes | `git stash` |
| `git reflog expire --expire-unreachable=now` | Destroys recovery history | Don't expire manually |
| `git gc --prune=now` | Immediately deletes objects | `git gc` (default prune) |
| `git filter-branch` | Rewrites history destructively | `git filter-repo` |
| `git branch -D` | Deletes without merge check | `git branch -d` |
| `git stash drop/clear` | Permanently loses stashed work | Review first |
| `git clean -f` | Deletes untracked files | `git clean -n` (dry-run) |
| `git checkout -- <file>` | Discards file changes | `git stash` |
| `git restore <file>` | Discards worktree changes | `git restore --staged` |

Bypass attempts through `sudo`, `bash -c`, and command chaining are also caught.

## Installation with SCC

SCC Safety Net is distributed via the [SCC marketplace](https://github.com/CCimen/sandboxed-code-plugins).

First, install [SCC](https://github.com/CCimen/scc) if you haven't:

```bash
pip install scc-cli
# or
pipx install scc-cli
```

Then enable the plugin in your org config:

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
    "enabled_plugins": ["scc-safety-net@sandboxed-code-official"]
  }
}
```

Start SCC normally. The plugin loads automatically:

```bash
scc start ~/my-project
```

For local testing without SCC, add to Claude Code's `settings.json`:

```json
{
  "plugins": ["/path/to/scc-safety-net"]
}
```

## Usage

Protection is automatic. When you hit a blocked command:

```
> git push --force origin main

BLOCKED: Force push destroys remote history.
Safe alternative: git push --force-with-lease
```

Check current policy with `/scc-safety-net:status`.

## Configuration

Policy is loaded from (first found wins):
1. `SCC_POLICY_PATH` environment variable
2. `./.scc/effective_policy.json`
3. `~/.cache/scc/org_config.json`
4. Built-in defaults (block mode)

### SCC Org Config Examples

#### Minimal Example (Quick Enable)

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
    "enabled_plugins": ["scc-safety-net@sandboxed-code-official"]
  }
}
```

#### Full Example (With Policy Configuration)

```json
{
  "organization": {
    "name": "my-organization"
  },
  "marketplaces": {
    "sandboxed-code-official": {
      "source": "github",
      "owner": "CCimen",
      "repo": "sandboxed-code-plugins"
    }
  },
  "security": {
    "safety_net": {
      "action": "block",
      "block_force_push": true,
      "block_reset_hard": true,
      "block_branch_force_delete": true,
      "block_checkout_restore": true,
      "block_clean": true,
      "block_stash_destructive": true
    }
  },
  "defaults": {
    "enabled_plugins": ["scc-safety-net@sandboxed-code-official"]
  },
  "profiles": {
    "devops": {
      "additional_plugins": ["some-devops-plugin@internal-marketplace"]
    }
  }
}
```

> **Policy Scope Note:**
> - **In SCC mode:** `SCC_POLICY_PATH` is set by SCC, so org policy takes precedence. Teams/projects cannot override.
> - **Standalone mode:** Workspace policy (`./.scc/effective_policy.json`) can override because no SCC environment variable is set.

### Action Modes

| Mode | Behavior |
|------|----------|
| `block` | Stop execution, show error (default) |
| `warn` | Show warning, allow execution |
| `allow` | No checks |

Set any rule to `false` to disable that specific check.

## How It Works

1. SCC materializes the plugin when starting a sandbox
2. Plugin registers a PreToolUse hook that intercepts Bash commands
3. Hook analyzes commands before Claude Code executes them
4. Dangerous commands are blocked with helpful alternatives

The plugin uses exit code 2 + stderr for blocking, which Claude receives as feedback.

## Development

```bash
cd scc-safety-net

# Run tests
uv run pytest

# Lint and format
uv run ruff check --fix scripts/ tests/
uv run ruff format scripts/ tests/
```

258 tests cover git rules, shell parsing, policy loading, secret redaction, and end-to-end hook behavior.

## Related

- [SCC (Sandboxed Code CLI)](https://github.com/CCimen/scc) - The main CLI for sandboxed AI development
- [SCC Marketplace](https://github.com/CCimen/sandboxed-code-plugins) - Official plugin repository

## License

MIT
