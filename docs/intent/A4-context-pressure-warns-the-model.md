---
id: A4
from: [O12, O5]
source: session
status: retired 2026-10-24
kind: check
implemented_by: [plugins/session-kit/hooks/context_pressure.py, plugins/session-kit/hooks/hooks.json]
proven_by: [plugins/session-kit/hooks/test_context_pressure.py]
supersedes: []
---

# A4 The context-pressure hook warns the model

After every tool call, a hook reads the transcript, and from half the window on tells the model every 25k tokens to find a clear point, commit, write the handoff and ask for a compaction.

## Context

The model is the one that knows where a clear point is, so the warning goes to it. It fires after tool calls, so it arrives while the model can still choose where to stop. Holding the end of every long turn was tried and dropped in 0.5.0: it put a closing paragraph about the context into every turn.

## Consequences

One Python start and a 256 kB transcript read per tool call of any kind. The window defaults to 1M tokens, set by `CLAUDE_KIT_CTX_WINDOW` since no API reports it, so on a 200k model that nobody set it for the trigger is never reached and the hook stays quiet. Reworked 2026-10-22. Retired 2026-10-24, superseded by `A16`: the hook and its test left `hooks.json` and the tree in session-kit 0.6.0, and git keeps them.
