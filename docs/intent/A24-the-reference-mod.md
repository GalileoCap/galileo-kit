---
id: A24
from: [O18]
source: owner
status: decided 2026-10-25
kind: behaviour
implemented_by: not yet built
proven_by: unproven
supersedes: []
---

# A24 The reference mod

A hooks module of `session-kit` that draws the name beside every intent id in a reply, on the screen alone. The engine's `ui.render` hook on `AssistantMessage` rewrites a reply's drawn text and leaves the stored message untouched, so `A20` is drawn as `A20 (one module per concern)` with no change to what the model wrote or to the transcript. The names come from the project's `docs/intent/` through the engine's file access, read once per turn.

## Context

The owner proposed it on 2026-10-25, as the alternative to a rule: "a mod identifies references and either automatically adds the name, or adds the UI for me to look them up quickly". The rule (`A23`, an id carries its name) depends on the model keeping it. The mod does not.

## Options

- Draw the name inline beside the id. One hook, no interaction, reads on every surface. Chosen.
- A pane listing the entries, opened by a command. More to build, and it needs the owner to look away from the reply. The index already gives the list.
- Rewriting the reply's stored text. The engine does not offer it, and the record should hold what the model wrote.

## Consequences

The drawing costs a read of the intent directory per turn. An id the directory does not know is drawn as written. It is built after the real-session run of the modules already waiting, since the display hook is unproven in this kit and one more untested module adds nothing until the first one runs.
