---
id: A103
from: [O3, O17]
source: owner
status: decided 2026-11-17
kind: rule
implemented_by: [global/CLAUDE.md, global/RATIONALE.md, plugins/session-kit/transcripts/week.py]
proven_by: [unproven]
supersedes: []
---

# A103 Memory holds only what no file can

The global rule sends a note to the file that holds its kind: a project's rule or fact to its `CLAUDE.md`, a skill or its docs, deferred work to its plan, and a rule the owner gives for every project into the reply as a candidate for the kit's global rules, kept in memory until it is one. The week review (`session-transcripts week`) ends with every project folder's memory files, their words and their index's, a folder whose project is gone from disk flagged, so the drift is seen each week.

## Context

`docs/analyses/memories-and-context-boundaries.md` read the 82 memory files in 30 project folders on 2026-11-17: none needed to be a memory. 35 belonged in their project's files, 18 repeated them, 18 outlived their project, and 11 were the owner's rules for every project, each stranded in the folder that heard it. The old rule ("Memory holds what crosses conversations: preferences and feedback") and the engine's own instructions sent every correction there. The owner agreed to the rule and the listing on 2026-11-17. The sweep of the existing files is prepared for their review in `docs/analyses/memory-sweep-plan.md` and applied only once approved.

## Options

- A kit check that fails on a memory file. Rejected: a preference with no file to hold it is still a memory's.

## Consequences

The listing reads a folder's directory from the working directory its sessions recorded, and from the folder's name matched against the disk when no session is left, so a folder whose name matches nothing reads as gone. Proven when a week passes with the listing short.
