---
id: A45
from: [O5, O12]
source: session
status: retired 2026-10-25
kind: behaviour
implemented_by: [plugins/session-kit/hooks/context.tsx, plugins/session-kit/types/index.d.ts]
proven_by: [plugins/session-kit/hooks/chain.test.tsx]
supersedes: []
---

# A45 A loop guard on the chain

The kit counts the chains that continued since the person's last prompt, in `$.state` under `chainsUnattended`. The count rises by one when the continue prompt is sent, and a prompt that is the person's own words (`A46`, prompt origins as a closed set) sets it to zero. At two, `clear_point` refuses the signal with its reason: end the turn and wait for the person, whose next prompt lets the chain run again. The refusal is written to the chain file as a stage.

## Context

The chain of `A17` (the model signals a clear point, the mod runs the chain) ran whenever `clear_point` was called. A model that calls it after each continue compacts on every turn with nobody present, each compaction a model call over the context, with nothing to stop it but the person's return. auto-handoff (`alexknowshtml/claude-auto-handoff`) keeps the same guard at two, after chaining six and eight handoffs in a row in real use. A chain that never ends is the kit's doing, the case `C1` (the kit is never the reason a session fails) names.

## Options

- No guard: the person dismisses the band. Rejected: the person is away, which is the case the guard is for.
- A floor of new tokens after a compaction, as compact-adviser's. Rejected for now: it slows a session with the person present and does not bound the unattended case.
- Two chains with no prompt of the person's between, then a refusal. Taken, the count in `$.state`, so a hot reload (which loses it) at worst lets one more chain run.

## Consequences

After two chains the model keeps working under the warning until the person returns. The engine's own compaction (`A18`, a backstop for the engine's own compaction) stands against overflow. A chain whose next step is the owner's sends no continue, so it counts nothing: it stops by itself. The refusal's text is in `docs/what-reaches-the-model.md`.

## Proof

One engine test: two chains continue, the third signal is refused, a task notification changes nothing, and the person's next prompt lets one run. It failed on 0.22.0, with three continues.
