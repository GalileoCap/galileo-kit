---
id: A22
from: [O17]
source: owner
status: decided 2026-10-25
kind: check
implemented_by: [plugins/session-kit/transcripts/session_transcripts.py, plugins/session-kit/transcripts/records.py, plugins/session-kit/bin/session-transcripts, plugins/session-kit/hooks/time_hooks.py, docs/measurements]
proven_by: [plugins/session-kit/transcripts/test_session_transcripts.py, docs/measurements/sessions-2026-10-25.md, docs/measurements/sessions-2026-10-25-with-archive.md, docs/measurements/sessions-2026-10-25-deduplicated-with-archive.md]
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

## Shape as built (2026-10-25, the reader)

The owner answered: all projects, reports committed under `docs/measurements/`, the warning's effect and the cache share first. `session-transcripts` has `list`, `session`, `warnings`, `cache`, `compactions`, `hooks` and `report`, standard-library Python behind `bin/session-transcripts`, reading 39 transcripts in about a second. Not built yet: `rules` (the patterns of a rule not held). The `measure` module is built as `A55` (a timeline of turns and tool calls with the kit's time per concern), with the engine's count of the memory files as `A56`. Three queries followed: `chains` with each session's own cost (`A57`, chains of sessions and each session's own cost), `waste` (`A58`, what a session read or ran again, a compaction's price in reads among it) and `asks` (`A59`, the person's repeated asks, ranked, their words printed only when asked). The reading moved into `records.py` beside the command.

Building them found four defects in the reader, fixed with a regression case each. The engine writes some records again under the same uuid, the messages a compaction keeps among them, and each was counted again. A compaction's summary and the engine's meta records, written as user records with string content, were counted as prompts. A fork's file begins with a copy of its parent's records, which were counted in both. And a session's cost was the engine's running total, which a fork and some clears carry on. Over the 59 transcripts on disk the prompts fall from 2,917 to 1,231, the compactions from 225 to 118 (their median from 227,016 tokens before to 190,947) and the cost from 1,149 USD to 737. The two reports below counted with those defects. `docs/measurements/sessions-2026-10-25-deduplicated-with-archive.md` reads the same sessions without them: 1,357 compactions at a median of 278,402 tokens before where the earlier count was 9,729 at 256,086, and 879 warnings where it was 5,985.

Its first report, `docs/measurements/sessions-2026-10-25.md`, found that the kit's context warning has never fired: no request in 39 sessions carried more than 515,000 tokens, and the 145 compactions were all manual, at a median of 152,000 tokens before, with none by the engine's own trigger. The warning's effect is therefore nil so far, and `A16`'s threshold of half the window sits above where the owner compacts by hand. The cache share runs 91% to 99% of input per session, with cold sends after gaps concentrated in the long sessions.

## Consequences

The reader's tables are versioned, so a change to a rule or a hook can be argued from the next report against this one. Validated when the owner reads one report and changes something because of it. The first candidate is `A16`'s threshold. A transcript holds the owner's and the model's words, so the tool reads locally and writes nothing outside the repository.
