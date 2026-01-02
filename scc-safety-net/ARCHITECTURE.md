# SCC Safety-Net Plugin: Architecture & Integration Analysis

> **Version**: 0.2.0
> **Last Updated**: January 2026
> **Purpose**: Comprehensive documentation of how the safety-net plugin works and integrates with SCC

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Plugin Components](#plugin-components)
4. [Command Analysis Pipeline](#command-analysis-pipeline)
5. [Policy System](#policy-system)
6. [SCC Integration](#scc-integration)
7. [Hook Execution Flow](#hook-execution-flow)
8. [Security Model](#security-model)
9. [Test Coverage](#test-coverage)
10. [Current Gaps & Improvement Opportunities](#current-gaps--improvement-opportunities)
11. [Recommended Roadmap](#recommended-roadmap)

---

## Executive Summary

The **scc-safety-net** plugin is a Claude Code PreToolUse hook that intercepts and blocks destructive git commands before execution. It provides a defense-in-depth layer within the SCC ecosystem, protecting remote repository history and uncommitted local work.

### Key Characteristics

| Aspect | Value |
|--------|-------|
| Plugin Version | 0.2.0 |
| Hook Type | PreToolUse (Bash matcher) |
| Exit Codes | 0 = allow, 2 = block |
| Default Mode | Block (fail-safe) |
| Test Coverage | 258 tests |
| Policy Modes | block, warn, allow |

### Blocked Operations

| Command | Risk Level | Safe Alternative |
|---------|-----------|------------------|
| `git push --force` / `-f` / `+refspec` | Critical | `git push --force-with-lease` |
| `git push --mirror` | Critical | `git push` (regular) |
| `git reset --hard` | High | `git stash` |
| `git reflog expire --expire-unreachable=now` | Critical | Don't expire manually |
| `git gc --prune=now` | Critical | `git gc` (default prune) |
| `git filter-branch` | Critical | `git filter-repo` |
| `git branch -D` | Medium | `git branch -d` |
| `git stash drop/clear` | Medium | Review with `git stash list` |
| `git clean -f` | High | `git clean -n` (dry-run) |
| `git checkout -- <path>` | Medium | `git stash` |
| `git restore <path>` | Medium | `git restore --staged` |

---

## Architecture Overview

### Three-Layer Security Model

```
┌─────────────────────────────────────────────────────────────────┐
│                     SCC ECOSYSTEM                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   LAYER 1: SCC CLI                        │   │
│  │  • Organization config management                         │   │
│  │  • Policy materialization                                 │   │
│  │  • Plugin marketplace integration                         │   │
│  │  • Docker sandbox orchestration                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │               LAYER 2: Docker Sandbox                     │   │
│  │  • Container isolation                                    │   │
│  │  • Read-only policy mounting                              │   │
│  │  • Environment variable injection                         │   │
│  │  • Network/filesystem restrictions                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │            LAYER 3: Plugin Guardrails                     │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │              scc-safety-net Plugin                  │  │   │
│  │  │  • PreToolUse hook on Bash commands                 │  │   │
│  │  │  • Command tokenization & analysis                  │  │   │
│  │  │  • Policy-driven blocking/warning                   │  │   │
│  │  │  • Safe alternative suggestions                     │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow Overview

```
User Request (e.g., "push my changes forcefully")
                    │
                    ▼
┌─────────────────────────────────────┐
│           Claude Code               │
│   Generates: git push --force       │
└─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────┐
│       PreToolUse Hook Trigger       │
│   Tool: Bash                        │
│   Command: git push --force         │
└─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────┐
│      scc_safety_net.py              │
│   Receives JSON on stdin            │
└─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────┐
│      Command Analysis Pipeline      │
│   1. Split on operators             │
│   2. Tokenize (POSIX)               │
│   3. Strip wrappers                 │
│   4. Extract bash -c                │
│   5. Analyze git subcommand         │
└─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────┐
│        Policy Evaluation            │
│   Mode: block | warn | allow        │
│   Rule: block_force_push = true     │
└─────────────────────────────────────┘
                    │
                    ▼
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌───────────────┐       ┌───────────────┐
│   BLOCKED     │       │   ALLOWED     │
│   Exit: 2     │       │   Exit: 0     │
│   stderr msg  │       │   (silent)    │
└───────────────┘       └───────────────┘
```

---

## Plugin Components

### File Structure

```
scc-safety-net/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest (name, version, metadata)
├── hooks/
│   └── hooks.json               # Hook registration (PreToolUse → Bash)
├── commands/
│   └── status.md                # Slash command: /scc-safety-net:status
├── scripts/
│   ├── scc_safety_net.py        # Main entry point (hook + status CLI)
│   └── scc_safety_impl/
│       ├── __init__.py          # Package init (version 0.2.0)
│       ├── shell.py             # Shell tokenization & command extraction
│       ├── git_rules.py         # Git-specific destructive pattern detection
│       ├── hook.py              # Hook orchestration & policy application
│       ├── policy.py            # Policy loading, resolution & rendering
│       └── redact.py            # Secret redaction & output sanitization
├── tests/
│   ├── conftest.py              # Pytest fixtures
│   ├── test_shell.py            # 44 tests - tokenization
│   ├── test_git_rules.py        # 100 tests - pattern matching
│   ├── test_redact.py           # 21 tests - secret redaction
│   ├── test_hook.py             # 47 tests - orchestration & E2E
│   └── test_policy.py           # 46 tests - policy handling
├── README.md                    # User documentation
├── pyproject.toml               # Build configuration
└── ARCHITECTURE.md              # This file
```

### Component Responsibilities

| Component | File | Responsibility |
|-----------|------|----------------|
| **Entry Point** | `scc_safety_net.py` | Hook handler + `--status` CLI command |
| **Shell Parser** | `shell.py` | POSIX tokenization, operator splitting, wrapper stripping |
| **Git Analyzer** | `git_rules.py` | 7 subcommand analyzers for destructive patterns |
| **Orchestrator** | `hook.py` | Coordinates analysis, applies policy, returns verdict |
| **Policy Manager** | `policy.py` | 4-tier resolution, fail-safe defaults, status rendering |
| **Secret Redactor** | `redact.py` | Masks secrets in error output, truncates long messages |

---

## Command Analysis Pipeline

### Stage 1: Command Splitting

Handles shell operators to analyze each command segment independently.

```python
split_commands("git add . && git push -f; echo done")
# Returns: ['git add .', 'git push -f', 'echo done']
```

**Operators handled**: `;`, `&&`, `||`, `|`

### Stage 2: POSIX Tokenization

Properly parses quoted strings and special characters.

```python
tokenize("git commit -m 'Fix bug'")
# Returns: ['git', 'commit', '-m', 'Fix bug']
```

### Stage 3: Wrapper Stripping

Removes command wrappers that could hide the actual command.

```python
strip_wrappers(['sudo', '-u', 'root', 'git', 'push', '-f'])
# Returns: ['git', 'push', '-f']
```

**Wrappers stripped**: `sudo`, `env`, `command`, `nice`, `nohup`, `time`

### Stage 4: Bash -c Extraction

Recursively extracts commands from nested bash invocations (depth-limited to 3).

```python
extract_bash_c(['bash', '-c', 'git push --force'])
# Returns: 'git push --force'
```

### Stage 5: Git Subcommand Analysis

Routes to specialized analyzers based on git subcommand.

| Subcommand | Analyzer Function | Patterns Detected |
|------------|-------------------|-------------------|
| `push` | `analyze_push()` | `--force`, `-f`, `+refspec`, combined flags |
| `reset` | `analyze_reset()` | `--hard` |
| `branch` | `analyze_branch()` | `-D`, `--delete --force` |
| `stash` | `analyze_stash()` | `drop`, `clear` |
| `clean` | `analyze_clean()` | `-f`, `--force`, combined flags |
| `checkout` | `analyze_checkout()` | `-- <path>` (path checkout) |
| `restore` | `analyze_restore()` | Worktree restore (not `--staged`) |

### Global Git Options Handling

Correctly skips git global options before identifying subcommand:

```python
normalize_git_tokens(['git', '-C', '/path', '-c', 'user.name=x', 'push', '-f'])
# Returns: ['push', '-f']  (skips -C, -c and their arguments)
```

---

## Policy System

### Resolution Priority (First Match Wins)

```
1. SCC_POLICY_PATH environment variable     ← Set by SCC container
2. ./.scc/effective_policy.json             ← Workspace-local
3. ~/.cache/scc/org_config.json             ← SCC cache
4. Built-in DEFAULT_POLICY                  ← Fail-safe (block all)
```

### Default Policy (Fail-Safe)

```python
DEFAULT_POLICY = {
    "action": "block",                    # block | warn | allow
    "block_force_push": True,
    "block_reset_hard": True,
    "block_branch_force_delete": True,
    "block_checkout_restore": True,
    "block_clean": True,
    "block_stash_destructive": True,
}
```

### Policy Configuration Formats

**Direct format:**
```json
{
  "action": "block",
  "block_force_push": true,
  "block_reset_hard": true
}
```

**Nested format (SCC org config):**
```json
{
  "organization": {
    "name": "my-company"
  },
  "security": {
    "safety_net": {
      "action": "block",
      "block_force_push": true,
      "block_reset_hard": true
    }
  }
}
```

Both formats are automatically detected and normalized.

### Action Modes

| Mode | Behavior | Exit Code | Use Case |
|------|----------|-----------|----------|
| `block` | Stops execution, shows error with alternative | 2 | Production (default) |
| `warn` | Allows execution, shows warning | 0 | Development/training |
| `allow` | No checks performed | 0 | Trusted environments |

### Rule Granularity

Individual rules can be disabled:

```json
{
  "action": "block",
  "block_force_push": true,
  "block_reset_hard": false,    // Allows git reset --hard
  "block_clean": true
}
```

---

## SCC Integration

### Integration Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        SCC CLI                                │
│                                                               │
│  1. Load org config from URL/GitHub                          │
│  2. Merge: org defaults → team profile → project overrides   │
│  3. Extract security.safety_net section                      │
│  4. Generate effective_policy.json                           │
│  5. Build Docker command with:                               │
│     - Mount policy file (read-only)                          │
│     - Set SCC_POLICY_PATH environment variable               │
│     - Enable plugins from marketplace                        │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                    Docker Sandbox                             │
│                                                               │
│  Environment:                                                 │
│    SCC_POLICY_PATH=/scc/effective_policy.json                │
│                                                               │
│  Mounts:                                                      │
│    /scc/effective_policy.json:ro                             │
│                                                               │
│  Plugins:                                                     │
│    scc-safety-net@sandboxed-code-official                    │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                  Claude Code + Plugin                         │
│                                                               │
│  Plugin loads policy from SCC_POLICY_PATH                    │
│  Hook intercepts Bash commands                               │
│  Policy cannot be overridden by workspace files              │
└──────────────────────────────────────────────────────────────┘
```

### SCC Org Config Example

```json
{
  "organization": {
    "name": "Safety-First Corp",
    "id": "safety-first-corp"
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
  }
}
```

### Marketplace Integration

Plugins are distributed via GitHub-based marketplaces:

```json
{
  "marketplaces": {
    "sandboxed-code-official": {
      "source": "github",
      "owner": "CCimen",
      "repo": "sandboxed-code-plugins"
    }
  }
}
```

Plugin key format: `{plugin-name}@{marketplace-key}`
Example: `scc-safety-net@sandboxed-code-official`

---

## Hook Execution Flow

### Hook Registration

**File**: `hooks/hooks.json`

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scc_safety_net.py"
      }]
    }]
  }
}
```

### Input Contract

The hook receives JSON on stdin:

```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "git push --force origin main"
  },
  "cwd": "/workspace/my-project"
}
```

### Output Contract

| Exit Code | Meaning | Stderr Output |
|-----------|---------|---------------|
| 0 | Allow execution | Empty (or warning message in warn mode) |
| 2 | Block execution | Error message with safe alternative |

### Example Block Message

```
BLOCKED: Force push destroys remote history.
Safe alternative: git push --force-with-lease
```

### Sequence Diagram

```
Claude Code          PreToolUse Hook         scc_safety_net.py
    │                      │                        │
    │  Execute Bash        │                        │
    │  "git push -f"       │                        │
    │─────────────────────>│                        │
    │                      │                        │
    │                      │  Invoke hook script    │
    │                      │  (JSON on stdin)       │
    │                      │───────────────────────>│
    │                      │                        │
    │                      │                        │  parse JSON
    │                      │                        │  load policy
    │                      │                        │  analyze command
    │                      │                        │  → BLOCKED
    │                      │                        │
    │                      │  Exit code 2           │
    │                      │  stderr: "BLOCKED..."  │
    │                      │<───────────────────────│
    │                      │                        │
    │  Block execution     │                        │
    │  Show error message  │                        │
    │<─────────────────────│                        │
    │                      │                        │
```

---

## Security Model

### Defense-in-Depth Principles

1. **Fail-Safe Defaults**: Missing or invalid config → block mode
2. **Multi-Layer Bypass Detection**: Catches sudo, bash -c, operators, paths
3. **Read-Only Policy**: SCC mounts policy file with `:ro` flag
4. **Environment Priority**: SCC_POLICY_PATH overrides workspace config
5. **Depth Limiting**: Bash -c recursion limited to 3 to prevent DoS

### Attack Vector Coverage

| Attack Vector | Protection | Status |
|---------------|------------|--------|
| `sudo git push -f` | Wrapper stripping | ✅ Covered |
| `bash -c "git push -f"` | Recursive extraction | ✅ Covered |
| `git push -f && echo ok` | Operator splitting | ✅ Covered |
| `/usr/bin/git push -f` | Path normalization | ✅ Covered |
| `git -C /path push -f` | Global option skipping | ✅ Covered |
| `env GIT_DIR=x git push -f` | Wrapper stripping | ✅ Covered |
| Nested `bash -c` (3+ levels) | Depth limiting | ✅ Covered |
| `echo "git push -f" \| bash` | Piped commands | ⚠️ Partial |
| Heredocs | - | ❌ Not covered |
| Git aliases | - | ❌ Not covered |

### Tested Attack Vectors

From `test_hook.py`:

```python
attacks = [
    "sudo bash -c 'git push -f'",
    "env HOME=/tmp git push --force",
    "git -C /path push --force",
    "echo foo && git reset --hard",
    "/usr/bin/git push +main",
    "bash -c \"bash -c 'git branch -D main'\"",
]
# All correctly detected and blocked
```

---

## Test Coverage

### Test Summary

| Test File | Tests | Coverage Area |
|-----------|-------|---------------|
| `test_shell.py` | 44 | POSIX tokenization, operators, wrappers |
| `test_git_rules.py` | 100 | Pattern matching, flag detection, analyzers |
| `test_hook.py` | 47 | Orchestration, E2E flows, attack vectors |
| `test_policy.py` | 46 | Resolution, loading, rendering, fail-safes |
| `test_redact.py` | 21 | Secret redaction, output truncation |
| **Total** | **258** | |

### Test Categories

**Unit Tests:**
- Individual function behavior with edge cases
- Error handling and graceful degradation

**Integration Tests:**
- Multi-component workflows
- Policy application across analysis pipeline

**Attack Vector Tests:**
- Bypass attempt detection
- Nested command extraction
- Wrapper/operator combinations

**Policy Tests:**
- All three action modes
- Partial rule configurations
- Nested config format extraction

### Running Tests

```bash
cd scc-safety-net
uv run pytest                    # Run all tests
uv run pytest -v                 # Verbose output
uv run pytest tests/test_hook.py # Specific file
uv run pytest -k "force_push"    # Pattern matching
```

---

## Current Gaps & Improvement Opportunities

### High Priority

| Gap | Description | Impact | Effort |
|-----|-------------|--------|--------|
| **Policy Delivery** | SCC CLI passes `env_vars=None` to Docker | Policy not enforced via SCC | Medium |
| **Audit Logging** | No record of blocked commands | No visibility for security teams | Medium |
| **Integration Tests** | No E2E tests between SCC and plugin | Integration bugs possible | Medium |

### Medium Priority

| Gap | Description | Impact | Effort |
|-----|-------------|--------|--------|
| **Additional Commands** | `git rebase --force`, `git filter-branch`, `git reflog expire` not blocked | Incomplete coverage | Low |
| **Heredoc Detection** | `bash <<EOF ... git push -f ... EOF` not analyzed | Bypass vector | High |
| **Pipe Detection** | `echo "git push -f" \| bash` partially handled | Bypass vector | Medium |
| **Policy Hot-Reload** | Requires container restart to update policy | Operational friction | Medium |

### Low Priority

| Gap | Description | Impact | Effort |
|-----|-------------|--------|--------|
| **Git Alias Resolution** | `git fpush` (alias for push -f) not detected | Edge case bypass | High |
| **Metrics/Telemetry** | No dashboard for blocked operations | Limited visibility | Medium |
| **Temporary Allowlist** | No mechanism for one-time override | Friction for legitimate use | Medium |
| **Custom Rules** | Users cannot add their own patterns | Limited extensibility | High |

### Bypass Vectors Not Covered

1. **Heredocs**:
   ```bash
   bash <<'EOF'
   git push --force
   EOF
   ```

2. **Git Aliases**:
   ```bash
   git config alias.fpush "push --force"
   git fpush  # Not detected
   ```

3. **Process Substitution**:
   ```bash
   bash <(echo "git push -f")
   ```

4. **Environment Variable Expansion**:
   ```bash
   CMD="git push -f"
   $CMD  # Not analyzed
   ```

---

## Recommended Roadmap

### Phase 1: Complete SCC Integration (High Priority)

**Goal**: Full policy delivery from SCC to plugin

1. **Wire SCC_POLICY_PATH** in SCC CLI (`cli.py`)
   - Generate `effective_policy.json` from org config
   - Pass path via Docker `-e` flag
   - Mount file read-only

2. **Add Integration Tests**
   - E2E test: SCC → Docker → Plugin → Block
   - Policy precedence verification
   - Hot-path performance benchmarks

3. **Add Audit Logging**
   - Log blocked commands with timestamp, user, reason
   - Integration with SCC audit system
   - Optional JSON output for SIEM integration

### Phase 2: Expand Coverage (Medium Priority)

**Goal**: Block additional destructive commands

1. **Add Analyzers For**:
   - `git rebase --force` / `git rebase --onto` with history rewrite
   - `git filter-branch` (history rewriting)
   - `git reflog expire` (reflog deletion)
   - `git gc --prune=now` (aggressive garbage collection)
   - `git push --mirror` (can destroy remote)

2. **Improve Shell Analysis**:
   - Heredoc detection and extraction
   - Improved pipe command analysis
   - Process substitution detection

### Phase 3: Enhanced UX (Lower Priority)

**Goal**: Better developer experience

1. **Policy Hot-Reload**
   - Watch for policy file changes
   - Reload without container restart

2. **Metrics Dashboard**
   - Blocked command counts by type
   - Top blocked patterns
   - Time-series visualization

3. **Temporary Allowlist**
   - `/scc-safety-net:allow-once git push --force`
   - Requires justification
   - Logged for audit

### Phase 4: Extensibility (Future)

**Goal**: User-defined rules

1. **Custom Rule Syntax**
   ```json
   {
     "custom_rules": [{
       "pattern": "git push.*--mirror",
       "action": "block",
       "message": "Mirror push is not allowed"
     }]
   }
   ```

2. **Git Alias Resolution**
   - Parse `.gitconfig` for alias definitions
   - Expand aliases before analysis

---

## Appendix: Quick Reference

### Status Command

```bash
# Show current policy status
/scc-safety-net:status

# JSON output for scripting
/scc-safety-net:status --json
```

### Environment Variables

| Variable | Purpose | Set By |
|----------|---------|--------|
| `SCC_POLICY_PATH` | Override policy file location | SCC container |
| `CLAUDE_PLUGIN_ROOT` | Plugin installation directory | Claude Code |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Allow command execution |
| 2 | Block command execution |

### Policy File Locations

| Priority | Path | Description |
|----------|------|-------------|
| 1 | `$SCC_POLICY_PATH` | Environment override |
| 2 | `./.scc/effective_policy.json` | Workspace local |
| 3 | `~/.cache/scc/org_config.json` | SCC cache |
| 4 | (built-in) | Fail-safe defaults |

---

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for development guidelines.

## License

MIT License - See [LICENSE](../LICENSE) for details.
