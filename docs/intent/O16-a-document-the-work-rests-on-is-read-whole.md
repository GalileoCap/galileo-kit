---
id: O16
from: [G4]
source: inferred
status: proposed 2026-10-24
---

# O16 A document the work rests on is read whole

A document the work rests on is short enough to be read whole, so that a session reads it in full after a compaction and does not work from a summary of it.

## Changes

The length of the documents under `docs/`, and what a session reads after a compaction.

## Known by

No document under `docs/` passes the length the hook warns at, and a session after a compaction reads each document the handoff lists in full.

Inferred from `doc_length.py`, which hung from a goal and no objective, and from the rule "read again in full the documents the work rests on". Proposed so that the hook has an objective, or is retired with it.
