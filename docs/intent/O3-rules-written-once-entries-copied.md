---
id: O3
from: [G1]
source: inferred
status: proposed 2026-10-24
---

# O3 Rules are written once, entries are copied

The rules and the process every project follows are written once, in `session-kit`'s global rules, and nothing else is shared: a project copies the entries it needs and owns the copy.

## Changes

Where a new project starts from, and where a rule is changed.

## Known by

A new project runs under the global rules on its first day with an empty `docs/intent/`, and no entry in one project links to an entry in another.

Inferred from G1, "abstracting certain rules and common requirements (like this whole intent thing)", and the owner's correction that a project owns a copy of each entry it needs.
