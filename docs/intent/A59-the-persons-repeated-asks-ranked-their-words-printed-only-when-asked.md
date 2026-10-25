---
id: A59
from: [O5, O17]
source: session
status: decided 2026-10-25
kind: check
implemented_by: [plugins/session-kit/transcripts/records.py, plugins/session-kit/transcripts/session_transcripts.py]
proven_by: [plugins/session-kit/transcripts/test_session_transcripts.py]
supersedes: []
---

# A59 The person's repeated asks, ranked, their words printed only when asked

`session-transcripts asks` ranks what the person asks again and again over the sessions read. An ask is a prompt of the person's own: a record whose origin is the person's, or that has none as before the engine wrote origins, and whose text is no command's markup, counted once. A plugin's, a notification's and a peer's prompts are left out. Two prompts are one ask when 70% or more of the words of both are shared, lower-cased with each run of digits one word, and a run of such pairs is one ask. The top twenty asks made more than once are ranked by prompts, then by sessions, each with its sessions, projects, length in words and first and last day. Their words are printed only with `--quote`, the most common wording of each cut at 80 characters, and never in the report.

## Context

`docs/analyses/mods-for-the-kit.md`, M20, from mod-maker's `/mod-audit`. `O5` (every step has a kind and moves to a program wherever one can do it) needs to know which steps the owner repeats, and the record of what they typed is in the transcripts. `A22`'s reader prints no prompt and no answer unless `--quote` is passed, which this keeps. Reading the prompts showed the engine writes some records several times, a prompt up to eight times, and that the reader counted a compaction's summary and the engine's meta records as prompts. Both are fixed in the reader with this.

## Options

- The same ask only when the words are the same. Rejected: an ask retyped with a word changed is the same ask.
- A model, or embeddings, grouping the prompts. Rejected: `A22` keeps a model out of the reader, and the reader is standard library alone.
- Every two prompts compared. Rejected: the count grows with the square of the prompts, and the archive holds thousands. A prefix of each prompt's rarest words finds every pair that alike (prefix filtering).
- The words printed by default. Rejected: the transcripts are the owner's words, and `A22` prints none of them unless asked.

## Consequences

The first run, over the 59 transcripts on disk: 737 prompts of the person's, 75 asks made more than once, the first a four-word ask made 52 times over 25 sessions in 11 projects. What each is, and whether a program should take it, is the owner's reading with `--quote`. A long ask that differs in more than three words of ten, or a short one in a single word of three, is a different ask. The plugin's own prompts, such as the chain's continue, are left out by their origin, so they are not counted against the person.

## Proof

The ranking was proved by cases written before the code and deleted once it passed, as blind tests. Kept in `test_session_transcripts.py`, as a rule whose failure is silent and costly: the asks are ranked over the sessions, a prompt written twice and a plugin's or a notification's prompt of the same words left out, and none of their words is printed without `--quote`. Kept as a regression: a prompt the engine wrote twice is counted once. Run on the 59 transcripts on disk without `--quote`, and with it into a scratch file to see the words column drawn.
