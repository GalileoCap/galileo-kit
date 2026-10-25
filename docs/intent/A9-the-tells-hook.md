---
id: A9
from: [O8]
source: session
status: decided 2026-10-11
kind: check
implemented_by: [plugins/session-kit/tells, plugins/session-kit/hooks/hooks.json]
proven_by: [plugins/session-kit/tells/scripts/test]
supersedes: []
---

# A9 The prose-tells hook

A PostToolUse hook on Edit, Write and Bash edits lists the prose tells an edit wrote, banned ones to rewrite and rationed ones to count, and `session-tells show` lists a file's.

## Context

Machine-written prose has tells a reader learns to spot. The rules are Python, with tree-sitter readers for the comments of TypeScript and Rust.

## Consequences

One `uv run` per edit, the heaviest hook. The rules stay Python under the port: a mod would spawn them with `$.process.run`, which keeps the cost, so the hook stays a settings hook unless the rules move to TypeScript.
