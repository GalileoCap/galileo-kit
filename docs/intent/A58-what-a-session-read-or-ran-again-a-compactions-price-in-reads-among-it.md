---
id: A58
from: [O12, O9, O17]
source: session
status: decided 2026-10-25
kind: check
implemented_by: [plugins/session-kit/transcripts/records.py, plugins/session-kit/transcripts/session_transcripts.py]
proven_by: [plugins/session-kit/transcripts/test_session_transcripts.py, docs/measurements/sessions-2026-10-25-deduplicated-with-archive.md]
supersedes: []
---

# A58 What a session read or ran again, a compaction's price in reads among it

`session-transcripts waste` counts, per session and from each `compact_boundary`, three things a session read or ran again. A file read again after a compaction: a `Read` of a file an earlier context of the session had read, counted at its first read in the new context, with its characters, and apart the files edited before the compaction (`Edit`, `Write`, `MultiEdit`, `NotebookEdit`). A file read again unchanged in one context: a `Read` whose result is what the same call returned before it in that context, or the engine's own answer that the file is unchanged. And a repeated output: any other call made again in one context, to the same input and the same output once runs of whitespace count as one. It ends with the totals and, over every compaction, the median and the largest characters read again after one. The report gives the same by project, and `session <id>` one line.

## Context

`docs/analyses/mods-for-the-kit.md`, M19, from context-inspector and agent-profiler. Question 9 of `docs/session-tooling-design.md` asks what a compaction is worth, and the warning's tiers (`A16`) rest on that number. While building it, the transcripts showed that the engine writes again, under the same uuid, records it already wrote: after a compaction, the messages it keeps. In 16 of the 59 transcripts on disk that was 97 `compact_boundary` records and about 10,000 tool results. Counted as they stood, every kept `Read` looked like a read after the compaction, 71% of all characters read where the count is 37%. So the reader of `A22` now counts each record once, which changed its other tables too.

## Options

- Near-identical output by a looser likeness (digits taken out, a share of lines in common). Rejected: a test run whose failure count changed would read as the same output, and that change is what the run was for.
- An unchanged read found by the edits between two reads. Rejected: a Bash command, a formatter or the person changes files the tools never see. The result's own text says whether the file changed.
- Every read again after a compaction called waste. Rejected: the global rules ask for the documents the work rests on to be read again after one, so those reads are the compaction's price, and the edited files among them are the state its summary did not carry.
- A module counting it live. Rejected: the transcripts hold it, and a count offline costs a session nothing.

## Consequences

The first run, over the 59 transcripts on disk: 530 `Read` calls, 5.37 million characters. 139 reads after a compaction of a file read before it, 2.0 million characters (37%), 90 of them files edited before it. Most compactions are followed by no read again (the median is 0) and the largest by 237,584 characters. One read of a file unchanged in one context, 93 characters: the engine's own answer covers that case. 88 other calls returned again what they had, 18,413 characters. The counts are in characters. A file a compaction kept in the messages it writes again, then read again, counts as a read after the compaction. Only `Read` is counted for files, so a `cat` through Bash is at most a repeated output, and a subagent's records are not counted. With the duplicates out, the 59 transcripts hold 118 compactions at a median of 190,947 tokens before, where the duplicates made 225 at 227,016, and the two reports committed earlier counted them with the duplicates. Over the owner's archive with them, 440 sessions: 14,654 `Read` calls and 78.5 million characters, 28% of them from 2,493 reads after a compaction, 1,728 of those files edited before it. The compactions are 1,357 at a median of 278,402 tokens before, where the earlier report counted 9,729 at 256,086, so the warning's tiers of `A16` sit where they were argued from.

## Proof

The cases that hold it in `test_session_transcripts.py` were written before the code and deleted once it passed, as blind tests. Kept, as regressions that failed before: a record the engine wrote twice is counted once, a prompt or a compaction, and a compaction's summary is not a prompt. Run on the 59 transcripts on disk and over the owner's archive into `docs/measurements/sessions-2026-10-25-deduplicated-with-archive.md`.
