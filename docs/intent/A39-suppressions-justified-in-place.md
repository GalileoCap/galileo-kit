---
id: A39
from: [O8, O3]
source: owner
status: decided 2026-10-25
kind: check
implemented_by: [plugins/session-kit/suppressions/session_suppressions.py, plugins/session-kit/hooks/suppressions.ts, global/CLAUDE.md, docs/suppressions.md]
proven_by: [plugins/session-kit/suppressions/test_session_suppressions.py, plugins/session-kit/hooks/suppressions.test.ts]
supersedes: [A26]
---

# A39 Suppressions justified in place

A suppression or a type escape carries its reason beside it: a comment of a few words on its line, after the marker and its codes, or on the line above, saying why the rule does not hold there. `session-suppressions index` writes `docs/suppressions.md`, a table of where, marker and reason, for the owner to review when they choose, and `check` fails on a marker without its reason and on an index that is missing or stale. The hook, after an edit that writes a marker, says to write the reason and regenerate the index. A rule relaxed in a config file carries its reason on its line, outside the check.

## Context

The owner, reading `docs/what-reaches-the-model.md` on 2026-10-25, changed the rule: a suppression does not need their approval outright, it is justified in place and indexed so it can be reviewed. The earlier check (`A26`) held a numbered row in `docs/decisions.md` cited beside each marker, and the rows sat under "awaiting the owner's approval" from the day they were written, with the reason far from the code it excused.

## Options

- The index printed on demand by `list` alone. A committed file is what the owner reviews in a diff and what the docs check names, and a stale one fails, so it is generated like the intent index.
- A reason of any length. One word excuses nothing, so three words is the floor, and the codes after the marker do not count.

## Consequences

The kit's seven markers carry their reasons and `docs/decisions.md` is gone. A project that took the ledger moves each row's reason beside its marker and runs `index`. Undone if the reasons become the same phrase pasted at every site, which would mean the floor is too low.

2026-11-19, session-kit 0.56.5, by the owner's order "Fix the kit's checker": a reason may run over several comment lines, and the check reads it whole. In tagents, 129 markers failed, and 75 of them did carry their reasons. Their reasons wrapped onto the comment lines under the marker or sat in a comment block above it, or the check had dropped their quoted words with the string literals. Three were prose inside block comments ("as any GET"). The 54 left have no reason or a short one.
