---
id: A29
from: [O8, O12]
source: session
status: decided 2026-10-25
kind: check
implemented_by: [plugins/session-kit/docs_check/session_docs.py, plugins/session-kit/bin/session-docs, global/CLAUDE.md]
proven_by: [plugins/session-kit/docs_check/test_session_docs.py]
supersedes: []
---

# A29 The docs check

`session-docs check` reads every markdown file under the project's documents directory and fails on one that the index does not name, and on a document the index names that does not exist. An index names a document by writing its path, or the path of a directory above it with its trailing slash, which covers a set of files one line describes: the intent entries, the reviews, the measurements. The documents directory alone covers nothing, and a path inside a fenced code block is an example. A project sets the directory and the indexes under `docs` in `.claude/claude-kit.json`. The default is `docs/` and `CLAUDE.md`.

## Context

A project's document list rots in both directions: a file is added and the line that would send a reader to it is never written, or the file is renamed and the line stays. generic-app held the first direction with a shell loop in its justfile, over `CLAUDE.md` and the README together. The kit's own `CLAUDE.md` keeps its list by hand, and the 2026-10-25 reading of the two projects named the check as the fifth tool to lift. Run over the kit, it found all 65 documents named.

## Options

- A link only (`](docs/x.md)`), as generic-app matched. The kit's `CLAUDE.md` names documents in backticks and names whole directories, so the check reads any mention of the path, and a directory's.
- Every index naming every document, or any one of them. Each index named in the settings must name every document, as generic-app wants of both its files. The default names `CLAUDE.md` alone, since a README is written for another reader.
- The second direction, a named document that is gone, was not in generic-app's loop. Added, since a dangling path is how a stale line announces itself, with fenced code skipped so an example is not a line.

## Consequences

A document the index should not list, a scratch file under `docs/`, fails the check until it is named or moved, which is the point. A mention in running prose counts as naming, so a document named once in passing passes. The check holds that a reader can find the document, and leaves whether the line describes it to the reader. Undone if projects keep their lists elsewhere than in the files the check reads, which a setting would then name.
