---
id: A32
from: [O8, O7, O3]
source: session
status: decided 2026-10-25
kind: behaviour
implemented_by: [global/CODE.md, global/RATIONALE.md]
proven_by: [unproven]
supersedes: []
---

# A32 The code-shape rules, opt-in

The rules about the shape of code live in `global/CODE.md`, beside the global rules and apart from them: a pure core with an effect shell whose functions name their effects, failures as values, proofs for writes and reads, views for what leaves, units as types, a component for a thing shown twice, and a tested gate for every structural rule. A project takes them by an `@` line in its `CLAUDE.md` or a copy, and a project with no core and no shell loads nothing. Their reasons are in `RATIONALE.md` under the same heading, with the measurements generic-app made.

## Context

The global rules are about how to work and apply to every project. generic-app's rules are about the shape of its code and would be wrong for a repository of shell scripts or documents. The analysis of 2026-10-25 put the choice to the owner, between the global file and an opt-in second file, and the owner chose the second.

## Options

- The rules in `global/CLAUDE.md` for every session. Every project would carry seven rules it cannot follow, and the rulebook budget would pay for them on every turn.
- The rules in each project's own `CLAUDE.md`, copied. Rules written once in this repository is the third objective, and a copy per project drifts.
- The docs-index rule and the lint-exception rule, which the analysis listed with these. Both hold for every project and are in the global file already, as `A29` and `A26`.

## Consequences

A project that takes the file loads it on every turn, and its words count in the project's rulebook budget. The file names `session-codeintel layers` and `session-codeintel looks` as the gates behind two of its rules, and the other five are held by the project's own types and rules. Validated when a second project takes the shape and its gates stay green.
