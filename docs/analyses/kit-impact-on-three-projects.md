# What session-kit did to lane1, demo-mat-porting and mat-lib (2026-10-26)

The question: is the kit's effect on real sessions positive, and where is it not. The measure is what the rules changed: where compactions land, what is lost or re-read at each one, and what the hooks add. Read from the transcripts with `kit-impact-scripts/` (reproduce with `python3 -I kit_scan.py <project dir>`, then `final_numbers.py` and `summarize.py`). Nothing in the three projects was changed.

## The answer

Positive where it was aimed, neutral on cost, and it leaves two costs the kit does not own.

- Recovery after a compaction is much better. Across the 49 compactions in the three projects, none had uncommitted edits in flight and none was followed by a clarifying question from the model in its next 30 requests. In the two pre-kit sessions (June, 57 compactions) 6 compactions had edits in flight and 20 were followed by a question (23 questions).
- The long tail is gone. Requests carrying more than 300k tokens of context were 12% to 17% of the requests before the kit and are 5% in lane1 and 0% in the other two.
- The kit's text costs under 1%. Hook text put in front of the model is 0.3% to 0.7% of the sessions' modeled cost.
- Re-reading after a compaction is about 20k tokens per compaction, and the kit did not cause it. Pre-kit mat-lib re-read 23k tokens of already-read files per compaction and the kit-era one 26k. It is 6% to 10% of modeled cost either way. The handoff's document list directs part of it (72% of the first re-reads in mat-lib, 25% in lane1) and does not shrink it.
- Compacting at 250k to 300k costs 11% to 25% more context-carrying than the replay's best point (150k to 200k). A lower threshold doubles the compactions in lane1, so this is not a free win.

## Method and what limits it

- A transcript file is not in time order. After a compact boundary it replays the preserved tail of the old conversation with its old timestamps, a fork starts with a copy of its parent, and one model response is stored as one record per content block. The first pass of this analysis, which cut segments by file position, double-counted all three, and its re-read figures were wrong. `kit_scan.py` merges every record, drops duplicates by uuid and message id, sorts by timestamp, and cuts segments at the boundaries.
- Cost is in relative units, an input token being 1, a cache read 0.1, a cache write 1.25 and an output token 5. They rank things and give shares. They are not dollars.
- The baseline is two archived sessions from 2026-06-05 and 06-06: mat-lib `2b1b279e` (3,222 requests, 30 compactions) and tagents' cx-optimization `653b173a` (2,304 requests, 27). The kit's first commit is 2026-10-11, so neither ran it. They are other models (opus-4-8, sonnet-4-6 against the current opus-5-5, sonnet-5-5), other tasks and an older engine. A difference between June and October is evidence for the kit and falls short of proof.
- Which kit ran. lane1 ran 0.21.1 command hooks with in-process hooks moving to 0.35.x mid-session (see `tagents-lane1-under-the-kit.md`). mat-lib ran the user-scope 0.35.2 install, demo-mat-porting the project-scope 0.35.2 installed before its session began.
- Not measured: whether the work was right, whether a summary dropped something that never surfaced as a question, and the owner's attention.

## The three projects against June

| | lane1 | demo-mat-porting | mat-lib | June mat-lib | June cx-optimization |
| --- | --- | --- | --- | --- | --- |
| Requests, compactions | 2,601, 35 | 271, 2 | 874, 12 | 3,222, 30 | 2,304, 27 |
| Requests per compaction | 74 | 136 | 73 | 107 | 85 |
| Context before, median / largest | 278k / 439k | 282k / 293k | 261k / 300k | 237k / 449k | 118k / 491k |
| Compactions over 300k / under 200k | 6 / 2 | 0 / 0 | 0 / 1 | 9 / 12 | 6 / 20 |
| Requests carrying over 300k | 5.2% | 0% | 0% | 17.3% | 12.2% |
| Handoff prompt before the compaction | 33 of 35 | 2 of 2 | 12 of 12 | none | none |
| Edits not yet committed at the boundary | 0 | 0 | 0 | 1 compaction (12 edits) | 5 compactions (15 edits) |
| Question to the owner in the next 30 requests | 0 | 0 | 0 | 12 compactions (15 questions) | 8 compactions (8) |
| Handoff prompt to the boundary | 62 s, 2 requests | 72 s | 56 s | none | none |
| Compaction itself, median | 44 s | 63 s | 41 s | 98 s | 98 s |

Every compaction in all five was a manual one: the engine's automatic compaction never ran, so the kit's warning and the owner's command are what choose the point.

## Is each compaction at a good point

The structure is good. Every compaction in the kit era follows a commit, a handoff and a `clear_point` call (32 of 35 in lane1, all in the others), and the model resumes without asking and without repeating a command from before. The pre-kit sessions compacted wherever the context happened to be: a median of 118k in cx-optimization with 20 of 27 under 200k, and a tail to 491k.

The position is later than the cost optimum. Replaying each session's own context growth (the increments are real, the policy is varied) gives the cost of carrying context plus compaction, relative to the cheapest threshold:

| Threshold | lane1 | demo-mat-porting | mat-lib |
| --- | --- | --- | --- |
| 150k | 1.02x, 139 compactions | 1.00x, 8 | 1.00x, 32 |
| 200k | 1.00x, 63 | 1.09x, 4 | 1.08x, 18 |
| 260k (about where the kit lands) | 1.11x, 38 | 1.17x, 2 | 1.25x, 12 |
| 320k | 1.22x, 27 | 1.57x, 2 | 1.46x, 9 |
| 400k | 1.46x, 19 | 1.59x, 1 | 1.73x, 6 |

