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

## Options

Designed 2026-10-25 in `docs/session-tooling-design.md`, put to the owner before anything is built.

- A reader, `session-transcripts`, standard-library Python like `session-intent`, over the JSONL transcripts under `~/.claude/projects/`: per session the context at each turn, the compactions, each hook that fired and what followed, the cache share and the cold sends, the cost, and the signs of a rule not held. Reports as tables under `docs/measurements/`. Proposed first, since the transcripts already on disk answer it.
- A `measure` module behind `kit.tsx` that appends one line per event to the plugin's data directory: what each in-process hook did and cost. Proposed after the first real session with the modules, which shows what the transcript keeps of them.
- A model reading the transcripts for quality or adherence. Rejected for now: a pattern answers the listed questions for free, and the owner's own read of one session says more than a judge.

## Consequences

The shape waits on the owner's answers to the design's five questions: the order of the two pieces, which questions first, committed reports or printed, all projects or this one, and the rule patterns. A transcript holds the owner's and the model's words, so the tool reads locally and writes nothing outside the repository.
