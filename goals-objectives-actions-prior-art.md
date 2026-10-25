# The ladder against prior art

What `goals-objectives-actions.md` shares with six established ideas, what it borrows from each, and what it leaves. Written 2026-10-24 at the owner's request, for the owner to confirm. It moves into `session-kit` beside the process and is read on demand, the way `RATIONALE.md` is. The examples in it (`O1`, `O6`, `O10` and the rest) are entries of `session-kit`'s own ladder, in `session-kit-port.md`, and stand for any project's.

## In one paragraph

The ladder is a light form of two things that already exist: impact mapping's chain from a goal down to deliverables, and the architecture decision record kept for each deliverable. What none of the six have is the part the owner wrote first: who may write each level and who approves it, between one person and an agent that works alone most of the time. That part stays as it is. The rest of this document is what the six add to the levels themselves. The revision of the process document takes the parts marked *borrowed*.

## OKRs

Objectives and Key Results (Grove at Intel, Doerr's *Measure What Matters*, 2018). An Objective is qualitative and directional, set for a period. Each has three to five Key Results, outcomes with a number, scored at the end of the period. The work done to move them is called initiatives and is kept apart from the results, since the known failure mode is a key result that is a task list.

Where it meets the ladder: the OKR Objective is the ladder's goal, and initiatives are its actions. The ladder's objective sits where a key result sits, and lacks what makes a key result useful: a way to tell whether it was met. "Lose nothing at a context boundary" has one. After a compaction the session takes its next step without reopening a settled decision. "Simple tasks are not slowed down" has one. A one-off task costs the same turns with the kit as without it.

*Borrowed*: each objective carries the observation that would show it met or missed. Left: the period, the score and the stretch target. The owner's goals move with the owner's needs, and grading them is attention spent on the process instead of the work (`O3`, `O5`). Also left: the names. The OKR "Objective" is the ladder's goal, which will confuse a reader who knows OKRs. See "Names" at the end.

## ADRs and requirements traceability

An architecture decision record (Nygard, 2011) has a title, a status (proposed, accepted, deprecated, superseded), the context that made a decision necessary, the decision, and its consequences. A record is never edited once accepted. A changed decision is a new record that supersedes the old, so the log keeps every state the system was in. MADR adds the options that were considered, with what spoke for and against each.

Requirements traceability (systems engineering, DO-178C) keeps links in both directions between a need, the requirement derived from it, the design that meets it, the code and the test. Backward, every artifact traces to a requirement, which catches work nobody asked for. Forward, every requirement reaches code and a test, which catches a requirement nobody met. The same field separates verification, the product does what its specification says, from validation, the specification was the right one (Boehm: building the product right against building the right product).

Where it meets the ladder: an action is an ADR, and `RATIONALE.md` is already its context and consequences in prose. The ladder's statuses map onto the ADR's. The verification section is backward traceability and nothing else. The owner's "validated by me" and "verified against the goals and objectives" is the V&V split, used the way the field uses it.

*Borrowed*, three things:

- An action records its context (what made the decision necessary), its consequences (what it costs or forecloses, and what result would undo it) and, where there were several options, the options with the objective each served best. The chain A/B/C section of the port document is this already.
- A validated action is superseded instead of rewritten: a new id that names the one it replaces. Goals and objectives are the owner's and may be rewritten in place with the change dated, since what matters there is the current text.
- Forward traceability: every approved objective has at least one action or says "no action yet". Every action names what implements it (a file, a rule, a step of a plan) and what proves it (a test, a run, or "unproven").

*Borrowed* too, on the owner's correction: a file per record. The first draft kept one table per level, which reads in a minute while a project has ten entries and fails at a hundred, where actions, the dominant kind, carry stale paths and nobody re-reads the table. The ADR tools (adr-tools, log4brains) settled the same problem the same way: one numbered file per decision, a header a tool can read, and an index the tool generates. Left: the traceability matrix as a maintained artifact. It is the downward view, and the index derives it from the upward links.

## Impact Mapping

Impact mapping (Adzic, 2012) draws a goal (why), the actors who can move it or block it (who), the change in each actor's behaviour that would move it (how), and only then the deliverables (what). Every path through the map is a hypothesis: this deliverable will change this actor's behaviour and so move the goal. The map is for choosing the cheapest path and stopping when the goal is met, instead of building every leaf.

Where it meets the ladder: the why is the goal, the what is the action. The ladder's objectives sit at how and say nothing about who. Here the actors are few and distinct: the agent, the owner, the work (for `session-kit`, the engine it runs in), and a third party's code. `O1` and `O2` change the agent's behaviour. `O3` changes the owner's, whose attention goes elsewhere. `O6` changes the engine's, which refuses what prose failed to stop. The port's open question on mod ordering is an actor who can hinder: a third-party mod that approves what the guard denies.

*Borrowed*: an objective names whose behaviour it changes. An action is written as the hypothesis it is ("the warning makes the agent ask to compact at a boundary"), with the objective's observation as its test. Where two actions could serve an objective, the cheaper goes first and the second waits on the first's result. Left: the map as a drawing, and actors as a level of their own. A field on the objective carries it.

## Goal-Question-Metric

GQM (Basili and Rombach, 1988) defines measurement top-down. A goal is stated for an object, a purpose, a quality focus and a viewpoint. Questions are what would characterize the object against the goal. Metrics answer each question. It is read bottom-up: a metric means nothing except as the answer to its question, and a question nothing except under its goal. The warning that produced it is repeated by every metrics programme since: numbers collected with no question are never used.

Where it meets the ladder: `RATIONALE.md` is already full of answers to unwritten questions. "One session reached 70% of its window after seven warnings inside a single turn" answers "how far past a warning does a session go before it asks to compact?", and the rule under it was written from that answer. The kit has the transcript and the session id, so most questions about sessions are cheap to answer.

*Borrowed*: the question. It is the same slot as OKR's key result and the fitness function below, and the cheapest of the three forms. A question can be written at approval time with nothing built, and a number or a check comes later where one is cheap. Left: the goal template. Its parts make a goal a paragraph, and the owner's goals are meant to stay a sentence.

## Information hiding and ports-and-adapters

Parnas (1972) decomposes a system around the decisions likely to change, and each module hides one. Cockburn's hexagonal architecture (2005) has the core define the interfaces it needs (ports) and lets each technology supply an implementation of each (adapters). Dependencies point inward, and the core never names an adapter.

Where it meets the ladder: these are about the kit's design, and the port to a mod is their worked case. The objectives are the core. The decisions that have changed or will: how the engine reports context size (parsing the transcript against `$.session.usage()`), how a tool call is intercepted (`PreToolUse` JSON against `tool.call`), how a warning reaches the model (`systemMessage` against a tool result's `context` or a band), where state lives (a file under the tempdir against `$.state`), and the window size (a constant against the engine's number). Each is an adapter. `context_pressure.py` welds three of them together, so its 1M constant made it silent on a 200k model. The port's pick of one hooks module per concern is a split by port, and this is its argument.

The direction of dependency is also the ladder's rule in another vocabulary. A goal written to fit an action is the core importing the adapter.

*Borrowed*: an action that is a mechanism names the decision it hides, so the port can swap it and leave the objective-facing behaviour alone, and so a reader knows what a change in the engine's API touches. Left: the vocabulary itself in the process document, since "port" already means something else in this project.

## Fitness functions

*Building Evolutionary Architectures* (Ford, Parsons, Kua, 2017) names a fitness function: any mechanism that gives an objective reading of one characteristic of the architecture, so that the system can change without that characteristic eroding. They test one piece or the system, run on a trigger or all the time, read the code or the running system, and run by hand or by machine. Some are temporal and fire on a date or an event instead of on a change. The book's advice is to write them before building, keep few, and review them, since a system with many loses the signal in the noise.

Where it meets the ladder: the guard, the tells hook, `doc_length.py` and the refused rules are fitness functions on a session's work, each the mechanical form of a rule whose prose failed (`O6`). The ladder's own verification (re-read the actions against their objectives when a piece changes) is a manual, triggered one, and part of it can be automated: ids resolve, every action names an objective, every objective a goal, every approved objective an action or "no action yet", no status without a date.

*Borrowed*: an action is one of two kinds, a behaviour (something the work does, or a rule it follows) or a check (a test, a gate or a hook that fails when the behaviour slips). Checks are where a rule's prose has failed, and they stay few. A temporal re-read joins the verification list: when the engine's API changes, the actions that name a part of it are re-read. A check on the record itself is proposed as an action. Left: the taxonomy beyond those two kinds.

## Also considered

- Quality attribute scenarios and trade-off points (ATAM, SEI). A requirement such as `O10`, "the kit is never the reason a session fails", does not come from a goal the way `O1` does. It bounds every action. The field calls it a constraint or a quality attribute and writes it as a scenario: stimulus, environment, response, measure. The ladder gets a constraint entry (`C1`) for these, with the scenario as its text. A trade-off point is where two pull against each other. The guard failing open is one (`O6` against `C1`), and the action records which won.
- Questions, Options, Criteria (MacLean et al., 1991). The shape of the port's chain section: a question, the options, and the criteria that decide, where the criteria are the objectives. The options field borrowed from MADR takes this shape.
- Cynefin (Snowden). The "where the process does not apply" section is a domain test: a task whose right action is known on sight is done without deliberation. The two signs stay, and this is their reason.
- Hypothesis-driven development. Covered by impact mapping's hypothesis form. Its one addition is the kill criterion, the result that would make the action be undone. The consequences field holds it.

## What it adds up to

One slot was missing at every level, and the six fill it from different sides: how anyone would know. OKR puts a number there, GQM a question, fitness functions a check, impact mapping a changed behaviour, traceability a test. The revision takes the cheapest form at each point and lets it harden: a question at approval, a number or a check when one is cheap, a behaviour named so the question has a subject.

The second addition is memory. ADRs keep every state, and the ladder only kept the current one. Superseding actions instead of rewriting them costs one id per change.

The third is the kit's own split, `CLAUDE.md` loaded and `RATIONALE.md` on demand, applied inside each project. The active goals, objectives and constraints, one line each, sit in the project's `CLAUDE.md`, since a session decides against them. The record with its questions, consequences and options is the project's `ladder/` directory, read on demand when a session proposes or re-reads an action. Nothing is shared between projects. The first draft had a global file of shared goals, and the owner struck it: the same words mean different things in different work, so a project copies an entry it needs and owns the copy.

What is left of the cost: each objective gains two short fields and each action four. They are a clause each, may say "not yet known", and are required at approval and validation. A proposal carries only the id, the text and what it comes from. That keeps `O5` whole, since a task that never reaches the ladder writes none of them.

## Names

The owner's words are goal, objective, action. OKR uses "objective" for the top level and the field uses "decision" for the bottom one, so a reader who knows them will misread the middle. Two options:

- Keep the names and carry the mapping in the process document, one line.
- Rename to goal, outcome, decision. "Outcome" says what the borrowed fields ask of the middle level, a changed behaviour anyone could observe. "Decision" brings the ADR literature in by name, and the handoff's "Decisions since" already uses the word for a session's actions. The cost is that `O4` ("manage the process") is not an outcome as written and would be reworded, to something like "the process is followed in every project".

The session's pick is the rename. The owner decides.
