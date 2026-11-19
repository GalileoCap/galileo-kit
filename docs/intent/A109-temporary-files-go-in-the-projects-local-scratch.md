---
id: A109
from: [O12]
source: owner
status: decided 2026-11-19
kind: rule
implemented_by: [global/CLAUDE.md, global/RATIONALE.md, .gitignore]
proven_by: [unproven]
supersedes: []
---

# A109 Temporary files go in the project's local-scratch

A session writes its temporary and untracked files in the project's `local-scratch/`, which is gitignored, and adds the line to `.gitignore` when it is missing. Nothing goes in `/tmp`, `/private/tmp/claude*` or the engine's scratchpad. A file with a place of its own, such as build output, stays in that place. A file in `local-scratch/` is named after the session or the worktree, since sessions share a checkout.

## Context

The owner, on 2026-11-19: "Add to the global CLAUDE.md that files should never be written to temporary directories (like `/private/tmp/claude*`), instead temporary/untracked files go in a gitignored `local-scratch` directory in the project (if they don't already have a pre-defined place like build output)".

The same day a transcript snapshot made for the owner was left under a session's scratchpad, whose path carries the session's id. The rule replaces the earlier one that a temporary file is named after its writer or made with `mktemp`, and keeps its scoping.

## Options

- A gitignored directory in each project (this one): the owner and the next session find the file where the work is.
- A global git excludes file listing `local-scratch/`. Not taken now: it lives in the nix-darwin configuration, and a project's own `.gitignore` shows the directory to anyone who clones it.

## Consequences

Every project gains a `local-scratch/` line in its `.gitignore` on first use. The engine's system prompt points sessions at its scratchpad, and this rule overrides it. The kit's test-log hook (`A11`) still writes under `TMPDIR`: it is a program's file, read by the kit alone, and moving it is a separate change.

## Proof

Unproven: no program checks it. A session that writes under `/tmp` or the scratchpad is the failure to watch for.
