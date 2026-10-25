---
id: A8
from: [O16]
source: session
status: decided 2026-10-11
kind: check
implemented_by: [plugins/session-kit/hooks/doc_length.py, plugins/session-kit/hooks/hooks.json]
proven_by: unproven
supersedes: []
---

# A8 The document-length warning

A PostToolUse hook on Edit and Write warns when a document under `docs/` passes 1500 lines.

## Context

A long document costs context every time it is read in full, and the rule after a compaction is to read in full.

## Consequences

One Python start per Edit or Write. It hung from a goal and no objective until `O16` was proposed, and is retired with `O16` if the owner cuts it. No test proves it.
