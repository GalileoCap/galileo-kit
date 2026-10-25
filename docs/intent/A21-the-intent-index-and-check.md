---
id: A21
from: [O3, O6]
source: session
status: decided 2026-10-24
kind: check
implemented_by: [plugins/session-kit/intent/session_intent.py, plugins/session-kit/bin/session-intent, docs/intent/INDEX.md]
proven_by: [plugins/session-kit/intent/test_session_intent.py]
supersedes: []
---

# A21 The index and check tool for docs/intent

A command of the kit generates `docs/intent/INDEX.md`, leading with the validation queue, and checks the record: ids resolve, every path in `implemented_by` exists, every approved objective has an action, every action an objective, no status lacks a date, every retired entry names its successor, and the `CLAUDE.md` Intent block matches the active entries.

## Context

The process keeps links upward only and derives the rest, and a derived view maintained by hand rots. The check is the program behind the record, so a stale entry announces itself through a dangling path instead of through a reader.

## Shape as built (2026-10-25, session-kit 0.7.0)

`session-intent index` writes `docs/intent/INDEX.md` and `session-intent check` reads the record, one line per problem, exit 1 on any. Standard library Python behind a `bin/` wrapper, no package of its own until a second command needs one. Beyond the list above it checks that a file's name carries its id, that an action has its four fields, that the paths in `proven_by` exist too, and that `INDEX.md` is current, so the index is held by the gate instead of by hand. A retired action's paths are not checked, since what implemented it is gone by design and git keeps it. An approved objective passes with no action when its body says "no action yet". A constraint may be `proposed` while it waits on the owner, which the process table does not say. The index leads with what waits on the owner, oldest first, then the ladder downward, the constraints, and the retired entries with their successors.

The first run over this record found six problems: `A4`'s paths to the deleted Python hook, `A5`'s prose in `proven_by`, and `O4`, `O10` and `O13` approved with no action and no word about it. Each was fixed in the entry.

## Consequences

Built in the kit, as a command beside `session-tells`. The `CLAUDE.md` Intent block is still written by hand and checked by the tool, since the block carries a clause per entry that the headers do not hold. Validated when the owner reads one `INDEX.md` and finds the queue is what they have to decide.
