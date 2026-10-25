---
id: A26
from: [O8, O6]
source: session
status: retired 2026-10-25
kind: check
implemented_by: [plugins/session-kit/hooks/suppressions.ts, plugins/session-kit/suppressions/session_suppressions.py, plugins/session-kit/bin/session-suppressions, global/CLAUDE.md]
proven_by: [plugins/session-kit/hooks/suppressions.test.ts, plugins/session-kit/suppressions/test_session_suppressions.py]
supersedes: []
---

# A26 The suppression check and its ledger

Two halves. In-process, after an Edit or a Write that puts a suppression or a type escape into a source file, the model is told it needs the owner's approval and, once approved, a numbered row in the project's decisions file cited beside the marker. On the command line, `session-suppressions check` fails on a marker that cites no row and on a citation whose row the ledger lacks, so the approval the global rule asks for has a place to live and a check that reads it.

## Context

The global rule has needed the owner's approval for a suppression since the kit began, and nothing checked it: the first project warned on the edit in `rule_guard.py` and kept no record, and generic-app kept the record (numbered rows under "awaiting approval" and "approved", cited from the code) and had no check. The 2026-10-25 reading of both projects put the two halves together as the second tool to build.

## Options

- `Any` and `cast(` among the markers, as the rule lists them. Both are too common in ordinary prose and code to match by text without reading types. Left out, and said in the module.
- Relaxed rules in config files (a ruff ignore, an ESLint rule off), which generic-app's table also records. Outside the check for now: what counts as a relaxation differs per tool.
- Refusing the edit instead of warning. The rule puts the choice to the owner, and an edit refused mid-turn is answered by the model alone.

## Consequences

A project that takes the check keeps `docs/decisions.md` or names its own ledger and citation pattern in `.claude/claude-kit.json`. A marker in a test's fixture needs a row or a citation like any other, so a test spells its markers in pieces, as the kit's own do. Undone if the ledger fills with rows nobody reads, which would mean suppressions are too cheap, and the warning should refuse.
