---
id: A88
from: [O19]
source: owner
status: decided 2026-10-29
kind: rule
implemented_by: [global/CLAUDE.md, global/RATIONALE.md]
proven_by: [unproven]
supersedes: []
---

# A88 A typo is a mistake unless the owner says it is meant

A session reads a misspelled word in the owner's text as the word they meant, and never carries the misspelling into a name, a file, a commit or a reply. A typo found in the code or the documents is fixed, and a misspelled name is renamed through the typechecker. The owner's explicit word that a spelling is meant is the only exception.

## Context

The owner, on 2026-10-29: "Add a rule to global/CLAUDE.md that typos are never intentional unless explicitly recognized".

## Options

- A rule in the global rulebook (this one): every session in every project loads it.
- A hook that spell-checks the owner's prompts. Not taken: the rule costs a line, and a checker would flag the project's own terms.

## Consequences

A spelling the owner wants, such as a product's name, has to be said once. The rulebook grows by about 50 words.

## Proof

Unproven: no program checks it. A session that names a file or a function after a misspelled word of the owner's is the failure to watch for.
