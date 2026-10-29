---
id: A89
from: [O17]
source: owner
status: decided 2026-10-29
kind: behaviour
implemented_by: [plugins/session-kit/hooks/pane.tsx, plugins/session-kit/footprint.toml]
proven_by: []
supersedes: []
---

# A89 The kit's pane is the session's dashboard

The pane holds six sections, each left out when it has nothing to say. Each is a card with a rounded border: its title and the figure that sums it up on the first line (the count of items or commits, the handoff's state, the context or usage percent in its tone), then its body. The fact that matters is in full weight and its context dim: a commit's hash dim and mono beside its subject cut at its first clause, a file's path dim and mono, a test command without its leading `cd`. A line runs to the card's edge and is truncated there.

- Your items: the owner's open tagged items, by id.
- This session: the commits made since the session started, the uncommitted files by name, and the last test run with its verdict in colour.
- Next: the next step and the open questions `CLAUDE.local.md` records, and the handoff's state.
- Context: the figure, the trigger, a gauge with a tick at the trigger and at the two higher tiers, the context percent over the last 24 turns, the cold timer, and the `Handoff` and `Handoff and compact` buttons.
- Usage: each window's figures over a gauge, ticked at 80% and 95%.
- Chain: the stage, the failure or the offer, and the journal, only while one of them is set.

The desktop, VS Code and the phone draw the gauges and the curve as SVG, and the terminal as cells. This replaces the pane's content in `A73` (the kit's numbers always on a status line, a turn line and a pane). The status line and the turn line stand.

## Context

The owner, on 2026-10-29, of the pane `A73` drew: "The current version is very ugly and not really useful". `docs/analyses/kit-display-inventory.md` read it against everything the kit shows and proposed these six sections. The owner: "Build all six so I can see your vision, I'll iterate on it after".

## Options

- All six (this one), for the owner to cut from.
- The pending `OWED.md` entries under Next. Not taken: an entry carries no mark that the owner saw it, so the pane cannot tell which are pending.

## Consequences

The pane repeats the status line's numbers, now as gauges. Each drawing runs `git log` and `git status` and reads `CLAUDE.local.md`. The validator's calls line stands at 961 of its cut near a thousand (`A60`, the kit's reach held to a reviewed footprint).

## Proof

The owner saw the first version on the desktop on 2026-10-29, sections in the band's ledger look, and asked for visual work: separators, alignment, cards, the relevant text bold against its context. The cards answer it.


A scaffolding test under `claude plugin test` on 2.1.308 drew the pane on the desktop and the terminal with git and the handoff stubbed: the session's commits and files, the next step, the questions, the handoff's state and the context showed, with one SVG on the desktop and none on the terminal. The test was deleted as blind scaffolding. Not yet seen on the desktop.
