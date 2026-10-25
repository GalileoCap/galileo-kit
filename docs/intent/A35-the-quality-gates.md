---
id: A35
from: [O8, O3]
source: session
status: decided 2026-10-25
kind: check
implemented_by: [plugins/session-kit/codeintel/src/session_codeintel/quality.py, plugins/session-kit/codeintel/src/session_codeintel/facts.py, plugins/session-kit/codeintel/src/session_codeintel/fallbacks.py, plugins/session-kit/codeintel/src/session_codeintel/cli.py, plugins/session-kit/codeintel/docs/api.md, global/CODE.md, quality-ledger.toml]
proven_by: [plugins/session-kit/codeintel/tests/test_quality.py, quality-ledger.toml]
supersedes: []
---

# A35 The quality gates

`session-codeintel quality` runs three gates over the Python files of the areas a project names under `quality.areas` in `.claude/claude-kit.json`: the duplicate gate (a function body written twice fails, at any length under one name and at three statements under different names, dunders and the methods a `Protocol` declares aside), the fallback finder (`x or v`, `.get(k, v)`, `getattr(o, n, v)`, a broad `except`, an `except` that returns a literal or swallows, and `if x is None: x = v` in both spellings, each a substitution the caller cannot see, outside the tests), and the file-length lint (a file over 500 code lines, unless a `long` entry raises or lifts its cap with a reason). The finder lists and the ledger judges: `quality-ledger.toml` names every family with its home and every site with its class (`declared`, `spoken`, `silent`, `refusal-class`) and disposition, the gate fails on a site it does not name and on a row nothing matches, and a row it cannot read refuses the ledger whole, a `dead` class included. `--report` prints the rows to fill in.

## Context

tagents wrote the gates after a census found 150 function names defined in more than one module and about eighty `or` substitutions, some choosing an identity or a permission level, and its code-quality rulebook names the pitfalls behind them: a model that re-derives what exists, copies the nearest pattern, adds a default to quiet a type checker. The 2026-10-25 reading named the gates as the fifth tool to lift, and the owner chose the order. Quality is held by gates at zero warnings so the owner reviews substance (`O8`), and a project owns its copy of the rule (`O3`): here the rule is in `global/CODE.md` and the judgement in the project's own ledger.

## Options

- jscpd for the duplicates and ast-grep rules for the fallbacks, as tagents' own abstraction note proposed. jscpd needs node, and an ast-grep rule cannot tell a literal substitute from a computed one or an `or` in test position from one in a body, which the syntax-tree finder tells and tagents measured. The finder is ported as written, read on `ast`.
- The code map (`CODEMAP.md` from `codemap.toml`, the hand-held half naming each module's system). The analysis said it does not generalise, and the kit's documents check and intent index cover what it covered for the kit. Not taken.
- One ledger per package, as tagents keeps it. The kit runs the gate over a root with areas, so one ledger per root, keyed by paths from the root, and a package that is its own root keeps its own.
- A `dead` class, for a fallback the types prove unreachable. tagents refuses it after one word had two rules, and here it is not a class the ledger reads, with the message saying a dead fallback is removed and not judged.

## Proof

Over the planted package the gate sees two copies and nothing else, each of the eleven planted forms once and the four shapes that look like them not at all, holds the ledger both ways with counts, and refuses a misspelt disposition, an unknown key and a dead class. Over the kit its first run named the three copies of the settings guards in `looks.py`, `layers.py` and `measure.py`, which became `settings.py`, and the `tree` helper of three tests, which moved into `tests/tools.py`. The kit's ledger holds 142 judged sites and four duplicate rows kept (the standalone test harnesses of the standard-library commands), six sites raised as findings for the owner: the guard letting an amend through when git cannot answer, a settings file that does not parse dropping the test commands, a looks allowance accepted without a reason, a file the tokenizer refuses counted short, an unreadable file searched for no marker, a transcript line that is not JSON skipped uncounted.

## Consequences

A project that takes the gate seeds its ledger on day one from `--report` and judges every row, which is the cost tagents paid per package. The forms are Python's: a TypeScript finder waits for a project that asks, and would be a second reader over the same ledger. The kit's own gate runs in its static legs. Undone if the ledgers grow instead of shrink, which would mean the rows are written to pass the gate and not to judge.
