---
id: A101
from: [O11, O12, O9]
source: owner
status: decided 2026-11-17
kind: behaviour
implemented_by: [plugins/session-kit/hooks/context.tsx, plugins/session-kit/hooks/lines.ts, plugins/session-kit/types/index.d.ts, plugins/session-kit/.claude-plugin/plugin.json, global/CLAUDE.md, global/RATIONALE.md, docs/what-reaches-the-model.md]
proven_by: [plugins/session-kit/hooks/chain.test.tsx]
supersedes: []
---

# A101 An owner-step clear point clears, and the kit alone writes the handoff

`clear_point` with `next_step: owner` writes the handoff when the turn ends and then runs `/clear` instead of `/compact`, and the band says "Cleared. The next step is yours". The owner's next prompt starts from `CLAUDE.local.md` alone. With `next_step: session` the chain compacts and continues as `A17` (the model signals, the mod acts) set it, and a chain the judge stopped still compacts, so the owner can read what it did. The tool's text, its result and the global rule say the kit writes the handoff and the session never writes it first, and that a handoff the owner asks for is `clear_point` with `next_step: owner`.

## Context

`docs/analyses/memories-and-context-boundaries.md`: the owner said "Handoff and clear" three times and each time got a compaction, since `clear_point` had no clear behind it, and once the next prompt drew a `new_task` offer for the old task the summary kept. 145 of 286 `clear_point` calls followed a handoff the session had just written, and the kit then wrote it again: the rule said "write `CLAUDE.local.md` and end the turn asking to compact" while the tool said the kit writes it. The owner took both proposals on 2026-11-17.

## Options

- The kit skips its own handoff when `CLAUDE.local.md` was written in the same turn. Rejected for now: the kit's facts section and the question carried into the file come with its own handoff, and the text change costs nothing.
- A third value of `next_step` for a clear. Rejected: a summary is worth least when the owner takes the next step.

## Consequences

A context ended for the owner keeps no summary, only the file, so a handoff that misses something loses it. The clear starts the session's named values over, so the band's waiting row is written after `/clear` returns. A failed clear stays on the band with Try again, which runs the clear again.
