---
id: A2
from: [O2]
source: session
status: decided 2026-10-24
kind: behaviour
implemented_by: [CLAUDE.md]
proven_by: unproven
supersedes: []
---

# A2 A fork is pinned in galileo-kit

A fork lives in the `galileo-kit` marketplace with a pinned `"version"`, by default as a separate plugin. It moves into `session-kit` itself only when it shares code or state with it.

## Context

A plugin installed from its author's marketplace changes when the author publishes, and auto-update is on for marketplaces that are not the user's own.

## Options

- Install as is: serves nothing once the source moves.
- Fork into `session-kit` itself: serves `O2`, and couples unrelated code to the kit's releases.
- Fork beside it, as its own plugin: serves `O2`. Taken.

## Consequences

Every upstream fix is merged by hand. Undone if the merges cost more than the reviews they save. Unproven: no fork has been made yet.
