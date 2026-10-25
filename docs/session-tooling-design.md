# Tooling over the transcripts and the hooks' effect: the shape, for the owner

The design behind `A22`, from `O17`: the system is observed, analysed and improved over time, from the sessions' transcripts and the hooks' measured effect. Written 2026-10-25 against Claude Code 2.1.308 and session-kit 0.9.0, before anything is built. The questions at the end are the owner's to answer. Answered 2026-10-25: all projects, reports committed, the warning's effect and the cache share first. The reader is built as `session-transcripts`, with `rules` and the module still to come.

## What there is to read

Every session leaves one JSONL file under `~/.claude/projects/<project>/<session id>.jsonl`. On this machine today: 39 files, 234 MB, across 30 project folders. One line is one record, and the records that matter are these.

| Record | What it holds | What it answers |
| --- | --- | --- |
| `assistant` | Each model request's `usage`: input, cache read, cache creation and output tokens, the model, the effort, the thinking duration, and the content blocks (text, thinking, `tool_use`). | The context size at every request (the three input counts summed), the cache share, tokens per turn, which tools were called and how often. |
| `user` | The person's prompts, and every `tool_result` with its `toolUseResult`. `isCompactSummary` marks the summary a compaction left. | What the model was told, how long each result was, what a summary kept. |
| `attachment` | What the engine attached beside a message. `hook_success`, `hook_additional_context` and `hook_system_message` carry a settings hook's name and its stdout, and `total_tokens_reminder`, `compact_file_reference`, `file` and the rest are the engine's own. | Which settings hook fired on which call and what it said. This session's file holds 18 `hook_success` rows, from the tells hook and the guard. |
| `system`, `stop_hook_summary` | Each Stop hook's command and `durationMs`. | Hook time, for Stop hooks alone. |
| `system`, `compact_boundary` | `compactMetadata`: the trigger (`manual`, `auto`), the tokens before, the duration, the messages preserved. | When compactions happen, what they cost and what they keep. |
| `cost-state` | The session's totals: cost in USD, API time, tool time, lines added and removed, and per model the five token counts. | The bill per session and per model. |
| `api-request` | The request's shape: its parameters, where the cache marks sit, which blocks are kept and which are the tail. | Where the prompt cache breaks, for `O10` and the cache-tax question. |

What the transcript does not hold: the duration of any hook but a Stop hook. Whether a hooks module's `context` entry (the in-process warning, the nudge, the test log's one line) reached the model, since no module has run in a real session yet and the row it leaves is unknown. And what the person read, as against what was written.

There is no debug log on disk by default (`~/.claude/debug/` does not exist). `claude --debug` writes one per run, with a line per hook occurrence, and it is the only record of a settings hook's duration outside Stop. `plugins/session-kit/hooks/time_hooks.py` measures that cost on its own, outside a session, and its tables are under `docs/measurements/`.

In-process there is more: `session.measure` hands a module the context fill, the rate limits and the cost after every turn, `turn.complete` carries the turn's usage, `session.compact` its tokens before and after, and `tool.call` lets a hook time what runs beneath it.

## What the tooling should answer

The questions, by the objective each serves. The first list is what the transcripts answer today. The second needs the module.

From the transcripts:

1. The warning and what followed (`O12`, `A16`). For each context warning, the tokens at which it fired, and whether a handoff, a commit and a compaction followed within the next few turns, and how many turns later. The warning was tuned twice on anecdote, and this is the number.
2. Compactions (`O12`, `G4`). Per session: how many, by trigger, the tokens before each, the duration, and what the summary dropped, read as the next turn's re-reads of documents (`Read` calls on files the handoff lists, right after a summary).
3. The cache share (`O10`). Per session and per project: cache reads over all input, cache creation per request, and the cold sends, where a request after a gap longer than the cache's life wrote the prefix again. This is the measurement `O10`'s *known by* says nothing takes yet, and it decides `cache-tax` with a number.
4. Cost per task (`G4`). The bill per session, per model, per thousand lines changed, and the share of output that was thinking.
5. Each settings hook's effect (`O5`, `O8`). The tells hook: how often it fired, and whether the next edit of the same file carried fewer tells. The guard: each deny and what the model did next (the right command, or a way around). The test log: each failed run, and whether the log file was read before the next run. Format: what lint it left.
6. The rules' adherence (`G3`). Signs of a rule not held, found by pattern: test output piped inline, a `git stash`, a commit message with an attribution line, a turn that ended without the ask to compact above the threshold. Each is a candidate for a hook, which is `O5`'s path.

