---
id: A12
from: [O14]
source: session
status: decided 2026-10-11
kind: behaviour
implemented_by: [plugins/session-kit/hooks/direnv_env.sh, plugins/session-kit/hooks/hooks.json]
proven_by: [plugins/session-kit/hooks/test_direnv_env.sh]
supersedes: []
---

# A12 The direnv environment

On SessionStart, CwdChanged and FileChanged, a hook exports the project's direnv environment into `CLAUDE_ENV_FILE`, which Claude Code sources before each Bash command.

## Context

A session's commands ran without the project's environment, so tools the owner has on PATH were missing.

## Consequences

Rare events, near zero cost. The 2.1.308 mod types have no equivalent of `CLAUDE_ENV_FILE`, so it stays a settings hook.
