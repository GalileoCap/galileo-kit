---
id: A20
from: [O7]
source: session
status: decided 2026-10-24
kind: behaviour
implemented_by: [not yet written: plugins/session-kit/hooks/hooks.json modules list]
proven_by: unproven
supersedes: []
---

# A20 One plugin, one hooks module per concern

The port stays inside the `session-kit` plugin, with the settings hooks that remain and one hooks module per concern: context, guard, test log. It ships in this order, each step leaving the kit working:

1. Context, as `A16`.
2. The chain, `A17`, behind its toggle.
3. `A11`, `A8` and `A7` in-process.
4. The guard, once mod ordering is answered, both guards side by side for a while.
5. One task per context, `A19`.
6. `A9`, `A10`, `A12` and `A13` stay settings hooks.

## Context

The context band, the chain and a future cache signal share figures and `$.state`, which is the research report's rule for merging. `hooks.json` takes a list of modules, so concerns stay in separate files, to confirm with `claude plugin validate` on the first module. The mods API is early access and moves between releases, while settings hooks ride a stable contract, which argues for keeping the guard's settings hook even after the mod guard lands.

## Consequences

Turning one concern off needs a `userConfig` toggle the kit writes. All of it is ours and tested together.
