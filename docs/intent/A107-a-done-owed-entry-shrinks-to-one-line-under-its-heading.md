---
id: A107
from: [O6, O16]
source: owner
status: decided 2026-11-18
kind: rule
implemented_by: [global/CLAUDE.md, global/RATIONALE.md, OWED.md]
proven_by: []
supersedes: []
---

# A107 A done owed entry shrinks to one line under its heading

When `OWED.md` is tracked in git and an entry is done everywhere it was owed, its body is one line: "Done by <date>." with a few words of what was done when the heading does not say it. The `###` heading and its `##` section stay. A void entry says why in its one line.

## Context

The owner, 2026-11-18: "If OWED.md is tracked in git, already-done things should be replaced with a short summary, to avoid crowding it". The kit's own file had 46 entries in 290 lines, and all but a few were done. A file read whole costs every done step on every read.

## Options

- Remove a done entry, or fold a done section into one summary line. Rejected: `session-owed` keys entries by section and heading and fails on a removal (`A38`, the owed record), so a deploy reading a range across the fold would be refused. Keeping the heading leaves the range reads whole with no code change.
- Move done entries to a second file. Rejected: a second file to name and keep, for what git already keeps.

## Consequences

A done entry costs a heading and a line. Its full text is in the file's git history, and the file being tracked is the condition. An untracked `OWED.md` keeps every entry whole. Whether an entry is done is the session's judgment from what it can check, and an entry it cannot check stays whole.
