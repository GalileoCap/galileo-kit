---
id: A17
from: [O5, O12]
source: session
status: decided 2026-10-24
kind: behaviour
implemented_by: [plugins/session-kit/hooks/context.tsx, plugins/session-kit/types/index.d.ts, plugins/session-kit/.claude-plugin/plugin.json]
proven_by: [plugins/session-kit/hooks/chain.test.tsx]
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

## Shape as built (2026-10-25, session-kit 0.7.0)

- The tool is `mcp__session-kit__clear_point`, registered at `session.start` when the `chain` option is on, listed in the prompt's tool list from the start, where ToolSearch would hide it. Its input is `next_step`, `session` or `owner`, and `note`, the next step in one line: the model says who takes the next step, since the mod cannot read that off the handoff. Its result tells the model to end the turn with nothing more started.
- The chain runs off `turn.complete` on the main loop, one stage per turn end. The signalling turn ends and the mod runs `session-kit:handoff` through `$.command.run`. The handoff turn ends and the mod compacts through `$.session.compact` with instructions naming `CLAUDE.local.md`, then submits the continue prompt, framed as the plugin's, or stops with the band saying the next step is the owner's and quoting the note. Each step starts from a zero-delay timer, since a command run inside a hook the turn waits on is refused.
- A compaction refused because the turn has not let go is tried again every 500 ms, six times. A turn that ends interrupted, refused or on an error cancels the chain. A handoff that cannot run, or a compaction skipped or refused for good, stops the chain with a toast saying why. The stage lives in `$.state` under `chain`, so the band draws it and a hot reload keeps it.
- The warning text names the tool when the option is on, and keeps asking the person otherwise.

## Consequences

Off by default until it has run in a few real sessions. Validated when the owner sees one chain run end to end in a real session, and the summary after it read back by the next turn. A continue prompt submitted without `asUser` reaches the model framed as the plugin's. To try with it, unverified: one model call instead of two, where the `session.compact` hook tells the summariser to write in the handoff's fields and the mod writes the file from the summary it gets back. The summariser has no tools, so it cannot check `git status` or the last test run the way the skill can. Measure the two summaries side by side before choosing. Undone if the model calls the tool mid-step often enough that the owner turns it off.
