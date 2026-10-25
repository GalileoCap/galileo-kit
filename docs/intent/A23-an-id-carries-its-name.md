---
id: A23
from: [O18]
source: session
status: decided 2026-10-25
kind: behaviour
implemented_by: [global/CLAUDE.md, global/RATIONALE.md, plugins/session-kit/intent/session_intent.py, plugins/session-kit/skills/handoff/SKILL.md]
proven_by: [plugins/session-kit/intent/test_session_intent.py]
supersedes: []
---

# A23 An id carries its name

A rule in the global rules: an id of any kind the project uses, an intent entry, an issue, a ticket, a planned chunk of work, is written with its name, `A20`, one module per concern, in every reply and in every document the owner decides from, and never as the id alone. `session-intent names` prints the name of every entry, or of the ids given, so a session that has lost the names to a compaction gets them back in one call.

## Context

The owner said on 2026-10-25 that the ids had stopped meaning anything: the record grew to five goals, eighteen objectives, a constraint and twenty-three actions in two days, and a reply that asked "Approve O14?" could not be acted on. The names live in `docs/intent/`, and after a compaction a session has the ids in its summary and the names nowhere in its context, which is where the bare ids come from.

## Options

- A rule alone. Serves the objective only while the session has the names at hand, which it does not after a compaction.
- The rule with a command that prints the names. The command makes the rule cheap to keep: one call, a few hundred tokens. Chosen.
- A mod that draws the name beside each id. Serves the objective without the model's cooperation, and only on the screen. The documents still need the rule. Decided beside this one as `A24`, the reference mod.

## Consequences

Replies grow by a few words per reference. A name repeated at every mention would be noise, so the rule asks for it at the first mention in a reply or a section. Undone if the owner finds the names as hard to track as the ids, which would mean the entries are too many or too alike.
