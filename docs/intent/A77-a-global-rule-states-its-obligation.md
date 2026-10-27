---
id: A77
from: [O3, O8]
source: owner
status: decided 2026-10-26
kind: rule
implemented_by: [global/CLAUDE.md, global/RATIONALE.md]
proven_by: [plugins/session-kit/bin/session-rulebook]
supersedes: []
---

# A77 A global rule states its obligation, and the program that enforces it holds the how

A rule in `global/CLAUDE.md` says what a session must do unprompted. What a program already tells the session when it matters (a refusal of the guard, a gate's failure, a hook's warning and its thresholds, a tool's `--help`) is cut from the rule to its obligation, and the reason stays under the same heading in `RATIONALE.md`. The rules the guard refuses share the `Refused outright` line, listed so a session does not spend a round trip on each. A new rule follows the same shape: its detail goes in the program's message, and only what no program says stays in the prose.

## Context

`session-rulebook` holds what every turn loads to 5,000 words, and the global rules took 2,391 of them before a project wrote any. tagents/desk stood at 5,338 and tagents/lane1 at 5,465, both over. The owner asked for the global rules to be cut to give each project more room. A peer session recommended two of the cuts: the Intent section repeated `goals-objectives-actions.md`, and the guard's rules were restated in prose. The reading is `docs/analyses/global-rules-trim.md`.

## Options

- Raise the budget for the projects that reach it. Rejected: the budget is what keeps a rulebook read (`A28`, the rulebook budget), and raising it where it binds removes it there.
- Move Intent into an import, as `CODE.md` is. Deferred: the projects that keep no record would save 171 words, and none of them is near the budget.
- Move the test rules into a skill. Rejected: a skill loads when its description matches the work, and when it does not, the session works without the rules and no gate notices.
- Cut each rule to its obligation, keeping its heading word for word, since `RATIONALE.md` is found by heading. Taken.

## Consequences

The global rules fall from 2,391 to 1,361 words, and every project gains about 1,030. The Intent section keeps its four rules inline and the sentence on who owns each level, since `RATIONALE.md` records that a one-line pointer left sessions treating the record as optional. `Test output goes to a file` is folded into the `Refused outright` line: its reason is under `Refused outright` in `RATIONALE.md`, and its positive half is the guard's message. A rule whose detail lived only in the prose now depends on the program's message being clear, so a refusal or a gate's failure that says too little is a defect of that program. Undone if sessions are seen breaking a cut rule's detail that no program surfaced: the detail returns to the prose, or the program learns to say it.
