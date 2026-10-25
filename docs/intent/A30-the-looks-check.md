---
id: A30
from: [O8, O7]
source: session
status: decided 2026-10-25
kind: check
implemented_by: [plugins/session-kit/codeintel/src/session_codeintel/looks.py, plugins/session-kit/codeintel/src/session_codeintel/cli.py, plugins/session-kit/codeintel/docs/api.md]
proven_by: [plugins/session-kit/codeintel/tests/test_looks.py]
supersedes: []
---

# A30 The looks check

`session-codeintel looks` fails when a class string of two or more classes is written in two places under a project's source: in a `className` or `*ClassName` prop, an argument of `cn`, or a value of a `*-looks.ts` file. A look kept in one component or one looks file is written once, so a look found twice is one nothing names yet, and the fix is a component named for what it shows or an entry in a looks file. A look that repeats by coincidence is allowed under `looks.allowed` in `.claude/claude-kit.json`, with the files it is written in, and the check also fails when it spreads to another file or leaves one, so the entry is reviewed then. The sites come from three ast-grep rules run by the package's pinned binary.

## Context

generic-app wrote the check in TypeScript over the compiler's AST, with the allowlist as a typed TypeScript file, and the first project's console had the same disease without a check: fifty-three hand-made dialogs and a loading ladder in sixteen files. The 2026-10-25 reading named it the sixth tool to lift. The kit has no node environment of its own, and `session-codeintel` already pins ast-grep and tests rules through it, so the check moved there, as the analysis proposed.

## Options

- The TypeScript checker shipped as a node script, resolving `typescript` from the project checked. It would run in any frontend, and the kit could not test it without a node environment of its own. The ast-grep rules match the same sites, proven against the same cases.
- The allowlist as a TypeScript file in the project, typed, as generic-app keeps it. In the kit it is JSON under the settings file every other check reads, so a project carries one file for the kit.
- A looks file's values are all read, as generic-app reads them, so a label kept in a looks file by mistake is reported as a look. A looks file holds looks.

## Consequences

A project that takes the check names its source directory and the directories to skip (shadcn's `components/ui` by default), and keeps the allowlist itself, without asking the owner, as generic-app's rule says. The check reads TypeScript and TSX only. Undone if the allowlist grows faster than the components do, which would mean the rule is held against the wrong grain.
