---
id: O15
from: [G4]
source: inferred
status: proposed 2026-10-24
---

# O15 Routine work takes the cheaper path

When the model does a routine thing two ways, it takes the cheaper: a single-line edit through the edit tool, a read through the read tool, a heredoc only for what needs one.

## Changes

How the model does a repeated small thing, and the tokens and time each takes.

## Known by

The nudges a session receives for the costlier path, counted per session, fall. Nothing counts them today.

Inferred from `nudge_single_edit.py`, which hung from a goal and no objective. Proposed so that the hook has an objective, or is retired with it.
