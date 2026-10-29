---
id: A80
from: [O3]
source: owner
status: decided 2026-10-29
kind: behaviour
implemented_by: [global/install.sh, global/CLAUDE.md, global/RATIONALE.md]
proven_by: [global/test_install.sh]
supersedes: [A15]
---

# A80 The global rules, imported into the user's own CLAUDE.md

The rules every project follows live in `global/CLAUDE.md`, with each rule's reason under the same heading in `global/RATIONALE.md`. `install.sh` adds the line `@<kit>/global/CLAUDE.md` to `~/.claude/CLAUDE.md`: it writes the file when there is none, appends the line to a file that lacks it, and replaces the old link with a file holding the line. The rest of that file is the machine's own.

The owner's words, 2026-10-29: "Switch to import, and install should handle the case where the file already exists (appending our import)", after asking how to add global rules specific to one machine.

## Context

A plugin cannot ship a `CLAUDE.md`, so the rules reach every session through `~/.claude/CLAUDE.md`. Under `A15` that file was a link to `global/CLAUDE.md`, so it was the repository's file: a rule for one machine had nowhere to go, and anything written to it was committed and pushed to every machine.

## Options

- The link (`A15`): serves `O3` (rules are written once in this repository), and leaves no place for a machine's own rules.
- A file under `~/.claude/rules/` beside the link: Claude Code loads it in every project, and `session-rulebook` does not count it, so its words escape the budget.
- The import (taken): serves `O3`, the machine's rules sit in the same file, and `session-rulebook` counts both, since it follows `@` lines.

## Consequences

A link pointing anywhere else is left alone with the line printed, since appending would write into its target. The import names the working copy, as the link did, so an uncommitted edit to `global/CLAUDE.md` reaches this machine's sessions at once. Each machine installed under `A15` runs `install.sh` once (`OWED.md`). Undone if the engine stops loading `@` lines from the user's file, or asks for approval of the import in every session. Validated when a session started after the install is seen loading `global/CLAUDE.md` through the import: on 2026-10-29 a headless `claude -p` could not reach the API (an SSL certificate error), so that run is still owed.