With the module:

7. Each hooks module's effect and cost. When the warning, the nudge, the document cap and the test log fired, what they added, and the time each took around `next`. The chain: each run, its stages, whether the continue landed, and the summary's size.
8. The hooks' time per call, live, where `time_hooks.py` measures it on a bench.

## The shape

Two pieces, one built now and one when the first real session with the modules shows what the transcript keeps of them.

### `session-transcripts`, a reader

Standard-library Python under `plugins/session-kit/transcripts/`, behind `bin/session-transcripts`, like `session-intent`: no package until a second command needs one. It reads the JSONL files under `~/.claude/projects/` (or `--root`), never writes outside the repository, and prints tables, or writes them as a report under `docs/measurements/` when asked.

- `session-transcripts list [--project <name>] [--since <date>]`: one row per session: date, project, turns, requests, tokens, cache share, compactions, cost.
- `session-transcripts session <id>`: one session's story: the context size at each turn, the compactions, each hook that fired with what it said, each warning with what followed, the tool calls by tool.
- `session-transcripts hooks [--since]`: the per-hook table of question 5, across sessions.
- `session-transcripts cache [--since]`: question 3: the cache share and the cold sends, per session and per project.
- `session-transcripts rules [--since]`: question 6: each pattern, its count, and the sessions it was seen in.
- `session-transcripts report [--since]`: the tables above as `docs/measurements/sessions-<date>.md`, so the record of the kit's effect is versioned beside the hook times.

A transcript holds the owner's words and the model's. The reader prints counts, sizes, names of hooks and tools, and the hooks' own text. It prints no prompt and no answer unless `--quote` is passed, and never writes a transcript's text into a report.

### `measure`, a module

A fourth file behind `kit.tsx`, written once the first real session shows what the transcript keeps of a module's `context` entries. It hooks `turn.complete`, `tool.call`, `session.compact` and `session.measure`, and appends one JSON line per event to `<CLAUDE_PLUGIN_DATA>/measure/<session id>.jsonl`: the event, the time, the context figure, the cost, and for each of the kit's own hooks whether it fired, what it added, and the milliseconds around `next`. The reader joins the file to the transcript by session id, which makes questions 7 and 8 answerable, and makes question 1 exact where the transcript only shows the warning's text.

It writes to the plugin's data directory alone, where the tells environment already lives, and costs one file append per event.

## What is not proposed

- A model reading the transcripts for quality, LLM-isms or rule adherence. A model call per session, over hundreds of thousands of tokens, to answer questions a pattern answers for free in the cases above. Where a pattern cannot answer (did the summary lose what mattered?), the owner's own read of one session says more than a judge. Rejected for now, as the per-prompt judge was in `A19`.
- Telemetry to anywhere. The engine's `$.telemetry` noun sends to Anthropic or to a collector. Everything here stays on this machine and in this repository.
- A dashboard. Tables in a markdown file, versioned, are what a session can read again and what the owner can diff.

## Open questions for the owner

1. The reader first, and the module after the first real session, or both now? The reader answers questions 1 to 6 on the 39 sessions already on disk. The module needs a real session to design against.
2. Which of the eight questions matter first? The order above is the session's guess: the warning's effect and the cache share before the rest, since `A16` and `cache-tax` wait on them.
3. Reports committed under `docs/measurements/`, or printed only? Committed is proposed, since `O17` is about change over time and the tables are small.
4. All projects' transcripts, or this project's alone? All is proposed: the rules are global, so their effect is.
5. The `rules` command's patterns: the six named in question 6, or a list the owner writes.
