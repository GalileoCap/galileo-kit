---
id: A13
from: [O14]
source: session
status: decided 2026-10-11
kind: behaviour
implemented_by: [plugins/session-kit/hooks/pyright_env.py, plugins/session-kit/hooks/hooks.json]
proven_by: [plugins/session-kit/hooks/test_pyright_env.py]
supersedes: []
---

# A13 A root pyrightconfig for multi-package repositories

On SessionStart, when the project asks for it, a hook writes a root `pyrightconfig.json` that gives the language server one view over every package.

## Context

A multi-package repository has no root config, and the language server sees one package at a time.

## Consequences

Once per session. Off unless the project asks, since it replaces a root config. Stays a settings hook.
