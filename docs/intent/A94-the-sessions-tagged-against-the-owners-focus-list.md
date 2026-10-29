---
id: A94
from: [O23]
source: owner
status: decided 2026-10-29
kind: behaviour
implemented_by: [plugins/session-kit/hooks/load.ts, plugins/session-kit/hooks/status.ts, plugins/session-kit/transcripts/week.py]
proven_by: [plugins/session-kit/hooks/load.test.tsx, plugins/session-kit/transcripts/test_week.py]
supersedes: []
---

# A94 The sessions tagged against the owner's focus list

The owner writes the week's must-haves to `~/.claude/session-kit/focus.md`: a heading `# Week of YYYY-MM-DD`, that week's Monday, then a `- ` line per must-have with its name and its folders, each starting with `~/` or `/`. Each of the owner's prompts that goes on, past the hold of `A92` (the working window holds the owner's prompt for a reason), is matched by its folder: it is on focus when a must-have's folder holds it, and off focus otherwise. It is logged in `~/.claude/session-kit/load/prompts-<monday>.jsonl` with the time, the session, the folder and the must-have's name, and the status line names the tag with the week's share of prompts on focus: "on focus: <name>, N% on this week", "off focus, N% on this week", or "the focus list is not this week's" when the heading names another Monday. With no list there is no tag. A list of this week is copied to `load/focus-<monday>.md`, and `session-transcripts week` (`A93`, the owner's week read against the window) reads that copy, else the list when its heading is that week, for a Focus section and a focus column per folder.

The owner's decisions of 2026-10-29, in the audit `~/devel/galileo/misc/claude-analysis/rules-and-load.md`, part 2a, item 1 (the weekly focus list) and item 6 (the weekly review's share per folder against the list), and "Focus list first", the order the owner gave the same day.

## Context

The kit sees a session's folder and nothing of the objective it works on, so a must-have is matched by its folders alone, and its name may mention an objective. Like the hold, the tag is the owner's alone (`C5`, nothing of the load measures reaches a session), and nothing of it reaches the model. A day runs from 04:00, as the review counts it, so a prompt at 02:00 on a Monday belongs to the week before.

## Options

- The band, as the audit proposed. Not taken: the band keeps only what needs a decision (`A86`), and the tag asks none, so it goes on the status line beside the pass.
- Count at the session's start. Not taken: the tag then shows before the owner has typed anything, and a prompt put back in the box would count.
- Read the share from the transcripts. Not taken: a hook reading every transcript at each prompt is slow, and the log is a line per prompt.

## Consequences

A prompt put back in the box is not counted. Two sessions writing the log at the same instant may lose one line, as `holds.jsonl` may. A worktree counts as its checkout. The tag rides on the hold's `prompt.submit` path, so it needs the settings for the time zone.
