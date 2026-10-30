---
id: A95
from: [O24]
source: owner
status: decided 2026-10-30
kind: behaviour
implemented_by: [plugins/session-kit/hooks/load.ts, plugins/session-kit/hooks/registry.ts, plugins/session-kit/hooks/band.tsx, plugins/session-kit/transcripts/week.py]
proven_by: [plugins/session-kit/hooks/load.test.tsx, plugins/session-kit/hooks/registry.test.ts, plugins/session-kit/transcripts/test_week.py]
supersedes: []
---

# A95 A prompt into one session more than three waits for a reason

With `sessions` in `~/.claude/session-kit/load/settings.json` (`max` 3, `idleMinutes` 30), the owner's prompt into a session that is not active, while `max` other sessions are, waits on the band for a one-line reason, the way a prompt outside the window does (`A92`, the working window holds the owner's prompt for a reason). The band names each active session by its folder, working or waiting since its last turn's end. A session is active when its record in the registry (`A91`, the session registry) beats and it is working, or its last main-loop turn ended within `idleMinutes`. The reason sends the prompt on as it came and is logged in `holds.jsonl`, with what held it and how many sessions were active. It opens no pass: the session is active from its turn on, so its next prompts go straight on. A prompt both outside the window and past the sessions waits once, for one reason, which opens the window's pass. The week review names what held each prompt. Without `sessions` nothing is held for it.

The owner's decision of 2026-10-29, in the audit `~/devel/galileo/misc/claude-analysis/rules-and-load.md`, part 2a, item 7: no hard cap, a reason for a prompt into a fourth active session, with the band listing the active ones, and 3 the owner's to change. The order was the owner's on 2026-10-30, after the focus list.

## Context

The registry's records show 7 of 8 open sessions waiting between turns on the morning of 2026-10-30, so an open session is not an active one. Active is set by work in the last half hour, which keeps a sitting's lanes free and holds a session opened or come back to. The registry now writes when a session's last turn ended (`turnEnded`, 0 before its first), since `since` moves with the question flag too. A session freshly started or cleared has had no turn, so its first prompt is held.

## Options

- Count every open session. Not taken: sessions stay open waiting for days, and every prompt would be held.
- A pass for the sitting, as the window has. Not taken: the held session becomes active by its own turn, which the pass would only repeat.
- Read the registry by a listing call. Not taken: a new call name puts the validator's calls line past its cut (`docs/PLAN.md`, Deferred), so the hold lists the folder through the shell it already runs.

## Consequences

The friction is the owner's alone (`C5`, nothing of the load measures reaches a session). A session whose record predates `turnEnded` counts only while it works, until its next turn. A session hot-reloaded writes its record again with no turn, so its next prompt may be held once. The `idleMinutes` of 30 is the session's choice, for the owner to change in the settings.
