---
id: A18
from: [O12]
source: session
status: retired 2026-10-26
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

## Retired

Retired on 2026-10-26 by the owner's word, superseded by `A67` (the kit hooks no event the security default sends past it). The organization's security default (`C2`) sends `session.compact` past every plugin the person installs, so the hook never ran on this machine, and the engine named it skipped in each session. The hook and `backstop` are removed in session-kit 0.35.2. The engine's own compaction goes on with its own instructions, and the chain's `/compact` (`A61`, the chain compacts through /compact in every session) carries the handoff's.
