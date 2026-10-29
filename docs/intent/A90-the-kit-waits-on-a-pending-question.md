---
id: A90
from: [O12, O19]
source: owner
status: decided 2026-10-29
kind: behaviour
implemented_by: [plugins/session-kit/hooks/question.ts, plugins/session-kit/hooks/context.tsx, plugins/session-kit/hooks/tags.ts, plugins/session-kit/hooks/band.tsx, plugins/session-kit/skills/handoff/SKILL.md]
proven_by: [plugins/session-kit/hooks/pending_question.test.tsx]
supersedes: []
---

# A90 The kit waits on a pending question

A question the session puts in the app's next-step box (the `ask` of `wrap_up`) waits on the owner from its turn until the owner's next prompt. While it waits, the chain does not start: a `clear_point` call is answered that the clear point is not taken, and one made before the question is dropped at the turn's end. The tagged-lines check sends no prompt of its own, and the band shows the missed items alone. A handoff that runs anyway, from the cold-cache timer or the owner's press, writes the question under Open questions word for word with its options. From then on the band shows it with its buttons until the owner answers, and a press sends the button's message as the owner's prompt.

The owner's report of 2026-10-29, in the audit `~/devel/galileo/misc/claude-analysis/rules-and-load.md` ("A defect: the handoff hides a pending question"): in lane5 a `wrap_up` question and a `clear_point` in the same turn ended in a handoff turn and a compaction that took the box's place. The owner's rule: "Nothing of the kit's should start a turn or a compaction while a question is waiting for me, and where it has to, the question comes across".

## Context

The kit sees `wrap_up` through `tool.call` (698 calls in the measure log on 2026-10-29). `AskUserQuestion` is answered inside its own turn and never waits past it. A question written in a reply's prose is not seen.

## Options

- The cold timer skips arming while a question waits. Rejected: the cache then goes cold, and the owner asked for the question to come across where the kit has to act.
- The chain is kept and run after the owner's answer. Rejected: the note was written before the answer, and the session calls `clear_point` again at its next clear point.

## Consequences

A button for an app action (`commit`, `create_pr`) cannot be pressed on the band and is named as the app's. The phone draws no band, so a carried question reaches it only in the handoff. A button's message is sent with the plugin's origin, so the kit's own hooks do not number tagged lines in it.
