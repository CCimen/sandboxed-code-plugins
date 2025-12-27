---
description: Show the effective scc-safety-net policy (mode, source, rules)
allowed-tools: ["Bash"]
---

# SCC Safety Net Status

Effective policy:

- !`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scc_safety_net.py --status`

## What This Shows

- **Mode**: Current action mode (BLOCK/WARN/ALLOW)
- **Policy**: Path to the policy file being used
- **Blocked Operations**: Commands that will be blocked with safe alternatives
- **Allowed Operations**: Safe versions of commands that are always permitted

## Troubleshooting

If the status shows unexpected settings, check:
1. `SCC_POLICY_PATH` environment variable
2. `./.scc/effective_policy.json` in your workspace
3. `~/.cache/scc/org_config.json` for organization defaults

Run with `--json` flag for machine-readable output:
- !`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scc_safety_net.py --status --json`
