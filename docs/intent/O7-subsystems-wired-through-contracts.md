---
id: O7
from: [G3]
source: inferred
status: approved 2026-10-24
---

# O7 Subsystems wired through contracts

A project is split into independent subsystems wired together through contracts, so that one can be rewritten while the rest does not care, and the owner reviews the architecture and the integration surface.

## Changes

The shape of each codebase, and which part of a change the owner reads.

## Known by

A subsystem's rewrite changes no file outside it, and the owner's review reads the contracts and the wiring, with the insides left to the gates.

Inferred from G3, "split pieces of projects into independent subsystems that are then wired together" and "mostly concerned with the general architecture and the integration surface".
