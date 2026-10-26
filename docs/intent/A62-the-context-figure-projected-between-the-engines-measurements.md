---
id: A62
from: [O12, O9]
source: session
status: decided 2026-10-26
kind: behaviour
implemented_by: [plugins/session-kit/hooks/context.tsx, plugins/session-kit/footprint.toml]
proven_by: [plugins/session-kit/hooks/context.test.tsx]
supersedes: []
---

# A62 The context figure projected between the engine's measurements

The warning of `A16` (context measured in-process, the model warned) and the band fire on a projection of the next request's size: the context the last main-loop request was answered over, read from its usage through a `turn.step` hook, plus what has landed since that request was sent, its output and each main-loop tool's result and context at 3.5 characters a token. Each request's usage starts the projection over. What landed while its response streamed stays counted, and a turn's end hands the figure back to the engine's own until the next request is measured.

## Context

`docs/analyses/mods-for-the-kit.md`, M6, from auto-handoff. The engine's figure is the last response's input side, so it moves once per request. A step of parallel reads lands whole between two requests, and the figure the warning read after each of those calls was the one before the step: one session went from 67k to 437k tokens with no request between. The warning then came a request late, or never, when the request that would have measured it failed.

auto-handoff's four characters a token came from one live test, so the ratio here comes from the record. Over the 669 pairs of consecutive main-loop requests in the transcripts on disk with at least 8,000 characters of tool output between them, the tool output cost 2.42 characters a token (2.45 on Opus 5.5, 2.53 on Fable 5.1), and no pair went above 3.21. A headless probe of when the engine moves its figure against a response's tools did not run: the account's weekly limit refused `claude -p`.

## Options

- Read the engine's figure at each call and start the count over whenever it moves. No new event. Rejected: whether the figure moves when a response starts or when it ends is not documented and the probe could not run, and if it moves at the end, the reads that finish while the response streams drop out of the count.
- Read each request's usage through `turn.step` and keep the base there, as built. The base and the count move together whichever way the engine orders its figure, so neither the streamed reads nor what the request already carries is counted twice. It adds `turn.step` to the kit's footprint (`A60`, the kit's reach held to a reviewed footprint), a hook that passes every chunk on unchanged.
- Count against the live figure and reset at each `turn.step`, as auto-handoff does. Rejected: where the engine moves its figure as the response starts, a read finishing during the stream counts the previous step's output on top of a figure that already holds it. That may be why auto-handoff's live test projected 83.7k against 72.5k measured.
- Four characters a token. Rejected: it gives about 60% of the measured cost, and the warning fires later than it needs to. A median ratio, 2.4, would overshoot half the time. The next figure would then fall below the warning's mark, which the step rule reads as a compaction, and the warning would fire again at every step. At 3.5 the projection stays under the next measurement in every pair on disk and gives about 70% of the true cost.

## Consequences

Between measurements the warning and the band show at least what the next request will carry, and never more than it in the pairs measured. A subagent's steps and tool calls leave the projection alone, since they land in the subagent's context. After a hot reload the projection starts from the engine's figure, since its counts are module variables. Images and the per-message wrapping are not counted, which keeps the figure low. Undone if a real session shows the warning firing again after a measurement with no compaction, which would mean the ratio runs above 3.5 on some output.

## Proof

Two engine tests in `context.test.tsx` were written before the code and failed on 0.31.0. Kept: a step of four reads with the engine's figure held at 100,000 warns at 301,000 and again at 331,000, past a step, and the band shows 331,000, since a warning that misses a step of reads is silent and lets the context pass the window. The second test was deleted once it passed, as a blind test. It held three things: a step's measurement starts the projection over, a read that finishes while the response streams stays counted, and a turn's end hands the figure back to the engine's. Not yet run: a real session, since the probe met the weekly limit.
