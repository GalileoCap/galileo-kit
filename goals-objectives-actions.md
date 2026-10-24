# Goals, objectives, actions

How work with agents is directed, in every project. Draft of 2026-10-24, from the owner's description in this project, for the owner to confirm. Once confirmed it moves into the `session-kit` repository's `global/`, beside `CLAUDE.md` and `RATIONALE.md`, and every project reads it from there.

## The three levels

| Level | What it is | Who writes it | Who approves it | How it changes |
| --- | --- | --- | --- | --- |
| Goal | An abstract, high-level need of the owner's. | The owner. Every goal rests on something the owner said or answered in so many words. A session never writes one, though it may ask a question whose answer becomes one. | Nobody: it is the owner's. | It grows and changes with the owner's needs. |
| Objective | A mid-level aim derived from one or more goals. | The owner, or a session that infers it. | The owner approves every addition and change before it binds. Until then it is a proposal. | Retired or rewritten by the owner when a goal moves. |
| Action | A specific decision in service of one or more objectives: a rule, a hook, a piece of a tool, a design choice, a step of a plan. | A session, on its own, or the owner. | The owner validates it, after the fact. | It can miss the mark. It is verified against its objectives and their goals, and changed or undone when it does. |

The direction of justification is fixed. An action names the objectives it serves, and an objective names the goals it comes from. An action that names no objective, or an objective that names no goal, is a sign that one of the three is missing or wrong.

## The record

Every entry carries an id (`G1`, `O3`, `A12`), its text in one or two sentences, what it comes from (goals for an objective, objectives for an action), its source, and its status.

| Level | Source | Status |
| --- | --- | --- |
| Goal | The owner's words, with the date. | `stated`, or `retired`. |
| Objective | `owner` (said in so many words) or `inferred` (by a session, from what). | `proposed`, `approved`, `retired`. |
| Action | `owner` or `session`. | `decided`, `validated`, `retired`, each with the date. A retired action names what replaced it, or why nothing did. |

An id is never reused. The text may be rewritten while the id stays, with the change dated.

## Verification

- When an action is proposed, the session names the objectives it serves and checks that each traces to a stated goal. An action with no trace is not taken. The gap is put to the owner as a question.
- When an action misfires (it costs more than expected, fires at the wrong moment, or is worked around), the error is fixed at the level that holds it. An action wrong for a right objective is changed by the session. An objective that produces wrong actions is put to the owner.
- When a piece is changed or released, the actions it carries are re-read against their objectives. A piece whose objective was retired goes with it.

## Where the process does not apply

Some tasks need no ladder, and are made worse by one. The process is for what is kept: a rule, a hook or a piece of a tool, a plan of several phases, a decision a later session relies on. A question, a read, a single edit, a quick script, a one-off fix is done, with no entry written.

The session decides which a task is, by two signs: the result outlives the session, or it adds to, changes or contradicts an existing entry. When unsure, do the task. If its result turns out to be kept, write the entry then.

## Where the entries live

- Goals and objectives shared by every project: one file in `session-kit`'s `global/`, loaded the way `global/CLAUDE.md` is. (Proposed. Whether it is loaded into every session or read on demand like `RATIONALE.md` is for the owner: loading costs tokens in every session, reading on demand risks a session that never reads it.)
- A project's own goals and objectives: in the project's `CLAUDE.md`, or a file it names. They add to the global ones and never contradict them.
- Actions: the rules in `global/CLAUDE.md` are actions, and `RATIONALE.md` already holds their trace to the reasons behind them. The reasons there are objectives in prose form. Over time each rule names its objective by id and `RATIONALE.md` becomes the objectives' record. (Proposed.)
- A session's own actions, as it takes them: the `Decisions since` section of `CLAUDE.local.md`, which the handoff already keeps. Each entry there names the objective it serves.

## Worked example: this project

The owner's goal for every project is consistent and good work with agents (`G3` in `session-kit-port.md`). This project is one of its objectives in action.

| Id | Entry | From | Source | Status |
| --- | --- | --- | --- | --- |
| O-mods-1 | Only code that has been read runs inside my sessions. | G3 | inferred, from the research ask ("review them for malicious/inefficient code") | proposed |
| O-mods-2 | What runs in my sessions changes only when I choose. | G3 | inferred, from "do plugins get auto-updated from under me?" | proposed |
| A-mods-1 | A candidate is reviewed from a clone at a recorded commit and never loaded before its review is written. | O-mods-1 | session | decided 2026-10-24 |
| A-mods-2 | A fork lives in `galileo-kit` with a pinned version, by default as a separate plugin. | O-mods-2 | session | decided 2026-10-24, awaiting validation |
| A-mods-3 | `session-kit` is ported first, documented through this ladder, and mods are weighed against it after. | O-mods-1, O-mods-2, and `O4` | owner | decided 2026-10-24 |

## Open questions for the owner

1. Is the split right: goals stated only, objectives approved, actions validated? Anything the owner wants to keep for themself at the action level (money, publishing, deletion are already refused by rule)?
2. Is the shared file loaded into every session, or read on demand?
3. Do the two signs for "needs the ladder" match what the owner has in mind for one-off tasks?
