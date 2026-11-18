---
id: A105
from: [O26]
source: session
status: decided 2026-11-18
kind: behaviour
implemented_by: [plugins/session-kit/reread/src/session_reread/sections.py, plugins/session-kit/reread/src/session_reread/baseline.py, plugins/session-kit/reread/src/session_reread/page.py, plugins/session-kit/reread/src/session_reread/cli.py, plugins/session-kit/bin/session-reread]
proven_by: [plugins/session-kit/reread/tests/test_reread.py]
supersedes: []
---

# A105 session-reread sorts a document's sections by what changed since the owner read it

`session-reread [files]` compares each Markdown file with the version the owner last read and writes a page under `~/.claude/session-kit/reread/`, printing a summary per file and the page's path (`--open` opens it). A section is a heading and its own body, at every depth, so a subsection's change is its own and a parent's verdict covers only its own text. A YAML front matter block and the text before the first heading are sections too. Old and new sections pair by heading path, then by heading alone, then by the likeness of their bodies, so a renamed or moved section is not taken for one removed and one new. Bodies compare word by word, so a paragraph wrapped again is unchanged.

Each section gets one verdict: unchanged, moved, renamed (skip), edited (the changed blocks rendered with words struck and marked, a table's changed rows alone, the whole section folded below), rewritten past `--threshold`'s share of words changed, 0.4 by default, or new (read whole), and removed (its text folded, to check nothing wanted went).

The baseline, by default, is the commit HEAD was on when the owner's prompt opened the latest turn that committed to the files, the prompt times read from the session's transcript and HEAD's position from the reflog. A later prompt, such as asking what changed, commits nothing and leaves the baseline alone. `--since <ref>` overrides it, and the page and summary say which was used and why. With no files, every Markdown file differing from the baseline counts, untracked ones included.

## Context

The owner's need (`O26`, after an agent edits a document I reviewed, I know which parts to read again): reviewing a spec a session revised, git's line diff is hard to read and worst when sections are moved or rewritten, and asking the session costs a round and rests on its account. The owner approved the design on 2026-11-18 with the recommendations: the baseline from the prompt, a page in the browser, Markdown only. The rule "the turn that last committed" replaced "the last prompt" when writing it, since the owner's next prompt often asks what changed.

## Options

- A snapshot the owner takes with a `mark` command after reading. Exact, but one more step each round, and forgotten once is a wrong baseline with no sign.
- Claude Code's file history, which keeps each file as it was before a turn's edits, uncommitted states included. Rejected for now: an undocumented format, and it misses edits made through the shell.
- A line diff of the rendered text. Rejected: a reflowed paragraph shows as changed, and a moved section as one removed and one added.

## Consequences

An edit left uncommitted when the owner reads is not in the baseline, so a session that does not commit before handing back shows the owner more than they need. The threshold is a guess, shown with each verdict's share so the owner can move it. Undone if the owner keeps reading whole files after using it.
