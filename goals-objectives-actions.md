# Goals, objectives, actions

How work with agents is directed, in every project. Draft of 2026-10-24, from the owner's description in this project, revised the same day against the prior art in `goals-objectives-actions-prior-art.md`. For the owner to confirm. Once confirmed it moves into the `session-kit` repository's `global/`, beside `CLAUDE.md` and `RATIONALE.md`, and every project reads it from there.

## The levels

| Level | What it is | Who writes it | Who approves it | How it changes |
| --- | --- | --- | --- | --- |
| Goal | An abstract, high-level need of the owner's. | The owner. Every goal rests on something the owner said or answered in so many words. A session never writes one, though it may ask a question whose answer becomes one. | Nobody: it is the owner's. | It grows and changes with the owner's needs. |
| Objective | A mid-level aim derived from one or more goals: a change in how someone or something behaves, that could be seen. | The owner, or a session that infers it. | The owner approves every addition and change before it binds. Until then it is a proposal. | Retired or rewritten by the owner when a goal moves. |
| Action | A specific decision in service of one or more objectives: a rule, a hook, a piece of a tool, a design choice, a step of a plan. It is a hypothesis that the objective moves once it is in place. | A session, on its own, or the owner. | The owner validates it, after the fact. | It can miss the mark. It is verified against its objectives and their goals, and superseded when it does. |
| Constraint | A bound on every action, stated as a scenario: when this happens, the kit responds so. It comes from the owner and from no goal in particular. | The owner. | Nobody. | Rewritten or retired by the owner. |

The direction of justification is fixed. An action names the objectives it serves, and an objective names the goals it comes from. An action that names no objective, or an objective that names no goal, is a sign that one of the three is missing or wrong. The direction never reverses: a goal is never written to fit an action already taken, and an objective is never reworded to admit one.

## The record

Every entry carries an id (`G1`, `O3`, `A12`, `C1`), its text in one or two sentences, what it comes from, its source, and its status with a date. A proposal carries only those. The other fields are filled when an objective is approved or an action validated, and a clause each is enough. A field may say "not yet known".

| Level | Fields | Source | Status |
| --- | --- | --- | --- |
| Goal | The text, in the owner's words, with the date. | The owner. | `stated`, or `retired`. |
| Objective | *From*: its goals. *Changes*: whose behaviour (the agent, the owner, the engine, a tool). *Known by*: the observation that would show it met or missed, as a question, a number or a check, whichever is cheapest. | `owner` (said in so many words) or `inferred` (by a session, from what). | `proposed`, `approved`, `retired`. |
| Action | *From*: its objectives. *Kind*: a behaviour (the kit does something) or a check (the kit tests something and warns or refuses). *Context*: what made the decision necessary. *Options*: when more than one was considered, each with the objective it served best. *Consequences*: what it costs or forecloses, and what result would undo it. *Implemented by*: a file, a rule, a step of a plan. *Proven by*: a test, a run, or `unproven`. | `owner` or `session`. | `decided`, `validated`, `retired`, each with the date. A retired action names what superseded it, or why nothing did. |
| Constraint | The scenario: what happens, where, and how the kit responds. | The owner. | `stated`, or `retired`. |

An id is never reused. A goal, an objective or a constraint may be rewritten in place while the id stays, with the change dated. A validated action is never rewritten: the change is a new action that names the one it supersedes, and the old one is retired. So the record keeps every state the kit was in.

## Verification

