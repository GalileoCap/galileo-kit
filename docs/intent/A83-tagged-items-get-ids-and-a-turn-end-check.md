---
id: A83
from: [O19]
source: owner
status: decided 2026-10-29
kind: check
implemented_by: [plugins/session-kit/hooks/tags.ts, plugins/session-kit/hooks/band.tsx]
proven_by: [plugins/session-kit/hooks/tags.test.tsx, OWED.md]
supersedes: []
---

# A83 Tagged items get ids from the kit, and the turn's end checks each has a line

At `prompt.submit`, the kit parses the person's tagged lines, gives each `Do`, `Decide`, `Ask` and `Later` item an id of the tag word, a hyphen and a number (`Do-1`), and attaches the list as hidden context with the closing-line forms. Lines in pasted content or a fenced block open no items. The counter runs per tag across the session, so an item open across turns keeps its id, and a clear starts the counts over. At the end of the turn the kit reads the reply's lines that start with an id. An `In progress` line keeps its item open, and any other line closes it. An item with no line gets a band row and, once per item, a prompt asking the session to report it or say why not. The check stands aside while the chain or a new-task offer is under way.

## Context

The owner's decision of 2026-10-29, from a side chat: match by an id the kit assigns. The item's first words, the proposal's key, break on a paraphrase, a translation or two items merged. One letter and digits would clash with the intent ids (`A1`, `C1`) and with `M27`, `T8` and `Q4` in the analyses. The word-hyphen-number shape matches neither. The ids stay visible in the reply, so the owner can refer back ("Do-3 isn't done") without ever writing one.

## Options

- Match on tag, order and first words, as proposed. Not taken, for the reasons above.
- Ids the kit assigns, quoted at the start of each closing line. Taken.

## Consequences

The check adds a turn when it prompts, at most once per item. A session that drops the id from a line it did write is prompted for it. Undone if the prompts on items the reply did address pass one in twenty.
