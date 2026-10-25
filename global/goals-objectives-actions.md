# Goals, objectives, actions

How work with agents is directed, in every project of every kind: code, writing, research, a tool, a plan. Draft of 2026-10-24, from the owner's description in this project, revised against the prior art in `goals-objectives-actions-prior-art.md` and against the owner's three corrections of the same day. Confirmed the same day: it lives in the `session-kit` repository as one of its rules, beside `CLAUDE.md` and `RATIONALE.md`. The entries live in each project.

## The levels

| Level | What it is | Who writes it | Who approves it | How it changes |
| --- | --- | --- | --- | --- |
| Goal | An abstract, high-level need of the owner's. | The owner. Every goal rests on something the owner said or answered in so many words. A session never writes one, though it may ask a question whose answer becomes one. | Nobody: it is the owner's. | It grows and changes with the owner's needs. |
| Objective | A mid-level aim derived from one or more goals: a change in how someone or something behaves, that could be seen. | The owner, or a session that infers it. | The owner approves every addition and change before it binds. Until then it is a proposal. | Retired or rewritten by the owner when a goal moves. |
| Action | A specific decision in service of one or more objectives: a rule, a design choice, a piece of the work, a check on it, a step of a plan. It is a hypothesis that the objective moves once it is in place. | A session, on its own, or the owner. | The owner validates it, after the fact. | It can miss the mark. It is verified against its objectives and their goals, and superseded when it does. |
| Constraint | A bound on every action, stated as a scenario: when this happens, the work responds so. It comes from the owner and from no goal in particular. | The owner. | Nobody. | Rewritten or retired by the owner. |

The direction of justification is fixed. An action names the objectives it serves, and an objective names the goals it comes from. An action that names no objective, or an objective that names no goal, is a sign that one of the three is missing or wrong. The direction never reverses: a goal is never written to fit an action already taken, and an objective is never reworded to admit one.

## One ladder per project

Every project owns its whole ladder: its goals, objectives, constraints and actions, with its own ids. Nothing is shared between projects, because the same words mean different things in different work. "Split the code by subsystem so each can be replaced" is one objective in a command-line tool and another in a service, and an entry shared by both would have to be vague enough to mean neither.

A project may copy an entry's text from another project when it needs the same thing. The copy is that project's entry, with its own id, its own *known by* and its own actions. Its body may say where it was copied from, for provenance, and the two drift apart from then on.

What is shared is this process, which is a rule of the `session-kit` project and reaches every session the way its other rules do. `session-kit` is a project like any other, with a ladder of its own, whose actions happen to be the rules every session loads.

## The record

Each entry is one file under the project's `docs/intent/`, named by its id and a slug. The id prefix says the level (`G`, `O`, `A`, `C`). A header the tool reads holds the short fields: `id`, `from`, `source`, `status` with its date, and for an action `kind`, `implemented_by`, `proven_by` and `supersedes`. The body holds the text, then the prose fields under their own headings: *Changes* and *Known by* for an objective, *Context*, *Options* and *Consequences* for an action, *Copied from* where it applies.

```
docs/intent/
  G1-vetted-mods.md
  O1-only-read-code-runs.md
  A1-review-from-a-clone.md
  INDEX.md
```

```
---
id: A1
from: [O1]
source: session
status: decided 2026-10-24
kind: behaviour
implemented_by: [CLAUDE.md]
proven_by: [reviews/cache-tax.md]
supersedes: []
---
```

A proposal carries only the id, the text and what it comes from. The other fields are filled when an objective is approved or an action validated, and a clause each is enough. A field may say "not yet known".

| Level | Fields | Source | Status |
| --- | --- | --- | --- |
| Goal | The text, in the owner's words, with the date. | The owner. | `stated`, or `retired`. |
| Objective | *From*: its goals. *Changes*: whose behaviour (the agent, the owner, the work, a tool). *Known by*: the observation that would show it met or missed, as a question, a number or a check, whichever is cheapest. | `owner` (said in so many words) or `inferred` (by a session, from what). | `proposed`, `approved`, `retired`. |
| Action | *From*: its objectives. *Kind*: a behaviour (something the work does, or a rule it follows) or a check (a test, a gate or a hook that fails when the behaviour slips). *Context*: what made the decision necessary. *Options*: when more than one was considered, each with the objective it served best. *Consequences*: what it costs or forecloses, and what result would undo it. *Implemented by*: a file, a rule, a step of a plan. *Proven by*: a test, a run, or `unproven`. | `owner` or `session`. | `decided`, `validated`, `retired`, each with the date. A retired action names what superseded it, or why nothing did. |
| Constraint | The scenario: what happens, where, and how the work responds. | The owner. | `stated`, or `retired`. |

Links are written in one direction only, upward: an action names its objectives, an objective its goals, a successor the entry it supersedes. Everything downward is derived: an objective's actions, a goal's objectives, the entries that await the owner. `INDEX.md` holds the derived view, and a tool generates it. A hand-written copy of a derived link rots at its own rate.

An id is never reused. A new entry's id comes from `session-intent next <level>`, which claims it under a lock shared by every worktree of the clone and never gives it twice, so two sessions writing at once never pick the same one, and a claim whose file was never written still spends its number. A goal, an objective or a constraint may be rewritten in place while the id stays, with the change dated. A validated action is never rewritten: the change is a new action that names the one it supersedes, and the old one is retired. No entry is deleted. A reader who follows an old id lands on the retired file and is sent on to its successor, and a session that has the same idea again finds that it was decided.

## Verification