- When an action is proposed, the session names the objectives it serves and checks that each traces to a stated goal. An action with no trace is not taken. The gap is put to the owner as a question.
- When an objective is approved, it has at least one action or says "no action yet". When an action is decided it names what implements it, and when it is validated, what proved it.
- When an action misfires (it costs more than expected, fires at the wrong moment, or is worked around), the error is fixed at the level that holds it. An action wrong for a right objective is superseded by the session. An objective that produces wrong actions is put to the owner. The consequences field names the result that undoes the action, so the undoing is argued once, when it is decided.
- When a piece is changed or released, the actions it carries are re-read against their objectives. A piece whose objective was retired goes with it. The actions that name a part of the engine's API are re-read when that API changes.
- A check on the record itself (proposed, a session's action): a script that reads the record and reports a missing trace, an approved objective with no action, a status with no date, or an id reused. Where it runs is for the port.

## Where the process does not apply

Some tasks need no ladder, and are made worse by one. The process is for what is kept: a rule, a hook or a piece of a tool, a plan of several phases, a decision a later session relies on. A question, a read, a single edit, a quick script, a one-off fix is done, with no entry written.

The session decides which a task is, by two signs: the result outlives the session, or it adds to, changes or contradicts an existing entry. When unsure, do the task. If its result turns out to be kept, write the entry then. The fields above are written only for what is kept, so a task that never reaches the ladder writes none of them.

## Where the entries live

- Loaded into every session: the goals, objectives and constraints shared by every project, one line each, in a file in `session-kit`'s `global/` loaded the way `global/CLAUDE.md` is. A session decides against these, so it needs them in front of it. (Proposed.)
- Read on demand: the record with its fields, beside that file, consulted when an action is proposed, validated or re-read. (Proposed. The split is the kit's own, `CLAUDE.md` loaded and `RATIONALE.md` on demand.)
- A project's own goals, objectives and constraints: in the project's `CLAUDE.md`, or a file it names. They add to the global ones and never contradict them.
- Actions: the rules in `global/CLAUDE.md` are actions, and `RATIONALE.md` already holds their context and consequences in prose. Over time each rule names its objective by id and `RATIONALE.md`'s paragraphs become the actions' records. (Proposed.)
- A session's own actions, as it takes them: the `Decisions since` section of `CLAUDE.local.md`, which the handoff already keeps. Each entry there names the objective it serves.

## Worked example: this project

The owner's goal for every project is consistent and good work with agents (`G3` in `session-kit-port.md`). This project is one of its objectives in action. The entries are written with the fields above, as far as they are known today.

- `O-mods-1` Only code that has been read runs inside my sessions. From `G3`. Changes: what the engine loads. Known by: no plugin or mod is enabled on this machine without a review file. Inferred from the research ask ("review them for malicious/inefficient code"). Proposed.
- `O-mods-2` What runs in my sessions changes only when I choose. From `G3`. Changes: the engine's update path. Known by: no installed plugin moves to a version nobody read. Inferred from "do plugins get auto-updated from under me?". Proposed.
- `A-mods-1` A candidate is reviewed from a clone at a recorded commit and never loaded before its review is written. From `O-mods-1`. Kind: behaviour, held by the project's rules. Context: a plugin runs code at load, so the review has to come first. Consequences: a review costs a session before any candidate is tried. Implemented by: the rules of engagement in `CLAUDE.md`. Proven by: `reviews/cache-tax.md` was written from a clone that was never loaded. Session, decided 2026-10-24.
- `A-mods-2` A fork lives in `galileo-kit` with a pinned version, by default as a separate plugin. From `O-mods-2`. Kind: behaviour. Options: install as is (serves nothing when the source moves), fork into `session-kit` itself (serves `O-mods-2`, and couples unrelated code), fork beside it (serves `O-mods-2`). Consequences: every upstream fix is merged by hand. Undone if the merges cost more than the reviews they save. Implemented by: the rules of engagement in `CLAUDE.md`. Proven by: unproven, no fork made yet. Session, decided 2026-10-24, awaiting validation.
- `A-mods-3` `session-kit` is ported first, documented through this ladder, and mods are weighed against it after. From `O-mods-1`, `O-mods-2` and `O4`. Kind: behaviour, a step of the plan. Context: a mod we fork may duplicate what the port gives. Consequences: `cache-tax` waits. Implemented by: `PLAN.md`. Owner, decided 2026-10-24.

## Open questions for the owner

1. Is the split right: goals stated only, objectives approved, actions validated? Anything the owner wants to keep for themself at the action level (money, publishing, deletion are already refused by rule)?
2. The loaded and on-demand split above: is it the answer to where the shared file lives?
3. Do the two signs for "needs the ladder" match what the owner has in mind for one-off tasks?
4. The borrowed fields, changes and known by on an objective, and kind, context, options, consequences, implemented by and proven by on an action: approve the set, or cut some. They are all the revision costs.
5. The names: keep goal, objective, action, or rename to goal, outcome, decision. The case is at the end of the prior-art document.
6. Constraints as a fourth kind of entry, with `O10` as the first.
