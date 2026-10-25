---
id: A19
from: [O11]
source: session
status: decided 2026-10-24
kind: behaviour
implemented_by: [not yet written: a rule in global/CLAUDE.md, then a new_task tool in the context module]
proven_by: unproven
supersedes: []
---

# A19 One task per context: the rule now, the signal with the port

Now: a rule in `global/CLAUDE.md` that a prompt unrelated to the task in `CLAUDE.local.md` is named as such, with the handoff and `/clear` proposed before it starts. With the port: the model calls a registered `new_task` tool and the mod offers the handoff and the clear in the band.

## Context

Nothing served `O11`. The only path was the owner running the handoff and `/clear` by hand. A cold cache makes the case stronger: clearing then avoids paying the cache write on a context about to be abandoned.

## Options

- 1. The rule alone. Costs nothing, and is prose, the kind of rule `O5` exists because prose fails to hold. Taken as the interim.
- 2. The model signals through a tool, the mod offers the clear. Taken as the port's form, with `A17`'s tool beside it.
- 3. The mod judges every prompt above a context size with one small model call that compares it to the handoff's task, drops it once on "unrelated" and offers the clear. Rejected: a model call per prompt, and a false "unrelated" costs the owner a resend.

## Consequences

The rule is written at the port's step 5. Validated when a session names a change of idea before starting on it. Undone if the rule is ignored as the others were, in which case only the tool remains.
