---
id: A106
from: [O12, O11, O9]
source: owner
status: decided 2026-11-18
kind: behaviour
implemented_by: [plugins/session-kit/hooks/context.tsx, plugins/session-kit/hooks/lines.ts, plugins/session-kit/types/index.d.ts, plugins/session-kit/.claude-plugin/plugin.json, global/CLAUDE.md, docs/what-reaches-the-model.md]
proven_by: [plugins/session-kit/hooks/chain.test.tsx]
supersedes: [A101]
---

# A106 An owner-step clear point compacts, and clears only on the owner's word

`clear_point` with `next_step: owner` writes the handoff when the turn ends, compacts, and stops, and the band says "Compacted. The next step is yours". It clears instead only when the call sets `clear`, which the tool's text keeps for a clear the owner's own words asked for. The band then says "Cleared. The next step is yours", as `A101` set it. `clear` with `next_step: session` is refused, since a clear stops the chain. The kit alone writes the handoff, as before.

## Context

On 2026-11-18 tagents' lane4 session, at 181,000 tokens, answered a list of the owner's comments and called `clear_point` with `next_step: owner` in the same turn, since the next step was the owner's answer. Under `A101` the kit cleared. The reply the owner was about to answer vanished from the chat, and so did the discussion it rested on. The owner had asked for no clear, and expected a compaction. The new session copied the reply back from the transcript. `A101` came from the owner's "Handoff and clear", but `next_step: owner` is also what a session uses at every context warning that lands in a discussion, where a clear costs the most. The pending-question guard did not hold, because it reads only the next-step box and the question was in prose. The owner approved the change on 2026-11-18.

## Options

- Read the owner's last prompt for a word like "clear". Rejected: a guess over free text, and wrong both ways.
- Keep the clear and widen the guard to any reply ending in a question. Rejected: the discussion is lost even when the reply asks nothing.

## Consequences

A context ended for the owner keeps a summary again, a few thousand tokens. A session that sets `clear` unasked costs what `A101` cost, and one that misses a clear the owner asked for costs only a summary.
