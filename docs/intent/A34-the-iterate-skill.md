---
id: A34
from: [O13, O8]
source: session
status: decided 2026-10-25
kind: behaviour
implemented_by: [plugins/session-kit/skills/iterate/SKILL.md, plugins/session-kit/skills/handoff/template.md, global/CLAUDE.md]
proven_by: [unproven]
supersedes: []
---

# A34 The iterate skill

`/session-kit:iterate` is the fast-working mode for while the owner iterates on a change. The session runs the project's static legs after each change, named under `iterate.static` in `.claude/claude-kit.json`, and no test runner. It commits as it goes, ends every report with *static checks green, tests not run (iterating)*, and keeps the mode as the `Mode:` line of `CLAUDE.local.md` so a compaction does not lose it. The owner turns it on and off, and it ends on its own the moment work is handed back, when the tests run once and what is red is fixed in its own commit.

## Context

The first project wrote the skill after the owner iterated on screens with a lane that ran every test after each change, and the 2026-10-25 reading named it the eighth tool to lift, since the owner iterates on screens in every project. The global rules say never deliver red and done means it was run, and the skill is how a session meets them at the end of an iteration instead of at every step of it.

## Options

- A plugin option or a tool instead of a skill, with the test log refusing test runs while the mode is on. The mode is a way of working that the owner turns on in words, and a skill is the shape the kit has for that. A hook that holds the test runners back waits for a second project to ask for it.
- The static legs guessed from the project's test commands. A gate that runs no test is a fact about the project, so the project names them, and a project that names none is asked once.

## Consequences

A project that takes the skill names its static legs, and the kit names its own. The handoff template carries the `Mode:` line, empty outside the mode. Validated when the owner has iterated through a compaction and the session kept the mode and ran the tests at the end. Undone if sessions end the mode late, after work was handed back red, which would mean the hook was needed after all.
