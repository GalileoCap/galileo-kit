---
id: A41
from: [O8, O16]
source: owner
status: decided 2026-10-25
kind: check
implemented_by: [plugins/session-kit/tells/src/session_tells/rules.py, global/CLAUDE.md]
proven_by: [plugins/session-kit/tells/tests/test_rules_and_readers.py]
supersedes: []
---

# A41 History is a tell

A document or a comment that places a fact in time, saying what stopped being done, what was done before, or what replaced what, describes a moment instead of what holds, and a model reading it has to work out which half is current. The `history-now` rule of `session-tells` bans seven such phrases, listed in the rule with the sentences it must catch and leave, in every kind of text, beside the rules that ban an issue number, a date and the `used to` phrase in the text a user reads and in comments. The sentence in `global/CLAUDE.md` about the refused rules says they hold whether or not they are read.

## Context

The owner, reading `docs/what-reaches-the-model.md`, found the loaded rules describing things that had stopped being done, which is useless to a session and confuses it, and named the habit: a model writes a document as if telling the person what changed since last time. The tells engine already held the history rules for codes and dates, and this is the same habit in words.

## Options

- Only in comments and the texts a user reads, as the other history rules. The owner's example was the rules file, a document, so this rule reads every kind of text, with a narrow list of phrases so a record that cites what was done is not caught by a common word.

## Consequences

A touched document with such a sentence fails the hook until the sentence says what holds. Undone if the phrases turn out to be needed in records, which would narrow the rule back to comments and guides.
