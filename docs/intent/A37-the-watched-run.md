---
id: A37
from: [O6, O13, O4]
source: session
status: decided 2026-10-25
kind: tool
implemented_by: [plugins/session-kit/bin/session-watched, global/CLAUDE.md]
proven_by: [plugins/session-kit/lib/test_watched.sh]
supersedes: []
---

# A37 The watched run

`session-watched -- <command>` runs a command and decides every few minutes whether to go on. Progress is CPU spent anywhere in the command's process tree, a process in it starting or ending, or its output growing when it goes to a file. After five minutes with none (`--stall`), it writes the tree as it stood and a stack sample of each process, ends the tree and exits 125, which is no verdict on the code. Every five minutes (`--check`) it says it has decided to go on and on what evidence. With `--warn` it writes the diagnostics and goes on, for a command that changes a remote host. The command sees `SESSION_WATCHED=1`, so a script that wraps itself does not wrap twice. The global rule says a run that may last goes through it.

## Context

tagents wrote the script after a proof stalled at 98% for forty-five minutes with every worker idle, holding the test slot, and the owner ruled that no script lasts over five minutes without an active decision. The 2026-10-25 reading named it the sixth tool, since any long run a session starts, in any project, can hang the same way, and the Bash tool's own timeout kills without diagnostics. A step that matters leaves a record a program wrote (`O6`), and here the record is the diagnostics directory.

## Options

- The test log hook running every test command through the wrapper. The hook would have to rewrite the Bash command string and quote it for a child shell, and the tool's own timeout runs regardless, so the wrapper is a command the session calls, held by a rule, until a real session shows the rule is not read.
- A stall setting in `.claude/claude-kit.json`. The environment variables and the options cover it, and a project that wants a default writes it in its own script's header, as tagents' scripts do.
- The lines reworded from tagents' so the tells gate reads them as the kit's own.

## Proof

Seventeen cases: the exit status and output pass through, the command is told it is watched, a stalled sleep is ended with 125 and its tree listed and gone, output growing into a file and a process starting each count as progress, `--warn` leaves a stalled run alone and warns, the check line is said, the label names the run. Not run inside a real session over a real test tier.

## Consequences

A long run reports its stall once instead of the tool's timeout reporting nothing. The wrapper needs `ps`, `awk` and `python3`, and `sample` where macOS has it. Undone if sessions do not reach for it, which would mean the hook was needed after all.
