---
id: A87
from: [O17]
source: owner
status: decided 2026-10-29
kind: behaviour
implemented_by: [plugins/session-kit/hooks/pane.tsx, plugins/session-kit/hooks/context.tsx, plugins/session-kit/footprint.toml]
proven_by: []
supersedes: []
---

# A87 The kit's pane is shown and hidden by a chip, and kept across sessions

A `kit` chip sits beside the footer's mode labels, at the right of the prompt's footer, on the terminal and the desktop. A press shows the kit's pane where it is hidden and hides it where it is shown, and `/kit` does the same. Each press keeps the choice in `$.store`, and a session starts with the pane open when the last press left it open. The pane's own close mark hides it for this session and leaves the next session's choice as the last press set it. The pane's content is `A73`'s (the kit's numbers always on a status line, a turn line and a pane).

## Context

The owner, on 2026-10-29: "the /kit panel is uncomfortable. I'd like a persistent panel I can hide and open with a click." Before, the pane opened only by typing `/kit`, and closed for good at its mark. `docs/analyses/mod-display-surfaces.md` lists every place a mod can show something. Of them, the footer's mode labels (`SessionMode`) are the only site always drawn that takes a `Button`. The band shows only when it has a row, the status line and the hint's tail take text alone, and the turn line is the terminal's only.

## Options

- A chip in the footer's mode labels (this one): always there, one row of no height, on the two surfaces that draw a footer.
- A row of the band holding a show button. Not taken: the band would never be empty, and its rows are for what needs a decision (`A86`, the band is a ledger, and the context row joins it at its higher tier).
- A button inside the pane to hide it. Not taken: the pane's own mark already hides it, and the chip is the way back.
- Recording the close mark too, through a `ui.close` hook. Not taken for now: the validator cuts a line of its report at about a thousand characters (`A60`, the kit's reach held to a reviewed footprint), and the kit's hooks line stood at 982. The chip's hook and the pane's are one hook matching both components, and the start-up calls are direct calls in the kit's single `session.start` hook, so the hooks line stands at 987 and the calls line at 950.

## Consequences

A pane opened at the start without the person's word is placed on a terminal from 144 columns (110 once the person has opened it), and waits undrawn below that. Whether the desktop draws a `Button` in the mode labels, and where it places a pane opened at the start, is the owner's look to settle. What undoes it: the chip not drawn on the desktop, which moves it to the hint line (`PromptHint`), or the owner wanting the close mark remembered, which needs room on the validator's line. Any new hook or helper making `$` calls now meets that cut within a few dozen characters.

## Proof

Under `claude plugin test` on 2.1.308, a scaffolding test pressed the chip on the desktop surface: the pane opened, the store held true, a second press closed it and the store held false, and a new session with the store true opened the pane. The test was deleted as blind scaffolding. The footprint, the type-check and the 84 engine tests pass. Not yet seen on the desktop.
