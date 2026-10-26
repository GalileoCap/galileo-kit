---
id: A55
from: [O17, O9, C2]
source: session
status: decided 2026-10-25
kind: check
implemented_by: [plugins/session-kit/hooks/measure.ts, plugins/session-kit/hooks/kit.tsx, plugins/session-kit/.claude-plugin/plugin.json]
proven_by: [plugins/session-kit/hooks/measure.test.ts]
supersedes: []
---

# A55 A timeline of turns and tool calls with the kit's time per concern

The `measure` module of `A22` (tooling over the sessions' transcripts and the hooks' effect). It writes one JSON line per turn start and end, tool call and session end, buffered in memory and written at each main-loop turn end and at the session's end as a new file, `~/.claude/session-kit/measure/<session id>/<epoch ms>.jsonl`. `kit.tsx` registers the module's hooks first and a stopwatch before each concern and after the last, so each tool call's line carries every concern's own time by name (`context`, `test_log`, `doc_length`, `nudge`, `checkout`, `suppressions`), the context each added, and the time beneath the kit. A turn end on the main loop carries the context figure and the session's cost. A clear or a resume in the same process starts the next session's first file with a line naming the session it came from. The `measure` option, on by default, turns it off. The line shapes are written at the head of `measure.ts`, the contract the readers hold to.

## Context

`docs/analyses/mods-for-the-kit.md`, M17, from agent-profiler, and M13's lineage from auto-handoff. `A22` asked what each of the kit's hooks does and costs, by name, which no transcript holds and agent-profiler cannot see. The design was a wrapper on each concern's `on`, and a probe plugin showed the 2.1.308 validator refuses one: the value of `on` may be passed, called and given a `.catch`, nothing else. The same probes showed that the hooks of one module nest as a single link of the chain, in the order they are registered, and that `next.trace` lists only the links beneath the module.

## Options

- A wrapper on each concern's `on`. Refused by the validator.
- `next.trace` from one outer hook. It times only the plugins and the engine beneath the module.
- agent-profiler installed for a session. Rejected by the owner with its review: it cannot name the kit's hooks.
- Stopwatch hooks between the concerns, each timing what was registered after it. Chosen: the difference between two adjacent laps is one concern's time, with no change to any concern. They hook `tool.call` matched `{ tool: /./ }` and `turn.complete` matched `{ turnId: /./ }`, since a module takes one unmatched hook per event and the context module holds those.
- One file per session, rewritten each turn. Rejected: `$.fs` has no append, the rewrite grows with the session, and a write over 4 MiB rejects. A file per turn costs one write per turn.
- `$.clock.now()` for each line's time. Rejected: a call on `$` is a host round trip, on every tool call. The module's own `Date.now()` and `performance.now()` cost none.
- A line per compaction from the `session.compact` hook. Dropped while building: the transcript's `compact_boundary` records each compaction with its trigger, size and duration, and the test kit raises a test's compaction without the engine's messages, so the hook could not be held by a test.

## Consequences

Each tool call costs two `performance.now()` calls per concern and no call on `$`. Each main-loop turn end costs one `$.session.usage()`, one `$.session.id()`, `$.env.get('HOME')` and one write, and the first turn end of a context one local breakdown more (`A56`). Nothing deletes the files: about a kilobyte per turn of a few tool calls. A subagent's tool calls carry its `agentId` and no turn, since the hooks an agent's spawn was nested in do not hear its turn's start. The approval split agent-profiler reads from telemetry is left out: the time beneath the kit less the tool's execution holds the permission prompt and the other plugins together. A line that cannot be written is dropped. Module variables are lost on a hot reload, so a reload between a clear and the next turn end loses that lineage line. Unread yet by any query of `session-transcripts`.

## Proof

Three engine tests in `measure.test.ts`, kept as the contract the Python readers rely on. A main-loop turn end writes the lines since the last as a new file: a turn start, each tool call with the six concerns timed in order and the test log's one entry of context on a failed run, a tool's execution, a subagent's tool call and turn end with its id, the turn end with its usage, figure and cost, and the memory files. A compaction (a smaller context) and a clear read the memory files again, the clear writes the old session's lines to its own directory, and the new session's first line names it. The option off writes nothing. A real headless turn on the 2.1.308 engine (`claude -p` on Haiku with this plugin folder, one `ls`) wrote the file: the kit's six concerns took 2.1 ms of a 235 ms Bash call, the tool 172 ms, and the checkout's git calls 24.6 ms of the turn end's 28.0 ms.
