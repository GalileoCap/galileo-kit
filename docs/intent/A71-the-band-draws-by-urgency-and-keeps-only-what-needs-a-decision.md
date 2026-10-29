---
id: A71
from: [O17]
source: session
status: retired 2026-10-29
kind: behaviour
implemented_by: [plugins/session-kit/hooks/band.tsx, plugins/session-kit/hooks/lines.ts, plugins/session-kit/hooks/options.ts, plugins/session-kit/hooks/context.tsx, plugins/session-kit/.claude-plugin/plugin.json]
proven_by: [plugins/session-kit/hooks/limits.test.tsx, plugins/session-kit/hooks/context.test.tsx, plugins/session-kit/hooks/cold_cache.test.tsx]
supersedes: [A50]
---

# A71 The band draws by urgency and keeps only what needs a decision

Each row of the band above the prompt is a bold label, the figures in compact form (`312k / 1M  31%`, `+12k last turn`) and the buttons that act, coloured by how urgent it is: `warning` past the context trigger, `error` from the firmer tier at 1.2 times the trigger, `error` for a window at 95% and for a failure. The old instruction sentence is gone from the band, since the buttons do what it told the person to do. A usage window draws a band row only from 95%, and the status line (`A73`) carries it from the first reading. With the `statusLine` option off the row draws from 80% as before. The row dismissals of `A43` (the bands are dismissable) and the composition with the bands beneath of `A44` (the band composes with the bands beneath it) stand. This supersedes `A50` (the plan's usage windows and the growth per turn beside the context figure) in its 80% row. The growth per turn and the dismissal at 95% carry over.

## Context

`docs/analyses/ui-surfaces.md` read every row as one dim sentence with a Dismiss button, the tiers the code knows drawn alike, and up to five rows stacked for little. The owner asked for the bands to be improved and then for all seven proposals of that analysis.

## Options

- Every row coloured. Rejected: a band all in colour is as flat as one in none, so colour marks the tier alone.
- The 80% window row kept on the band beside the status line. Rejected: the same number twice. The option keeps it where the status line is off.
- Colours as hard-coded values. Rejected: theme keys follow the person's theme.
- The toast and model texts reworded to match. Rejected: a toast has no buttons, so its sentence still has to say what to do.

## Consequences

The sentence `figureLine` stays for the toast and nothing else draws it. The pure formatters moved to `lines.ts` and the options to `options.ts`, so the band, the pane and the status line share them. What undoes it: a person who misses the 80% row on the band sets `statusLine` off. Unverified on a real surface: how the colours read in the desktop theme.

## Proof

The usage-window tests of `limits.test.tsx` now hold the 95% rule, the dismissal and the growth row. The context and cold-cache tests hold the compact figure. The blind tests written first for the row, the label's tier colour, the order of the buttons and the status-line-off case were removed once they passed.
