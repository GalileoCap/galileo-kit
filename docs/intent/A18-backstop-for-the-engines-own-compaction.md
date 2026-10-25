---
id: A18
from: [O12]
source: session
status: decided 2026-10-24
kind: check
implemented_by: [not yet written: a session.compact hook in the context module]
proven_by: unproven
supersedes: []
---

# A18 A backstop for the engine's own compaction

A `session.compact` hook on `trigger: "auto"` adds instructions that make the engine's own summary keep the task, the decisions and the next step.

## Context

When the context hits the engine's threshold, the compaction comes without a handoff, and the summary keeps conclusions and drops the detail a decision turns on.

## Consequences

It cannot run the handoff first, since that needs a model turn. Validated when a summary written under it is checked against the handoff the session would have written.
