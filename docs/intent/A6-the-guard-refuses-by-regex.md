---
id: A6
from: [O5]
source: session
status: decided 2026-10-11
kind: check
implemented_by: [plugins/session-kit/hooks/guard.py, plugins/session-kit/hooks/hooks.json]
proven_by: [plugins/session-kit/hooks/test_guard.py]
supersedes: []
---

# A6 The guard refuses by regex

A PreToolUse hook on Bash and Artifact refuses the commands the rules mark refused: `--no-verify`, `reset --hard`, amending a pushed commit, a force-push, a bare stash, test output piped inline, `-x`, shell `timeout`, and any Artifact.

## Context

A reminder in a `CLAUDE.md` had already failed to hold these. Each check is a narrow regex over the command text with carve-outs, and a settings hook runs in every permission mode.

## Consequences

One Python start per Bash call, plus a `git branch -r --contains` on `--amend`. It fails open, so a crash lets through the call it exists to refuse, which `C1` names as the exception. On a personal login another mod can approve a call it denied. The mod port, `A20`'s order step 4, fails closed and waits on the mod-ordering question.
