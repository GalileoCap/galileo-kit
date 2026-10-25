---
id: A14
from: [O5, O8, O14]
source: session
status: decided 2026-10-12
kind: behaviour
implemented_by: [plugins/session-kit/bin, plugins/session-kit/codeintel, plugins/session-kit/tells]
proven_by: [plugins/session-kit/codeintel/scripts/test, plugins/session-kit/tells/scripts/test]
supersedes: []
---

# A14 The session-tells and session-codeintel commands

Two commands on the Bash tool's PATH: `session-tells` lists a file's prose tells, and `session-codeintel` runs the language-server shims and the `ast-grep` recipes a mechanical sweep starts from.

## Context

The rules ask for a tool that matches syntax and for a language server's view, and a plugin can put commands on PATH.

## Consequences

No cost per call. The shims are installed once per machine from the marketplace clone. Unchanged by the port.
