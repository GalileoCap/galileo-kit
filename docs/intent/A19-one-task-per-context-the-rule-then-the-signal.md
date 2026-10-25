---
id: A19
from: [O11]
source: session
status: decided 2026-10-24
kind: behaviour
implemented_by: [global/CLAUDE.md, global/RATIONALE.md, plugins/session-kit/hooks/context.tsx, plugins/session-kit/types/index.d.ts]
proven_by: [plugins/session-kit/hooks/new_task.test.tsx]
supersedes: []
---

# A19 One task per context: the rule now, the signal with the port

A rule in `global/CLAUDE.md` that a prompt unrelated to the task this context holds is named as such before anything starts on it, and, with the `chain` option on, a registered `new_task` tool: the model calls it with the task in one line and ends the turn, and the band offers the handoff and a clear, or to keep going here. Either press sends the person's own prompt again, kept by a `prompt.submit` hook, so naming the new task costs them no resend.

## Context

Nothing served `O11`. The only path was the owner running the handoff and `/clear` by hand. A cold cache makes the case stronger: clearing then avoids paying the cache write on a context about to be abandoned.

## Options

- 1. The rule alone. Costs nothing, and is prose, the kind of rule `O5` exists because prose fails to hold. Taken as the interim.
- 2. The model signals through a tool, the mod offers the clear. Taken as the port's form, with `A17`'s tool beside it.
- 3. The mod judges every prompt above a context size with one small model call that compares it to the handoff's task, drops it once on "unrelated" and offers the clear. Rejected: a model call per prompt, and a false "unrelated" costs the owner a resend.

## Shape as built (2026-10-25, session-kit 0.9.0)

The rule and the tool shipped together, with the rule's reason under the same heading in `global/RATIONALE.md`. The tool rides beside `clear_point` in `context.tsx`, with its own state (`newTask`, `lastPrompt`). "Handoff and clear" runs the handoff skill, and when that turn ends runs `clear` and submits the kept prompt as the person's own words (`asUser`), from a closure, since a clear ends the session's state. "Keep going here" submits it at once. An interrupted turn drops the offer. Unverified in a real session: whether the module's timers and `$` survive a `/clear` long enough to resend, which the engine tests cannot show.

## Revised (2026-10-25, session-kit 0.21.1)

The rule measured a prompt against the task in `CLAUDE.local.md`. In gastainas the owner cleared by hand and gave a new task, the file still described the one before, and the session called `new_task` in a context that held nothing. The rule now measures against the task the context holds, and a new or just-cleared context takes the prompt as its own. The module holds it too: at each prompt it records whether the context is fresh (the engine counts no prompt of the person's and no answer of the model's), and `new_task` called there answers that there is nothing to clear and offers no band. A compacted context holds its summary's task and is not fresh. Unverified in a real session: that `$.session.turns()` starts over at a `/clear` in the desktop app.

## Consequences

Validated when a session names a change of idea before starting on it, and one press of either button lands the prompt where it should. Undone if the rule is ignored as the others were, in which case only the tool remains, or if the resend after a clear does not arrive, in which case the band stops at the clear and the person types the prompt again.
