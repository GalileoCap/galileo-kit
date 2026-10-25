---
id: A33
from: [O17, O8]
source: session
status: decided 2026-10-25
kind: check
implemented_by: [plugins/session-kit/codeintel/src/session_codeintel/measure.py, plugins/session-kit/codeintel/src/session_codeintel/cli.py, plugins/session-kit/codeintel/docs/api.md, docs/analyses/generic-app-impact-scripts.md]
proven_by: [plugins/session-kit/codeintel/tests/test_measure.py, docs/analyses/generic-app-impact-measure.md, docs/measurements/code-2026-10-25.md]
supersedes: []
---

# A33 The code measure

`session-codeintel measure` gives, per area and per snapshot, the size of the code (files, lines, code, comment and docstring lines), its complexity (McCabe per function: the count, the total, the mean, the functions at 6 or more and the maximum, with the JSX elements beside) and its repetition (the looks check's repeated class strings and their places), as a markdown report printed or written under `docs/measurements/`. A snapshot is the working tree or a `git archive` of a ref, so a change is argued from one row against the next. The areas come from `measure.areas` in the settings file or from the command line. The Python complexity comes from ruff's `C901` at cap zero, which made ruff a pinned runtime dependency of the package, and the TypeScript complexity from ast-grep, counting the branches inside the innermost function.

## Context

The system is observed and improved over time (`O17`), and the transcript tooling (`A22`) observes the sessions. This observes what the sessions produce. generic-app argued its conventions from these counts over five snapshots (2.6% less code, 16.5% less complexity, six defects turned into type errors), with three scripts in a session's scratchpad that the session's deletion took with it. On the owner's word they were rescued first, from an archived sibling's transcript, and kept under `docs/analyses/` as written, and the command was built from them.

## Options

- The TypeScript complexity on the compiler's AST, as the rescued script did. That needs node and the project's `typescript`, which the kit does not have, and ast-grep counts the same nodes from the same grammar, attributed to the innermost function by byte range.
- A McCabe of the kit's own for Python, with no ruff. It would diverge from the figure every project's gate already reports, and ruff pinned is the figure generic-app's report used.
- Writing under `docs/measurements/` by default, as the transcript report does. The measure prints unless `--out` is given, since a measure is read first and kept when it argues something.

## Proof

Run over generic-app at the two snapshots its impact report compares, the command gives the report's figures: the code lines to the line, the Python functions and their complexity to the function, the frontend's functions and totals likewise, with the JSX elements 13 higher for the fragments tree-sitter counts as elements. The kit's own first measure is `docs/measurements/code-2026-10-25.md`, from the remote's main to the head of this work.

## Consequences

The package pins a third tool, and its version moves with the lock. The TypeScript line scan counts a `//` inside a string as a comment and a one-line block comment as one comment line, the same as the rescued script, so the rows stay comparable with generic-app's report. The repeated looks are counted only when the project has a `looks` block. Undone if the numbers are never read against each other, which would mean the measure runs once and never again.
