---
id: A22
from: [O17]
source: owner
status: decided 2026-10-25
kind: check
implemented_by: [plugins/session-kit/hooks/time_hooks.py, docs/measurements/hook-times.md]
proven_by: unproven
supersedes: []
---

# A22 Tooling over the sessions' transcripts and the hooks' effect

Build tooling that reads and analyses the sessions' transcripts, and that measures what the hooks and the rest of the kit do to a session.

## Context

The owner's proposal, 2026-10-25: "build tooling around reading and analyzing the sessions' transcripts, and also the impact our hooks and such do." The transcripts are the JSONL files under `~/.claude/projects/<project>/`, one per session, and the engine's debug log times each hook. The first piece exists: `time_hooks.py` measures what each settings hook adds to a tool call, with its results under `docs/measurements/`.

## Consequences

Its shape is not decided: what the tool reads, what it counts, and where its results go are the next session's design, put to the owner before it is built. A transcript holds the owner's and the model's words, so the tool reads locally and writes nothing outside the repository.
