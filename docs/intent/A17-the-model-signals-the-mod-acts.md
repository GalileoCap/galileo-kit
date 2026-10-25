---
id: A17
from: [O5, O12]
source: session
status: decided 2026-10-24
kind: behaviour
implemented_by: [not yet written: the context module of the session-kit mod, behind a userConfig toggle]
proven_by: unproven
supersedes: []
---

# A17 The model signals a clear point, the mod runs the chain

The mod registers a tool, `clear_point`, and the warning names it. At a clear point the model calls it. When that turn ends the mod runs `/session-kit:handoff`, compacts with `$.session.compact`, and submits a continue prompt that says to read again the documents the handoff lists. When the handoff's next step waits on the owner, the mod stops after the compaction and the band says the next step is theirs.

## Context

The owner's idea: the warning acted on without the model reading it, and the handoff, compaction and continue run by the mod. Hiding the warning saves about 1,600 tokens a session at cache-read prices, so the saving is in the steps the owner stops running by hand. Only the model knows whether it is half way through a step or ended on a question, so the model says when, and the mod does the rest.

## Options

- A. The owner runs the chain by hand: `A16` alone. Leaves `O5` unmet here.
- B. The model calls a tool at the clear point, the mod runs the chain. Taken. The risk is a call at the wrong moment, held by the warning text and the tool's description, which carry the definition of a clear point.
- C. The mod decides alone. Rejected, as in `A16`.

## Consequences

Off by default until it has run in a few real sessions. A continue prompt submitted without `asUser` reaches the model framed as the plugin's. To try with it, unverified: one model call instead of two, where the `session.compact` hook tells the summariser to write in the handoff's fields and the mod writes the file from the summary it gets back. The summariser has no tools, so it cannot check `git status` or the last test run the way the skill can. Measure the two summaries side by side before choosing. Undone if the model calls the tool mid-step often enough that the owner turns it off.
