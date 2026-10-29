---
id: A86
from: [O17]
source: owner
status: decided 2026-10-29
kind: behaviour
implemented_by: [plugins/session-kit/hooks/band.tsx, plugins/session-kit/hooks/lines.ts]
proven_by: [plugins/session-kit/hooks/ui.test.tsx, plugins/session-kit/hooks/limits.test.tsx, plugins/session-kit/hooks/context.test.tsx, plugins/session-kit/hooks/cold_cache.test.tsx]
supersedes: [A71]
---

# A86 The band is a ledger, and the context row joins it at its higher tier

Every row of the band is drawn the same way. A label in a column as wide as the longest label the band shows, the row's text, then its buttons together at the right with the ✕ right after them, centred against all the row's lines. Detail lines (the pre-send check's findings, the cold-cache deadline under the context row) indent to the text column. The kit's rows are inset by one on the left, to match the room the ✕ leaves on the right, and take a gap beneath them only when a band of another plugin follows. The label of the most urgent row is the only one in colour, and that row holds the band's only filled button. The others draw their labels in `subtle` and their buttons plain. The most urgent row is the first, in the band's order, whose own colour is not `subtle`, or the first row when none has one. Every row has a label: `Failed`, `Held`, `No line`, `New task`, `Chain`, `Context`, `Cache`, `Usage`. The context row draws from the firmer tier, at 1.2 times the trigger (300k by default), and below it the figure stays on the status line (`A73`, the kit's numbers on a status line, a turn line and a pane). This supersedes `A71` (the band draws by urgency and keeps only what needs a decision). The context label is `warning` at the firmer tier and `error` from the stop tier, at 1.6 times the trigger. Carried over from `A71`: the compact figures, the growth per turn, the usage windows from 95%, and the dismissals of `A43` (the bands are dismissable).

## Context

The owner, on 2026-10-29, with a screenshot of the Held row above the Context row: "I don't like the way the bands are looking (not just this new one, all of ours)". `docs/analyses/band-look.md` read eight findings and offered three layouts, and the owner picked the ledger, with the context row off the band below its higher tier.

## Options

- A ledger (this one): the smallest change, one rule for every row.
- Cards, a headline and a line of buttons per row. Not taken: twice the height for a band that mostly holds one or two rows.
- One row with the rest behind a press. Not taken, except its change to the context row.

## Consequences

Between the trigger and the firmer tier the person has no band button for the handoff or the chain, and the model's warning is the prompt to act. The cold-cache row draws on its own there when its timer is armed, since it acts by itself. What undoes it: the owner reaching for the handoff button below 300k, or the colours still reading flat on the desktop. On the desktop, the first version's fixed column of 8 left a wide gap after a short label, centred the buttons on the first line alone and left space under the last row, which the owner saw on 2026-10-29.

## Proof

The band's tests hold the labels, the order and the texts. The context tests hold the row's absence below the firmer tier and its return after a compaction.
