# tagents' lane1 under the kit (2026-10-25 to 2026-10-26)

What session-kit did to one real piece of work: lane1's session `16cac123` in `~/devel/iquall/tagents/lane1`, from #909 to #911 under the lane's O16 (the full suite fits its ten minutes). Read from its transcript (45 MB, 574 requests, 55 prompts, 47.47 USD, 98% of the input read from the cache) with `session-transcripts` and short scripts over the JSON lines, and from the lane's commits and its `CLAUDE.local.md`. Nothing in lane1 was changed.

## Which kit ran

Two versions at once. The command hooks and the skills came from the 0.21.1 copy throughout (75 paths under `session-kit/0.21.1/` in the transcript). The in-process hooks were 0.35.0's from 12:36 UTC on 2026-10-26, two minutes after the 0.35.0 copy was written to the cache, with no restart: the stale-run verdict that appears then exists in no cached copy before 0.35.0. So an update reaches a running session's in-process hooks and leaves its command hooks behind. The mechanism is inferred from the timing and was not traced in the engine.

## What it did, and what came of it

| Kit part | Fires | Effect on the work |
| --- | --- | --- |
| The chain: `clear_point`, then handoff, compaction and "Continue" | 4 clear points, 3 automatic continues, 1 stop for the owner | Carried the lane across six compactions with no prompt from the owner but the next ask. Each continue reread the documents `CLAUDE.local.md` lists: 6 rereads, 135,526 characters, 33% of all reads. |
| The context warning | 11, from 250k tokens | All 11 were followed by a handoff, but late: the first came at 251k and the compaction nine turns later, at 439k. About two hours of requests carried 250k to 439k tokens of context. |
| The guard: test output piped to `grep` or `head` | 11 refusals | All 11 were false. Each was a `grep` or `wc` over a file whose name or pattern held a runner (`scripts/test`, `playwright`, `pytest.mark`, `vitest`). Each cost a retry. Run against these 11 commands, 0.21.1's guard refuses 6 by a replay of its rules, and the guard on `main` refuses none: fixed since, and lane1 never got the fix. |
| The test log: "the test run failed" | 7 | 6 of the 7 fell in the same second as a guard refusal: the in-process log counts a call the guard refused as a failed test run and points the model at a log holding the refusal. The seventh is unpaired. |
| The test log: stale run | 3 to the model at a commit, plus the dim line at every turn's end | All three were false: a `sed -i 's/def te…'`, a `python3 -I` heredoc and a `grep -n "scripts/test…"`, each counted as a test run since the command mentions a runner. The owner saw the dim line, which repeats until a real test run. |
| The tells hook | 30 | Two commits that only rewrite prose in the files the lane touched (`079acf613`, 6 files, and `8c3d46178`, 2 files). The rule asks for that cost. |
| The suppression reason nudge | 4 | Each `noqa` written got its reason. tagents' own guard fired beside it on the same edits. |
| The heredoc nudge | 4 | A Python heredoc doing one edit, pointed at the Edit tool. |
| `session-watched` | 27 runs | Every long run went through it, the seven timed full runs included. |
| `session-intent`, `session-tells`, `session-docs`, `session-suppressions` | 29, 37, 5, 2 runs | The lane's record (O16, A81 to A87) is kept with the kit's tools, and each commit names its objective by id and name. |
| The global rules' gates on a project that has not adopted them | 2 | `session-docs check` (113 documents not named) and `session-suppressions check` (144 markers with no reason) are red in tagents, none of it the lane's. The session put both to the owner. Any session in tagents that follows the rules lands on the same two asks. |

The lane measured the kit's own cost in run 7 (`docs/quality/full-suite-timing-2026-10-26.md`, §8): the guard 27 ms per Bash call, the formatter and tells hooks 34 ms and 80 ms per edit. The larger hook costs there are tagents' own: 240 ms per edit for its code map and 1.0 s per turn's end for its Stop hook.

## What the kit got wrong here

1. A test run is any command that mentions a runner. `isTestRun` in `hooks/test_log.ts` matches a runner's name anywhere, quoted text included. The guard on `main` already holds the right rule (quoted text blanked, a runner only where a command segment starts, behind a launcher). The log should share it.
2. A refused call is logged as a failed run. The test log returns early on an in-process `deny`, but a refusal by a command hook reaches it as an error result, so it is recorded as a run that failed.
3. The stale line repeats at every turn's end while nothing changes. One line when the verdict or the run changes says the same once.
4. Worktrees keep an old copy of the command hooks. lane1's install record stayed at 0.21.1, so the guard's fix never reached it while the in-process hooks moved to 0.35.0.
5. The warning came late in practice. Every warning was heeded, but only at the next safe point, which on a long benchmark came 190k tokens later.

## Outside the kit, seen in passing

tagents' own `PreToolUse` hook on Edit and Write printed `jq: parse error: Invalid string: control characters` on 85 of 90 edits, so its code map reached the model once. Its `SessionStart` hook failed with a non-blocking error after 6 of 6 compactions. Its Stop hook repeats the kit's stale-handoff advice ("CLAUDE.local.md predates the last commit", 65 times).
