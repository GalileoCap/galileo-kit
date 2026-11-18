---
id: A100
from: [O10, O12]
source: owner
status: decided 2026-11-17
kind: behaviour
implemented_by: [plugins/session-kit/hooks/context.tsx, docs/what-reaches-the-model.md]
proven_by: [plugins/session-kit/hooks/cold_cache.test.tsx]
supersedes: []
---

# A100 The cold-cache timer reads the wall clock

The cold-cache timer of `A49` (the cold-cache timer runs the chain before the cache goes cold) reads the wall clock each minute up to its deadline instead of one timer set for the lifetime less the lead. Woken past the deadline, it runs the chain at once. Woken past the cache's lifetime too, it writes nothing and drops the deadline, since the cache is cold already and a handoff would write it again for nothing.

## Context

A machine asleep holds a timer back while the wall clock runs on. Two of the 51 cold returns in `docs/analyses/memories-and-context-boundaries.md` show the handoff running after the hour was out, at 263,000 and 301,000 tokens, most likely after a sleep. The owner took the proposal on 2026-11-17.

## Options

- A timer per minute from the turn's end, against one timer per minute up to the deadline: the same thing. Taken as the latter, the deadline kept in `$.state` as before.

## Consequences

A minute's timer runs about 55 times per idle hour, each reading the clock. The regression test brings a clock of its own whose `now` runs through a sleep while its timers do not, since the engine's mock clock keeps the two together.
