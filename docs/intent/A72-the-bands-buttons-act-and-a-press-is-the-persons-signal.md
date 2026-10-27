---
id: A72
from: [O5, O12]
source: session
status: decided 2026-10-26
kind: behaviour
implemented_by: [plugins/session-kit/hooks/band.tsx, plugins/session-kit/hooks/context.tsx]
proven_by: [plugins/session-kit/hooks/ui.test.tsx]
supersedes: []
---

# A72 The band's buttons act and a press is the person's signal

The figure row has `Handoff` (runs the handoff command) and, with the chain on, `Handoff and compact`. The cold-cache row has `Run chain now`. The second and third start the same chain the model's `clear_point` starts, from its handoff stage with the next step the owner's: the handoff, the compaction, then it waits with its note on the band and sends no continue prompt. The action buttons are absent while a turn runs. A press is the person's own signal, so the rule of `A19` (one task per context: the rule, then the signal) that the chain starts on a signal and never on the kit's own judgement holds.

## Context

The figure row told the person to find a clear point, commit, write the handoff and ask to compact, and gave a Dismiss button. The offer row already had buttons that did what it said. The analysis asked whether a press may start the chain. The owner took all seven proposals without answering, so the session took yes and recorded it here.

## Options

- Only `Handoff`. Rejected: the compaction is what the person is walking toward, and the cold row already ran it unattended.
- The press continues after the compaction. Rejected: the person is at the screen, so the next step is theirs. Nothing is sent in their place.
- Hotkeys on the buttons. Not built: a hotkey works only while the band holds focus and a bare digit answers a survey alone.

## Consequences

A press compacts the context, which costs the cache once, as the cold timer does. The note on the band after it reads "go on from the handoff, written at your request". What undoes it: if a press compacts at a moment the person did not mean, the button goes and the sentence returns.

## Proof

Kept is the case whose failure costs context with nothing said: a press of `Handoff and compact` runs the handoff, then `/compact` when the handoff's turn ends, then waits on the owner with no prompt sent. Deleted once they passed: the button order, `Handoff` alone, and `Run chain now` disarming the timer and starting the same chain.
