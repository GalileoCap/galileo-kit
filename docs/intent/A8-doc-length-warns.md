---
id: A8
from: [O16]
source: session
status: decided 2026-10-11
kind: check
implemented_by: [plugins/session-kit/hooks/doc_length.ts, plugins/session-kit/hooks/kit.tsx, plugins/session-kit/.claude-plugin/plugin.json]
proven_by: [plugins/session-kit/hooks/doc_length.test.ts]
supersedes: []
---

# A8 The document-length warning

A `tool.call` hook on Edit and Write tells the model when a markdown document under `docs/` it touched is past the cap, the `docLines` option, 1500 lines, so that it splits the file.

## Context

A long document costs context every time it is read in full, and the rule after a compaction is to read in full.

## Consequences

No process started since 0.8.0, in `hooks/doc_length.ts`. The warning goes to the model as context on the result, where the Python hook's went to the person as a system message: the model is the one that splits. It hung from a goal and no objective until `O16` was proposed, and is retired with `O16` if the owner cuts it.
