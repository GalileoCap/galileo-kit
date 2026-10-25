---
id: A53
from: [O6, O5]
source: session
status: decided 2026-10-25
kind: check
implemented_by: [plugins/session-kit/hooks/test_log.ts, plugins/session-kit/types/index.d.ts]
proven_by: [plugins/session-kit/hooks/test_log.test.ts]
supersedes: []
---

# A53 The two-tries rule as a program

The test log of `A11` (the test log) counts the same test command failing with the same error. A failed run after a file was edited is a try at a fix, and the second such try adds a line of context naming the global rule, "a fix that has not worked after two tries stops and shows evidence", with what the rule asks. A rerun with no edit between is no try. A different error, or a run that passes, starts the count over. An edit is an `Edit`, `Write` or `NotebookEdit` call that landed. The error's signature is its failure lines (`FAILED`, `ERROR`, `FAIL`, `--- FAIL`, `not ok`, `... FAILED`, the runners' marks), or every line where none is one, with colour, timings and addresses taken out.

## Context

`docs/analyses/mods-for-the-kit.md`, M15, from loop-detective. The global rule had nothing behind it: a session looping on a failing test is seen by the owner reading the transcript, after the third and fourth try. Every step moves to a program where one can do it (`O5`), and the count is a record a program wrote (`O6`).

## Options

- Every failure counted, with or without an edit, at loop-detective's threshold of three. Rejected: the rule is about fixes, and a rerun that fails the same way gathers the evidence the rule asks for.
- Every line of the output as the signature. Rejected: a traceback carries the line numbers an edit moves, so the same failure would read as a new one after every fix. The failure lines hold still, and pytest's carry the message.
- A shell command that writes a file (`sed`, a heredoc) counted as an edit. Rejected: the kit cannot tell which commands write, and `A47` (the guard reads the command as the shell runs it) made the same choice for the runners.

## Consequences

The count lives in `testRetry` in `$.state`, one for the session, keyed by the command's text: a narrowed rerun (one test file) is a different command and starts over, and a subagent's edits and runs count with the main loop's. An output whose failure lines change on every run (a date, a port, a temporary path) never matches, so the rule misses it. A failure with no failure line and a moving traceback reads as a new error each time. The line is given again at every failed try after the second, while the loop goes on.

## Proof

One engine test in `test_log.test.ts`. The third failure of the same command, after two edits, carries the rule, with a line number, a timing and a colour code changed between. A rerun with no edit is not counted, and the next edit's failure is named again. A different failure line starts over, and so does a pass. A refused edit is no edit. It failed on 0.25.0.
