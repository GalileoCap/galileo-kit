---
id: A50
from: [O12, O4]
source: session
status: decided 2026-10-25
kind: behaviour
implemented_by: [plugins/session-kit/hooks/context.tsx, plugins/session-kit/types/index.d.ts]
proven_by: [plugins/session-kit/hooks/limits.test.tsx]
supersedes: []
---

# A50 The plan's usage windows and the growth per turn beside the context figure

The band above the prompt draws one line per rate-limit window of the account at 80% or more, naming the window and when it resets, from the windows `session.measure` carries. The line has a Dismiss button (`A43`, the bands are dismissable): dismissed below 95%, it stays away until the window reaches 95%, and dismissed there, until the window resets below where it was dismissed. The figure's own line (`A16`, context measured in-process) says how much the context grew over the last main-loop turn, read from the engine at the turn's end, and says nothing before a second turn or when the context shrank.

## Context

`docs/analyses/mods-for-the-kit.md`, M9, from effortless, context-meter and token-weather: the owner approved the order that puts it beside the cold-cache timer (`A49`). The engine measures the session after each main-loop turn and when a window moves a whole point, and `rateLimits` rides on that event, which the kit already hooks for the figure. The growth per turn tells the owner when to stop sooner than a figure past a threshold does.

## Options

- The windows read from `$.session.usage()` after every tool call, where the figure is read. Rejected: the measurement event already carries them whenever one moved, and reading them per call would churn the band's state on calls that moved nothing.
- A sparkline of the last turns, as token-weather draws. Rejected for now: a `Raster` draws differently per surface, and the figure the owner acts on is the last turn's growth, which one number says.
- The growth read from the figure the last tool call left. Rejected: the final response's tokens would count in the next turn. The turn's end reads the engine's figure, which also keeps the band current after a turn with no tool call.
- The 80 and 95 marks as options. Rejected: they come from the analysis the owner approved, and no second setting needs them yet.
- The model told of a window near its end. Rejected: the limit is the person's to manage, and the warning text stays about the context.

## Consequences

The windows and the dismissals live in `$.state` (`rateLimits`, `limitsDismissed`), the latter keyed by the window's kind with the percent at which it was dismissed, dropped when the window resets below it. The turn's end calls `$.session.usage()` once more, in process. Two tests of the chain and the offer narrowed their assertions to their own lines, since a turn ending past the threshold now draws the figure's line where before no tool call had set it. Off a subscription the list is empty and nothing draws. Unverified in a real session: the windows' kinds and reset times as the engine reports them, and the growth figure against the owner's sense of a turn.

## Proof

Four engine tests in `limits.test.tsx`. A window at 80% draws its line with the reset time above the band beneath, and at 79% nothing. The two dismissal tiers and the reset hold. Two windows get their own buttons, the 7-day window naming its day. The growth per turn is read at the turn's end, absent before a second turn and after a compaction. All four failed on 0.24.0.
