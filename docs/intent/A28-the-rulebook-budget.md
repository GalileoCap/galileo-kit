---
id: A28
from: [O8, O9]
source: session
status: decided 2026-10-25
kind: check
implemented_by: [plugins/session-kit/rulebook/session_rulebook.py, plugins/session-kit/bin/session-rulebook, .claude/claude-kit.json, global/CLAUDE.md]
proven_by: [plugins/session-kit/rulebook/test_session_rulebook.py]
supersedes: []
---

# A28 The rulebook budget

`session-rulebook` counts the words of what every turn loads (the user's `~/.claude/CLAUDE.md` and the project's `CLAUDE.md`, each with the files its `@path` lines import, the files under `.claude/rules/`, and `CLAUDE.local.md`) and, apart, of the skills, prints each file's count and the two totals against their budgets, and fails when one is over. The budgets are 5,000 and 16,000 words until a project sets its own under `rulebook` in `.claude/claude-kit.json`, where `skills_from` names further skill files, as the kit names its plugin's. A rule that takes the rulebook over its budget removes another.

## Context

Instruction following degrades as instructions stack, and the first project's rulebook had grown to about 26,800 tokens read on every turn before it was split and put under a budget. The kit's own global file has had no budget since it was cut from that rulebook, and the kit adds a rule with every tool it builds. The 2026-10-25 reading of the two projects named the budget as the fourth tool to lift. The kit stands at 4,290 words of rules a turn, 1,535 of them the handoff.

## Options

- Words or tokens. Tokens are the cost in the goal's terms, but a count needs a tokenizer the kit would have to ship or call. Words are counted by the standard library, and the two move together.
- One budget over everything, or two. A skill is loaded when its work starts and a rule on every turn, so the two groups cost differently and are budgeted apart, as the first project did.
- The handoff in the rules group or out. It is loaded every turn, so it is counted, and the count shows the owner what the handoff costs beside the rules.
- A hook that warns when an edit to a rulebook file takes it over. Left for a second use: the check runs with the gates, where the first project ran its.

## Consequences

The defaults are starting figures, set so the kit passes with room, and unmeasured against instruction following. A project with a long handoff fails the check before its rules do, which is the handoff's own rule seen from the other side. Undone if the budgets are raised every time they are reached, which would mean a budget is not what holds a rulebook's size.
