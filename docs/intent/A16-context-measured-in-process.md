---
id: A16
from: [O12, O9]
source: session
status: decided 2026-10-24
kind: check
implemented_by: [plugins/session-kit/hooks/context.tsx, plugins/session-kit/hooks/hooks.json, plugins/session-kit/types/index.d.ts, plugins/session-kit/.claude-plugin/plugin.json]
proven_by: [plugins/session-kit/hooks/context.test.tsx, docs/measurements/hook-times.md]
supersedes: [A4]
---

# A16 Context measured in-process, the model warned

The kit's first mod measures the context from `$.session.usage()`, with the engine's own window, warns the model through a tool result's `context` as `A4` does today, and draws a band above the prompt with the figure for the person.

## Context

`A4` starts a Python process and reads the transcript on every tool call, and its window is a constant that is wrong for every model but the 1M one. The mod API of 2.1.308 gives the figure in-process.

## Options

- A. Port as is: the mod measures and warns, the owner runs the handoff and `/compact`. Nothing new to go wrong. `O5` stays unmet here. Taken, as the first step.
- B. The model signals, the mod acts: `A17`, the next step, on top of A.
- C. The mod decides alone, by heuristics at `turn.complete`: compacts mid-step whenever the heuristics misread, and continues past a question to the owner. Rejected.

## What the transcripts say (2026-10-25)

`session-transcripts` over 39 sessions: no request has carried more than 515,000 tokens, and every compaction, 145 of them, was manual, at a median of 152,000 tokens. The warning at half the window has never fired, so nothing here is validated by a real session yet, and the threshold is the first thing the report puts in question: a threshold near where the owner compacts by hand, around 150,000 tokens, would have fired in most long sessions. The owner decided the same day: the threshold is a token count, `thresholdTokens`, default 150,000, with the percent of the window kept as the alternative (`threshold`, 0 by default, the first reached warns). The firmer tiers moved with it, to one and a half times and twice the threshold, and the global rule's "skip the ask" line moved from 30% of the window to 100,000 tokens to stay below it. session-kit 0.10.0.

The owner raised it the same day: the warning starts at 250,000 tokens and is firmer at 500,000, because the 152,000 median counts only the sessions whose transcripts survived (a cleared or deleted session leaves none) and because a compaction at 170,000 tokens after two small tasks would only force the re-reads and cold the cache. The session set the firmest tier at three times the threshold, 750,000, and the "skip the ask" line at 150,000, both unmeasured. What a compaction or a clear is worth is a question for the transcript tooling (`A22`). session-kit 0.11.0.

The owner's archive of 381 sessions, read the same day with the 40 live ones (`docs/measurements/sessions-2026-10-25-with-archive.md`), shows what the kept sessions hid: 9,729 manual compactions at a median of 256,086 tokens before each, one automatic at 418,303, and the largest context at 926,637. The retired warning (`A4`, the context-pressure hook at half the window) fired 5,985 times, all from 500,000 tokens, median 528,000, and a compaction followed within a turn 5,961 times, a handoff 4,536 times. So the owner's 250,000 sits at the median of their own compactions, and 500,000 is where the old warning was obeyed.

## Consequences

Retires one Python start per tool call: 28 ms on this machine, measured by `plugins/session-kit/hooks/time_hooks.py` before and after, a small share of a call that reaches the model. The window is the engine's, so the warning fires on a 200k model where `A4` stayed quiet. The threshold and the step are `userConfig` options in place of the environment variables. Validated when the owner has seen the warning and the band in a few real sessions, on the terminal and in the desktop app. Undone if the mod API moves under it faster than the kit can follow, in which case `A4` returns.
