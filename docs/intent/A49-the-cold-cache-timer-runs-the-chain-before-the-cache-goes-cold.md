---
id: A49
from: [O9, O10, O12]
source: owner
status: decided 2026-10-25
kind: behaviour
implemented_by: [plugins/session-kit/hooks/context.tsx, plugins/session-kit/types/index.d.ts, plugins/session-kit/.claude-plugin/plugin.json]
proven_by: [plugins/session-kit/hooks/cold_cache.test.tsx]
supersedes: []
---

# A49 The cold-cache timer runs the chain before the cache goes cold

With the chain on, a main-loop turn that ends with the context past the floor, and no chain or `new_task` offer under way, sets a timer for the prompt cache's lifetime less a lead. A turn starting before then clears it. When it fires, the kit runs the chain of `A17` (the model signals a clear point, the mod runs the chain) from the handoff stage with the next step the owner's: the handoff command, then the compaction, and it stops there. The lifetime is the `cacheMinutes` option, 60 by default as a subscription's and 5 on an API key, and 0 turns the timer off. What the engine states replaces it: the split of a subagent's cache writes on the Agent tool's result, and `cache_ttl` on a model switch. The lead is `cacheLeadMinutes` (5), so a 5-minute cache leaves none and arms nothing. The floor is `cacheFloorTokens`, and at 0 the context warning's own trigger (`A16`, context measured in-process). The band draws the time the chain runs, with a Dismiss button that clears the timer until the next turn ends (`A43`, the bands are dismissable).

## Context

The owner, on 2026-10-25, correcting M8 of `docs/analyses/mods-for-the-kit.md`: a cache that has lapsed has already lost its value, and what makes sense is "a timer that detects when the cache is going cold (eg: 55m) and auto-handoffs+compacts, to give me time to come back". While the cache is warm the handoff turn and the compaction read the context at cache-read prices, and the person's next prompt writes the compacted context to the cache instead of all of it. This is the cold-send guard `PLAN.md` deferred from the cache-tax review, at the right moment.

The 2.1.308 types give no lifetime per response on the main loop: `TurnUsage` carries the four counts and the model. The split by lifetime (`ephemeral_1h_input_tokens`, `ephemeral_5m_input_tokens`) is on the Agent tool's result, and `cache_ttl` on the model-switch hooks. The analysis's M7 read the split as every response's. It is a subagent's, which runs on the same account.

## Options

- The lifetime assumed at one hour, as cache-tax does. Rejected: on an API key the cache lives five minutes, and the timer would run a handoff over a cold cache.
- The lifetime as an option, with the engine's statements over it. Taken. Before any statement the option holds, and the owner is on a subscription.
- The timer measured from the turn's last request, through a `turn.step` hook on every model request. Rejected for now: a turn's end comes seconds after its last request for most turns, and a streaming hook costs every request. The lead absorbs the difference.
- The floor at the global rule's 150,000 tokens, from which a compaction is asked for at a clear point. Rejected as the default: the kit asks the model to find a clear point from the warning's trigger, so it compacts on its own only from there. The floor stays an option.
- The timer held while the chain's loop guard (`A45`, a loop guard on the chain) is at its limit. Not needed: this chain sends no continue, counts nothing and stops by itself.

## Consequences

The timer's chain ends with the band saying the next step is the owner's, with the note "go on from the handoff, written before the cache went cold". The wait is measured from the turn's end, so a final answer that streamed for minutes shortens the lead by that much. The handoff command is queued at once, and in the real run of `A17` its turn started within a second. The deadline lives in `$.state` under `coldTimerAt` so the band draws it. The timer itself is a module variable a hot reload drops, and `session.start` sets it again from the deadline, unverified in a real session. A timer firing on a phone or an SDK host runs the chain with no band to see, and the chain file has the stages. The floor exists because a context the timer compacted is read again whole by the next turn, as after any compaction.

## Proof

Eight engine tests in `cold_cache.test.tsx`. The chain runs at 55 minutes and not at 54, and stops after the compaction. A turn starting disarms it and the next end arms it afresh. The floor and the lead are options, and the floor's default is the warning's trigger. A 5-minute cache and 0 arm nothing. The engine's word comes from a subagent's result and from a model switch. The band's line draws beside the figure's, and Dismiss stops it. Six failed on 0.23.0 with nothing armed. The second half of the 5-minute test was added after that run, and the off test is a negative case alone.
