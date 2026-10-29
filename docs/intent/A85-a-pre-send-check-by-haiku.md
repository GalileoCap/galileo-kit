---
id: A85
from: [O19]
source: owner
status: decided 2026-10-29
kind: check
implemented_by: [plugins/session-kit/hooks/presend.ts, plugins/session-kit/hooks/band.tsx]
proven_by: [plugins/session-kit/hooks/presend.test.tsx]
supersedes: []
---

# A85 A pre-send check by Haiku, held on the band

A message of the person's that starts with `??`, or holds four bullets or more outside fenced and pasted blocks, is read by Haiku before it is sent. Haiku reads it against the owner's rules for a message: tags on a mixed message and a tag offered for each untagged line, a tag its line contradicts, an id without its name, a short go-ahead after several questions, a long run with no estimate or stop, a reversal with no reason. Haiku also gets the last reply's questions and the project's intent names, and never the transcript. When it finds something, the message is held, put back in the box above whatever the person typed there since, and the band shows up to three findings with Send as is, Use the rewrite and a dismissal. Send as is sends the message as it was held and takes it out of the box where it stands unchanged. Use the rewrite puts the rewrite in its place, or above the box's text when the person has changed it. Nothing is rewritten without a press, and no other text in the box is touched (`C3`, a hook that writes to the owner's input loses none of it). A message with no finding, a check that fails or passes 15 seconds, and a surface that draws no band let the message through as written.

The owner's decision of 2026-10-29 in the proposal (`docs/analyses/proposal-prefixes-and-check-ins.md`, "Your decisions", item 6), and the ask after the first tagged trial: "I want to try out the haiku session asking me things".

## Context

The proposal counted 96 messages of four bullets or more in the live sessions, where most lost items came from. The read (`docs/analyses/prefixes-and-check-ins-read.md`, item 8) named the costs this design answers: the owner waits on Haiku, a failure must not hold a message (`C1`, the kit is never the reason a session fails), a surface with no band cannot show the buttons, and Send as is must not be held again.

## Options

- Haiku inside `prompt.submit`, holding the message (taken).
- A check after the message is sent, as a note on the reply. Rejected: the item it would catch is already lost by then.
- The secret hold, which needs no model. Left out of this action: it serves no approved objective yet.

## Consequences

The owner waits a few seconds on every message of four bullets or more. Undone if the owner accepts fewer than three findings in ten, in which case the four-bullet trigger goes and `??` stays.
