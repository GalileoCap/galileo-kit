---
id: A11
from: [O6, O9]
source: session
status: decided 2026-10-11
kind: check
implemented_by: [plugins/session-kit/hooks/test_log.py, plugins/session-kit/hooks/hooks.json]
proven_by: [plugins/session-kit/hooks/test_test_log.py]
supersedes: []
---

# A11 The test log

A PostToolUse and PostToolUseFailure hook on Bash writes the last test run's whole output to `<tempdir>/claude-kit-last-test-<session id>.log` and names the file when a run fails.

## Context

A test run's output is evidence. Kept whole in a file, it is read again instead of the run being repeated, and a claim of green has a record behind it.

## Consequences

One Python start per Bash call. Under the port a `tool.call` hook sees the output in-process and writes it with `$.fs`.
