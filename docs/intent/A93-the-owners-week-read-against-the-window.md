---
id: A93
from: [O22, O23]
source: owner
status: decided 2026-10-29
kind: behaviour
implemented_by: [plugins/session-kit/transcripts/week.py, plugins/session-kit/transcripts/session_transcripts.py, plugins/session-kit/transcripts/records.py]
proven_by: [plugins/session-kit/transcripts/test_week.py]
supersedes: []
---

# A93 The owner's week read against the window

`session-transcripts week` writes the owner's Friday review to `~/.claude/session-kit/load/week-<monday>.md`, beside the hold's settings and log, and prints its path alone. From that Monday to the day asked for (`--week`, today by default) it gives the messages and the hours in and out of the work window by day, each day's first and last message, the streak, the sittings reopened within an hour of the window closing, the messages by folder, the reasons log from `holds.jsonl`, and the 2b bar from the settings' `bar`. Folders named in the settings' `watch` are marked on their own lines, and the bar's off-window share is given again without them, so kit evenings show apart. A message in the personal slot counts as off-window for the bar. The week 2a went live in is week 0. From the week the bar's `weeks` are up, the review gives the verdict in one line, from that week's figures.

The owner's decisions of 2026-10-29, in the audit `~/devel/galileo/misc/claude-analysis/rules-and-load.md`: part 2a, item 6 (the weekly review), "How we'll know whether 2b is needed" (the bar, and being held to it), and "Yours" (galileo-kit on its own line).

## Context

The measures port the audit's `volume.py` to the kit's transcript reader: the owner's typed prompts, the same text sent again within two minutes in one folder counted once, a day running from 04:00 to 04:00, a sitting broken by twenty minutes without a message. Hours are the time between two messages twenty minutes or less apart, and a minute for each message. The owner's messages themselves, `owner-messages*.jsonl`, stay out of the kit.

## Options

- Print the review, as the reader's other commands do. Not taken: a session that ran it would read the figures (`C5`, nothing of the load measures reaches a session).
- Judge the bar over the four weeks together. Not taken: the audit asks whether the share "has fallen" by week four, which the fourth week's own figures answer.
- Hard-code galileo-kit's folder. Not taken: the settings' `watch` list names it.

## Consequences

The owner runs it from a terminal, or opens the file. Showing it in the pane on Friday at 16:30 is part of 2a's later steps. A slash command or a shell line the owner typed is not counted, since the reader keeps a prompt's text only when it is not markup. The phone's prompts count as typed, and the log names them.
