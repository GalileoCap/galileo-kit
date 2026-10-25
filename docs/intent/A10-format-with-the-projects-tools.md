---
id: A10
from: [O14]
source: session
status: decided 2026-10-11
kind: behaviour
implemented_by: [plugins/session-kit/hooks/format.py, plugins/session-kit/hooks/hooks.json]
proven_by: [plugins/session-kit/hooks/test_format.py]
supersedes: []
---

# A10 Format with the project's own tools

A PostToolUse hook on Edit, Write and Bash edits runs the formatter the project configures, ruff, oxlint or biome, over the files the edit touched.

## Context

The formatter is picked from the project's own configuration, so a session's edit is held to the same tool as the owner's.

## Consequences

One Python start, then the tools themselves. The port saves only the wrapper. A file ruff's config excludes is kept out of both ruff steps (0.5.1).
