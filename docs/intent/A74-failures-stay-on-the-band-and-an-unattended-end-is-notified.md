---
id: A74
from: [O6, O12]
source: session
status: decided 2026-10-26
kind: behaviour
implemented_by: [plugins/session-kit/hooks/context.tsx, plugins/session-kit/hooks/band.tsx, plugins/session-kit/types/index.d.ts]
proven_by: [plugins/session-kit/hooks/ui.test.tsx]
supersedes: []
---

# A74 Failures stay on the band and an unattended end is notified

A handoff, a compaction, a clear or an effort that did not run leaves a `Failed` row on the band, above the others, until the person dismisses it. A chain's failure carries `Try again`, which runs the stage again with the note and the owner's say the chain had. The others have Dismiss alone. A toast goes out only where no band is drawn, with the same words. The kit also tells the person's notifications (`$.ui.notify`) when a chain ends its compaction with the next step theirs and when a chain fails, since the person may be away. A chain that continues by itself says nothing.

## Context

A failure that stops the chain was a toast on a timer, and the person away saw nothing. The record of a failed step is `O6` (a step that matters leaves a record a program wrote), and a failed compaction loses the continuity `O12` guards.

## Options

- The toast kept on every surface beside the row. Rejected: it says the same thing twice where the band is drawn.
- The wording of the `session-kit chain:` transcript rows changed. Not done: the chain file and the tests read those words, and the row now carries the plain sentence.
- A notification for every failure. Rejected: the new-task flow has the person at the screen, so only a chain's failures notify.

## Consequences

`failure` lives in `$.state`, so a reload keeps it. A retry of the handoff restarts the chain from its handoff stage. Whether `$.ui.notify` reaches the person depends on the engine's channel settings. A refusal is not an error.

## Proof

Kept: a chain's handoff that does not run leaves the `Failed` row with `Try again` and `Dismiss` until dismissed, with no toast on a terminal. `Try again` runs the handoff or the compaction again from where it stopped. A chain ending its compaction waiting on the owner notifies while one that continues says nothing. Deleted once they passed: the clear's row without a retry, the toast on a phone, and the unattended failure's notice.
