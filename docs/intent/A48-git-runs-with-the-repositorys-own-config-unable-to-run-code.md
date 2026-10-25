---
id: A48
from: [O1]
source: session
status: decided 2026-10-25
kind: behaviour
implemented_by: [plugins/session-kit/hooks/checkout.ts]
proven_by: [plugins/session-kit/hooks/checkout.test.ts]
supersedes: []
---

# A48 Git runs with the repository's own config unable to run code

`checkout.ts` runs its `git log` and `git status` as `git -c core.fsmonitor=false ...`, so a repository whose `.git/config` names a fsmonitor command runs none at every turn end.

## Context

The turn-end line of `A25` (the checkout checks) runs two git commands in every repository a session opens. A `core.fsmonitor` set to a command in that repository's config is code the kit would run, unread, on every turn, against `O1` (only code that has been read runs). rulebook-guard runs git with the same flag. Low weight: Claude Code runs `git status` itself.

## Options

- Leave git as it is. Rejected: the flag costs nothing.
- The flag on both calls. Taken.
- A port that allows two git argv shapes (M21 of `docs/analyses/mods-for-the-kit.md`). Left for the guard's mod form, step 4 of `A20` (one module per concern).

## Consequences

None seen. The test's engine reads the subcommand after the `-c` pair.

## Proof

One assertion in the turn-end test: both argv start with `git -c core.fsmonitor=false`. It failed on 0.22.0.
