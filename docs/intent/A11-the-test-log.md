---
id: A11
from: [O6, O9]
source: session
status: decided 2026-10-11
kind: check
implemented_by: [plugins/session-kit/hooks/test_log.ts, plugins/session-kit/hooks/kit.tsx]
proven_by: [plugins/session-kit/hooks/test_log.test.ts]
supersedes: []
---

# A11 The test log

A `tool.call` hook on Bash writes the last test run's whole output to `<tempdir>/claude-kit-last-test-<session id>.log` and names the file when a run fails.

## Context

A test run's output is evidence. Kept whole in a file, it is read again instead of the run being repeated, and a claim of green has a record behind it.

## Consequences

No process started since 0.8.0, in `hooks/test_log.ts`: the hook sees the output in-process and writes it with `$.fs`. A failed run is the result's `isError`, so one hook covers what took a PostToolUse and a PostToolUseFailure hook. The temporary directory is `TMPDIR`, else `/tmp`, read through `$.env`.
