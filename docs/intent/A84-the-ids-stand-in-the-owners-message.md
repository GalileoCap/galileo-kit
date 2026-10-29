---
id: A84
from: [O19]
source: owner
status: decided 2026-10-29
kind: behaviour
implemented_by: [plugins/session-kit/hooks/tags.ts]
proven_by: [plugins/session-kit/hooks/tags.test.tsx]
supersedes: []
---

# A84 The ids stand in the owner's message

The kit writes each item's tag as its id in the message the person sent (`Do:` becomes `Do-1:`), so the ids stand where the owner wrote the lines and the owner can refer back to them. `FYI:` lines and lines in fenced or pasted blocks keep their text.

The owner's words, 2026-10-29, after the first tagged trial: "Can we change my message so that I see the IDs?"

## Context

The trial of `A83` (tagged items get ids from the kit and a turn-end check) showed the ids only in the hidden context and in the reply's closing lines. The owner had nothing in their own message to point at.

## Options

- Rewrite the message's text at `prompt.submit` (taken). The model reads the ids in place. Whether the desktop draws the rewritten text or the typed one is for a real session to show.
- A band row listing the open items with their ids. Kept for later, if the desktop draws the typed text.

## Consequences

The transcript holds `Do-1:` where the owner typed `Do:`. Undone if the desktop draws the typed text, in which case the band row takes over.
