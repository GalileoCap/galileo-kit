---
id: A99
from: [O12, O10, O9]
source: owner
status: decided 2026-11-17
kind: behaviour
implemented_by: [plugins/session-kit/hooks/options.ts, plugins/session-kit/.claude-plugin/plugin.json, docs/what-reaches-the-model.md, global/RATIONALE.md]
proven_by: [plugins/session-kit/hooks/context.test.tsx]
supersedes: [A68]
---

# A99 The warning and the cold floor start at 150,000 tokens

The context warning starts at 150,000 tokens, the figure the global rule names for asking for a compaction. Its tiers keep `A68`'s ratios: firmer at 1.2 times the trigger (180,000) and the order to stop at 1.6 times (240,000), a tier that rises warning at once. The cold-cache timer's floor stays the trigger, so it arms from 150,000 too.

## Context

`docs/analyses/memories-and-context-boundaries.md` read every session since 2026-11-01. The rule said 150,000 and the kit warned at 250,000, and sessions followed the kit: 212 of 286 `clear_point` calls came after its warning, at a median of 274,551 tokens. 44 of the 51 returns to a cold cache, 8.4 million tokens written to the cache again, sat between 150,000 and 250,000, where no timer armed. On 2026-11-17 the owner took the proposal and chose the figure: "Threshold: 150k".

## Options

- The rule says 250,000. Rejected by the owner.
- The timer's floor alone at 150,000, the warning left at 250,000. The cold returns argue for it, and it would spare handoffs in contexts that end soon anyway. Rejected: the owner chose one figure.

## Consequences

More handoffs and compactions, each at a smaller context. The stop tier now comes at 240,000, below where most compactions happened before. A project that wants another figure sets `thresholdTokens`, and the floor follows it unless `cacheFloorTokens` is set. The test suite pins 250,000 in the two cases that prove the dismissal and the projection, which do not depend on the figure.
