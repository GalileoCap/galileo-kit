---
id: A24
from: [O18]
source: owner
status: decided 2026-10-25
kind: behaviour
implemented_by: [plugins/session-kit/hooks/reference.ts, plugins/session-kit/hooks/kit.tsx]
proven_by: [plugins/session-kit/hooks/reference.test.tsx]
supersedes: []
---

# A24 The reference mod

A hooks module of `session-kit` that draws the name beside each intent id in a reply, on the screen alone. The engine's `ui.render` hook on `AssistantMessage` rewrites a reply's drawn text and leaves the stored message untouched, so `A20` is drawn as `A20` (one module per concern) with no change to what the model wrote or to the transcript. The names come from the project's generated `INDEX.md`, under `intent.directory` in `.claude/claude-kit.json`, read again only when its modification time moves. An id is named at its first mention in each block of a reply. It is drawn as written when the model already named it there (the name's first words in the sentence, an aside after a comma, or a parenthesis right after it), when it stands in a code block, a path or a file name, and when the index does not hold it.

## Context

The owner proposed it on 2026-10-25, as the alternative to a rule: "a mod identifies references and either automatically adds the name, or adds the UI for me to look them up quickly", and the same day widened it: "our mod should be extensible for this (eg: each project carries a settings file detailing the naming schema and pointing at the source directories)". The rule (`A23`, an id carries its name) depends on the model keeping it. The mod does not.

## Options

- Draw the name inline beside the id. One hook, no interaction, reads on every surface. Chosen.
- A pane listing the entries, opened by a command. More to build, and it needs the owner to look away from the reply. The index already gives the list.
- Rewriting the reply's stored text. The engine does not offer it, and the record should hold what the model wrote.

## Consequences

Built on 2026-11-18, by the owner's word that `A23` (an id carries its name) is often not kept. The `references` setting for other kinds of id (an issue tracker's, printed by a command) waits for a project that has a second kind, since the intent is the only one today. In this repository, which alone writes about other projects' entries, an id of tagents' is drawn with this kit's name for the same id. The owner judged that rare and accepted it on 2026-11-18.

The drawing costs one read of `INDEX.md` after each change to it, and a check of its modification time per drawn block. An id the index does not hold is drawn as written. A stale `INDEX.md` gives a new entry no name until `session-intent index` runs, which `session-intent check` already demands. Only a real session shows the drawing: the engine's tests prove the text it hands the surface.
