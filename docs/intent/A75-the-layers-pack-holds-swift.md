---
id: A75
from: [O8, O7, O4]
source: owner
status: decided 2026-10-26
kind: check
implemented_by: [plugins/session-kit/codeintel/src/session_codeintel/layers.py, plugins/session-kit/codeintel/docs/api.md]
proven_by: [plugins/session-kit/codeintel/tests/test_layers.py]
supersedes: []
---

# A75 The layers pack holds Swift

`session-codeintel layers` writes the gate for a Swift project as it does for Python and TypeScript, from a `swift` block under `layers` in `.claude/claude-kit.json`: `core` and `shell` (directories), `tests` (the tests directory), `core_module` (the one module a test may import beyond `Testing`) and `source` (the tree `throw` is refused in, the core's parent by default). It writes four ast-grep rules with a test file each:

- `swift-core-imports-nothing`: no `import_declaration` in the core. The Swift core needs no Foundation, so no import at all is stricter than an allowlist and simpler.
- `swift-shell-declares-effects`: every `function_declaration` in the shell is immediately preceded by a `///` comment matching `Effects:`. The `Effects:` line has to be the last doc line. Modifiers such as `override` and `private` sit inside the declaration, so they do not break the adjacency.
- `swift-no-throw`: no `throw`, no `throws` and no `try?` or `try!` in the source. A plain `try` inside a do/catch stays allowed, so a system call that throws is caught where it is made.
- `swift-tests-import-only-the-core`: in the tests directory, every import matches `(@testable )import (Testing|<core_module>)`.

## Context

brain-dumping wrote the four rules for its own Swift gate (its `A6`), with the node kinds confirmed under the pinned ast-grep 0.45.3, and proposed them to the kit; it retires its copy once the kit ships them. Wiring them on a machine with only the Command Line Tools found three facts about the toolchain, which belong to the project and not to the pack: `swift test` needs swift-tools-version 6.4 (under 6.0 the Testing macros plugin is not found); SwiftPM passes the linker two `CommandLineTools/Developer` search paths that do not exist there, so a zero-warning gate has to filter exactly those `ld: warning: search path ... not found` lines, with the reason beside the filter; and swift-testing's `.timeLimit` takes whole minutes, so the global rule of a few seconds per test cannot be written and `.timeLimit(.minutes(1))` is the closest.

## Options

- The rules stay in each Swift project, as brain-dumping has them. They name the project's directories and module, the same four files copied per project, which `A31` argued against for the other languages.
- Settings that name all four paths (taken), against a convention (`Sources/<Core>`, `Tests`) the pack would assume. A convention fails silently on a project laid out otherwise, and the three Python and TypeScript blocks already name their paths.
- A tests directory and core module optional, the fourth rule skipped without them. Not taken: a Swift project without tests is not one that holds the shape, so the block is read only when all four are named, as `python` is read only with `core` and `shell`.

## Consequences

A Swift project names four paths and runs the command; the `sgconfig.yml` it writes, or the project's own, runs the rules with the `ast-grep` the package pins. The rules cover what ast-grep can see of the tree-sitter Swift grammar: a `throws` inside a closure type or a protocol requirement is flagged like any other, and the `Effects:` line must be the last doc line. The gate does not reach the toolchain facts above. Undone if the grammar's node kinds change under a new ast-grep pin, which the rules' own cases catch when the pin moves.
