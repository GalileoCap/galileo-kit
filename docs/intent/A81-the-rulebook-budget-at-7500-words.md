---
id: A81
from: [O8, O9]
source: owner
status: decided 2026-10-29
kind: check
implemented_by: [plugins/session-kit/rulebook/session_rulebook.py, plugins/session-kit/bin/session-rulebook, .claude/claude-kit.json, global/CLAUDE.md]
proven_by: [plugins/session-kit/rulebook/test_session_rulebook.py]
supersedes: [A28]
---

# A81 The rulebook budget at 7,500 words

`session-rulebook` counts the words of what every turn loads (the user's `~/.claude/CLAUDE.md` and the project's `CLAUDE.md`, each with the files its `@path` lines import, the files under `.claude/rules/`, and `CLAUDE.local.md`) and, apart, of the skills, prints each file's count and the two totals against their budgets, and fails when one is over. The budgets are 7,500 and 16,000 words until a project sets its own under `rulebook` in `.claude/claude-kit.json`, where `skills_from` names further skill files. A rule that takes the rulebook over its budget removes another.

The owner's words, 2026-10-29: "increase the (default) limit to 7500 words", after asking what the budget comes to in tokens.

## Context

`A28` set the rules budget at 5,000 words as a starting figure, unmeasured against instruction following. At 1.93 tokens a word, as the engine counted `global/CLAUDE.md`, 5,000 words is about 9,650 tokens and 7,500 about 14,500. The global rules take 1,432 words before a project writes any, and tagents/desk and tagents/lane1 had already run over 5,000 (`A77`).

## Options

- Keep 5,000 and let a project that needs more set its own under `rulebook`: the budget stays a pressure on every project, and each override is a decision written in its config.
- Raise the default (taken, the owner's): every project gets the room without a setting of its own.

## Consequences

`A28` read a budget raised each time it is reached as a budget that has stopped holding the rulebook's size. This raise is the first. Undone if a project's rules grow toward the new figure and instruction following is seen to slip, or if a second raise is asked for, which would put the budget itself in question.
