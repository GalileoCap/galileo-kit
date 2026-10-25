---
id: O14
from: [G3, G4]
source: inferred
status: proposed 2026-10-24
---

# O14 Commands run with the project's own tools

A command a session runs uses the project's own tools and configuration: its direnv environment, its formatters, its language-server view.

## Changes

The environment of each command a session runs, and the formatter and checker a change is held to.

## Known by

A command a session runs gives the same result as the owner's shell: same environment, same formatter, same checker configuration. A difference between the two is a defect of the kit.

Inferred from `direnv_env.sh`, `format.py` and `pyright_env.py`. Folded from `session-kit`'s ladder, where it was proposed under "improve performance" and "consistent and good across projects".
