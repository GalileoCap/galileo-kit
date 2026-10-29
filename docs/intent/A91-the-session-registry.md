---
id: A91
from: [O22, O24]
source: session
status: decided 2026-10-29
kind: behaviour
implemented_by: [plugins/session-kit/hooks/registry.ts, plugins/session-kit/hooks/context.tsx]
proven_by: [plugins/session-kit/hooks/registry.test.ts]
supersedes: []
---

# A91 The session registry

Each session keeps a record of itself in `~/.claude/session-kit/sessions/<id>.json`, outside every project: its id, its working directory, its state (`working`, `waiting` on the owner, or `ended`), `since` when, whether a `wrap_up` question of its waits on the owner, and `beat`, rewritten each minute while the session lives. A main-loop turn's start marks it working and its end marks it waiting. A subagent's turn changes nothing. A clear ends the old session's record as the new one starts. A session that quits stops beating, and a reader tells it by the record's age, two minutes or more.

## Context

The rules-and-load audit's part 2a (`docs/analyses/rules-and-load-read.md`, section 1) counts the owner's load across sessions: the window's close names how many sessions are working or waiting, the concurrent-session friction counts them, and the morning list reads them. Today no session can see another. The owner chose to start here on 2026-10-29.

## Options

- A `session.end` hook to end the record. Not taken: the kit's hooks line stands at the validator's cut (`docs/PLAN.md`, Deferred), and the engine takes one unmatched hook of an event per plugin, which the timeline's already is. The beat covers a quit, and the next session's start covers a clear.
- A record per project instead of per session. Not taken: `O24` counts sessions, and two run in one project.

## Consequences

Nothing reads the records yet. The first reader is the band's count of sessions at once, in 2a's later steps. The records of ended sessions stay, one small file each, until a reader needs them pruned. A session hot-reloaded writes its record again as waiting. Nothing of the record reaches a session's context (`C5`, nothing of the load measures reaches a session).
