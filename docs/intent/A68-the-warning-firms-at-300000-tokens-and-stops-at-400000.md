---
id: A68
from: [O12, O9]
source: session
status: decided 2026-10-26
kind: behaviour
implemented_by: [plugins/session-kit/hooks/context.tsx, plugins/session-kit/.claude-plugin/plugin.json, docs/what-reaches-the-model.md, global/CLAUDE.md]
proven_by: [plugins/session-kit/hooks/context.test.tsx]
supersedes: []
---

# A68 The warning firms at 300,000 tokens and stops at 400,000

The context warning keeps its first tier at 250,000 tokens. Its second tier ("End this turn at the next green commit") moves from 500,000 to 300,000 and its third ("Stop starting anything new") from 750,000 to 400,000, as 1.2 and 1.6 times the trigger, and a tier that rises warns at once instead of waiting for the next 25,000-token step. This replaces the tier points `A16` (context measured in-process, the model warned) set, 2 and 3 times the trigger.

## Context

The owner asked for a second nudge past 300,000 tokens after `docs/analyses/kit-impact-on-three-projects.md` read lane1, demo-mat-porting and mat-lib against two pre-kit sessions.

- The tiers at 500,000 and 750,000 never fired in those three projects: the largest context was 439,000. Every warning lane1's model got, 56 of them, said "Aim for a safe point".
- Compactions land at 260,000 to 280,000 tokens, but 6 of lane1's 35 came after 300,000, up to 439,000, and the longest wait from the first warning to the compaction was 110 requests, on a long benchmark. Requests carrying more than 300,000 tokens were 5.2% of lane1's (0% in the other two, 12% to 17% before the kit).
- A step is 25,000 tokens, so a tier reached 3,000 tokens after a warning would wait 22,000 more before the model heard it.

## Options

- A. Keep 500,000 and 750,000. The tiers are the owner's, set on the 256,000 median of their compactions. They never fire in practice, so the third tier is dead text. Rejected.
- B. Tiers at 1.2 and 1.6 times the trigger. They scale with the percent option and the engine's window as the old ones did. Taken.
- C. Refuse tool calls past 400,000. The kit never blocks a call (`C1`, the kit is never the reason a session fails) and the model is the one that knows where a clear point is. Rejected.
- D. Fixed offsets (the trigger plus 50,000 and 150,000). They do not scale with a small window or the percent option. Rejected.

## Consequences

Where a long run is in progress the model is told at 300,000 to stop at the next green commit, and at 400,000 to stop starting anything. A benchmark that cannot be interrupted is not interrupted: the advice reaches a model that ignores it, as the first tier did, and the report shows how often. A tier rise adds at most two warnings of about 180 characters to a session. The cost of the tail above a 280,000-token ceiling was 1.1% of lane1's session cost, so the gain is small in cost and larger as a bound on the worst context.

Known by the next `session-transcripts` report: the share of requests over 300,000 tokens and the requests from the first warning to the compaction (lane1: 5.2%, longest 110). Undone if models end turns at 300,000 with the task unfinished more often than the owner wants, which shows as a handoff written at a red tree or a prompt that restates the task after a compaction. Not validated until the owner has seen the second tier in a real session. session-kit 0.35.3.
