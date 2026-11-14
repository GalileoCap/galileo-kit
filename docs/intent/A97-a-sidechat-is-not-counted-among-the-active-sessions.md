---
id: A97
from: [O24]
source: owner
status: decided 2026-11-14
kind: behaviour
implemented_by: [plugins/session-kit/hooks/registry.ts, plugins/session-kit/hooks/context.tsx, plugins/session-kit/hooks/load.ts]
proven_by: [plugins/session-kit/hooks/registry.test.ts, plugins/session-kit/hooks/load.test.tsx]
supersedes: []
---

# A97 A sidechat is not counted among the active sessions

A sidechat, the side question the desktop opens beside a session as a `btw:` fork, is not one of the sessions `A96` (the owner's prompt goes on, and the band asks why) counts. It does not count toward `sessions.max`, the band never names it, and a prompt into a sidechat is never asked about for the sessions. The window's question is unchanged.

The owner's ask of 2026-11-14: "Sidechats should not be counted to the total of running sessions".

## Context

The engine gives a hooks module no sign of a sidechat. The desktop keeps a record of each session it starts under `~/Library/Application Support/Claude/claude-code-sessions/<account>/<organization>/<host session id>.json`, and a sidechat's record says `spawnedFrom.btw: true`. On 2026-11-14, 84 of the 170 records there did. The session reads that record once at its start, the path from the variables the desktop sets (`CLAUDE_CODE_HOST_SESSION_ID`, `CLAUDE_CODE_ACCOUNT_UUID`, `CLAUDE_CODE_ORGANIZATION_UUID`), and writes `side: true` in its registry record (`A91`, the session registry). The count leaves such records out.

## Options

- Leave out every session another started (`spawnedFrom.sideSession`). Not taken: a session a session starts on its own task is real work the owner reviews, and the ask named sidechats.
- Have the reader look up each record in the desktop's folder at every prompt. Not taken: it reads every record of the app on each prompt, where the session's own start reads one.

## Consequences

The desktop's record is not a published contract: if its shape or place changes, a sidechat reads as an ordinary session and counts again, which is the behaviour before this entry. Outside the desktop the variables are unset and nothing changes. A sidechat started before the install has no `side` in its record and counts until it starts again.
