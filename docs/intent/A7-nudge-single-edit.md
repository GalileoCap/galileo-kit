---
id: A7
from: [O15]
source: session
status: decided 2026-10-11
kind: check
implemented_by: [plugins/session-kit/hooks/nudge.ts, plugins/session-kit/hooks/kit.tsx]
proven_by: [plugins/session-kit/hooks/nudge.test.ts]
supersedes: []
---

# A7 The single-edit nudge

A `tool.call` hook on Bash tells the model, when a Python heredoc makes a single edit, that the Edit tool is cheaper. The nudge rides the tool result as context.

## Context

Until 0.8.0 a settings hook, with a shell `case` filtering the input before Python started. Since 0.8.0 in-process, in `hooks/nudge.ts`: the heredoc body is classified by regex (a `re.sub`, a glob, several path literals, a loop or two replaces are left alone) where the Python hook parsed it with `ast`.

## Consequences

No process started. Low value on its own. It hung from a goal and no objective until `O15` was proposed, and is retired with `O15` if the owner cuts it.
