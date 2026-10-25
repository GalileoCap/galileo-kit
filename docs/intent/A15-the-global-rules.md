---
id: A15
from: [O3]
source: session
status: decided 2026-10-11
kind: behaviour
implemented_by: [global/CLAUDE.md, global/RATIONALE.md, global/install.sh]
proven_by: [global/test_install.sh]
supersedes: []
---

# A15 The global rules, linked into every session

The rules every project follows live in `global/CLAUDE.md`, with each rule's reason under the same heading in `global/RATIONALE.md`, and `install.sh` links the file at `~/.claude/CLAUDE.md`.

## Context

A plugin cannot ship a `CLAUDE.md`, so the rules reach every session through the link.

## Consequences

Loaded into every session. Under the process each rule names the action it is, and `RATIONALE.md` splits into one file per rule, proposed in `global/goals-objectives-actions.md` and not yet done.
