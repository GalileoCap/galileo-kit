---
id: A40
from: [O3, O4]
source: owner
status: decided 2026-10-25
kind: behaviour
implemented_by: [plugins/session-kit/intent/session_intent.py, global/goals-objectives-actions.md, global/CLAUDE.md]
proven_by: [plugins/session-kit/intent/test_session_intent.py]
supersedes: []
---

# A40 The intent levels in the settings

`session-intent` reads the project's levels from `intent` in `.claude/claude-kit.json`: the `directory` (`docs/intent`) and the `levels`, each with its letter, word, the letters it hangs from, its statuses, the status that waits on the owner with what the owner does to it, its required fields, whether the Intent block lists it, its place in the index (a root section, nested under its parent, or a section of its own) and the status at which a child must name it. The four levels of the process are the default, and every verb reads the ladder: `next` accepts the levels there, the index renders root levels as sections with their children nested, the check holds each entry to its level's statuses, parents and fields, and `names` orders by the ladder.

## Context

The owner asked on 2026-10-25 that things like the id allocator be made generic through the settings file, since the first project keeps its own kinds of entry and a ladder hardcoded in the tool is the kit's alone. A tool useful to every project reaches each through the marketplace (`O4`), and each project owns its copy of the process (`O3`).

## Options

- The letters alone in the settings, the index and the check keeping the four kinds. The owner chose every field of a level: a project whose kinds differ needs the check to know their statuses and their parents, or the gate holds nothing of theirs.
- Who writes each level, as a setting the check reads against the entry's `source`. The record uses `owner`, `session` and `inferred` without a rule per level, so the process document keeps who writes what and the setting was left out.

## Consequences

The kit's own record reads under the default ladder as before, and its index gains nothing but the objectives before the actions in the queue. The other hardcoded conventions stay where they are: the handoff's name is a rule of its own, and the documents and suppressions index paths were settings already. Undone if no project sets levels, which would mean the default was the only ladder after all.
