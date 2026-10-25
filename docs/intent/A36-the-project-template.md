---
id: A36
from: [O4, O8, O3]
source: session
status: decided 2026-10-25
kind: tool
implemented_by: [plugins/session-kit/codeintel/src/session_codeintel/template.py, plugins/session-kit/codeintel/src/session_codeintel/template/python, plugins/session-kit/codeintel/src/session_codeintel/cli.py, plugins/session-kit/codeintel/docs/api.md]
proven_by: [plugins/session-kit/codeintel/tests/test_template.py, plugins/session-kit/codeintel/scripts/check, plugins/session-kit/tells/scripts/check]
supersedes: []
---

# A36 The project template

`session-codeintel template` carries the quality bar as three base files the template owns, `ruff.base.toml` (every rule, the four ignores with their reasons, the complexity and size caps), `pyright.base.json` (strict) and `scripts/check.base.sh` (the formatter's check, ruff, basedpyright at zero warnings, every leg run), which a project's own `pyproject.toml`, `pyrightconfig.json` and `scripts/check` extend with the project's exceptions, each with its reason. `new` writes the base files and the project's starting files into a directory, leaving every file the project already has alone, so an existing project takes the bar the same way. `refresh` writes the base files back when the bar moves. `check` fails on a base file that differs or is missing, on a project file that no longer extends its base, and on a ruff `select` or `per-file-ignores` that would discard the base's, and runs in the project's gate.

## Context

A family of projects shares its bar by copying, and each copy drifts: the kit's two packages carried the same forty lines of ruff and pyright settings with a comment saying where they came from. tagents' `abstract-template` states the bar once, after measuring that a template which shares a file with the project conflicts on every merge and one that owns base files does not. A tool useful to every project reaches each through the marketplace (`O4`), and the bar is the gate behind `O8`.

## Options

- copier, as abstract-template renders with. The base files are verbatim and the project files need three substitutions, so the standard library's `string.Template` does it, and the package gains no dependency. copier's `update` merge is not needed, since the base files are replaced whole and the project files never touched after `new`.
- The three kinds (python, console, library). The console and library kinds are tagents' frontend stack, and no project of the kit's takes them yet, so the Python kind alone, and a kind is added when a project asks.
- The base gate stopping at its first red leg, as tagents' does. Every leg runs and the status accumulates, so one run shows every failure there is, which is the kit's own gates' shape.

## Proof

A fresh project passes ruff, the formatter's check and basedpyright strict as written. `check` names each way a project leaves the bar, in the test and over a project edited by hand. The kit's two packages took the base files in the same change: their `pyproject.toml` now extends `ruff.base.toml` with an empty `ignore`, their checker settings moved into `pyrightconfig.json` extending the base, and each gate runs the base legs and the drift check, green on both.

## Consequences

A change to the bar is one edit to the template and a `refresh` in each project, held by `check` in its gate. A project reaches the command through the pinned wrapper the package's README gives. The five pages a new project gets are headings to fill. Undone if projects edit the base files in place and silence `check`, which would mean the bar belongs to each project after all.
