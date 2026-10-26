---
id: A65
from: [O11, O15]
source: owner
status: decided 2026-10-26
kind: behaviour
implemented_by: [plugins/session-kit/hooks/context.tsx, plugins/session-kit/types/index.d.ts, plugins/session-kit/.claude-plugin/plugin.json, docs/what-reaches-the-model.md]
proven_by: [plugins/session-kit/hooks/new_task.test.tsx]
supersedes: []
---

# A65 An effort for the new task carried by the offer

The `new_task` tool takes an optional `effort` (`low`, `medium`, `high`, `xhigh` or `max`) with `effort_reason`, the effort the model judges the new task needs. The kit keeps the proposal only when it differs from the effort the session's last main-loop request was sent at, read on `turn.step`. The band's offer then ends "Proposed effort <level>: <reason>" and gains a primary button, "Handoff, clear, effort <level>". On that press the kit writes the handoff, clears, runs `/effort <level>` and then sends the person's prompt again. "Handoff and clear" keeps the session's effort, and "Keep going here" never changes it. An effort that is not a level is refused. An `/effort` that fails is named in a toast, and the prompt is still sent, at the session's effort.

## Context

The owner, on 2026-10-25 from effortless, asked whether a session should get a tool to change its own effort before a new task. The session's answer in `PLAN.md` was no mid-task, and yes at a context boundary with the person choosing. The owner named it M27 and, on 2026-10-26, asked for it before the install. An effort change is a change to the request's top level, so mid-context it writes all the context to the cache again (the API's invalidation hierarchy, measured by effortless's author at 56 to 100% on Fable 5.1). After a clear there is nothing cached to lose. The desktop app refuses `set_session_effort` for the calling session, and the Agent tool's own `effort` field says never on the model's judgement, so the model proposes and the person decides.

## Options

- The effort set by a `turn.step` hook rewriting every main-loop request. Rejected: the engine's own effort indicator would show the session's level while the kit sent another, and a later `/effort` pick by the person would be overridden without a word.
- `/effort <level>` through `$.command.run` after the clear. Taken: the engine prints its own line in the transcript, and the indicator shows the level. Probed headless on 2.1.308 with a throwaway config directory: "Set effort level to low (this session only)", and no settings file written, so the level is not saved as the default for new sessions. The interactive path, which the desktop app runs, is the same command with arguments and is unverified until a real session.
- A default effort per task kind in `.claude/claude-kit.json`, as the analysis's answer suggested. Not built: the model's proposal covers it, and a table of kinds has no second use yet.
- The proposal offered under "Keep going here" too. Rejected: the change mid-context costs a write of all the context.
- Every proposal shown, the session's own level included. Rejected: a button that changes nothing is noise.

## Consequences

The first action under `O15` (routine work takes the cheaper path), still proposed. The model sees one more field on `new_task` and one more sentence in its description, listed in `docs/what-reaches-the-model.md`. The proposal and the press flag live in the `newTask` state, read out before the clear since the clear starts the session's named values over. The session's effort is read on every main-loop request, with a state write only when it changes. Where no band is drawn (the phone, VS Code) the offer cannot be pressed, as before.

## Proof

Three engine tests in `new_task.test.tsx` were written before the code, and two failed on 0.34.0 for want of it. The third, an effort equal to the session's offering no button of its own, passed as a negative case. Kept is the case whose failure costs money with nothing said: with the session at `high` and `low` proposed, the press runs the handoff, the clear, `/effort low` and then the prompt, across a clear that starts the state over, and "Keep going here" sends the prompt with no `/effort`. Deleted once they passed: the equal effort, and the refusal of a level that is not one with a failed `/effort` named in a toast while the prompt is still sent.
