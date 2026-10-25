---
id: C1
from: []
source: inferred
status: proposed 2026-10-24
---

# C1 The kit is never the reason a session fails

When a hook of the kit crashes, or a tool it runs is missing, the session goes on and the hook reports the failure where the model can read it. The exception is the guard, which refuses the call it was checking: a crash there lets through what it exists to refuse.

Inferred from every hook's docstring, "a hook never breaks the session". A constraint comes from the owner, so this one is proposed until the owner states it or strikes it. `session-kit`'s ladder held it as an objective, `O10`, and the process made it the first constraint.
