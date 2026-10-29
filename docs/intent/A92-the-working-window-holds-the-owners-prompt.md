---
id: A92
from: [O22]
source: owner
status: decided 2026-10-29
kind: behaviour
implemented_by: [plugins/session-kit/hooks/load.ts, plugins/session-kit/hooks/context.tsx, plugins/session-kit/hooks/band.tsx, plugins/session-kit/hooks/status.ts]
proven_by: [plugins/session-kit/hooks/load.test.tsx]
supersedes: []
---

# A92 The working window holds the owner's prompt for a reason

With `~/.claude/session-kit/load/settings.json` in place, the owner's prompt outside its window waits while the band asks for a one-line reason. A project under one of the settings' personal folders has the personal slot (05:30 to 22:00, every day) as its window, and any other has the work hours (weekdays 06:00 to 11:00 and 15:00 to 17:00). So the sleeping hours hold every prompt. The reason sends the prompt on as it came, and is logged in `holds.jsonl` beside the settings with the time, the session, its folder and its kind. It also opens a pass of 30 minutes for every session, kept in `pass.json` and named on the status line. The ✕, an interrupt, or ten minutes without a reason put the prompt back in the box, keeping what the owner typed there since, and log it as returned. A prompt from the phone, which draws no band, goes on and is logged with no reason. With no settings file nothing is held.

The owner's decisions of 2026-10-29, in the audit `~/devel/galileo/misc/claude-analysis/rules-and-load.md`, part 2a, item 2, with the personal slot under "Yours". The same day the owner chose to pass and log the phone's prompts, since they rarely answer from it, and a pass that holds for the sitting, across every session. Personal is `~/devel/galileo` and work is the rest, confirmed the same day.

## Context

A hook's own time is bounded at 10 seconds, and no `$` call waits on the person. The hold probe of 2026-10-29 (`docs/analyses/rules-and-load-read.md`, section 1) showed a hook waiting on a process keeps the prompt as it came, screenshot and origin included, and that an interrupt drops a held prompt. So the wait is a shell loop that ends when the reason file holds text, and the band, an interrupt and the ✕ write that file. It rides on `context.tsx`'s `prompt.submit` hook, the kit's outermost, so a held prompt is not first sent to the pre-send check.

## Options

- Drop the prompt and send it again after the reason. Not taken: a plugin's prompt loses pasted images and `@` mentions, and takes the `plugin` origin.
- Refuse the phone's prompts. Not taken, by the owner.

## Consequences

Nothing of it reaches the model (`C5`, nothing of the load measures reaches a session): the reason, the band row, the drop's text and the status line are the owner's alone. A prompt typed while one is held waits behind it. The ten-minute bound is `$.process.run`'s own. The interrupt's path is unproven by the tests, which cannot interrupt, and is to be seen on the desktop. A slash command is never held.
