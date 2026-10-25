---
id: A18
from: [O12]
source: session
status: decided 2026-10-24
kind: check
implemented_by: [plugins/session-kit/hooks/context.tsx]
proven_by: [plugins/session-kit/hooks/chain.test.tsx]
supersedes: []
---

# A18 A backstop for the engine's own compaction

A `session.compact` hook on `trigger: "auto"` adds instructions that make the engine's own summary keep the task, the decisions and the next step.

## Context

When the context hits the engine's threshold, the compaction comes without a handoff, and the summary keeps conclusions and drops the detail a decision turns on.

## Consequences

It cannot run the handoff first, since that needs a model turn. Built 2026-10-25 in session-kit 0.7.0 as a `session.compact` hook matched on `trigger: "auto"`, main conversation only, that appends to the engine's instructions what a handoff keeps: the task in the user's words, the decisions with who took them, where the work stands, the last proof, the open questions, the next step in one line, and the paths of the documents the work rests on. The text is the exported `backstop`, which the test proves. A test cannot raise a compaction with the `auto` trigger, so the hook's firing is proven only by `claude plugin validate` listing it. Validated when a summary written under it is checked against the handoff the session would have written.
