---
id: A73
from: [O17]
source: session
status: decided 2026-10-26
kind: behaviour
implemented_by: [plugins/session-kit/hooks/status.ts, plugins/session-kit/hooks/lines.ts, plugins/session-kit/hooks/pane.tsx, plugins/session-kit/hooks/band.tsx, plugins/session-kit/hooks/context.tsx, plugins/session-kit/hooks/kit.tsx, plugins/session-kit/types/index.d.ts, plugins/session-kit/footprint.toml]
proven_by: [plugins/session-kit/hooks/ui.test.tsx]
supersedes: []
---

# A73 The kit's numbers always on a status line, a turn line and a pane

Three places for what the band only shows past a threshold. A status line under the prompt, on every surface, reads `ctx 31% 312k (+12k) · 5h 62% · 7d 20% · compacts at 14:25`: the figure with the last turn's growth, each usage window (with when it resets from 80%), and when the cold timer compacts. It is written only when the text changes, and not at all with the `statusLine` option off. The line that closes a turn gets ` · ctx 31%`, the percent that turn ended at, found by the turn's duration so an old line never shows a later figure. `/kit` opens a pane, drawn on every surface, with the context and a bar, each window with a bar, the cache timer, the chain or offer or failure with the last eight journal lines, the handoff's state, the uncommitted files and the last test run.

## Context

The band is an alarm with no gauge (`docs/analyses/ui-surfaces.md`, finding 2), and the phone and VS Code drew only toasts. The pane is also the answer to the facts on the UI that `docs/PLAN.md` left open from `A63` (facts from git and the session beside the model's prose in the handoff).

## Options

- A ticking cache countdown in the status line. Rejected: it needs a clock call a minute for a number the person reads once. The time of the compaction is enough.
- The turn line showing the current figure. Rejected: every old line would change with it. The figure is kept per turn under the turn's duration, and a line whose duration matches no turn shows the engine's alone.
- The pane opened by the kit at the session's start. Rejected: it takes room the person did not ask for.
- A second `session.start` hook for the command. Refused by the engine, so the context concern registers it in its one hook and the pane cannot cost the tools below it.

## Consequences

Three more state values (`failure`, `stages`, `turnFigures`) and five `$` calls enter the footprint with their reasons. A module's atoms are declared in the module that reads them, since the validator reads no atom imported from another file. Unverified on a real surface: how the status line sits beside the person's own `statusLine` command, and that the turn line's duration equals the engine's.

## Proof

Kept is the case that would show a wrong figure with nothing said: a turn line finds the percent its own turn ended at by duration and shows the engine's line alone for a duration no turn had. The pane's and the status line's blind tests were removed once they passed.
