---
id: A27
from: [O18, O12]
source: session
status: decided 2026-10-25
kind: check
implemented_by: [plugins/session-kit/intent/session_intent.py, plugins/session-kit/bin/session-intent, global/goals-objectives-actions.md, global/CLAUDE.md]
proven_by: [plugins/session-kit/intent/test_session_intent.py]
supersedes: []
---

# A27 The id allocator

A new entry's id comes from `session-intent next <level>`, which claims it under a lock and never gives it again. The floor is the highest id the record holds or the last one claimed, whichever is higher, so a fresh clone needs no seeding and a claim whose file was never written still spends its number. The claims live outside every checkout, under `~/.claude/session-kit/intent/`, one directory per clone named after its git common directory, so every worktree of the clone draws from one counter, with an append-only log saying which checkout took each id, at which commit, with what title.

## Context

Until now a session picked an id by reading `docs/intent/` and adding one, which is a read-modify-write race with prose for a database. The first project did the same across its worktrees and paid for it: four renumberings and two live collisions, one beyond repair because a tag on the remote quotes it, before it wrote an allocator behind a mutex. The kit's ids are what the communication objective (`O18`) rests on, and an id that names two entries is worse than one with no name.

## Options

- The counter inside the tree, beside the entries. Every worktree reads a different commit, so the counter is wrong in all but one, and it conflicts on every merge.
- The counter under the clone's `.git` directory. Shared by its worktrees and gone with the clone, which is right, but a second clone on the same machine would start its own. Under `~/.claude/session-kit/` the key is the common directory's path, so the counter outlives the clone and a second clone at another path keeps a separate one, which the record's floor corrects on its first claim.
- `peek`, `retire` and `floor` commands, as the first project has. Left out until a second use asks: the record's floor replaces seeding, a hole in the numbering is allowed, and the log is read with `cat`.

## Consequences

A session that takes an id by hand is not stopped, and the next `next` moves past it. The counter is one machine's, so two machines claiming the same level at once can still collide until one pushes. The floor from the record then catches it on the other machine's next claim. Undone if the claims log is never read and the directory is never shared across a machine's clones, which would mean the lock could live in the tree after all.
