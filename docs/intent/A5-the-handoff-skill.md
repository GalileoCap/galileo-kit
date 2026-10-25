---
id: A5
from: [O12]
source: session
status: decided 2026-10-11
kind: behaviour
implemented_by: [plugins/session-kit/skills/handoff/SKILL.md, plugins/session-kit/skills/handoff/template.md]
proven_by: unproven
supersedes: []
---

# A5 The handoff skill writes the live state

`/session-kit:handoff` rewrites `CLAUDE.local.md` whole from the conversation's state: task, documents, decisions, where it stands, last proof, open questions, next step.

## Context

Only the model can summarise decisions and state, so the handoff is a skill and costs a model turn when run.

## Consequences

One model turn per handoff. Stays a skill under the port. A mod runs it with `$.command.run`, as `A17`'s chain does. Proven by use alone: every `CLAUDE.local.md` of this project was written by it, and no test holds it.
