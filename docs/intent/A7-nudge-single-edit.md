---
id: A7
from: [O15]
source: session
status: decided 2026-10-11
kind: check
implemented_by: [plugins/session-kit/hooks/nudge_single_edit.py, plugins/session-kit/hooks/hooks.json]
proven_by: unproven
supersedes: []
---

# A7 The single-edit nudge

A PreToolUse hook on Bash tells the model, when a Python heredoc makes a single edit, that the edit tool is cheaper.

## Context

A shell `case` filters the input before Python starts, so only Python heredocs pay the start.

## Consequences

Near zero cost. Low value on its own. It hung from a goal and no objective until `O15` was proposed, and is retired with `O15` if the owner cuts it. No test proves it.
