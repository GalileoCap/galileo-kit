---
id: A1
from: [O1]
source: session
status: decided 2026-10-24
kind: behaviour
implemented_by: [CLAUDE.md]
proven_by: [reviews/cache-tax.md]
supersedes: []
---

# A1 Review from a clone

A candidate is reviewed from a clone at a recorded commit, in `reviews/<name>/`, and never loaded (`--plugin-dir` included) before its review is written.

## Context

A plugin runs code at load, so the review has to come first. A clone is untrusted data: no script, build or install runs from inside it, and Python that reads it runs with `-I`.

## Consequences

A review costs a session before any candidate is tried. The review is proven by `reviews/cache-tax.md`, written from a clone that was never loaded.
