---
id: A56
from: [O9, O8]
source: session
status: decided 2026-10-25
kind: check
implemented_by: [plugins/session-kit/hooks/measure.ts, plugins/session-kit/rulebook/session_rulebook.py]
proven_by: [plugins/session-kit/hooks/measure.test.ts, plugins/session-kit/rulebook/test_session_rulebook.py]
supersedes: []
---

# A56 The engine's token count of the memory files beside the rulebook's words

At the first main-loop turn end of a context (a new session, or a context smaller than the last turn end's, which is a compaction), the timeline of `A55` (a timeline of turns and tool calls with the kit's time per concern) reads `$.session.usage({ breakdown: 'summary' })` and writes a `memory` line: each memory file the engine loaded, with its path, where it was loaded from and its estimated tokens. `session-rulebook` reads the newest such line that lists a file of the project and prints each file's tokens beside its words, then the memory files the engine loads and the rulebook does not count, with the engine's total. The budget of `A28` (the rulebook budget) stays in words.

## Context

`docs/analyses/mods-for-the-kit.md`, M18, from context-inspector. `A28` counts words because a token count needed a tokenizer the kit would ship or call. The engine counts the memory files itself, with no request, so the rulebook can be measured as the model pays for it, auto memory and managed files included, which the rulebook does not list.

## Options

- The budget moved to tokens. Rejected: the count exists only where a session with the kit has run in the project, and the gate runs anywhere. Words stay the gate and tokens the measure.
- A breakdown read at every turn end. Rejected: the memory files change only when a context starts, and the breakdown builds all of `/context` to answer.
- `full` in place of `summary`. Rejected: `full` sends one token-count request per tool and memory file.
- The reading done by `session-transcripts`. Rejected: the words are `session-rulebook`'s, and the owner reads the two side by side.

## Consequences

The count is the engine's estimate, as of the newest session in the project, so a rule edited since is shown with its old count until the next session's first turn end. The first reading on this repository: 4,540 words of rules a turn are 9,384 tokens, about two tokens a word, the global rules 4,594 of them and the handoff 2,740. A file is matched by its resolved path, so the global rules read through the link at `~/.claude/CLAUDE.md` count as `global/CLAUDE.md`.

## Proof

The engine test of `A55` holds the `memory` line, read at the first turn end and again after a compaction and a clear and not between. Three cases in `test_session_rulebook.py`: the tokens beside each file, from the newest line that lists the project and from no older one or other project's, the engine's file the rulebook does not count listed apart with the total, and no timeline leaving the words alone. Run on this repository after the real headless turn of `A55`.
