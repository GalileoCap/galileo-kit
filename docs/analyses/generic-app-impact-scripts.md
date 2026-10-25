# generic-app's impact scripts, rescued

The three scripts behind generic-app's `CONVENTIONS-IMPACT.md` (its measurements of size, complexity and repeated looks over five snapshots of the project) were written in a session's scratchpad on 2026-10-24, and that session was deleted the same day. On 2026-10-25 they were read back out of the archived transcript of a sibling session (`~/claude-archive/-Users-galileo-devel-galileo-misc-generic-app/09c4e654-8f56-4d62-9204-2a729a26dfe2.tar.xz`), from the Bash heredocs that wrote them, and are kept beside this file as written, in `generic-app-impact-scripts/`:

- `size.py <snapshot>`: files, lines, code, comment and docstring lines per area. Python through the tokenizer and `ast` (a docstring is the first expression of a module, class or function), TypeScript by a line scan, YAML by a line scan.
- `cc-ts.cjs <typescript module> <src>`: McCabe complexity per function over the TypeScript compiler's AST, counting `if`, `?:`, loops, `case`, `catch`, `&&`, `||` and `??`, with the JSX elements counted beside, over every `.ts` and `.tsx` outside `ui/` and the tests.
- `looks-count.ts <repeated-looks.ts> <src>`: the repeated looks and their places, through generic-app's own checker.

The Python complexity came from ruff's `C901` with `lint.mccabe.max-complexity = 0`, run with `--output-format json --exit-zero` over each snapshot's `backend/src` and `backend/tests`. Each snapshot was a `git archive` of its commit.

They are the input to `session-codeintel measure` (`A33`), which does the same over any project from its settings, and they can go once generic-app's impact report names that command instead of the directory that is gone.
