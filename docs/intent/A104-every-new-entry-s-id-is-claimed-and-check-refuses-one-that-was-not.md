---
id: A104
from: [O18]
source: session
status: decided 2026-11-18
kind: check
implemented_by: [plugins/session-kit/intent/session_intent.py, global/goals-objectives-actions.md, global/CLAUDE.md]
proven_by: [plugins/session-kit/intent/test_session_intent.py]
supersedes: []
---

# A104 Every new entry's id is claimed, and check refuses one that was not

`session-intent next <level>` takes one `--title` per id and claims them consecutively under one lock, each logged with its title, and refuses a claim with no title or a blank one. `session-intent check` reads the clone's claims log and refuses an entry the branch adds whose id this checkout never claimed, or whose id the integration branch's tip holds under another file name. An entry the branch adds is one missing from the integration branch where the branch forked from it. The integration branch is `intent.integration` in `.claude/claude-kit.json`, by default the remote's default branch, and with neither, every entry counts. Ids below their level's first claim are older than the log and pass, and a machine with no log, such as CI, checks no claims. The refusal names the fix: a new id from `next`, given to the file name, the `id` and every `from`, `supersedes` and Intent-block line naming it.

## Context

The allocator (`A27`, the id allocator) let a session number by hand, trusting the next `next` to move past it. In tagents that failed twice: sessions writing several entries claimed one id and numbered the rest themselves, the log never saw those, and `next` gave the same numbers to another worktree, whose `check` read only its own tree. The tagents lane4 session proposed both changes on 2026-11-18 and the owner approved them with three amendments: titles required, the check skipped with no log, the refusal naming every link to rename. Run against tagents' worktrees with `dev` as the integration branch, the check refused lane1's six hand-numbered actions, and the tip test added lane1's `A224`, claimed in order but already taken on `dev` by lane4's hand-numbered one.

## Options

- `--count N` beside `--title`, as proposed. Rejected: the titles already count the ids, and a count with fewer titles would log claims nobody can read.
- Accept a claim by any checkout. Rejected: a hand-numbered id another worktree claimed later would pass.
- Match each entry's title against its claim's title, with no integration branch. Rejected: an entry renamed after its claim would fail against a log that is never edited.

## Consequences

A project whose worktrees merge into a branch other than the remote's default must set `intent.integration`, or entries already on that branch and claimed elsewhere are refused. An entry merged straight from another worktree's branch is refused until the integration branch holds it. Undone if refusals of entries that were claimed in order outnumber the clashes caught.
