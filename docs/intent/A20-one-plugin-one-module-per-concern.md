---
id: A20
from: [O7]
source: session
status: decided 2026-10-24
kind: behaviour
implemented_by: [plugins/session-kit/hooks/hooks.json, plugins/session-kit/hooks/kit.tsx]
proven_by: [docs/PLAN.md]
supersedes: []
---

# A20 One plugin, one hooks module per concern

The port stays inside the `session-kit` plugin, with the settings hooks that remain and one hooks module, `hooks/kit.tsx`, whose register calls one file per concern: context, test log, document length, nudge, and the guard to come. It ships in this order, each step leaving the kit working:

1. Context, as `A16`.
2. The chain, `A17`, behind its toggle.
3. `A11`, `A8` and `A7` in-process.
4. The guard, once mod ordering is answered, both guards side by side for a while.
5. One task per context, `A19`.
6. `A9`, `A10`, `A12` and `A13` stay settings hooks.

## Context

The context band, the chain and a future cache signal share figures and `$.state`, which is the research report's rule for merging. The engine loads one hooks module per plugin: `hooks.json`'s `modules` refuses a second entry, found at step 3 on 2026-10-25, which corrected the premise written here on 2026-10-24. A module may import files of its own, so the concerns stay in separate files behind one entry module. The mods API is early access and moves between releases, while settings hooks ride a stable contract, which argues for keeping the guard's settings hook even after the mod guard lands.

## Consequences

Turning one concern off needs a `userConfig` toggle the kit writes. All of it is ours and tested together. Steps 1 to 3 shipped 2026-10-25 as 0.6.0, 0.7.0 and 0.8.0. The hook times after each are in `docs/measurements/hook-times.md`.
