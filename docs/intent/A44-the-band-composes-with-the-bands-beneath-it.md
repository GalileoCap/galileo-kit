---
id: A44
from: [O4]
source: session
status: decided 2026-10-25
kind: behaviour
implemented_by: [plugins/session-kit/hooks/context.tsx]
proven_by: [plugins/session-kit/hooks/context.test.tsx, plugins/session-kit/hooks/chain.test.tsx, plugins/session-kit/hooks/new_task.test.tsx]
supersedes: []
---

# A44 The band composes with the bands beneath it

The kit's `AbovePrompt` hook calls `next(e)` first and returns what the plugins beneath drew when it has nothing to draw. When it has (the context figure past its trigger, the chain's stage, the `new_task` offer), it returns a column with its own line above theirs.

## Context

The hook returned its own tree alone, so while the kit drew, every band seated beneath it (another plugin's, the engine's own) was hidden. `docs/analyses/mods-for-the-kit.md` lists this as M1, after seeing effortless and replay-theater hide the kit's bands the same way. A fork pinned in this marketplace (`A2`, a fork is pinned in galileo-kit) runs beside the kit, so the kit's band has to leave room for its. open-loops (`charlie947/mod-maker`) draws this way.

## Options

- Return the kit's tree alone, as before. Rejected: the order of mods is nobody's to set (the mod-ordering question in `PLAN.md`), so which band shows would depend on the seat.
- Call `next(e)` first and draw above it. Taken. One `Box` in a column, the kit's row then what came up.
- Draw below it. Rejected: the kit's line is what the person acts on, and the prompt sits under the band.

## Consequences

A plugin beneath that draws nothing costs one element. In a test an engine drawing has to stand beneath the kit, since `next(e)` with nothing beneath is refused by the test kit. One test gained its stand-in. Unverified in a real session: how the desktop draws two stacked bands.

## Proof

Three engine tests, one per band, find the engine's line beside the kit's. Each failed on 0.22.0.
