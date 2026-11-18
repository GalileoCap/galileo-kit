---
id: A102
from: [O11, O13]
source: owner
status: decided 2026-11-17
kind: behaviour
implemented_by: [plugins/session-kit/hooks/context.tsx, plugins/session-kit/types/index.d.ts, docs/what-reaches-the-model.md]
proven_by: [plugins/session-kit/hooks/new_task.test.tsx]
supersedes: []
---

# A102 The first prompt after the person's Handoff and compact holds no task

After a compaction the person asked for with the band's Handoff and compact, their first prompt opens a context with no task to clear: `new_task` answers "nothing to clear" there, as in a new or just-cleared context (`A19`, one task per context). Their second prompt meets a context that holds the first's task, as before. A compaction the cold-cache timer ran is not the person's word, so a new task after it is still offered a clear.

## Context

`opensFreshContext` takes a context as fresh only when the engine counts no turn and holds no answer of the model's, which is never so after a compaction. So the owner's own handoff and compaction was followed, at the first prompt about other work, by an offer to hand off and clear again: 7 of 21 offers since 2026-11-01 came on the first prompt after a compaction, among them one four minutes after the owner's "Handoff and compact, and we'll discuss the next step" (`docs/analyses/memories-and-context-boundaries.md`). The owner took the proposal on 2026-11-17. `A101` covers the other owner-step end, which now clears, so the engine's own count holds there.

## Consequences

A summary of the last task stays in the context the new one starts in, a few thousand tokens. The mark is a named value of the session's, set at the compaction and spent by the person's first prompt.
