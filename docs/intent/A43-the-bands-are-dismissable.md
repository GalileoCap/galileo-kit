---
id: A43
from: [O11, O12]
source: owner
status: decided 2026-10-25
kind: behaviour
implemented_by: [plugins/session-kit/hooks/context.tsx, plugins/session-kit/types/index.d.ts]
proven_by: [plugins/session-kit/hooks/context.test.tsx, plugins/session-kit/hooks/chain.test.tsx, plugins/session-kit/hooks/new_task.test.tsx]
supersedes: []
---

# A43 The bands are dismissable

Each band `context.tsx` draws above the prompt carries a Dismiss button, marked `role="dismiss"` so a desktop draws its native close control. What a press does depends on the band. The context figure's band stays away until the figure moves a step (`step`, 25,000 tokens by default) past where it was dismissed, or falls below it after a compaction. The chain's band stops the chain where it stands. Dismissed before the turn ends, nothing runs. During the handoff, no compaction follows it, and during the compaction, no continue prompt follows it. The new task's band drops the offer and sends no prompt again, and dismissed while the handoff runs, no clear follows it.

## Context

The owner asked on 2026-10-25: "please make the bands dismissable". Every band stayed until its state changed: the figure's for the rest of the context, the chain's until a turn ended, the offer's until a press or an interrupted turn. A chain stuck at a stage held its line with no way to clear it.

## Options

- A press hides the band and leaves the state as it is. Rejected for the chain and the offer: a band that says the chain will compact, hidden while the compaction still runs, leaves the person unable to tell what the session is about to do.
- A press clears the band's state, so dismissing a pending action cancels it. Taken for the chain and the offer. The person stays the one who decides whether a context is compacted or cleared, as `A17` (the model signals a clear point, the mod runs the chain) and `A19` (one task per context) already have it.
- For the figure, hiding it for good. Rejected: the figure keeps growing, and the model's warning returns each step, so the person's band returns on the same cadence.

## Consequences

A compaction already asked of the engine when the chain's band is dismissed still completes: the engine offers no way to withdraw it. The module counts the dismissals in a variable of its own, beside the chain's state, so the step after a compaction never depends on whether the engine kept `$.state` through it. A hot reload loses that count, which at worst lets one dismissed chain continue after its compaction.

## Proof

Three engine tests, one per band. The chain's test fails when the count is not checked after a refused compaction (checked by hand on 0.22.0). Unverified in a real session: how the desktop app draws the dismiss control in the band.
