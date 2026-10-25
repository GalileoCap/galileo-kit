---
id: A42
from: [O5, O13]
source: owner
status: decided 2026-10-25
kind: behaviour
implemented_by: [global/CLAUDE.md]
proven_by: [unproven]
supersedes: []
---

# A42 A mechanical unrelated failure is fixed

A failure the change did not cause is fixed in its own commit when the fix is mechanical, changes no behaviour and needs no decision (a format, a lint finding, a stale generated file, a missing index line, a failing test whose fix is of that kind), and the reply names it. One that would change behaviour or needs a choice is reported in one line with a proposed next step, and never called flaky.

## Context

The rule read "a failure that is not yours is never fixed without a word", and the owner found sessions reading every failure as not theirs, so the mechanical ones accumulated with nobody to fix them. On 2026-10-25 they asked that a session take on the mechanical ones, with the owner still told. Every step moves to a program or an agent where one can do it (`O5`), and a one-off fix is not slowed by a report and a wait (`O13`).

## Options

- Formatting and lint findings alone as the mechanical kind. The owner widened it to a failing test when its fix changes no behaviour and needs no decision.

## Consequences

A session fixes more and reports less, and a commit of its own keeps each fix reviewable. Undone if the fixes start carrying behaviour changes, which would mean the line needs a check and not a sentence.
