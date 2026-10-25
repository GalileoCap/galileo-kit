---
id: A21
from: [O3, O6]
source: session
status: decided 2026-10-24
kind: check
implemented_by: [not yet written: a command of the kit]
proven_by: unproven
supersedes: []
---

# A21 The index and check tool for docs/intent

A command of the kit generates `docs/intent/INDEX.md`, leading with the validation queue, and checks the record: ids resolve, every path in `implemented_by` exists, every approved objective has an action, every action an objective, no status lacks a date, every retired entry names its successor, and the `CLAUDE.md` Intent block matches the active entries.

## Context

The process keeps links upward only and derives the rest, and a derived view maintained by hand rots. The check is the program behind the record, so a stale entry announces itself through a dangling path instead of through a reader.

## Consequences

Built in the kit, as a command beside `session-tells`. Until it exists there is no `INDEX.md` and the `CLAUDE.md` block is kept by hand.
