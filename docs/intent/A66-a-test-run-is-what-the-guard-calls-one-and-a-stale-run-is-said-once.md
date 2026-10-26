---
id: A66
from: [O6, O8]
source: owner
status: decided 2026-10-26
kind: check
implemented_by: [plugins/session-kit/hooks/test_log.ts, plugins/session-kit/types/index.d.ts, .claude/claude-kit.json, docs/what-reaches-the-model.md]
proven_by: [plugins/session-kit/hooks/test_log.test.ts]
supersedes: []
---

# A66 A test run is what the guard calls one, and a stale run is said once

The test log of `A52` (a check result stamped with the tree it ran on) reads a command as the guard reads it: quoted text and heredoc bodies are blanked, and a runner counts only where it starts a command segment, behind a launcher (`uv run`, `npx`, `python -m`, `session-watched --` and the guard's others) or a path, or neither. A call that a command hook refused, which the engine hands back as an error starting "PreToolUse:Bash hook error:", never ran, and is neither logged nor counted. At a main-loop turn's end, a STALE run's dim line is said once, and again only after the tree has come back to the run's and left it. The model's words at a `git commit` are unchanged.

## Context

The owner saw "the last test run (…; grep -n "^def te…) passed on a different tree" at every turn's end in tagents' lane1, and asked for the fix after `docs/analyses/tagents-lane1-under-the-kit.md`. The log matched a runner's name anywhere in a command, so lane1's `grep` for `pytest.param` and a heredoc that wrote `scripts/test` into a document were logged as passing runs. Once files changed, the line came back at every turn until a real run replaced the record. The 0.21.1 guard's refusals reached the in-process log as error results, so 6 of lane1's 7 "the test run failed" pointers named a refusal and not a run.

## Options

- The guard's reading, ported to TypeScript beside its Python. Taken: the two decide the same question, and a command the guard lets through as no test run is now no test run in the log. The two copies are kept in step by hand, and each says where the other is.
- A runner anywhere outside quoted text. Rejected: `wc -l scripts/test` still counts.
- A refusal read from a field of the result. Not available: the 2.1.308 declarations carry `deny` for an in-process refusal only, so the engine's own wording is matched. A change of that wording brings back the old behaviour, a refusal logged as a failure.
- Both lines, FAIL and STALE, said once. Not taken: the owner asked for the stale line, and a failure left standing is the one to keep in sight.

## Consequences

`TestRun` gains `staleShown`, written at the turn's end when the verdict moves into or out of STALE, and dropped with the record at the next run. This repository's runner entry becomes `claude plugin test`, since `plugin test` never starts a segment: a run through the desktop app's binary by its quoted path is not logged until the terminal's `claude` is 2.1.308 (`OWED.md`). A project runner behind a launcher of the project's own (lane1's `scripts/watched --`) is not a test run, as the guard has it.

## Proof

Three engine tests in `test_log.test.ts`, each from lane1's commands, written before the code and failing on 0.35.0. Its grep, heredoc and `wc` are no test run, while its `session-watched -- scripts/test stack` is one. A call refused with the engine's hook-error words leaves the passing run before it as the last. A run gone stale across edits and turn ends draws one line, then one more after the tree comes back and leaves. `A52`'s test has its untracked-file and deletion cases each start from the run's own tree.
