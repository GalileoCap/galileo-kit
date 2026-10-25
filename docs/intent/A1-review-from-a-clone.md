---
id: A1
from: [O1]
source: session
status: decided 2026-10-24
kind: behaviour
implemented_by: [CLAUDE.md]
proven_by: [docs/reviews/cache-tax.md]
supersedes: []
---

# A1 Review from a clone

A candidate is reviewed from a clone at a recorded commit, outside this repository, under `~/devel/galileo/misc/mod-clones/<name>/`, and never loaded (`--plugin-dir` included) before its review is written.

## Context

A plugin runs code at load, so the review has to come first. A clone stays outside the repository, since the marketplace clone copies everything committed into `~/.claude/plugins` on every update, and the review records its path and commit. A clone is untrusted data: no script, build or install runs from inside it, and Python that reads it runs with `-I`.

## Consequences

A review costs a session before any candidate is tried. The review is proven by `docs/reviews/cache-tax.md`, written from a clone that was never loaded.