- When an action is proposed, the session names the objectives it serves and checks that each traces to a stated goal. An action with no trace is not taken. The gap is put to the owner as a question.
- When an objective is approved, it has at least one action or says "no action yet". When an action is decided it names what implements it, and when it is validated, what proved it.
- When an action misfires (it costs more than expected, fires at the wrong moment, or is worked around), the error is fixed at the level that holds it. An action wrong for a right objective is superseded by the session. An objective that produces wrong actions is put to the owner. The consequences field names the result that undoes the action, so the undoing is argued once, when it is decided.
- When a piece of the work is changed or released, the actions it carries are re-read against their objectives. A piece whose objective was retired goes with it. The actions that name a part of a tool's interface are re-read when that interface changes.
- The tool that generates `INDEX.md` is also the check on the record (`session-intent`, the kit's `A21`): ids resolve, every path in *implemented by* exists, every approved objective has an action, every action an objective, no status lacks a date, and every retired entry names its successor. A dangling path is how a stale entry announces itself.

## Over time

Actions dominate the count. Every rule, design choice and plan step is one, so a project reaches hundreds, and some carry information that has gone wrong or stale. The record above is built for that: one file per entry so a link is a path, upward links only so nothing is maintained twice, a generated index so the downward view is always current, and retirement instead of deletion so the trace survives.

The owner's validation is what scales worst, one action at a time. So `INDEX.md` leads with the queue: objectives proposed and actions decided but not validated, oldest first. The owner validates in batches at a clear point, a release or the end of a phase, and a session never waits on validation to continue.

## Where the process does not apply

Some tasks need no ladder, and are made worse by one. The process is for what is kept: a rule, a piece of the work, a plan of several phases, a decision a later session relies on. A question, a read, a single edit, a quick script, a one-off fix is done, with no entry written.

The session decides which a task is, by two signs: the result outlives the session, or it adds to, changes or contradicts an existing entry. When unsure, do the task. If its result turns out to be kept, write the entry then. The fields above are written only for what is kept, so a task that never reaches the ladder writes none of them.

## Where the entries live

- The project's `docs/intent/`: every entry, one file each, and the generated `INDEX.md`. Read on demand, when an action is proposed, validated or re-read.
- The project's `CLAUDE.md`: the active goals, objectives and constraints, one line each with their ids, since a session decides against them and needs them in front of it. Every rule stated there names the action it is. Retired entries never appear. The block is written by hand, and the tool checks it against the record.
- `session-kit`'s own ladder: `RATIONALE.md` splits into one file per rule, each rule in `global/CLAUDE.md` names its id, and the paragraph that is there today becomes that action's context and consequences. (Proposed.)
- A session's own actions, as it takes them: the `Decisions since` section of `CLAUDE.local.md`, which the handoff already keeps. Each entry there names the objective it serves, and becomes a file under `docs/intent/` when the result is kept.

## Worked example: the `claude-mods` project

Ids are per project, so this project's `G1` has nothing to do with `session-kit`'s `G1`. The entries are written with the fields above, as far as they are known today, and are the files under that project's `docs/intent/`.

- `G1` Vet third-party Claude Code plugins and mods before installing them, and decide for each one whether to fork it under our own control. The owner's original ask, stated 2026-10-24.
- `O1` Only code that has been read runs inside my sessions. From `G1`. Changes: what the engine loads. Known by: no plugin or mod is enabled on this machine without a review file. Inferred from "review them for malicious/inefficient code". Proposed.
- `O2` What runs in my sessions changes only when I choose. From `G1`. Changes: the engine's update path. Known by: no installed plugin moves to a version nobody read. Inferred from "do plugins get auto-updated from under me?". Proposed.
- `A1` A candidate is reviewed from a clone at a recorded commit and never loaded before its review is written. From `O1`. Kind: behaviour, a rule of the project. Context: a plugin runs code at load, so the review has to come first. Consequences: a review costs a session before any candidate is tried. Implemented by: the rules of engagement in `CLAUDE.md`. Proven by: `reviews/cache-tax.md` was written from a clone that was never loaded. Session, decided 2026-10-24.
- `A2` A fork lives in `galileo-kit` with a pinned version, by default as a separate plugin. From `O2`. Kind: behaviour. Options: install as is (serves nothing when the source moves), fork into `session-kit` itself (serves `O2`, and couples unrelated code), fork beside it (serves `O2`). Consequences: every upstream fix is merged by hand. Undone if the merges cost more than the reviews they save. Implemented by: the rules of engagement in `CLAUDE.md`. Proven by: unproven, no fork made yet. Session, decided 2026-10-24, awaiting validation.
- `A3` `session-kit` is ported first, documented through this ladder, and mods are weighed against it after. From `O1` and `O2`. Kind: behaviour, a step of the plan. Context: the owner reordered the work, since a mod we fork may duplicate what the port gives. Consequences: `cache-tax` waits. Implemented by: `PLAN.md`. Owner, decided 2026-10-24.

## Open questions for the owner

1. Is the split right: goals stated only, objectives approved, actions validated? Anything the owner wants to keep for themself at the action level (money, publishing, deletion are already refused by rule)?
2. Do the two signs for "needs the ladder" match what the owner has in mind for one-off tasks?
3. The borrowed fields, changes and known by on an objective, and kind, context, options, consequences, implemented by and proven by on an action: approve the set, or cut some. They are all the revision costs.
4. The names: keep goal, objective, action, or rename to goal, outcome, decision. The case is at the end of the prior-art document.
5. Constraints as a fourth kind of entry, with `session-kit`'s `O10` as the first.
6. The record's shape: the header fields, the generated index and the validation queue. The header format is the session's pick.
7. This project's `G1` is the original ask as `CLAUDE.md` records it. Is that the goal in the owner's words, or does the owner want to restate it?