At 260k the replay predicts 38 and 12 compactions for lane1 and mat-lib, against 35 and 12 that happened. Moving from 260k to 200k would save about 7% of lane1's session cost and 9% of mat-lib's, at the price of 25 and 6 more compactions, each a handoff, a compaction of 40 to 60 seconds and about 20k tokens of re-reading. The kit's 250k warning is a reasonable place, and the tail above 300k is the part to act on: it is 135 requests in lane1 (1.1% of its cost), and the longest wait from the first warning to the compaction was 110 requests, on a long benchmark.

## Does the kit make the session re-read files

Re-reading after a compaction is a property of compacting. The model has a summary and reads the files again to work on them.

| | lane1 | demo-mat-porting | mat-lib | June mat-lib | June cx-optimization |
| --- | --- | --- | --- | --- | --- |
| Reads of a file read in an earlier segment, per compaction | 19k tokens | 1k | 26k | 23k | 10k |
| Share of the session's cost | 6.3% | 0.3% | 9.9% | 8.2% | 5.5% |
| In the first 15 requests: named by the handoff / chosen by the model | 45 / 136 | 0 / 0 | 66 / 25 | 0 / 152 | 0 / 34 |

- The handoff's "Documents in hand" list is read in mat-lib, where it holds about 20 source files and documents, and is mostly not read in lane1 and demo-mat-porting. In demo-mat-porting the model read parts of its listed documents with `sed` and `grep` in Bash, which this count of Read calls does not see.
- The list replaces the model's own choices more than it adds to them. mat-lib re-read about as much after a handoff as before one existed. Whether the list makes the restart better than the model's own picks cannot be told from this data, since the pre-kit restarts also went without errors in the sense measured here. The clear gains above (no questions, nothing in flight) come from the commit-first handoff.
- A restart is larger than in June: 87k to 112k tokens of context after a compaction against 44k to 47k, and 32k to 57k tokens written to the cache at each restart against 17k. The kit's own text is about 8k to 12k of that (the global rules 4.6k tokens, `CODE.md` about 1.5k where imported, `CLAUDE.local.md` 1.9k to 3.7k). The rest is the engine's tools, skill listing and instructions, which differ from June and are not the kit's. The restart rewrite is 2% to 3% of cost now and 1% in June. `restart-size.md` breaks the restart into its sources and prices the cuts.

Taken together, the compaction machinery (summary request, restart rewrite, carried summary and re-reads) is 13.0% of lane1's cost, 15.2% of mat-lib's and 4.2% of demo-mat-porting's, against 12.0% and 9.7% in June.

## Questions that were not asked

- What does the kit's text cost? 41.6k tokens in lane1, 23.5k in mat-lib, 2.7k in demo-mat-porting: 0.39%, 0.70% and 0.28% of modeled cost, counting about 60 requests of carrying each. The largest part is the lint feedback after an edit (about 780 to 840 characters a fire, 93 to 103 fires), then the test log line (71 fires in lane1) and the prose tells.
- Is the lint feedback acted on? An edit of the same file followed within five requests for 71 of 95 fires in mat-lib (75%), 31 of 103 in lane1 (30%, a mix of the kit's findings and tagents' own rules, which the count cannot separate) and 2 of 5 in demo-mat-porting.
- Did the guard get in the way? Only in lane1: 12 refusals, 11 of them the false ones of the 0.21.1 guard described in `tagents-lane1-under-the-kit.md`. None in the other two. The test log's false lines are fixed in 0.35.1 (A66, a test run is what the guard calls one, and a stale run is said once).
- Is the cache kept warm? (O10, the prompt cache stays warm across a session.) lane1 had 5 cold sends writing 855k tokens (about 1.4% of cost), the other two none. They follow the owner's pauses.
- How many prompts is the lifecycle? Handoff plus compact prompts against the owner's own asks: lane1 68 to 50, mat-lib 25 to 32, demo-mat-porting 4 to 5. In June it was 34 compaction prompts to 193 asks and 30 to 139. Two prompts per compaction against one explains part. The rest is more work per ask: 52 requests per ask in lane1 and 27 in mat-lib against 17 in June.
- Did the handoff chain lose nothing at the boundary? (O12, lose nothing at a context boundary.) No re-run commands and no questions in 49 compactions is the strongest evidence in this data that it did not.

## What to do with it

1. Keep the commit-first handoff before every compaction. It is the measured gain.
2. Do not lower the warning from 250k now. The saving is 7% to 9% of cost for 50% to 100% more compactions. Revisit it if the handoff and the compaction become one step, since the owner's prompts are what a lower threshold would multiply.
3. Treat the tail as the target: a nudge that fires again past 300k while a long run is in progress, since 6 of lane1's 35 compactions came after it and the worst after 110 requests.
4. Trim `Documents in hand` to what the next step needs, as an experiment on one project: mat-lib's list drives 26k tokens a compaction and nothing here shows it is worth more than the model's own choice.
5. Make the baseline repeatable: two June sessions are all there is. Keep `kit-impact-scripts/` and run it again after the next week of sessions.
