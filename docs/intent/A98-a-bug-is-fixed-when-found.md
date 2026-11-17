---
id: A98
from: [O5, O13]
source: owner
status: decided 2026-11-17
kind: behaviour
implemented_by: [global/CLAUDE.md]
proven_by: [unproven]
supersedes: [A42]
---

# A98 A bug or issue is fixed the moment it is found

A bug or issue a session finds is fixed then, unless it is large or needs a design change. One the change did not cause goes in its own commit, and the reply names every fix. A large one, or one that needs a design change, is reported in one line with a proposed next step, and never called flaky.

## Context

On 2026-11-17 the owner asked for the rule in these words: "All bugs and issues should be solved the moment they are found unless they are large and/or require design changes". `A42` already let a session fix an unrelated failure, but only when the fix changed no behaviour and needed no decision, which leaves most bugs reported and waiting. Two rules would contradict each other on a small behavioural bug, so this one takes `A42`'s place and keeps its parts that still hold: the commit of its own, the reply naming the fix, and no failure called flaky. A step an agent can do moves off the owner (`O5`), and a small fix is not slowed by a report and a wait (`O13`).

## Options

- Add the rule beside `A42`. Rejected: the two disagree on a bug whose fix changes behaviour.

## Consequences

A session fixes more and asks less, and the defect regression test rule applies to each fix. Large and design-changing are judgments the session makes. The rule is undone or narrowed if fixes start landing changes the owner would have wanted to decide.
