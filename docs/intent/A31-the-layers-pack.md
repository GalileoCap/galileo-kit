---
id: A31
from: [O8, O7, O4]
source: session
status: decided 2026-10-25
kind: check
implemented_by: [plugins/session-kit/codeintel/src/session_codeintel/layers.py, plugins/session-kit/codeintel/src/session_codeintel/cli.py, plugins/session-kit/codeintel/docs/api.md]
proven_by: [plugins/session-kit/codeintel/tests/test_layers.py]
supersedes: []
---

# A31 The layers pack

`session-codeintel layers` writes the gate that holds the pure-core shape, from the layers a project names under `layers` in `.claude/claude-kit.json`: for Python, the core and shell directories, the tree `raise` is refused in and the files that may unwind, and for TypeScript, the core and effects directories and the import prefixes the core may not use. It writes seven ast-grep rules with a test file each (no I/O, clock, randomness or `await` in the core, every shell function naming its effects, no `raise` outside the unwinding files, no effect global, framework or outside import in the TypeScript core), a `ruff.toml` in the Python core that bans the effect modules and extends the nearest config above, and an `sgconfig.yml` when the project has none. Every file carries a header naming the command, and a file without it is never replaced.

## Context

generic-app holds the shape with thirty-one ast-grep rules, a nested `ruff.toml` and an ESLint block, each naming the project's own paths. The five rules that define the shape are the same in any project that takes it, and only the paths differ. The 2026-10-25 reading named the pack as the seventh tool to lift, and the owner chose it on the same day with the code-shape rules as an opt-in `global/CODE.md`.

## Options

- Rules the project copies and retargets by hand, as the recipes are. A rule copied once drifts from the pack, and the paths appear in each of seven files. A generator keeps the paths in one place and the rules current with the pack.
- The TypeScript core's purity as the ESLint block generic-app wrote. An ESLint config is the project's code, and a generated block inside it would be a merge. The same bans are one ast-grep rule, run by the binary the package already pins, and ESLint's scope-aware globals rule is given up: `location` and `history` are left out of the list because a parameter of that name would be flagged.
- The `*-through-*` rules, "X has one home". They name the project's vocabulary, and the pack has no shape for them yet. A rule generator for that shape waits for a second project with such rules.

## Consequences

A project that takes the pack keeps its settings in one block and runs the command after changing them. A file the project wrote by hand under the same name is refused, so a project that already has the rules moves them aside or lets the command replace its own. The core's `ruff.toml` extends the nearest config above it, which the Python project has to keep at or above the core. Undone if projects edit the generated rules instead of the settings, which the header and the refusal make visible.
