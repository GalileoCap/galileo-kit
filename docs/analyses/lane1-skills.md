# lane1's skills and what they cost at a restart (2026-10-26)

For understanding, as `restart-size.md` found that lane1 carries 15.3k tokens of its own skills at every restart. The skills are in `~/devel/iquall/tagents/lane1/.claude/skills/` (19 of them, 106k characters), and the sessions were read from lane1's transcripts. Nothing was changed.

## What the skills are

Each is a `SKILL.md` with a description in the skill list and a body loaded when the model invokes it. The descriptions are written to be loaded just in time ("Load it before bringing a stack up", "Load it before running a gate"). They fall in three groups:

- Process: `lane` (a lane's whole cycle, 6.6k characters), `bugfix` (2.6k), `iterate` and `handoff` (4.3k), `verify`, `integration-test`.
- Reference: `stack` (12.9k: names, ports, bucket, Zitadel, the seeded world, the toolchain), `findings` (7.9k: the tracker and its licences), `prove` (7.3k: runners, tiers, the test slot, the offload host), `frontend` (9.9k).
- Work for one kind of worktree: `deploy`, `patch`, `new-worktree`, `close-worktree`, `clear-worktree`, `restore-prod` (dev only), `verifier`, `desk`, `demo`.

## What happened in lane1

lane1 is one session, `16cac123`, that ran for two days and compacted 35 times. It invoked six of the skills once each: `lane` at the start (2026-10-25 19:32), `findings`, `handoff` and `prove` in the next half hour, `stack` three hours in, and `bugfix` on the 26th at 17:59. After a compaction the engine re-attaches every skill invoked earlier in the session in full, so each one stayed in the context from then on, through all the compactions that followed. The kit's `session-kit:handoff` was invoked 36 times by slash command and is re-attached once.

A skill meant to be loaded for a moment became resident for the life of the session. It is the same text each time, and what it costs is the carrying: 1k tokens of restart messages is 0.32% of lane1's session cost.

| Skill | Characters | Tokens | Carried at | Share of lane1's cost | Commands it governs in the session |
| --- | --- | --- | --- | --- | --- |
| `stack` | 12,659 | 4.7k | 37 of 38 restarts | 1.5% | 6 (`devweb`, `devdb`, the world seed) |
| `findings` | 7,648 | 2.9k | 38 | 0.9% | 43 (`scripts/findings`) |
| `prove` | 7,117 | 2.7k | 37 | 0.9% | 282 (`scripts/test`, `check`, `prove`, `testslot`) |
| `lane` | 6,439 | 2.4k | 38 | 0.8% | 103 (`scripts/merge`, `overlap`, `regenerate`, `session-intent`) |
| `handoff` (the project's) | 4,147 | 1.6k | 38 | 0.5% | 1 call of `/handoff` |
| `bugfix` | 2,423 | 0.9k | 24 | 0.2% | 27 (regression tests) |
| `session-kit:handoff` | 2,629 | 1.0k | 38 | 0.3% | 36 calls |
| Total | 42,862 | 16.1k | | 5.1% | |

The commands are counted by pattern over the session's Bash calls and rank the skills by how much work they steer. They do not prove a skill was consulted.

## What stands out

1. `stack` is the biggest and governs the least. It is reference for bringing a stack up and seeding a world, and the session ran six such commands in 2,601 requests. It costs more than any other skill at every restart. `prove` and `lane` steer hundreds of commands and earn the carrying.
2. Two handoff skills write the same file. The project's `handoff` has its own fields (Stack, Intent, Inbox, open items ranked in six groups) and says to write at the end of every turn and skip the ask under 30% of the window. The kit's says to write at clear points and skip it under 150,000 tokens. The session used the kit's 36 times and the project's once. The project's fields are part of why lane1's `CLAUDE.local.md` is 8.6k characters against mat-lib's 6.0k, and both bodies are carried (2.6k tokens). The project's `iterate` is likewise beside the kit's.
3. The skills repeat the global rules. "Blind tests are scaffolding", "two tries then stop", "an unrelated failure is never called flaky" and "a defect fix lands with a regression test that failed first" are in `prove`, `bugfix` and `lane`, and in the global rules that every request already carries. I did not count the characters.
4. The lane's own clear point is a clear. `lane` ends with "the turn ends asking to clear", and `handoff` prefers a clear to a compaction. The kit's chain compacts, which is the step that re-attaches the skills, restores files and writes a summary. A clear would carry none of them, only the prefix, the rules and `CLAUDE.local.md`.
5. Nine skills belong to other kinds of worktree. `deploy`, `patch`, `new-worktree`, `close-worktree`, `clear-worktree`, `restore-prod`, `verifier`, `desk` and `demo` say in their descriptions that they run in dev, the verifier's worktree, the desk or a demo lane. All 19 descriptions are in every lane's skill list, 5.1k characters or 1.9k tokens, 0.6% of the session.

## What could change it

These are the options the reading shows, with the share of lane1's cost each would take away. None is applied, and each is the project's or the owner's call.

- Split `stack` into a short skill (the rules, and "read `docs/…/stack.md` before bringing a stack up") and a document. A Read is not re-attached after a compaction unless it is among the last few files read, which the engine restores. About 4k tokens, 1.3%. The same split for the commands and tables of `findings` and `prove` would take another 2k to 3k, about 0.8%.
- Keep one handoff. Moving the project's extra fields into the kit's template or the project's `CLAUDE.md`, and dropping the project's `handoff`, takes out 1.6k tokens (0.5%) and settles which rule about when to write wins.
- Remove from the skills the lines the global rules already say. Unmeasured.
- Chain with a clear in place of a compaction, at the points where `lane` already asks for one. A restart would hold no skills, summary or restored files: 15.3k + 5.3k + 5.7k tokens, 8.4% of lane1's cost, while the state travels in `CLAUDE.local.md` and its document list. It is the largest of these and the riskiest, since the summary is what carries what the file does not (`O12`, lose nothing at a context boundary). The 49 compactions in the three projects had no question after them, which shows the handoff is carrying the state, and says nothing yet about a restart with no summary.

## Limits

- Tokens are characters over 2.67, the density fitted in `restart-size.md`. Shares use the 0.32% per 1k tokens measured there.
- The command counts are patterns over one session's Bash calls. They miss a skill used by reading its text, and a command run through a script.
- One session is one case. Whether other lanes invoke other skills was not read.
